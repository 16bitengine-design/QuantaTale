"""Free, procedural sample-video renderer for QuantaTale.

Requires Pillow, Kokoro TTS, CPU PyTorch, soundfile and system executables ffmpeg/ffprobe/espeak-ng.
Kokoro's open-weight model is downloaded by its runtime on first use. eSpeak NG is retained only as a phonemization dependency used by Kokoro, not as a voice.

The renderer is deliberately separate from research assessment: the bundled
sample is a demonstration asset and is not cleared for public release.
"""
from __future__ import annotations

import json
import re
import math
import random
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .production_standards import PRODUCTION_STANDARDS, validate_production_voice

WIDTH, HEIGHT, FPS = 720, 1280, 24
NAVY = (4, 10, 28)
CYAN = (73, 226, 255)
BLUE = (63, 142, 255)
VIOLET = (159, 104, 255)
WHITE = (232, 246, 255)
MUTED = (143, 174, 201)


def validate_sample_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise ValueError("Sample specification must be a JSON object.")
    visual_profile = spec.get("visual_profile", "sky_blue_v1")
    if visual_profile not in {"sky_blue_v1", "sunset_red_v1", "holographic_science_v1", "lowpoly_diorama_v1"}:
        raise ValueError(f"No renderer exists for visual profile {visual_profile!r}; refusing to reuse an unrelated storyboard.")
    for field in ("title", "narration", "sources"):
        if field not in spec:
            raise ValueError(f"Sample specification is missing '{field}'.")
    if not isinstance(spec["title"], str) or not spec["title"].strip():
        raise ValueError("Sample title must be a non-empty string.")
    if not isinstance(spec["narration"], str) or len(spec["narration"].split()) < 12:
        raise ValueError("Sample narration must contain at least 12 words.")
    if not isinstance(spec["sources"], list) or not spec["sources"]:
        raise ValueError("At least one traceable source is required.")
    for source in spec["sources"]:
        if not isinstance(source, dict) or not str(source.get("url", "")).startswith("https://"):
            raise ValueError("Every source must include an HTTPS URL.")


def _scene_state(seconds: float, duration: float) -> tuple[int, float]:
    """Return a four-scene storyboard index and eased progress within the scene."""
    progress = min(1.0, max(0.0, seconds / max(duration, 0.1)))
    index = min(3, int(progress * 4))
    local = progress * 4 - index
    eased = local * local * (3 - 2 * local)
    return index, eased
# Pacing: this is an entertainment channel, so the narrator talks a little slower than Kokoro's default and leaves
# a breath between sentences (a longer one after the opening question) so every idea has room to land.
NARRATION_SPEED = 0.9
PAUSE_AFTER_SENTENCE = 0.6
PAUSE_AFTER_QUESTION = 1.0
PAUSE_AT_END = 0.8
SAMPLE_RATE = 24000


def _narration_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _generate_kokoro_audio(text: str, output_path: Path, voice: str = "af_heart",
                           speed: float = NARRATION_SPEED) -> list[tuple[float, float]]:
    """Generate natural narration with the open-weight Kokoro model, one sentence at a time.

    Returns the (start, end) seconds each sentence is spoken, so captions follow the real timing.
    """
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as exc:
        raise RuntimeError(
            "Kokoro narration dependencies are missing. Install the optional "
            "'tts' extra (kokoro, soundfile and CPU PyTorch)."
        ) from exc

    language_code = "b" if voice.startswith(("bf_", "bm_")) else "a"
    pipeline = KPipeline(lang_code=language_code)
    sentences = _narration_sentences(text)
    pieces: list[Any] = []
    spans: list[tuple[float, float]] = []
    cursor = 0.0
    for index, sentence in enumerate(sentences):
        chunks = [np.asarray(audio, dtype=np.float32) for _, _, audio in pipeline(sentence, voice=voice, speed=speed)
                  if audio is not None and len(audio)]
        if not chunks:
            raise RuntimeError(f"Kokoro did not return any narration audio for: {sentence[:60]!r}")
        spoken = np.concatenate(chunks)
        last = index == len(sentences) - 1
        pause = PAUSE_AT_END if last else (PAUSE_AFTER_QUESTION if sentence.endswith("?") else PAUSE_AFTER_SENTENCE)
        pieces += [spoken, np.zeros(int(pause * SAMPLE_RATE), dtype=np.float32)]
        spans.append((cursor, cursor + len(spoken) / SAMPLE_RATE))
        cursor += (len(spoken) / SAMPLE_RATE) + pause
    sf.write(str(output_path), np.concatenate(pieces), SAMPLE_RATE, subtype="PCM_16")
    return spans


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{millis:03}"


def _split_caption(text: str, max_words: int = 9, max_chars: int = 58) -> list[str]:
    """Break a sentence into on-screen pieces that fit two caption lines, so no words are cut off."""
    chunks: list[str] = []
    current: list[str] = []
    for word in text.split():
        trial = " ".join(current + [word])
        if current and (len(current) >= max_words or len(trial) > max_chars):
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


def _caption_segments(narration: str, duration: float,
                      spans: list[tuple[float, float]] | None = None,
                      max_words: int = 9, max_chars: int = 58) -> list[tuple[float, float, str]]:
    """Caption pieces with start/end times. With real per-sentence ``spans`` each caption follows the spoken sentence."""
    spoken = _narration_sentences(narration)
    if spans and len(spans) == len(spoken):
        segments: list[tuple[float, float, str]] = []
        for number, (sentence, (start, end)) in enumerate(zip(spoken, spans)):
            chunks = _split_caption(sentence, max_words, max_chars)
            counts = [max(1, len(c.split())) for c in chunks]
            cursor = start
            for chunk, count in zip(chunks, counts):
                stop = cursor + (end - start) * count / sum(counts)
                segments.append((cursor, stop, chunk))
                cursor = stop
            nxt = spans[number + 1][0] if number + 1 < len(spans) else duration
            segments[-1] = (segments[-1][0], nxt, segments[-1][2])  # keep the caption up through the pause
        return segments
    sentences = [part.strip() for part in narration.replace("—", ",").split(".") if part.strip()]
    if not sentences:
        sentences = [narration.strip()]
    weights = [max(1, len(sentence.split())) for sentence in sentences]
    total = sum(weights)
    cursor = 0.0
    segments = []
    for sentence, weight in zip(sentences, weights):
        start = cursor
        cursor += duration * weight / total
        text = sentence.rstrip(" ,;:") + ("." if not sentence.endswith((".", "?", "!")) else "")
        chunks = _split_caption(text, max_words, max_chars)
        words = [max(1, len(c.split())) for c in chunks]
        chunk_start = start
        for chunk, count in zip(chunks, words):
            chunk_end = chunk_start + (cursor - start) * count / sum(words)
            segments.append((chunk_start, chunk_end, chunk))
            chunk_start = chunk_end
    if segments:
        segments[-1] = (segments[-1][0], duration, segments[-1][2])
    return segments


def _wrap_text(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines



def _fit_font(draw: Any, text: str, font: Any, max_width: int, min_size: int = 18) -> Any:
    """Return a smaller variant of a TrueType font when text would overflow."""
    fitted = font
    while draw.textbbox((0, 0), text, font=fitted)[2] > max_width:
        size = getattr(fitted, "size", min_size)
        if size <= min_size:
            break
        fitted = fitted.font_variant(size=max(min_size, size - 1))
    return fitted

def _draw_frame(spec: dict[str, Any], seconds: float, duration: float, caption: str, fonts: dict[str, Any], stars: list[tuple[int, int, int]],
                backdrop: Any = None, cue: tuple[str | None, float] = (None, 0.0)) -> Any:
    """Render a narration-led frame using only holographic scientific imagery."""
    from PIL import Image, ImageDraw
    from .holographic_scenes import draw_generic_science_scene, draw_holographic_scene, draw_sunset_scene

    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image, "RGBA")

    lowpoly = spec.get("visual_profile") == "lowpoly_diorama_v1"
    if lowpoly:
        if backdrop is not None:  # real 3D backdrop (three.js); Pillow drawing is the fallback below
            from .holographic_scenes import scene_position
            scenes = spec.get("scenes") or []
            narration = str(spec.get("narration", ""))
            position, local = scene_position(narration, scenes, seconds, duration) if scenes and narration and duration else (0, 0.0)
            motif = str(scenes[min(position, len(scenes) - 1)].get("motif", "")) if scenes else ""
            image.paste(backdrop(motif, seconds, local, position, cue[0], cue[1]))
        else:
            from .lowpoly_scenes import draw_lowpoly_scene
            draw_lowpoly_scene(draw, WIDTH, HEIGHT, seconds, spec.get("scenes") or [], str(spec.get("narration", "")), duration)
        draw.text((40, 40), "QUANTATALE", font=fonts["tiny"], fill=(73, 226, 255, 120))
        fade = max(0.0, min(1.0, (4.0 - seconds) / 1.0))  # the title shows for ~3 s, then gets out of the way
        if fade > 0:
            title_text = spec["title"].upper()
            title_font = _fit_font(draw, title_text, fonts["title"], WIDTH - 96, min_size=20)
            draw.text((48, 90), title_text, font=title_font, fill=(255, 255, 255, int(255 * fade)),
                      stroke_width=1, stroke_fill=(25, 88, 120, int(255 * fade)))
    else:
        # Dark holographic chamber: technical grid, stars and animated scan plane.
        for x in range(24, WIDTH, 48):
            draw.line((x, 0, x, HEIGHT), fill=(27, 68, 98, 35), width=1)
        for y in range(20, HEIGHT, 48):
            draw.line((0, y, WIDTH, y), fill=(27, 68, 98, 28), width=1)
        for x, y, radius in stars:
            alpha = 110 + int(90 * (0.5 + 0.5 * math.sin(seconds * 2 + x * 0.03)))
            draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                         fill=(93, 204, 255, alpha))

        draw.text((48, 55), "QUANTATALE", font=fonts["small"], fill=CYAN)
        title_text = spec["title"].upper()
        title_font = _fit_font(draw, title_text, fonts["title"], WIDTH - 96, min_size=20)
        draw.text((48, 105), title_text, font=title_font, fill=WHITE,
                  stroke_width=1, stroke_fill=(25, 88, 120))
        draw.line((48, 177, WIDTH-48, 177), fill=(73, 226, 255, 150), width=2)


    scene_index, scene_progress = _scene_state(seconds, duration)
    profile = spec.get("visual_profile", "sky_blue_v1")
    if lowpoly:
        headline = subline = ""  # the diorama explains the narration without on-screen banners
    elif profile == "holographic_science_v1":
        headline, subline = draw_generic_science_scene(draw, scene_index, scene_progress, seconds, fonts, spec.get("scenes") or [],
                                                       narration=str(spec.get("narration", "")), duration=duration)
        headline = subline = ""  # science topics show animation only: no banner, no source credit
    else:
        scene_renderer = draw_sunset_scene if profile == "sunset_red_v1" else draw_holographic_scene
        headline, subline = scene_renderer(draw, scene_index, scene_progress, seconds, fonts)

    # Scene identity is explicit and changes with the narrated explanation.
    if headline:
        panel = (48, 985, WIDTH-48, 1080)
        draw.rounded_rectangle(panel, radius=18, fill=(3, 15, 36, 225),
                               outline=(73, 226, 255, 175), width=2)
        headline_font = _fit_font(draw, headline, fonts["heading"], panel[2] - panel[0] - 44)
        headline_width = draw.textbbox((0, 0), headline, font=headline_font)[2]
        draw.text(((WIDTH-headline_width)//2, 1000), headline, font=headline_font, fill=CYAN)
        subline_font = _fit_font(draw, subline, fonts["small"], panel[2] - panel[0] - 44)
        subline_width = draw.textbbox((0, 0), subline, font=subline_font)[2]
        draw.text(((WIDTH-subline_width)//2, 1044), subline, font=subline_font, fill=WHITE)

    if lowpoly:  # one short, large line over the picture: no panel, no footer
        line = _wrap_text(draw, caption, fonts["title"], WIDTH - 80)[0] if caption else ""
        font = fonts["title"]
        width = draw.textbbox((0, 0), line, font=font)[2]
        draw.text(((WIDTH - width) // 2, 1060), line, font=font, fill=WHITE, stroke_width=4, stroke_fill=(4, 12, 30))
        return image

    # Synchronized caption area remains separate from scene labels.
    caption_lines = _wrap_text(draw, caption, fonts["caption"], WIDTH-112)[:2]
    cap_top = 1110
    cap_height = 42 * max(1, len(caption_lines)) + 30
    draw.rounded_rectangle((34, cap_top, WIDTH-34, cap_top+cap_height),
                           radius=16, fill=(1, 7, 19, 235),
                           outline=(86, 190, 235, 150), width=2)
    for line_index, line in enumerate(caption_lines):
        bbox = draw.textbbox((0, 0), line, font=fonts["caption"])
        text_width = bbox[2] - bbox[0]
        draw.text(((WIDTH-text_width)//2, cap_top+14+line_index*42), line,
                  font=fonts["caption"], fill=WHITE)

    draw.text((48, 1230), "KNOW MORE. SEE DIFFERENTLY.", font=fonts["tiny"], fill=MUTED)
    footer_label = str(spec.get("production_label", "LOW-POLY DEMO" if lowpoly else "HOLOGRAPHIC DEMO"))
    footer_font = _fit_font(draw, footer_label, fonts["tiny"], 205, min_size=12)
    draw.text((WIDTH-48-draw.textbbox((0, 0), footer_label, font=footer_font)[2], 1230),
              footer_label, font=footer_font, fill=VIOLET)
    return image


def _cue_at(spec: dict[str, Any], spans: list[tuple[float, float]] | None, seconds: float,
            duration: float) -> tuple[str | None, float]:
    """The visual cue for the sentence being spoken at ``seconds`` and how far through it we are."""
    cues = spec.get("cues")
    if not cues or not spans or len(cues) != len(spans):
        return None, 0.0
    for index, (start, _end) in enumerate(spans):
        stop = spans[index + 1][0] if index + 1 < len(spans) else duration
        if start <= seconds < stop:
            return (str(cues[index]) or None), (seconds - start) / max(0.001, stop - start)
    return None, 0.0


def _open_backdrop(spec: dict[str, Any]) -> tuple[Any, Any]:
    """Start the optional three.js backdrop for the low-poly profile; (None, None) means use Pillow."""
    if spec.get("visual_profile") != "lowpoly_diorama_v1":
        return None, None
    from .webgl_render import WebGLBackdrop, WebGLUnavailable
    scene = WebGLBackdrop(WIDTH, HEIGHT)
    try:
        scene.__enter__()
    except WebGLUnavailable as exc:
        print(f"::warning title=3D backdrop unavailable::{exc} Falling back to the Pillow low-poly renderer.")
        return None, None
    return scene, scene.frame


def render_sample_video(spec_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Render a narrated 9:16 MP4 sample and quality-check the encoded file."""
    from PIL import ImageFont

    spec_path = Path(spec_path)
    output_dir = Path(output_dir)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    validate_sample_spec(spec)
    output_dir.mkdir(parents=True, exist_ok=True)

    for executable in ("ffmpeg", "ffprobe", "espeak-ng"):
        if shutil.which(executable) is None:
            raise RuntimeError(f"Required free system tool '{executable}' was not found.")

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not Path(font_path).is_file() or not Path(bold_path).is_file():
        raise RuntimeError("DejaVu fonts are required; install fonts-dejavu-core.")

    fonts = {
        "title": ImageFont.truetype(bold_path, 37),
        "heading": ImageFont.truetype(bold_path, 30),
        "caption": ImageFont.truetype(bold_path, 27),
        "label": ImageFont.truetype(bold_path, 19),
        "small": ImageFont.truetype(font_path, 20),
        "tiny": ImageFont.truetype(font_path, 14),
    }

    audio_path = output_dir / "narration.wav"
    video_path = output_dir / "quantatale-sample-vertical.mp4"
    thumbnail_path = output_dir / "thumbnail.png"
    srt_path = output_dir / "captions.srt"
    metadata_path = output_dir / "sample-metadata.json"

    voice = validate_production_voice(spec)
    spans = _generate_kokoro_audio(spec["narration"], audio_path, voice=voice)
    import soundfile as sf
    duration = float(sf.info(str(audio_path)).duration)
    if not 8 <= duration <= 90:
        raise RuntimeError(f"Sample narration duration {duration:.1f}s is outside the safe 8-90s range.")

    if spec.get("visual_profile") == "lowpoly_diorama_v1":  # short, glanceable captions
        segments = _caption_segments(spec["narration"], duration, spans, max_words=5, max_chars=30)
    else:
        segments = _caption_segments(spec["narration"], duration, spans)
    with srt_path.open("w", encoding="utf-8") as handle:
        for index, (start, end, text) in enumerate(segments, 1):
            handle.write(f"{index}\n{_timestamp(start)} --> {_timestamp(end)}\n{text}\n\n")

    rng = random.Random(20261114)
    stars = [(rng.randrange(20, WIDTH-20), rng.randrange(190, HEIGHT-80), rng.choice((1, 1, 2))) for _ in range(95)]
    frame_count = math.ceil(duration * FPS)
    ffmpeg_command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s:v", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
        "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0",
        "-frames:v", str(frame_count), "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", str(video_path),
    ]
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    web_scene, backdrop = _open_backdrop(spec)
    try:
        assert process.stdin is not None
        for frame_index in range(frame_count):
            seconds = frame_index / FPS
            caption = next((text for start, end, text in segments if start <= seconds < end), segments[-1][2])
            frame = _draw_frame(spec, seconds, duration, caption, fonts, stars, backdrop, _cue_at(spec, spans, seconds, duration))
            if frame_index == min(frame_count - 1, FPS):
                frame.save(thumbnail_path, format="PNG", optimize=True)
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise
    finally:
        if web_scene is not None:
            web_scene.__exit__(None, None, None)
    if return_code != 0:
        raise RuntimeError(f"FFmpeg video encoding failed: {stderr[-3000:]}")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,width,height:format=duration",
         "-of", "json", str(video_path)],
        check=True, capture_output=True, text=True,
    )
    probe_data = json.loads(probe.stdout)
    streams = probe_data.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    encoded_duration = float(probe_data.get("format", {}).get("duration", 0))
    if not video_stream or not audio_stream:
        raise RuntimeError("Quality check failed: encoded MP4 must contain both video and audio.")
    if (video_stream.get("width"), video_stream.get("height")) != (WIDTH, HEIGHT):
        raise RuntimeError("Quality check failed: video dimensions do not match the 9:16 preset.")
    if not 8 <= encoded_duration <= 90 or not video_path.stat().st_size:
        raise RuntimeError("Quality check failed: encoded video duration or file size is invalid.")

    metadata = {
        "schema_version": 1,
        "project": "QuantaTale",
        "title": spec["title"],
        "format": "vertical_9_16",
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "duration_seconds": round(encoded_duration, 3),
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name"),
        "narration_engine": PRODUCTION_STANDARDS["narration_engine"],
        "production_standards": PRODUCTION_STANDARDS,
        "narration_voice": voice,
        "animation": "four-scene procedural holographic Python/Pillow storyboard",
        "visual_profile": spec.get("visual_profile", "sky_blue_v1"),
        "visual_scenes": (
            ["long_sunset_atmospheric_path", "short_wavelength_scattering", "red_orange_light_reaching_observer", "holographic_sunset_horizon"]
            if spec.get("visual_profile", "sky_blue_v1") == "sunset_red_v1"
            else [f"generic_scene_{i + 1}" for i in range(len(spec.get("scenes") or [None] * 4))]
            if spec.get("visual_profile") in {"holographic_science_v1", "lowpoly_diorama_v1"}
            else ["sunlight_visible_spectrum", "atmospheric_molecular_scattering", "holographic_human_eye", "holographic_earth_and_blue_sky"]
        ),
        "render_engine": "FFmpeg",
        "sources": spec["sources"],
        "publication_status": "sample_not_approved_for_publication",
        "editorial_review_required": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": [video_path.name, audio_path.name, srt_path.name, thumbnail_path.name],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "video": str(video_path),
        "thumbnail": str(thumbnail_path),
        "captions": str(srt_path),
        "metadata": str(metadata_path),
        "duration_seconds": round(encoded_duration, 3),
        "size_bytes": video_path.stat().st_size,
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
    }
