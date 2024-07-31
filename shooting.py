import socketio
import requests
from picamera2 import Picamera2
from io import BytesIO
import time
from datetime import datetime
import pytz

# Create a Socket.IO client
sio = socketio.Client(logger=True, engineio_logger=True)

# Initialize the Pi Cameras
cameras = []
camera_ids = []

# Function to initialize a camera
def initialize_camera(camera_id):
    try:
        camera = Picamera2()
        camera_config = camera.create_still_configuration(main={"size": (3280, 2464)})
        camera.configure(camera_config)
        camera.start()
        time.sleep(1)  # Ensure the camera is properly initialized and available
        camera.stop()  # Properly release the camera
        cameras.append(camera)
        camera_ids.append(camera_id)
        print(f"{camera_id} initialized")
    except Exception as e:
        print(f"{camera_id} not initialized: {e}")

# Initialize cameras
initialize_camera('camera1')
#initialize_camera('camera2')

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

def capture_image(camera):
    try:
        stream = BytesIO()
        camera.start()
        # Give the camera some time to adjust to lighting conditions
        time.sleep(0.5)
        print("Capturing image...")
        camera.capture_file(stream, format='jpeg')
        stream.seek(0)
        camera.stop()
        print("Image captured")
        return stream.read()
    except Exception as e:
        print(f"Error capturing image: {e}")
        return None

def send_image(image_data, folder_name, camera_id):
    if image_data is None:
        print(f"Skipping send_image for {camera_id} due to previous error.")
        return
    url = 'https://snapcmd.carlery.xyz/upload_image'  # Ensure this is the correct server URL
    files = {'image': ('image.jpeg', image_data, 'image/jpeg')}
    data = {
        'session_id': 'session123',  # Replace with actual session ID
        'camera_id': camera_id,      # Camera ID
        'start_time': datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'folder_name': folder_name
    }
    try:
        print(f"Sending image from {camera_id} to server...")
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(f'Server response: {response.json()}')
    except requests.exceptions.RequestException as e:
        print(f"Failed to send image to server from {camera_id}: {e}")
        if e.response is not None:
            print(f"Response content: {e.response.content}")

# Event handler for connection
@sio.event
def connect():
    print('Connected to broadcast server')

# Event handler for disconnection
@sio.event
def disconnect():
    print('Disconnected from broadcast server')

# Event handler for receiving capture request
@sio.event
def capture_request(data):
    print('Capture request received:', data)
    folder_name = data['folder_name']
    try:
        for camera, camera_id in zip(cameras, camera_ids):
            image_data = capture_image(camera)
            print(f"Captured image size from {camera_id}: {len(image_data) if image_data else 'None'} bytes")
            send_image(image_data, folder_name, camera_id)
    except Exception as e:
        print(f"Error during image capture or sending: {e}")

if __name__ == '__main__':
    try:
        # Connect to the broadcast server
        print("Connecting to broadcast server...")
        sio.connect('http://localhost:5000')  # Use the correct broadcast server address
        sio.wait()
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}")
