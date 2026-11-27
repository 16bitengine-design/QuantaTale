"""Render a short silent 3D preview of every low-poly motif and report real render speed.

Used by the manual/path-triggered workflow to measure the 3D backend on a GitHub runner.
    python -m factflow.webgl_preview --output build/lowpoly-3d-preview.mp4
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

MOTIFS = ("lp_seasons", "lp_sky_scatter", "lp_water_cycle", "lp_volcano", "lp_plates", "generic")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="build/lowpoly-3d-preview.mp4")
    parser.add_argument("--seconds-per-motif", type=float, default=3.0)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=1280)
    args = parser.parse_args(argv)

    from .webgl_render import WebGLBackdrop, WebGLUnavailable

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    per = int(args.seconds_per_motif * args.fps)
    total = per * len(MOTIFS)
    ffmpeg = subprocess.Popen(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{args.width}x{args.height}", "-r", str(args.fps), "-i", "-", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)
    started = time.time()
    try:
        with WebGLBackdrop(args.width, args.height) as backdrop:
            for motif in MOTIFS:
                for i in range(per):
                    frame = backdrop.frame(motif, i / args.fps, i / max(1, per - 1))
                    ffmpeg.stdin.write(frame.tobytes())  # type: ignore[union-attr]
    except WebGLUnavailable as exc:
        ffmpeg.kill()
        print(f"3D backend unavailable: {exc}", file=sys.stderr)
        return 1
    ffmpeg.stdin.close()  # type: ignore[union-attr]
    if ffmpeg.wait() != 0:
        print("FFmpeg failed", file=sys.stderr)
        return 1
    elapsed = time.time() - started
    video_seconds = total / args.fps
    print(f"Rendered {total} frames ({video_seconds:.0f}s of video) in {elapsed:.0f}s: "
          f"{elapsed / total:.3f}s per frame, {elapsed / video_seconds:.1f}x video length.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
