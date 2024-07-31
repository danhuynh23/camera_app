import socketio
import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime
import pytz
import threading
import logging
import time

# Configure logging
logging.basicConfig(filename='/home/admin/Desktop/server.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Flask app and Socket.IO server setup
app = Flask(__name__)
CORS(app)
socketio_server = SocketIO(app, cors_allowed_origins="*")

# Socket.IO client setup to connect to the external server
sio = socketio.Client(logger=True, engineio_logger=True)

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

# Function to send a request to the local API
def send_request_to_local_api(data):
    url = 'http://localhost:5000/emit-capture'  # Your local API endpoint
    try:
        logging.info("Sending request to local API...")
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f'Local API response: {response.json()}')
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send request to local API: {e}")
        if e.response is not None:
            logging.error(f"Response content: {e.response.content}")

# Event handler for connection to external server
@sio.event
def connect():
    logging.info('Connected to external server')

# Event handler for disconnection from external server
@sio.event
def disconnect():
    logging.info('Disconnected from external server')
    # Retry connection
    connect_to_external_server()

# Event handler for receiving capture request from external server
@sio.event
def capture_request(data):
    logging.info(f'Capture request received from external server: {data}')
    # Pass the request to the local API
    send_request_to_local_api(data)

@app.route('/emit-capture', methods=['POST'])
def emit_capture():
    try:
        folder_name = request.json.get('folder_name', 'default_folder')
        logging.info(f'Emitting capture request with folder name: {folder_name}')
        socketio_server.emit('capture_request', {'folder_name': folder_name})
        return jsonify({'message': 'Capture request emitted'})
    except Exception as e:
        logging.error(f'Error in emit_capture: {e}')
        return jsonify({'error': 'Failed to emit capture request'}), 500

@socketio_server.on('connect')
def handle_connect():
    logging.info('Client connected')

@socketio_server.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')

@socketio_server.on_error_default  # handles all namespaces without an explicit error handler
def default_error_handler(e):
    logging.error(f'Error: {e}')
    return jsonify({'error': 'An error occurred'}), 500

def connect_to_external_server():
    connected = False
    while not connected:
        try:
            # Connect to the external Socket.IO server
            external_server_url = 'https://rcv.carlery.xyz'  # External server URL
            logging.info(f"Connecting to external server at {external_server_url}...")
            sio.connect(external_server_url, transports=['websocket'])
            sio.wait()
            connected = True
            logging.info("Successfully connected to external server.")
        except socketio.exceptions.ConnectionError as e:
            logging.error(f"Connection to external server failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    # Start the Socket.IO client in a separate thread
    client_thread = threading.Thread(target=connect_to_external_server)
    client_thread.daemon = True
    client_thread.start()
    
    # Start the Flask app and Socket.IO server
    logging.info('Starting server...')
    try:
        socketio_server.run(app, host='0.0.0.0', port=5000)
    except Exception as e:
        logging.error(f'Failed to start server: {e}')
