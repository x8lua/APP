# GRAB — Video Downloader

Supports: YouTube, Instagram, TikTok, Douyin

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

> You also need `ffmpeg` installed:
> - macOS: `brew install ffmpeg`
> - Ubuntu/Debian: `sudo apt install ffmpeg`
> - Windows: download from https://ffmpeg.org/download.html and add to PATH

### 2. Run the server
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Open in iOS Safari
Go to `http://YOUR_LOCAL_IP:8000` on your iPhone.

To find your local IP:
- Mac/Linux: `ifconfig | grep "inet "`
- Windows: `ipconfig`

Make sure your phone and computer are on the same WiFi network.

## Deploy to the internet (optional)

### Railway (free tier)
1. Push this folder to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub
3. Add a `Procfile`:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. Done. Railway gives you a public HTTPS URL.

### Render (free tier)
1. Push to GitHub
2. Go to render.com → New Web Service
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Project Structure
```
app/
├── main.py        # FastAPI backend
├── index.html     # Frontend UI (served by backend)
├── requirements.txt
└── README.md
```

## Notes
- Instagram requires being logged in for some content. For private posts,
  you can pass cookies via yt-dlp's `--cookies-from-browser` flag (advanced).
- Douyin geo-restrictions may require a proxy.
- TikTok watermark-free download is handled automatically by yt-dlp.
