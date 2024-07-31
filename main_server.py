import os
import socketio
import uvicorn
from fastapi import FastAPI
from datetime import datetime

# Create a Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', logger=True, engineio_logger=True)
app = FastAPI()

# Wrap with an ASGI application
app_sio = socketio.ASGIApp(sio, app)

# Event handler for client connection
@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)

# Event handler for client disconnection
@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

# Function to send capture request to all connected clients
@sio.event
async def capture_request(data):
    print('Sending capture request to all clients')
    folder_name = create_timestamped_folder()
    await sio.emit('capture_request', {'message': 'Please capture and send data', 'folder_name': folder_name})

# Create a directory to store images with a timestamped folder inside 'snapshots'
def create_timestamped_folder():
    base_folder = 'snapshots'
    timestamp = datetime.now().strftime('%Y-%m-%d___%H-%M-%S')
    folder_name = f'images_{timestamp}'
    full_path = os.path.join(base_folder, folder_name)
    os.makedirs(full_path, exist_ok=True)
    return full_path

# HTTP route to trigger capture request
@app.post('/send_capture_request')
async def trigger_capture_request():
    await capture_request('')
    return {'message': 'Capture request sent to all clients!'}

if __name__ == '__main__':
    uvicorn.run(app_sio, host='0.0.0.0', port=8801)
