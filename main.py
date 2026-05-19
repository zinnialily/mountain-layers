# use fast api to run basic process

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from processing import generate_layers
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi.staticfiles import StaticFiles

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
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