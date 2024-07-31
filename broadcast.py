import asyncio
import threading
import subprocess
import socketio
from fastapi import FastAPI

# Create a Socket.IO client to connect to the main server
main_server_sio = socketio.Client(logger=True, engineio_logger=True)

# Create a Socket.IO server for Raspberry Pi clients
broadcast_sio = socketio.AsyncServer(async_mode='asgi', logger=True, engineio_logger=True)
app = FastAPI()

# Wrap with an ASGI application
app_broadcast_sio = socketio.ASGIApp(broadcast_sio, app)

# Global variable for the event loop
loop = None

# Event handler for connection to the main server
@main_server_sio.event
def connect():
    print('Connected to main server')

# Event handler for disconnection from the main server
@main_server_sio.event
def disconnect():
    print('Disconnected from main server')

# Event handler for receiving capture request from the main server
@main_server_sio.event
def capture_request(data):
    print('Capture request received from main server:', data)
    asyncio.run_coroutine_threadsafe(relay_capture_request(data), loop)

async def relay_capture_request(data):
    print(f"Emitting capture_request to all clients: {data}")
    await broadcast_sio.emit('capture_request', data)
    print("Event emitted successfully")

# Connect to the main server
def start_main_server_connection():
    try:
        print("Connecting to main server...")
        main_server_sio.connect('https://rcv.carlery.xyz')  # Use the correct main server address
        main_server_sio.wait()
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}")

# Event handler for client connection to the broadcast server
@broadcast_sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')

# Event handler for client disconnection from the broadcast server
@broadcast_sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')

# Function to start the broadcast server in a subprocess
def start_broadcast_server():
    subprocess.Popen(["python3", "-m", "uvicorn", "broadcast:app_broadcast_sio", "--host", "0.0.0.0", "--port", "8802", "--log-level", "info"])

if __name__ == '__main__':
    # Create an event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start the broadcast server in a separate subprocess
    broadcast_server_thread = threading.Thread(target=start_broadcast_server)
    broadcast_server_thread.start()

    # Start the connection to the main server in the main event loop
    loop.run_in_executor(None, start_main_server_connection)

    # Run the event loop
    loop.run_forever()
