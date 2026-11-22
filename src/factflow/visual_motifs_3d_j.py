"""Holographic 3D motifs, batch J: shorter days, lightning, its heat and thunder, tides, lunar eclipse.

Same names as the flat motifs, so existing topics upgrade without a spec change. Words only on screen.
"""

from __future__ import annotations

import math
from typing import Any

from .holo3d import box, floor_grid, pt, view
from .visual_motifs import BLUE, CX, CYAN, GREEN, GREY, ORANGE, RED, WATER, WHITE, YELLOW, _c, _dot, _glow, _label
from .visual_motifs_3d import _solid


def _lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


def _cloud(draw: Any, ang: float, x: float, y: float, z: float, scale: float = 1.0) -> None:
    for dx, dy, dz, r in ((-70, 0, -20, 46), (-15, 14, 10, 58), (45, 4, -10, 50), (95, -6, 20, 38), (10, -14, 40, 40)):
        sx, sy = pt(x + dx * scale, y + dy * scale, z + dz * scale, ang)
        _solid(draw, sx, sy, r * scale, GREY, 225)


def _bolt_points(ang: float, x: float, y_top: float, y_bot: float, jitter: float, seed: float, n: int = 12):
    pts = []
    for i in range(n + 1):
        s = i / n
        dx = jitter * math.sin(i * 2.3 + seed) * (1 if 0 < i < n else 0)
        dz = jitter * 0.6 * math.cos(i * 1.7 + seed) * (1 if 0 < i < n else 0)
        pts.append(pt(x + dx, _lerp(y_top, y_bot, s), dz, ang))
    return pts


def daylight_fade(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    arc = [pt(-250 + 500 * i / 40, 40 + 300 * math.sin(math.pi * i / 40), 0, ang) for i in range(41)]
    draw.line(arc, fill=_c(YELLOW, 110), width=2)
    pos = 0.5 + 0.38 * (1 - p) * math.sin(t * 0.6) * 0 + (0.5 - 0.5 * p) * 0.0
    s = _lerp(0.5, 0.82, p)
    sx, sy = pt(-250 + 500 * s, 40 + 300 * math.sin(math.pi * s), 0, ang)
    _glow(draw, sx, sy, int(50 - 14 * p), _c(YELLOW, 230))
    _solid(draw, sx, sy, int(34 - 10 * p), YELLOW, 245)
    box(draw, -110, 140, 80, 80, 40 + 150 * (1 - p), ang, YELLOW, 225)
    box(draw, 110, 140, 80, 80, 30 + 150 * (1 - p), ang, GREEN, 225)
    for text, x, col in (("daylight", -110, YELLOW), ("chlorophyll", 110, GREEN)):
        sx, sy = pt(x, 0, 240, ang)
        _label(draw, (sx, sy), text, fonts, col, "mm")
    sx, sy = pt(0, 420, 0, ang)
    _label(draw, (sx, sy), "shorter days, less chlorophyll", fonts, CYAN, "mm")


def lightning_bolt(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    _cloud(draw, ang, 0, 470, 0)
    flash = 0.5 + 0.5 * math.sin(t * 14)
    pts = _bolt_points(ang, 0, 440, 0, 45, 0.0)
    draw.line(pts, fill=_c(CYAN, 90), width=18)
    draw.line(pts, fill=_c(WHITE, int(150 + 100 * flash)), width=7)
    for k, (i0, side) in enumerate(((4, 1), (7, -1))):
        a = pts[i0]
        b = (a[0] + side * 70, a[1] + 110)
        draw.line((*a, *b), fill=_c(WHITE, int(100 + 80 * flash)), width=3)
    _glow(draw, *pts[-1], 26 * (0.6 + 0.6 * flash), _c(YELLOW, 200))
    sx, sy = pt(0, 560, 0, ang)
    _label(draw, (sx, sy), "a lightning channel", fonts, CYAN, "mm")


def heat_halo(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    pts = _bolt_points(ang, 0, 470, 0, 30, 0.5)
    mid = pts[len(pts) // 2]
    for r, a in ((150, 35), (110, 60), (75, 95), (45, 130)):
        draw.ellipse((mid[0] - r * 0.7, mid[1] - r * 1.5, mid[0] + r * 0.7, mid[1] + r * 1.5),
                     fill=_c(ORANGE, int(a * (0.5 + 0.7 * p))))
    draw.line(pts, fill=_c(WHITE, 245), width=7)
    for i in range(10):
        s = (t * 0.6 + i / 10) % 1.0
        a = i * 0.9 + t
        _dot(draw, mid[0] + 120 * s * math.cos(a), mid[1] + 200 * s * math.sin(a), 4, _c(ORANGE, int(220 * (1 - s))))
    sx, sy = pt(0, 580, 0, ang)
    _label(draw, (sx, sy), "the air around the channel", fonts, ORANGE, "mm")
    _label(draw, (sx, sy + 34), "becomes extremely hot", fonts, WHITE, "mm")


def pressure_wave(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.55)
    floor_grid(draw, ang, half=320, step=80)
    cx, cy = -120, 150
    sx, sy = pt(cx, cy, 0, ang)
    _glow(draw, sx, sy, 22, _c(WHITE, 240))
    for k in range(4):
        r = ((p * 1.4 + k * 0.22 + t * 0.1) % 1.0) * 330
        a = int(220 * (1 - r / 330))
        draw.line([pt(cx + r * math.cos(u), cy, r * math.sin(u), ang) for u in [i * math.pi / 30 for i in range(61)]],
                  fill=_c(CYAN, a), width=3)
        draw.line([pt(cx + r * math.cos(u), cy + r * math.sin(u), 0, ang) for u in [i * math.pi / 30 for i in range(61)]],
                  fill=_c(CYAN, a // 2), width=2)
    box(draw, 230, 0, 40, 40, 60, ang, WHITE, 230, y0=0)
    sx, sy = pt(230, 100, 0, ang)
    _label(draw, (sx, sy), "listener", fonts, WHITE, "mm")
    sx, sy = pt(0, 380, 0, ang)
    _label(draw, (sx, sy), "the hot air expands suddenly", fonts, ORANGE, "mm")
    _label(draw, (sx, sy + 34), "and we hear thunder", fonts, WHITE, "mm")


def tide_gauge(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    days = 2 * p
    level = 0.5 + 0.5 * math.sin(2 * math.pi * 2 * days)
    box(draw, -140, 0, 180, 130, 230, ang, BLUE, 34)
    h = 50 + 150 * level
    box(draw, -140, 0, 170, 120, h, ang, WATER[:3] + (220,), 175, wire=False)
    for k in range(5):
        a, b = pt(-30, 50 + k * 36, 0, ang), pt(-12, 50 + k * 36, 0, ang)
        draw.line((*a, *b), fill=_c(WHITE, 200), width=2)
    box(draw, -20, 0, 8, 8, 215, ang, GREY, 235, y0=0)
    sx, sy = pt(-140, h, 0, ang)
    _glow(draw, sx, sy, 10, _c(YELLOW, 230))
    pts = [pt(-290 + 300 * i / 80, 380 + 40 * math.sin(2 * math.pi * 2 * (2 * i / 80)), -140, ang) for i in range(81)]
    draw.line(pts, fill=_c(CYAN, 120), width=3)
    m = pt(-290 + 300 * (days / 2), 380 + 40 * math.sin(2 * math.pi * 2 * days), -140, ang)
    _glow(draw, *m, 12, _c(YELLOW, 235))
    word = "high tide" if level > 0.75 else ("low tide" if level < 0.25 else "water rising and falling")
    sx, sy = pt(-140, 0, 150, ang)
    _label(draw, (sx, sy), word, fonts, YELLOW, "mm")
    sx, sy = pt(190, 150, 0, ang)
    _label(draw, (sx + 20, sy), "tidal range:", fonts, WHITE, "mm")
    _label(draw, (sx + 20, sy + 34), "high minus low", fonts, WHITE, "mm")


def eclipse_shadow(draw, p, t, fonts, color):
    ang = view(t, sway=0.18, base=0.5)
    floor_grid(draw, ang, half=320, step=80)
    y = 250
    sun = pt(-270, y, 0, ang)
    _glow(draw, sun[0], sun[1], 56, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 40, YELLOW, 245)
    e = pt(-60, y, 0, ang)
    sh = [pt(-60, y, 56, ang), pt(300, y, 26, ang), pt(300, y, -26, ang), pt(-60, y, -56, ang)]
    draw.polygon(sh, fill=(5, 10, 25, 170), outline=_c(CYAN, 70))
    _solid(draw, e[0], e[1], 44, BLUE, 245)
    mx = _lerp(290, 120, p)
    m = pt(mx, y, 0, ang)
    inside = mx < 220
    _solid(draw, m[0], m[1], 24, (150, 60, 50, 240) if inside else GREY, 240)
    sx, sy = pt(0, 420, 0, ang)
    _label(draw, (sx, sy), "only in a lunar eclipse", fonts, CYAN, "mm")
    _label(draw, (sx, sy + 34), "does Earth's shadow fall on the Moon", fonts, WHITE, "mm")


MOTIFS_3D_J = {name: fn for name, fn in (
    ("daylight_fade", daylight_fade), ("lightning_bolt", lightning_bolt), ("heat_halo", heat_halo),
    ("pressure_wave", pressure_wave), ("tide_gauge", tide_gauge), ("eclipse_shadow", eclipse_shadow))}
