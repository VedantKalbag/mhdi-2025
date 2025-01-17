from http.client import HTTPException
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from audioproject import download_audio, time_stretch, split_audio_demucs
from utils import get_video_id
import config

import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class AudioRequest(BaseModel):
    youtube_url: str
    timestretch_ratio: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/separate-stems")
def separate_stems(request: AudioRequest):
    # print(request.model_dump())
    logger.debug(f"Full request data: {request.model_dump()}")
    # print(request.youtube_url)
    # print(request.timestretch_ratio)
    video_id = get_video_id(request.youtube_url)
    download_audio(request.youtube_url)
    audio_path = f"{config.OUTPUT_DIR}/{video_id}.wav"
    time_stretch(audio_path, request.timestretch_ratio)

    stems = [path for path in split_audio_demucs(audio_path)]
    return stems

# API endpoint to send the audio files from disk

# @app.get("/audio/{file_path}")
# def get_audio(file_path: str):
#     logger.debug(f"Received request for file: {file_path}")
#     return FileResponse(file_path,
#                         media_type="audio/wav",
#                         content_disposition_type="inline")
@app.get("/audio/{full_path:path}")
def get_audio(full_path: str):
    logger.debug(f"Received request for file: {full_path}")
    
    # Remove any leading slashes for consistency
    full_path = full_path.lstrip('/')
    
    # Log the path for debugging
    logger.debug(f"Looking for file at: {full_path}")
    
    # Check if file exists before sending
    if not os.path.exists(full_path):
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        full_path,
        media_type="audio/wav",
        content_disposition_type="inline"
    )