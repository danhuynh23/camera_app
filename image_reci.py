import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form

app = FastAPI()

@app.post("/upload_image")
async def upload_image(
    session_id: str = Form(...),
    camera_id: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    folder_name: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        print("Received image upload request")
        print(f"Session ID: {session_id}")
        print(f"Camera ID: {camera_id}")
        print(f"Start Time: {start_time}")
        print(f"End Time: {end_time}")
        print(f"Folder Name: {folder_name}")
        image_folder = os.path.join('.', folder_name)
        os.makedirs(image_folder, exist_ok=True)
        image_path = os.path.join(image_folder, f'image_{camera_id}.jpeg')
        with open(image_path, 'wb') as f:
            content = await image.read()
            f.write(content)
        print(f'Image saved to {image_path}')
        return {"status": "success", "path": image_path}
    except Exception as e:
        print(f"Error saving image: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)
