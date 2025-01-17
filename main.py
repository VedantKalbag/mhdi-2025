from fastapi import FastAPI
from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from audioproject import download_audio, time_stretch, split_audio_demucs
from utils import get_video_id

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
    print(request)
    print(request.youtube_url)
    print(request.timestretch_ratio)
    video_id = get_video_id(request.youtube_url)
    download_audio(request.youtube_url)
    audio_path = f"{video_id}.wav"
    time_stretch(audio_path, request.timestretch_ratio)

    stems = [path for path in split_audio_demucs(audio_path)]
    return stems

# API endpoint to send the audio files from disk

@app.get("/audio/{file_path}")
def get_audio(file_path: str):
    return FileResponse(file_path,
                        media_type="audio/wav",
                        content_disposition_type="inline")
