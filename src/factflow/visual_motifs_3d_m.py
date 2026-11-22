"""Holographic 3D motifs, batch M: seasons, how the Sun shines, asteroid deflection, the Moon's near side, Saturn's rings.

Words only on screen; no numbers.
"""

from __future__ import annotations

import math
from typing import Any

from .holo3d import floor_grid, pt, view
from .visual_motifs import BLUE, CX, CYAN, GREEN, GREY, ORANGE, RED, WHITE, YELLOW, _c, _dot, _glow, _label
from .visual_motifs_3d import _solid


def _lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


def _ring(draw: Any, ang: float, r: float, y: float, color: Any, width: int = 2, cx: float = 0.0) -> None:
    draw.line([pt(cx + r * math.cos(a), y, r * math.sin(a), ang) for a in [i * math.pi / 30 for i in range(61)]], fill=color, width=width)


def seasons_tilt_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.12, base=0.55)
    floor_grid(draw, ang, half=320, step=80)
    sun = pt(0, 150, 0, ang)
    _glow(draw, sun[0], sun[1], 56, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 38, YELLOW, 245)
    R = 270
    _ring(draw, ang, R, 150, _c(CYAN, 90))
    tilt = math.radians(23.5)
    for k in range(4):
        a = k * math.pi / 2 + p * 2 * math.pi
        x, z = R * math.cos(a), R * math.sin(a)
        ex, ey = pt(x, 150, z, ang)
        # the axis points the same way at every point on the orbit
        a0, a1 = pt(x - 80 * math.sin(tilt), 150 - 80 * math.cos(tilt), z, ang), pt(x + 80 * math.sin(tilt), 150 + 80 * math.cos(tilt), z, ang)
        draw.line((*a0, *a1), fill=_c(WHITE, 200), width=3)
        _solid(draw, ex, ey, 30, BLUE, 240)
    _label(draw, (CX, 420), "Earth's axis always leans the same way", fonts, WHITE, "mm")
    _label(draw, (CX, 455), "so each half takes turns leaning toward the Sun", fonts, CYAN, "mm")


def fusion_core_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.12, base=0.45)
    floor_grid(draw, ang, half=300, step=75)
    c = pt(0, 330, 0, ang)
    R = 130
    _glow(draw, c[0], c[1], R + 5, _c(ORANGE, 60))
    _solid(draw, c[0], c[1], R, (240, 150, 40, 230), 200)
    _glow(draw, c[0], c[1], 40, _c(YELLOW, 120))
    _solid(draw, c[0], c[1], 30, YELLOW, 245)
    for k in range(8):
        s = (t * 0.35 + k / 8) % 1.0
        a = k * math.pi / 4 + 0.3
        r = _lerp(110, 8, s)
        _dot(draw, c[0] + r * math.cos(a), c[1] + r * math.sin(a) * 0.8, 6, _c(WHITE, 235))
    for k in range(6):
        s = (t * 0.5 + k / 6) % 1.0
        a = k * math.pi / 3 + 1.0
        r = _lerp(20, 170, s)
        _dot(draw, c[0] + r * math.cos(a), c[1] + r * math.sin(a), 4, _c(YELLOW, int(240 * (1 - s))))
    _label(draw, (CX, 860), "hydrogen fuses into helium", fonts, WHITE, "mm")
    _label(draw, (CX, 895), "and releases energy", fonts, YELLOW, "mm")


def dart_impact_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.15, base=0.5)
    floor_grid(draw, ang, half=320, step=80)
    big = pt(0, 150, 0, ang)
    _solid(draw, big[0], big[1], 60, (170, 150, 130, 240), 240)
    hit = p >= 0.5
    after = max(0.0, (p - 0.5) / 0.5)
    r = _lerp(210, 165, min(1.0, after * 2))
    _ring(draw, ang, 210, 150, _c(GREY, 110 if hit else 140))
    if hit:
        _ring(draw, ang, r, 150, _c(ORANGE, 220), 3)
    a = 2 * math.pi * p + 2.5 * after
    mx, my = pt(r * math.cos(a), 150, r * math.sin(a), ang)
    if p < 0.5:
        k = p / 0.5
        impact = pt(-210, 150, 0, ang)
        sx, sy = pt(_lerp(-330, -210, k), 150, 0, ang)
        draw.line((sx - 40, sy, sx, sy), fill=_c(CYAN, 150), width=3)
        draw.rectangle((sx - 10, sy - 7, sx + 10, sy + 7), fill=_c(CYAN, 245))
    elif after < 0.15:
        _glow(draw, mx, my, 40 * (1 - after / 0.15) + 12, _c(YELLOW, 220))
    _solid(draw, mx, my, 20, GREY, 245)
    _label(draw, (CX, 440), "a spacecraft crashes into the small moon", fonts, CYAN, "mm")
    _label(draw, (CX, 475), "and its orbit changes", fonts, ORANGE if hit else WHITE, "mm")


def moon_lock_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.1, base=0.55)
    floor_grid(draw, ang, half=320, step=80)
    e = pt(0, 150, 0, ang)
    _solid(draw, e[0], e[1], 54, BLUE, 245)
    R = 260
    _ring(draw, ang, R, 150, _c(CYAN, 90))
    for k, a0 in enumerate((0.0, math.pi / 2, math.pi, 3 * math.pi / 2)):
        a = a0 + p * 2 * math.pi
        mx, my = pt(R * math.cos(a), 150, R * math.sin(a), ang)
        _solid(draw, mx, my, 28, GREY, 235)
        ex, ey = pt(R * math.cos(a) * 0.86, 150, R * math.sin(a) * 0.86, ang)
        _dot(draw, ex, ey, 6, _c(RED, 245))
    _label(draw, (CX, 440), "the Moon turns once each time it circles Earth", fonts, WHITE, "mm")
    _label(draw, (CX, 475), "so the same face always looks at us", fonts, RED, "mm")


def saturn_rings_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.1, base=0.6)
    c = pt(0, 300, 0, ang)
    parts = []
    for i in range(260):
        r = 150 + (i * 37) % 190
        if 260 < r < 280:
            r += 25
        a = i * 2.399 + t * (1.6 * (180 / r))
        x, z = r * math.cos(a), r * math.sin(a) * 0.95
        sx, sy = pt(x, 300 + ((i * 13) % 7 - 3), z, ang)
        parts.append((sy, sx, 3 + (i % 3), i))
    for sy, sx, rad, i in parts:
        if sy < c[1]:
            _dot(draw, sx, sy, rad, _c((220, 205, 180), 190))
    _solid(draw, c[0], c[1], 100, (225, 190, 120, 240), 240)
    for sy, sx, rad, i in parts:
        if sy >= c[1]:
            _dot(draw, sx, sy, rad, _c((235, 220, 190), 230))
    _label(draw, (CX, 410), "rings of ice chunks, from specks to mountains", fonts, WHITE, "mm")
    _label(draw, (CX, 445), "wide, yet very thin", fonts, CYAN, "mm")


MOTIFS_3D_M = {name: fn for name, fn in (
    ("seasons_tilt_3d", seasons_tilt_3d), ("fusion_core_3d", fusion_core_3d), ("dart_impact_3d", dart_impact_3d),
    ("moon_lock_3d", moon_lock_3d), ("saturn_rings_3d", saturn_rings_3d))}
