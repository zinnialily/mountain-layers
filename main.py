# use fast api to run basic process

from fastapi import FastAPI, UploadFile, File
import shutil
import os

from processing import generate_layers

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process")
async def process_image(file: UploadFile = File(...)):

    # force filename
    file_path = os.path.join(UPLOAD_DIR, "image-upload.jpg")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = generate_layers(file_path)

    return result