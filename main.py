# use fast api to run basic process
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
from processing import generate_layers

app = FastAPI()
#create folders for runtime
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
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