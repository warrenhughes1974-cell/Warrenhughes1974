#!/usr/bin/env python3
"""
Broadcast-quality Austin → Dallas travel transition renderer.
Output: Austin_to_Dallas_45_Minutes_Later.mp4 (1920x1080, 30fps, H.264)
"""

import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Canvas ──────────────────────────────────────────────────────────────────
W, H = 1920, 1080
FPS = 30
DURATION = 5.5  # seconds
BG_COLOR = (0xF7, 0xB6, 0xD2)

# ── Timing (seconds) ───────────────────────────────────────────────────────
T_MAP_FADE_START = 0.0
T_MAP_FADE_END = 0.8
T_CITIES_APPEAR = 0.4
T_PATH_DRAW_START = 0.8
T_PATH_DRAW_END = 1.2
T_PLANE_START = 1.2
T_PLANE_END = 4.8
T_TEXT_FADE_START = 1.4
T_TEXT_FADE_END = 2.0
T_FADE_BLACK_START = 5.2
T_FADE_BLACK_END = 5.5

# ── Geography ────────────────────────────────────────────────────────────────
AUSTIN = (-97.7431, 30.2672)   # lon, lat
DALLAS = (-96.7970, 32.7767)

ASSETS = Path(__file__).parent / "assets"
OUTPUT = Path(__file__).parent / "Austin_to_Dallas_45_Minutes_Later.mp4"

FONT_SEMIBOLD = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"


def ease_in_out_cubic(t: float) -> float:
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - pow(-2.0 * t + 2.0, 3.0) / 2.0


def ease_out_cubic(t: float) -> float:
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return 1.0 - pow(1.0 - t, 3.0)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def load_texas_polygons():
    with open(ASSETS / "tx.geojson") as f:
        data = json.load(f)
    polys = []
    for feat in data["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            polys.append(geom["coordinates"])
        elif geom["type"] == "MultiPolygon":
            polys.extend(geom["coordinates"])
    return polys


def build_projection(polys, margin_frac=0.12):
    """Build lon/lat → pixel projection centered on Texas."""
    all_lons, all_lats = [], []
    for poly in polys:
        for ring in poly:
            for lon, lat in ring:
                all_lons.append(lon)
                all_lats.append(lat)

    min_lon, max_lon = min(all_lons), max(all_lons)
    min_lat, max_lat = min(all_lats), max(all_lats)

    # Slight vertical bias to leave room for bottom text
    usable_w = W * (1.0 - 2 * margin_frac)
    usable_h = H * (1.0 - 2 * margin_frac - 0.08)  # extra bottom margin for text

    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat

    # Preserve aspect ratio
    scale = min(usable_w / lon_span, usable_h / lat_span)

    map_w = lon_span * scale
    map_h = lat_span * scale

    offset_x = (W - map_w) / 2.0
    offset_y = (H - map_h) / 2.0 - 30  # nudge up slightly

    def project(lon, lat):
        x = offset_x + (lon - min_lon) * scale
        y = offset_y + (max_lat - lat) * scale  # flip Y
        return x, y

    return project


def polygon_to_screen(poly, project):
    return [[project(lon, lat) for lon, lat in ring] for ring in poly]


def draw_texas_outline(draw, screen_polys, opacity=1.0, stroke_width=2.5):
    alpha = int(255 * clamp(opacity, 0, 1))
    color = (255, 255, 255, alpha)
    sw = int(stroke_width)
    for poly in screen_polys:
        for ring in poly:
            if len(ring) < 2:
                continue
            # Draw closed polygon outline with anti-aliased segments
            pts = ring + [ring[0]]
            for i in range(len(pts) - 1):
                draw.line([pts[i], pts[i + 1]], fill=color, width=sw, joint="curve")


def draw_glow_circle(base_rgba, cx, cy, radius=6, glow_radius=18, opacity=1.0):
    """Draw a marker with soft glow onto an RGBA layer."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    alpha = int(255 * clamp(opacity, 0, 1))

    # Outer glow rings
    for i in range(4, 0, -1):
        gr = glow_radius * (i / 4.0)
        ga = int(alpha * 0.08 * i)
        d.ellipse(
            [cx - gr, cy - gr, cx + gr, cy + gr],
            fill=(255, 255, 255, ga),
        )

    # Core dot
    d.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=(255, 255, 255, alpha),
    )

    return Image.alpha_composite(base_rgba, layer)


def draw_city_label(base_rgba, text, x, y, opacity=1.0, font_size=22):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = ImageFont.truetype(FONT_SEMIBOLD, font_size)
    alpha = int(255 * clamp(opacity, 0, 1))

    # Position label offset from marker (avoid overlap)
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Keep labels inside safe margins
    margin = 48
    lx = x + 14
    ly = y - th / 2 - 2

    if lx + tw > W - margin:
        lx = x - tw - 14
    if ly < margin:
        ly = margin
    if ly + th > H - margin:
        ly = H - margin - th

    d.text((lx, ly), text, font=font, fill=(255, 255, 255, alpha))
    return Image.alpha_composite(base_rgba, layer)


def draw_flight_path(base_rgba, p0, p1, progress, line_width=3):
    """Draw animated line from p0 to p1 up to progress (0-1)."""
    x0, y0 = p0
    x1, y1 = p1
    t = clamp(progress, 0, 1)
    ex = lerp(x0, x1, t)
    ey = lerp(y0, y1, t)

    if t <= 0.001:
        return base_rgba

    # Soft glow underlay
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.line([(x0, y0), (ex, ey)], fill=(255, 255, 255, 60), width=line_width + 6)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=4))

    line_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line_layer)
    ld.line([(x0, y0), (ex, ey)], fill=(255, 255, 255, 255), width=line_width)

    result = Image.alpha_composite(base_rgba, glow_layer)
    return Image.alpha_composite(result, line_layer)


def make_airplane_sprite(size=32):
    """
    Minimal flat vector airplane — side profile, nose pointing right (+X).
    Returns RGBA PIL Image.
    """
    s = size * 3  # render at 3x for anti-aliasing
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx, cy = s / 2, s / 2
    scale = s / 28.0

    # Fuselage
    body = [
        (cx - 10 * scale, cy - 1.5 * scale),
        (cx + 9 * scale, cy - 1.5 * scale),
        (cx + 11 * scale, cy),
        (cx + 9 * scale, cy + 1.5 * scale),
        (cx - 10 * scale, cy + 1.5 * scale),
    ]
    d.polygon(body, fill=(255, 255, 255, 255))

    # Top wing
    wing_top = [
        (cx - 1 * scale, cy - 1 * scale),
        (cx + 3 * scale, cy - 1 * scale),
        (cx + 1 * scale, cy - 7 * scale),
        (cx - 3 * scale, cy - 7 * scale),
    ]
    d.polygon(wing_top, fill=(255, 255, 255, 255))

    # Bottom wing (smaller)
    wing_bot = [
        (cx - 1 * scale, cy + 1 * scale),
        (cx + 2 * scale, cy + 1 * scale),
        (cx + 0.5 * scale, cy + 5 * scale),
        (cx - 2 * scale, cy + 5 * scale),
    ]
    d.polygon(wing_bot, fill=(255, 255, 255, 230))

    # Tail fin
    tail = [
        (cx - 9 * scale, cy - 1 * scale),
        (cx - 7 * scale, cy - 1 * scale),
        (cx - 8 * scale, cy - 5 * scale),
    ]
    d.polygon(tail, fill=(255, 255, 255, 255))

    # Nose highlight
    d.ellipse(
        [cx + 8 * scale, cy - 0.8 * scale, cx + 10.5 * scale, cy + 0.8 * scale],
        fill=(255, 255, 255, 255),
    )

    img = img.resize((size, size), Image.LANCZOS)
    return img


def rotate_sprite(sprite, angle_deg):
    return sprite.rotate(-angle_deg, resample=Image.BICUBIC, expand=True)


def draw_airplane(base_rgba, pos, angle_deg, opacity=1.0, sprite=None):
    if sprite is None:
        sprite = make_airplane_sprite(32)

    rotated = rotate_sprite(sprite, angle_deg)
    alpha = clamp(opacity, 0, 1)

    if alpha < 1.0:
        r, g, b, a = rotated.split()
        a = a.point(lambda p: int(p * alpha))
        rotated = Image.merge("RGBA", (r, g, b, a))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px, py = pos
    rw, rh = rotated.size
    layer.paste(rotated, (int(px - rw / 2), int(py - rh / 2)), rotated)
    return Image.alpha_composite(base_rgba, layer)


def draw_bottom_text(base_rgba, text, opacity=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = ImageFont.truetype(FONT_BOLD, 64)
    alpha = int(255 * clamp(opacity, 0, 1))

    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W - tw) / 2
    y = H - 140

    # Drop shadow
    shadow_alpha = int(alpha * 0.35)
    d.text((x + 2, y + 3), text, font=font, fill=(0, 0, 0, shadow_alpha))
    d.text((x, y), text, font=font, fill=(255, 255, 255, alpha))

    return Image.alpha_composite(base_rgba, layer)


def apply_fade_black(img_rgba, amount):
    """amount 0 = no fade, 1 = fully black."""
    if amount <= 0:
        return img_rgba
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp(amount, 0, 1))))
    return Image.alpha_composite(img_rgba, overlay)


class TransitionRenderer:
    def __init__(self):
        polys = load_texas_polygons()
        self.project = build_projection(polys)
        self.screen_polys = [polygon_to_screen(p, self.project) for p in polys]
        self.austin_xy = self.project(*AUSTIN)
        self.dallas_xy = self.project(*DALLAS)

        # Flight angle (screen space, degrees from +X axis)
        dx = self.dallas_xy[0] - self.austin_xy[0]
        dy = self.dallas_xy[1] - self.austin_xy[1]
        self.flight_angle = math.degrees(math.atan2(dy, dx))

        self.airplane_sprite = make_airplane_sprite(32)

        # Pre-render Texas outline at 2× supersample for smooth anti-aliased edges
        ss = 2
        big = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
        bd = ImageDraw.Draw(big)

        def scale_polys(polys):
            scaled = []
            for poly in polys:
                scaled.append(
                    [[x * ss, y * ss] for x, y in ring] for ring in poly
                )
            return scaled

        draw_texas_outline(bd, scale_polys(self.screen_polys), opacity=1.0, stroke_width=2.5 * ss)
        self._texas_layer = big.resize((W, H), Image.LANCZOS)

    def render_frame(self, t: float) -> np.ndarray:
        # Background
        img = Image.new("RGBA", (W, H), BG_COLOR + (255,))

        # Map fade in
        map_opacity = ease_out_cubic(
            (t - T_MAP_FADE_START) / (T_MAP_FADE_END - T_MAP_FADE_START)
        ) if t >= T_MAP_FADE_START else 0.0

        if map_opacity > 0:
            texas = self._texas_layer.copy()
            if map_opacity < 1.0:
                r, g, b, a = texas.split()
                a = a.point(lambda p: int(p * map_opacity))
                texas = Image.merge("RGBA", (r, g, b, a))
            img = Image.alpha_composite(img, texas)

        # City markers
        city_opacity = ease_out_cubic(
            (t - T_CITIES_APPEAR) / 0.5
        ) if t >= T_CITIES_APPEAR else 0.0

        if city_opacity > 0:
            ax, ay = self.austin_xy
            dx, dy = self.dallas_xy
            img = draw_glow_circle(img, ax, ay, radius=5, glow_radius=16, opacity=city_opacity)
            img = draw_glow_circle(img, dx, dy, radius=5, glow_radius=16, opacity=city_opacity)
            img = draw_city_label(img, "Austin", ax, ay, opacity=city_opacity)
            img = draw_city_label(img, "Dallas", dx, dy, opacity=city_opacity)

        # Flight path draw
        if t >= T_PATH_DRAW_START:
            path_progress = ease_in_out_cubic(
                (t - T_PATH_DRAW_START) / (T_PATH_DRAW_END - T_PATH_DRAW_START)
            )
            img = draw_flight_path(img, self.austin_xy, self.dallas_xy, path_progress)

        # Airplane
        if t >= T_PLANE_START:
            plane_t = ease_in_out_cubic(
                (t - T_PLANE_START) / (T_PLANE_END - T_PLANE_START)
            )
            px = lerp(self.austin_xy[0], self.dallas_xy[0], plane_t)
            py = lerp(self.austin_xy[1], self.dallas_xy[1], plane_t)
            img = draw_airplane(img, (px, py), self.flight_angle, sprite=self.airplane_sprite)

        # Bottom text
        if t >= T_TEXT_FADE_START:
            text_opacity = ease_out_cubic(
                (t - T_TEXT_FADE_START) / (T_TEXT_FADE_END - T_TEXT_FADE_START)
            )
            img = draw_bottom_text(img, "45 Minutes Later...", opacity=text_opacity)

        # Fade to black
        if t >= T_FADE_BLACK_START:
            fade = (t - T_FADE_BLACK_START) / (T_FADE_BLACK_END - T_FADE_BLACK_START)
            img = apply_fade_black(img, ease_in_out_cubic(fade))

        # Convert to RGB numpy array for moviepy
        rgb = img.convert("RGB")
        return np.array(rgb)


def main():
    print("Initializing renderer...")
    renderer = TransitionRenderer()
    print(f"  Austin: {renderer.austin_xy}")
    print(f"  Dallas: {renderer.dallas_xy}")
    print(f"  Flight angle: {renderer.flight_angle:.1f}°")

    total_frames = int(DURATION * FPS)
    print(f"Rendering {total_frames} frames at {FPS}fps ({DURATION}s)...")

    from moviepy import ImageSequenceClip

    frames = []
    for i in range(total_frames):
        t = i / FPS
        frames.append(renderer.render_frame(t))
        if i % 30 == 0:
            print(f"  Frame {i}/{total_frames} (t={t:.2f}s)")

    clip = ImageSequenceClip(frames, fps=FPS)
    clip.write_videofile(
        str(OUTPUT),
        codec="libx264",
        audio=False,
        fps=FPS,
        preset="slow",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-crf", "18"],
        logger="bar",
    )
    print(f"\n✓ Exported: {OUTPUT}")
    print(f"  Size: {OUTPUT.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
