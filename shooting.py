import socketio
import requests
from picamera2 import Picamera2
from io import BytesIO
import time
from datetime import datetime
import pytz
import logging

# Configure logging
logging.basicConfig(filename='/home/admin/Desktop/shooting.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

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
        logging.info(f"{camera_id} initialized")
    except Exception as e:
        logging.error(f"{camera_id} not initialized: {e}")

# Initialize cameras
initialize_camera('camera1')
#initialize_camera('camera2')

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

def capture_image(camera):
    retries = 3
    for attempt in range(retries):
        try:
            stream = BytesIO()
            camera.start()
            # Give the camera some time to adjust to lighting conditions
            time.sleep(0.5)
            logging.info("Capturing image...")
            camera.capture_file(stream, format='jpeg')
            stream.seek(0)
            camera.stop()
            logging.info("Image captured")
            return stream.read()
        except Exception as e:
            logging.error(f"Error capturing image (attempt {attempt + 1}/{retries}): {e}")
            camera.stop()  # Ensure the camera is stopped on error
        if attempt < retries - 1:
            time.sleep(1)  # Wait a bit before retrying
    return None

def send_image(image_data, folder_name, camera_id, start_time):
    if image_data is None:
        logging.error(f"Skipping send_image for {camera_id} due to previous error.")
        return
    url = 'https://snapcmd.carlery.xyz/upload_image'  # Ensure this is the correct server URL
    files = {'image': ('image.jpeg', image_data, 'image/jpeg')}
    end_time = datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S')
    data = {
        'session_id': 'session123',  # Replace with actual session ID
        'camera_id': camera_id,      # Camera ID
        'start_time': start_time,
        'end_time': end_time,
        'folder_name': folder_name
    }
    try:
        logging.info(f"Sending image from {camera_id} to server...")
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f'Server response: {response.json()}')
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send image to server from {camera_id}: {e}")
        if e.response is not None:
            logging.error(f"Response content: {e.response.content}")

# Event handler for connection
@sio.event
def connect():
    logging.info('Connected to broadcast server')

# Event handler for disconnection
@sio.event
def disconnect():
    logging.info('Disconnected from broadcast server')

# Event handler for receiving capture request
@sio.event
def capture_request(data):
    logging.info(f'Capture request received: {data}')
    folder_name = data['folder_name']
    start_time = datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S')
    try:
        for camera, camera_id in zip(cameras, camera_ids):
            image_data = capture_image(camera)
            logging.info(f"Captured image size from {camera_id}: {len(image_data) if image_data else 'None'} bytes")
            send_image(image_data, folder_name, camera_id, start_time)
    except Exception as e:
        logging.error(f"Error during image capture or sending: {e}")

def connect_to_broadcast_server():
    connected = False
    while not connected:
        try:
            logging.info("Connecting to broadcast server...")
            sio.connect('http://192.168.1.100:5000')  # Use the correct broadcast server address
            connected = True
            logging.info("Successfully connected to broadcast server.")
        except socketio.exceptions.ConnectionError as e:
            logging.error(f"Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    try:
        # Connect to the broadcast server with retries
        connect_to_broadcast_server()
        sio.wait()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
