import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np
from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont, ImageFilter

MOVIEPY_IMPORT_ERROR = None
try:  # pragma: no cover - optional dependency check
    from moviepy.audio.AudioClip import AudioArrayClip
    from moviepy.editor import ImageClip, concatenate_videoclips
except ImportError as exc:  # pragma: no cover - surface missing dependency
    AudioArrayClip = ImageClip = concatenate_videoclips = None  # type: ignore[assignment]
    MOVIEPY_IMPORT_ERROR = exc


BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/generate")
    def generate_reel():
        if any(module is None for module in (AudioArrayClip, ImageClip, concatenate_videoclips)):
            return (
                jsonify(
                    {
                        "error": "MoviePy is not installed.",
                        "details": "Install the moviepy dependency, e.g. `pip install moviepy`.",
                    }
                ),
                500,
            )

        payload = request.get_json(silent=True) or {}
        project_title = (payload.get("title") or "My Reel").strip()
        scenes = payload.get("scenes") or []
        tempo = int(payload.get("tempo") or 100)
        aspect_ratio = payload.get("aspectRatio") or "9:16"

        if not scenes:
            return jsonify({"error": "Please add at least one scene."}), 400

        validated_scenes = []
        for raw_scene in scenes:
            text = (raw_scene.get("text") or "").strip()
            duration = max(float(raw_scene.get("duration") or 3), 1)
            accent = (raw_scene.get("accentColor") or "#FF9F1C").strip()
            divider = (raw_scene.get("dividerShape") or "wave").strip()
            bg_start = (raw_scene.get("backgroundStart") or "#11001C").strip()
            bg_end = (raw_scene.get("backgroundEnd") or "#32004B").strip()

            if not text:
                continue

            validated_scenes.append(
                {
                    "text": text,
                    "duration": duration,
                    "accent": accent,
                    "divider": divider,
                    "background": (bg_start, bg_end),
                }
            )

        if not validated_scenes:
            return jsonify({"error": "All scenes are empty. Add some text first."}), 400

        resolution = (720, 1280) if aspect_ratio == "9:16" else (1280, 720)
        fps = 30

        scene_images = []
        try:
            for index, scene in enumerate(validated_scenes, start=1):
                image = build_scene_image(
                    scene["text"],
                    resolution,
                    scene["background"],
                    scene["accent"],
                    scene["divider"],
                    project_title,
                    index,
                    len(validated_scenes),
                )
                scene_images.append((image, scene["duration"]))

            clips = [
                ImageClip(np.array(image)).set_duration(duration)
                for image, duration in scene_images
            ]

            video = concatenate_videoclips(clips, method="compose")

            total_duration = sum(scene["duration"] for scene in validated_scenes)
            audio = build_audio_track(total_duration, tempo)
            video = video.set_audio(audio)

            file_id = uuid.uuid4().hex
            output_filename = f"{slugify(project_title or 'reel')}-{file_id}.mp4"
            output_path = GENERATED_DIR / output_filename

            video.write_videofile(
                output_path.as_posix(),
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                threads=2,
                logger=None,
            )

        except Exception as exc:  # pragma: no cover - surface error to client
            return (
                jsonify({"error": "Failed to generate reel.", "details": str(exc)}),
                500,
            )

        download_url = f"/generated/{output_filename}"
        return jsonify(
            {
                "title": project_title,
                "filename": output_filename,
                "downloadUrl": download_url,
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "durationSeconds": total_duration,
            }
        )

    @app.get("/generated/<path:filename>")
    def serve_generated(filename: str):
        return send_from_directory(GENERATED_DIR, filename, as_attachment=True)

    return app


def build_scene_image(
    text: str,
    resolution: Tuple[int, int],
    gradient: Tuple[str, str],
    accent: str,
    divider_shape: str,
    project_title: str,
    current_index: int,
    total_scenes: int,
) -> Image.Image:
    width, height = resolution
    background = make_gradient_background(width, height, gradient)
    draw = ImageDraw.Draw(background)

    margin = int(width * 0.08)
    content_width = width - (margin * 2)
    top_section = int(height * 0.16)
    bottom_section = height - top_section - margin

    title_font = load_font(int(width * 0.045))
    scene_font = load_font(int(width * 0.07))
    meta_font = load_font(int(width * 0.035))

    # Header
    header_text = project_title.upper()
    draw.text(
        (margin, margin / 2),
        header_text,
        font=title_font,
        fill=accent,
    )

    # Step indicator
    indicator_text = f"{current_index}/{total_scenes}"
    indicator_size = draw.textlength(indicator_text, font=meta_font)
    draw.text(
        (width - margin - indicator_size, margin / 2),
        indicator_text,
        font=meta_font,
        fill="#F9F9F9",
    )

    # Divider
    draw_divider(draw, (margin, top_section), (width - margin, top_section + 12), accent, divider_shape)

    # Main text block
    wrapped = wrap_text(text, scene_font, content_width)
    text_bbox = draw.multiline_textbbox(
        (0, 0), wrapped, font=scene_font, spacing=12, align="left"
    )
    text_height = text_bbox[3] - text_bbox[1]
    text_x = margin
    text_y = top_section + ((bottom_section - text_height) // 2)
    draw.multiline_text(
        (text_x, text_y),
        wrapped,
        font=scene_font,
        spacing=12,
        fill="#FFFFFF",
    )

    # Footer tag
    footer_text = "#reel-generator"
    tag_width = draw.textlength(footer_text, font=meta_font)
    tag_height = meta_font.size + 16
    tag_x = margin
    tag_y = height - margin - tag_height
    draw.rounded_rectangle(
        [tag_x, tag_y, tag_x + tag_width + 24, tag_y + tag_height],
        radius=20,
        fill=accent,
    )
    draw.text(
        (tag_x + 12, tag_y + 8),
        footer_text,
        font=meta_font,
        fill="#0B0316",
    )

    # Soft glow
    glow_radius = int(width * 0.06)
    glow = background.filter(ImageFilter.GaussianBlur(glow_radius))
    blend = Image.blend(background, glow, alpha=0.1)
    return blend


def make_gradient_background(width: int, height: int, colors: Tuple[str, str]) -> Image.Image:
    base = Image.new("RGB", (width, height), color=colors[0])
    top = Image.new("RGB", (width, height), color=colors[1])
    mask = Image.linear_gradient("L").resize((width, height))
    return Image.composite(top, base, mask)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    words = text.split()
    if not words:
        return ""

    lines: List[str] = []
    current_line: List[str] = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if font.getlength(test_line) > max_width:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
        else:
            current_line.append(word)

    if current_line:
        lines.append(" ".join(current_line))

    return "\n".join(lines)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def draw_divider(
    draw: ImageDraw.ImageDraw,
    start: Tuple[int, int],
    end: Tuple[int, int],
    color: str,
    shape: str,
) -> None:
    x0, y0 = start
    x1, y1 = end
    height = y1 - y0
    if shape == "wave":
        steps = 12
        wave_points = []
        for step in range(steps + 1):
            progress = step / steps
            x = x0 + (x1 - x0) * progress
            amplitude = height * 2
            y = y0 + height / 2 + amplitude * np.sin(progress * np.pi * 2) / 2
            wave_points.append((x, y))
        draw.line(wave_points, fill=color, width=6)
    elif shape == "zigzag":
        segments = 16
        zig_points = []
        for step in range(segments + 1):
            progress = step / segments
            x = x0 + (x1 - x0) * progress
            y = y0 if step % 2 == 0 else y1
            zig_points.append((x, y))
        draw.line(zig_points, fill=color, width=6)
    else:
        draw.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=color, width=6)


def build_audio_track(duration: float, tempo: int) -> AudioArrayClip:
    sample_rate = 44100
    beat_duration = 60 / max(tempo, 60)
    total_samples = int(duration * sample_rate)

    t = np.linspace(0, duration, total_samples, endpoint=False)
    base_freq = 110
    beat = np.sin(2 * np.pi * base_freq * t) * 0.2

    click = np.zeros_like(beat)
    beat_samples = int(beat_duration * sample_rate)
    for start in range(0, total_samples, beat_samples):
        end = min(start + int(sample_rate * 0.05), total_samples)
        envelope = np.linspace(1, 0, end - start)
        click[start:end] += 0.6 * np.sin(2 * np.pi * 880 * np.linspace(0, (end - start) / sample_rate, end - start, endpoint=False)) * envelope

    audio_wave = np.clip(beat + click, -1, 1)
    stereo_wave = np.stack([audio_wave, audio_wave], axis=1)
    return AudioArrayClip(stereo_wave, fps=sample_rate)


def slugify(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value)
    safe = "-".join(filter(None, safe.split("-")))
    return safe or "reel"


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

