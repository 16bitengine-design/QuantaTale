"""Holographic 3D motifs, batch I: atomic jump, wave counting, El Nino winds, jet stream, hearing.

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


def _arr(draw: Any, a: tuple[float, float], b: tuple[float, float], color: Any, width: int = 4) -> None:
    draw.line((*a, *b), fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-0.5, 0.5):
        draw.line((*b, b[0] - 20 * math.cos(ang + s), b[1] - 20 * math.sin(ang + s)), fill=color, width=width)


def _ring_yz(draw: Any, x: float, y: float, z: float, r: float, ang: float, color: Any, width: int = 3) -> None:
    pts = [pt(x, y + r * math.sin(a), z + r * math.cos(a), ang) for a in [i * math.pi / 20 for i in range(41)]]
    draw.line(pts, fill=color, width=width)


def atom_jump(draw, p, t, fonts, color):
    ang = view(t, sway=0.25, base=0.45)
    floor_grid(draw, ang, half=300, step=75)
    cy0 = 330
    n = pt(0, cy0, 0, ang)
    jump = p > 0.5
    flash = max(0.0, 1 - abs(p - 0.5) * 8)
    _glow(draw, n[0], n[1], 34 + 40 * flash, _c(YELLOW if flash else RED, int(230 if not flash else 160 + 80 * flash)))
    _solid(draw, n[0], n[1], 22, RED, 245)
    for r in (130, 230):
        draw.line([pt(r * math.cos(a), cy0, r * math.sin(a), ang) for a in [i * math.pi / 30 for i in range(61)]],
                  fill=_c(GREY, 140), width=2)
    r = 230 if jump else 130
    a = t * 2.2
    ex, ey = pt(r * math.cos(a), cy0, r * math.sin(a), ang)
    _glow(draw, ex, ey, 16, _c(YELLOW, 160))
    _solid(draw, ex, ey, 9, YELLOW, 245)
    pts = [pt(-300 + 160 * i / 60, cy0 + 24 * math.sin(i * 0.7 - t * 8), 0, ang) for i in range(61)]
    draw.line(pts, fill=_c(CYAN, 230), width=4)
    _label(draw, (pt(-220, cy0 + 70, 0, ang)[0], pt(-220, cy0 + 70, 0, ang)[1]), "microwaves", fonts, CYAN, "mm")
    sx, sy = pt(0, 520, 0, ang)
    _label(draw, (sx, sy), "only at exactly the right frequency", fonts, WHITE, "mm")


def cycle_counter(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    for dz, a in ((-40, 90), (0, 230), (40, 90)):
        pts = [pt(-280 + 560 * i / 140, 250 + 55 * math.sin(i / 140 * 2 * math.pi * 8 - t * 4), dz, ang) for i in range(141)]
        draw.line(pts, fill=_c(CYAN, a), width=4 if dz == 0 else 2)
    reached = _lerp(-280, 280, min(1.0, p * 1.1))
    for k in range(17):
        x = -280 + k * 35
        on = x <= reached
        a0, a1 = pt(x, 160, 0, ang), pt(x, 340, 0, ang)
        draw.line((*a0, *a1), fill=_c(YELLOW if on else GREY, 210 if on else 70), width=3)
    sx, sy = pt(reached, 250, 0, ang)
    _glow(draw, sx, sy, 20, _c(YELLOW, 220))
    sx, sy = pt(0, 450, 0, ang)
    _label(draw, (sx, sy), "a fixed count of waves", fonts, YELLOW, "mm")
    sx, sy = pt(0, 60, 0, ang)
    _label(draw, (sx, sy), "marks exactly one second", fonts, WHITE, "mm")


def enso_winds(draw, p, t, fonts, color):
    ang = view(t, sway=0.18, base=0.45)
    floor_grid(draw, ang, half=320, step=80)
    box(draw, 0, 0, 380, 240, 26, ang, WATER[:3] + (190,), 170)
    box(draw, -225, 0, 70, 240, 44, ang, GREEN, 235)
    box(draw, 225, 0, 70, 240, 44, ang, GREEN, 235)
    shift = max(0.0, min(1.0, (p - 0.45) * 2.2))
    bx = _lerp(-110, 110, shift)
    for r, a in ((120, 55), (85, 100), (50, 170)):
        sx, sy = pt(bx, 28, 0, ang)
        draw.ellipse((sx - r, sy - r * 0.38, sx + r, sy + r * 0.38), fill=_c(ORANGE, a))
    weak = shift >= 0.5
    for k in range(4):
        x = -150 + k * 100
        a0, a1 = (x + 40, x - (20 if weak else 60))
        _arr(draw, pt(a0, 150, 0, ang), pt(a1, 150, 0, ang), _c(WHITE, 110 if weak else 235), 2 if weak else 5)
    for text, x in (("Indonesia", -190), ("South America", 190)):
        sx, sy = pt(x, 0, 160, ang)
        _label(draw, (sx, sy), text, fonts, WHITE, "mm")
    sx, sy = pt(0, 290, 0, ang)
    _label(draw, (sx, sy), "El Niño: winds weaken" if weak else "normal: winds push warm water west", fonts, CYAN, "mm")
    if weak:
        sx, sy = pt(0, 240, 0, ang)
        _label(draw, (sx, sy), "warm water piles up near South America", fonts, WHITE, "mm")


def jet_stream_shift(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    k = min(1.0, p * 1.4)
    box(draw, -130, 90, 200, 160, 6, ang, GREEN, 215)
    box(draw, 130, 90, 200, 160, 6, ang, (170, 120, 70, 255), 215)
    zc = _lerp(-120, 20, k)
    pts = [pt(-290 + 580 * i / 80, 330 + 14 * math.sin(i / 6 + t * 2), zc + 50 * math.sin(i / 9 + t), ang) for i in range(81)]
    draw.line(pts, fill=_c(CYAN, 235), width=7)
    for i in range(4):
        sx, sy = pt(-185 + i * 50, 200 + 14 * (i % 2), 90, ang)
        _solid(draw, sx, sy, 26, GREY, 215)
    for i in range(6):
        s = (t * 0.7 + i / 6) % 1.0
        sx, sy = pt(-185 + i * 36, 190 - 180 * s, 90, ang)
        draw.line((sx, sy, sx - 3, sy + 12), fill=_c(BLUE, 220), width=3)
    sx, sy = pt(-120, 0, 200, ang)
    _label(draw, (sx, sy), "more rain", fonts, BLUE, "mm")
    sx, sy = pt(190, 0, 200, ang)
    _label(draw, (sx, sy), "drought", fonts, ORANGE, "mm")
    sx, sy = pt(0, 420, 0, ang)
    _label(draw, (sx, sy), "the jet stream shifts", fonts, CYAN, "mm")


def ear_signal(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    for k in range(4):
        s = (t * 0.35 + k / 4) % 1.0
        x = _lerp(-290, -110, s)
        _ring_yz(draw, x, 250, 0, 40 + 25 * s, ang, _c(CYAN, int(230 * (1 - s))))
    ear = pt(-90, 250, 0, ang)
    _solid(draw, ear[0], ear[1], 38, WHITE, 240)
    nerve = [pt(-70 + 190 * i / 30, 250 + 20 * math.sin(i / 4), 0, ang) for i in range(31)]
    draw.line(nerve, fill=_c(GREY, 220), width=5)
    for k in range(5):
        s = (t * 0.6 + k / 5) % 1.0
        i = int(s * 30)
        _dot(draw, *nerve[i], 6, _c(YELLOW, 245))
    br = pt(200, 250, 0, ang)
    _glow(draw, br[0], br[1], 70, _c(CYAN, 60))
    _solid(draw, br[0], br[1], 54, (240, 150, 190, 240), 240)
    for text, x, y, col in (("sound waves", -230, 380, CYAN), ("ear", -90, 170, WHITE), ("auditory nerve", 60, 360, YELLOW), ("brain", 200, 170, WHITE)):
        sx, sy = pt(x, y, 0, ang)
        _label(draw, (sx, sy), text, fonts, col, "mm")


def hearing_protect(draw, p, t, fonts, color):
    ang = view(t, sway=0.18, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    arch = [pt(150 * math.cos(a), 240 + 150 * math.sin(a), 0, ang) for a in [math.pi * i / 30 for i in range(31)]]
    draw.line(arch, fill=_c(WHITE, 235), width=10)
    for x in (-150, 150):
        box(draw, x, 0, 50, 70, 120, ang, CYAN, 225, y0=180)
    _solid(draw, *pt(0, 250, 0, ang), 70, GREY, 120)
    for k in range(4):
        s = (t * 0.4 + k / 4) % 1.0
        x = _lerp(-290, -190, s)
        _ring_yz(draw, x, 240, 0, 50 + 30 * s, ang, _c(RED, int(230 * (1 - s))), 3)
    sx, sy = pt(0, 430, 0, ang)
    _label(draw, (sx, sy), "nearly always preventable", fonts, GREEN, "mm")
    sx, sy = pt(0, 70, 0, ang)
    _label(draw, (sx, sy), "get a hearing test every year", fonts, WHITE, "mm")
    _label(draw, (sx, sy + 34), "if noise is hazardous", fonts, WHITE, "mm")


MOTIFS_3D_I = {name: fn for name, fn in (
    ("atom_jump", atom_jump), ("cycle_counter", cycle_counter), ("enso_winds", enso_winds),
    ("jet_stream_shift", jet_stream_shift), ("ear_signal", ear_signal), ("hearing_protect", hearing_protect))}
