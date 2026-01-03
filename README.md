# ReelCraft Studio 🎬

Generate stylish social reels straight from your browser with a clean Flask + MoviePy backend and a modern UI. Define scene-by-scene copy, pick colours, set the beat, and export a ready-to-post MP4 — no timeline editing required.

## Features

- Scene builder with tempo, gradient backgrounds, and divider styles
- Auto-generated beat-based soundtrack (no audio assets required)
- Aspect ratio presets for vertical `9:16` or landscape `16:9`
- Instant downloads served from the Flask backend

## Requirements

- Python 3.10+
- FFmpeg (MoviePy uses it to encode the MP4). Install it and ensure `ffmpeg` is available on your `PATH`.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate   # PowerShell
pip install -r requirements.txt
```

## Run the app

```bash
flask --app app run --debug
```

Then open http://127.0.0.1:5000/ in your browser.

## Workflow

1. Fill in the project meta: title, aspect ratio, tempo.
2. Add as many scenes as you need — adjust text, duration, accent, gradients.
3. Hit **Generate Reel**. The backend renders each scene into imagery, stitches the slideshow, and adds a beat-matched soundtrack.
4. Download the MP4 and share.

## Project structure

```
.
├── app.py                 # Flask application
├── requirements.txt       # Dependencies
├── templates/
│   └── index.html         # Jinja2 template with the UI skeleton
└── static/
    ├── css/style.css      # Custom styling
    └── js/main.js         # Scene management + API calls
```

Rendered reels are stored under `generated/` and surfaced via `/generated/<filename>`. Add a cleanup cron or manual purge if you deploy long-term.

