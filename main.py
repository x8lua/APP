from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
import tempfile
import os
import re
from pathlib import Path

BASE = Path(__file__).parent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str
    quality: str = "best"
    format: str = "mp4"

def detect_platform(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram.com" in url:
        return "Instagram"
    elif "tiktok.com" in url:
        return "TikTok"
    elif "douyin.com" in url:
        return "Douyin"
    return "Unknown"

@app.post("/api/info")
async def get_video_info(req: VideoRequest):
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
            formats = info.get("formats", [])
            available = set()
            for f in formats:
                h = f.get("height")
                if h:
                    if h >= 1080: available.add("1080p")
                    elif h >= 720: available.add("720p")
                    elif h >= 480: available.add("480p")
                    elif h >= 360: available.add("360p")
            return {
                "title": info.get("title", "Video"),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "platform": detect_platform(req.url),
                "available_qualities": ["best"] + sorted(list(available), key=lambda x: int(x[:-1]), reverse=True) + ["audio"],
                "uploader": info.get("uploader", ""),
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def download_video(req: VideoRequest):
    tmpdir = tempfile.mkdtemp()
    output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
    audio_only = req.quality == "audio"

    if audio_only:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
            "quiet": True,
        }
    else:
        if req.quality == "best":
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            h = req.quality.replace("p", "")
            fmt = f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}][ext=mp4]/best[height<={h}]"
        ydl_opts = {
            "format": fmt,
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "quiet": True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            title = info.get("title", "video")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    files = list(Path(tmpdir).iterdir())
    if not files:
        raise HTTPException(status_code=500, detail="Download failed")

    filepath = files[0]
    ext = filepath.suffix.lstrip(".")
    mime = "audio/mpeg" if ext == "mp3" else "video/mp4"
    safe_title = re.sub(r'[^\w\s-]', '', title)[:60].strip()
    filename = f"{safe_title}.{ext}"

    def iterfile():
        with open(filepath, "rb") as f:
            yield from f
        try:
            os.unlink(filepath)
            os.rmdir(tmpdir)
        except:
            pass

    return StreamingResponse(
        iterfile(),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# Serve static files (icon.png, manifest.json, etc.)
@app.get("/icon.png")
async def serve_icon():
    icon_path = BASE / "icon.png"
    if not icon_path.exists():
        raise HTTPException(status_code=404, detail="Icon not found")
    return FileResponse(icon_path, media_type="image/png")

@app.get("/manifest.json")
async def serve_manifest():
    manifest_path = BASE / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    return FileResponse(manifest_path, media_type="application/json")

# Serve frontend (must be last)
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return (BASE / "index.html").read_text()
