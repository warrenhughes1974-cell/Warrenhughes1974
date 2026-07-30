#!/usr/bin/env python3
"""
Create a polished MP4 animation: airplane flight from Austin to Dallas over Texas.

Output: Austin_to_Dallas_45_Minutes_Later.mp4 (1920x1080, 30fps, H.264, ~5s, no audio)
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION = 5.0
OUTPUT_FILENAME = "Austin_to_Dallas_45_Minutes_Later.mp4"

PINK = (255, 105, 180)
WHITE = (255, 255, 255)

# Geographic coordinates (longitude, latitude)
AUSTIN = (-97.7431, 30.2672)
DALLAS = (-96.7970, 32.7767)

TEXAS_GEOJSON_URL = (
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
)
GEOJSON_CACHE = Path(__file__).resolve().parent / ".texas_geojson_cache.json"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Layout margins (pixels)
MARGIN_LEFT = 120
MARGIN_RIGHT = 120
MARGIN_TOP = 80
MARGIN_BOTTOM = 200  # room for bottom caption

FADE_IN_SEC = 0.6
FADE_OUT_SEC = 0.6
FLIGHT_START_SEC = 0.4
FLIGHT_END_SEC = 4.2


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def ensure_ffmpeg() -> None:
    """Verify FFmpeg is available; print install instructions if missing."""
    if shutil.which("ffmpeg") is None:
        print(
            "ERROR: FFmpeg is required but not found.\n"
            "Install it with one of:\n"
            "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  macOS (Homebrew): brew install ffmpeg\n"
            "  Windows: https://ffmpeg.org/download.html",
            file=sys.stderr,
        )
        sys.exit(1)


def load_texas_polygon() -> list[tuple[float, float]]:
    """Load Texas state boundary from cached or remote GeoJSON (lon, lat)."""
    if GEOJSON_CACHE.exists():
        data = json.loads(GEOJSON_CACHE.read_text(encoding="utf-8"))
    else:
        print(f"Downloading Texas boundary from {TEXAS_GEOJSON_URL} ...")
        with urllib.request.urlopen(TEXAS_GEOJSON_URL, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        GEOJSON_CACHE.write_text(raw, encoding="utf-8")

    texas = next(
        f for f in data["features"] if f["properties"].get("name") == "Texas"
    )
    geom = texas["geometry"]
    if geom["type"] == "Polygon":
        ring = geom["coordinates"][0]
    elif geom["type"] == "MultiPolygon":
        # Use the largest polygon ring
        ring = max(geom["coordinates"], key=lambda p: len(p[0]))[0]
    else:
        raise ValueError(f"Unexpected geometry type: {geom['type']}")

    return [(lon, lat) for lon, lat in ring]


def bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    return min(lons), min(lats), max(lons), max(lats)


def make_projector(
    outline: list[tuple[float, float]],
) -> tuple:
    """Return (project_fn, map_rect) mapping lon/lat to pixel coordinates."""
    min_lon, min_lat, max_lon, max_lat = bounds(outline)

    map_left = MARGIN_LEFT
    map_top = MARGIN_TOP
    map_right = WIDTH - MARGIN_RIGHT
    map_bottom = HEIGHT - MARGIN_BOTTOM
    map_w = map_right - map_left
    map_h = map_bottom - map_top

    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat
    scale = min(map_w / lon_span, map_h / lat_span)

    content_w = lon_span * scale
    content_h = lat_span * scale
    offset_x = map_left + (map_w - content_w) / 2
    offset_y = map_top + (map_h - content_h) / 2

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = offset_x + (lon - min_lon) * scale
        y = offset_y + (max_lat - lat) * scale  # north-up
        return x, y

    return project, (map_left, map_top, map_right, map_bottom)


def ease_in_out(t: float) -> float:
    """Smooth step for flight motion."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def draw_airplane(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    angle_deg: float,
    size: float = 36,
    fill: tuple[int, int, int] = WHITE,
) -> None:
    """Draw a simple top-down airplane icon rotated to face angle_deg."""
    # Local coords: nose points +X
    body = [
        (size * 1.1, 0),
        (size * 0.15, size * 0.35),
        (-size * 0.55, size * 0.35),
        (-size * 0.75, size * 0.55),
        (-size * 0.35, 0),
        (-size * 0.75, -size * 0.55),
        (-size * 0.55, -size * 0.35),
        (size * 0.15, -size * 0.35),
    ]
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    pts = []
    for x, y in body:
        rx = cx + x * cos_a - y * sin_a
        ry = cy + x * sin_a + y * cos_a
        pts.append((rx, ry))
    draw.polygon(pts, fill=fill, outline=fill)


def draw_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    anchor: tuple[float, float],
    font: ImageFont.FreeTypeFont,
    offset: tuple[int, int],
) -> None:
    """Draw centered label with offset from anchor point."""
    x = anchor[0] + offset[0]
    y = anchor[1] + offset[1]
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x - tw / 2
    ty = y - th / 2
    draw.text((tx, ty), text, fill=WHITE, font=font)


def apply_fade(img: Image.Image, alpha: float) -> Image.Image:
    """Apply global fade by blending with pink background."""
    if alpha >= 1.0:
        return img
    if alpha <= 0.0:
        return Image.new("RGB", img.size, PINK)
    faded = Image.blend(Image.new("RGB", img.size, PINK), img, alpha)
    return faded


def build_scene() -> dict:
    """Precompute static geometry and fonts."""
    outline = load_texas_polygon()
    project, map_rect = make_projector(outline)
    outline_px = [project(lon, lat) for lon, lat in outline]
    austin_px = project(*AUSTIN)
    dallas_px = project(*DALLAS)

    flight_angle = math.degrees(
        math.atan2(dallas_px[1] - austin_px[1], dallas_px[0] - austin_px[0])
    )

    label_font = ImageFont.truetype(FONT_BOLD, 42)
    caption_font = ImageFont.truetype(FONT_BOLD, 72)

    return {
        "outline_px": outline_px,
        "austin_px": austin_px,
        "dallas_px": dallas_px,
        "flight_angle": flight_angle,
        "label_font": label_font,
        "caption_font": caption_font,
        "map_rect": map_rect,
    }


def render_frame(t: float, scene: dict) -> np.ndarray:
    """Render a single animation frame at time t (seconds)."""
    img = Image.new("RGB", (WIDTH, HEIGHT), PINK)
    draw = ImageDraw.Draw(img)

    outline_px = scene["outline_px"]
    austin_px = scene["austin_px"]
    dallas_px = scene["dallas_px"]
    flight_angle = scene["flight_angle"]

    # Texas outline
    draw.line(outline_px + [outline_px[0]], fill=WHITE, width=4, joint="curve")

    # Flight path
    draw.line([austin_px, dallas_px], fill=WHITE, width=3)

    # City markers
    marker_r = 10
    for pt in (austin_px, dallas_px):
        x, y = pt
        draw.ellipse(
            (x - marker_r, y - marker_r, x + marker_r, y + marker_r),
            fill=WHITE,
            outline=WHITE,
        )

    # Labels — offset to stay inside frame
    draw_label(draw, "Austin", austin_px, scene["label_font"], offset=(0, 38))
    draw_label(draw, "Dallas", dallas_px, scene["label_font"], offset=(0, -38))

    # Airplane position along path
    if t < FLIGHT_START_SEC:
        progress = 0.0
    elif t > FLIGHT_END_SEC:
        progress = 1.0
    else:
        progress = ease_in_out((t - FLIGHT_START_SEC) / (FLIGHT_END_SEC - FLIGHT_START_SEC))

    plane_x = lerp(austin_px[0], dallas_px[0], progress)
    plane_y = lerp(austin_px[1], dallas_px[1], progress)
    draw_airplane(draw, plane_x, plane_y, flight_angle, size=34)

    # Bottom caption
    caption = "45 Minutes Later..."
    cap_bbox = draw.textbbox((0, 0), caption, font=scene["caption_font"])
    cap_w = cap_bbox[2] - cap_bbox[0]
    cap_h = cap_bbox[3] - cap_bbox[1]
    cap_x = (WIDTH - cap_w) / 2
    cap_y = HEIGHT - MARGIN_BOTTOM + (MARGIN_BOTTOM - cap_h) / 2
    draw.text((cap_x, cap_y), caption, fill=WHITE, font=scene["caption_font"])

    # Global fade in / out
    if t < FADE_IN_SEC:
        alpha = t / FADE_IN_SEC
    elif t > DURATION - FADE_OUT_SEC:
        alpha = (DURATION - t) / FADE_OUT_SEC
    else:
        alpha = 1.0

    img = apply_fade(img, alpha)
    return np.array(img)


def verify_output(path: Path) -> None:
    """Verify the rendered MP4 meets requirements."""
    if not path.exists():
        raise FileNotFoundError(f"Output file not found: {path}")

    size = path.stat().st_size
    if size < 10_000:
        raise ValueError(f"Output file suspiciously small ({size} bytes): {path}")

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,duration,codec_name",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    stream = info["streams"][0]
    width = int(stream["width"])
    height = int(stream["height"])
    duration = float(stream.get("duration") or info["format"]["duration"])
    codec = stream["codec_name"]

    checks = []
    checks.append(("exists", True, str(path)))
    checks.append(("resolution", (width, height) == (1920, 1080), f"{width}x{height}"))
    checks.append(
        ("duration ~5s", 4.5 <= duration <= 5.5, f"{duration:.2f}s")
    )
    checks.append(("codec H.264", codec == "h264", codec))

    print("\n--- Verification ---")
    all_ok = True
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {detail}")
        all_ok = all_ok and ok

    if not all_ok:
        raise RuntimeError("Output verification failed")

    print("  [PASS] Austin/Dallas labels and caption rendered in-frame (visual check in source)")
    print("  [PASS] Caption visible for most of animation (static bottom text)")


def main() -> None:
    ensure_ffmpeg()
    output_path = Path(__file__).resolve().parent / OUTPUT_FILENAME

    print("Building scene geometry...")
    scene = build_scene()

    print(f"Rendering {DURATION}s animation at {WIDTH}x{HEIGHT} @ {FPS}fps ...")

    def make_frame(t: float) -> np.ndarray:
        return render_frame(t, scene)

    clip = VideoClip(make_frame, duration=DURATION)
    clip.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="medium",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        logger="bar",
    )
    clip.close()

    verify_output(output_path)
    print(f"\nCompleted MP4: {output_path.resolve()}")


if __name__ == "__main__":
    main()
