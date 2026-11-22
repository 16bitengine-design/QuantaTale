"""Holographic 3D motifs, batch K: one planet year, water in the body, light in water and sky, muddy water.

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
    th = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-0.5, 0.5):
        draw.line((*b, b[0] - 18 * math.cos(th + s), b[1] - 18 * math.sin(th + s)), fill=color, width=width)


def orbit_year(draw, p, t, fonts, color):
    ang = view(t, sway=0.15, base=0.5)
    floor_grid(draw, ang, half=320, step=80)
    sun = pt(0, 150, 0, ang)
    _glow(draw, sun[0], sun[1], 46, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 30, YELLOW, 245)
    R = 220
    draw.line([pt(R * math.cos(a), 150, R * math.sin(a), ang) for a in [i * math.pi / 30 for i in range(61)]],
              fill=_c(CYAN, 90), width=2)
    u = p * 2 * math.pi - math.pi / 2
    trail = [pt(R * math.cos(a), 150, R * math.sin(a), ang) for a in [-math.pi / 2 + (u + math.pi / 2) * i / 40 for i in range(41)]]
    if len(trail) > 1:
        draw.line(trail, fill=_c(ORANGE, 220), width=4)
    px, py = pt(R * math.cos(u), 150, R * math.sin(u), ang)
    _solid(draw, px, py, 22, (190, 160, 140, 240), 240)
    _label(draw, (px, py - 46), "Mercury", fonts, WHITE, "mm")
    _label(draw, (CX, 440), "one full lap around the Sun", fonts, YELLOW, "mm")
    _label(draw, (CX, 475), "one Mercury year", fonts, WHITE, "mm")


def water_carry(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    c = pt(0, 240, 0, ang)
    _glow(draw, c[0], c[1], 130, _c(CYAN, 40))
    _solid(draw, c[0], c[1], 90, (70, 170, 210, 200), 190)
    draw.ellipse((c[0] - 30, c[1] - 30, c[0] + 30, c[1] + 30), fill=_c((240, 200, 120), 230))
    for k in range(9):
        a = (t * 0.45 + k / 9) % 1.0
        y = 150 + (k % 3) * 80
        z = (k % 3 - 1) * 60
        x, y2 = pt(_lerp(-280, -100, a), y, z, ang)
        _dot(draw, x, y2, 7, _c(GREEN, int(240 * (1 - 0.3 * a))))
        x, y2 = pt(_lerp(100, 280, a), y, -z, ang)
        _dot(draw, x, y2, 7, _c(ORANGE, int(240 * (1 - 0.7 * a))))
    _label(draw, pt(-200, 360, 0, ang), "nutrients in", fonts, GREEN, "mm")
    _label(draw, pt(200, 360, 0, ang), "waste out", fonts, ORANGE, "mm")
    _label(draw, pt(0, 70, 0, ang), "water carries it all", fonts, WHITE, "mm")


def water_balance(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    level = 0.8 - 0.35 * min(1.0, p * 1.3)
    if p > 0.75:
        level += 0.4 * (p - 0.75)
    box(draw, -120, 0, 170, 130, 250, ang, BLUE, 34)
    box(draw, -120, 0, 160, 120, 20 + 220 * level, ang, WATER[:3] + (220,), 175, wire=False)
    for k, name in enumerate(("sweat", "bathroom", "breath")):
        y = 70 + k * 70
        _arr(draw, pt(-30, y, 0, ang), pt(110, y, 0, ang), _c(ORANGE, 220), 3)
        _label(draw, pt(190, y, 0, ang), name, fonts, ORANGE, "lm")
    if p > 0.75:
        _arr(draw, pt(-120, 400, 0, ang), pt(-120, 290, 0, ang), _c(CYAN, 235), 5)
        _label(draw, pt(-120, 430, 0, ang), "drinking refills it", fonts, CYAN, "mm")
    else:
        _label(draw, pt(-120, 330, 0, ang), "water leaves all day", fonts, WHITE, "mm")


def light_absorption(draw, p, t, fonts, color):
    ang = view(t, sway=0.18, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 340, 200, 300, ang, WATER[:3] + (130,), 70)
    colours = [(RED, 90), (ORANGE, 150), (YELLOW, 210), (GREEN, 260), (BLUE, 300)]
    for i, (col, depth) in enumerate(colours):
        x = -130 + i * 65
        reach = depth * min(1.0, p * 1.6 + 0.2)
        a, b = pt(x, 380, 0, ang), pt(x, 300, 0, ang)
        draw.line((*a, *b), fill=col, width=8)
        c = pt(x, 300 - reach, 0, ang)
        draw.line((*b, *c), fill=col, width=8)
        _glow(draw, c[0], c[1], 10, _c(col, 220))
    _label(draw, pt(0, 450, 0, ang), "white light enters water", fonts, WHITE, "mm")
    _label(draw, pt(-270, 230, 0, ang), "red fades first", fonts, RED, "mm")
    _label(draw, pt(0, -20, 160, ang), "blue travels deepest", fonts, BLUE, "mm")


def scattering_compare(draw, p, t, fonts, color):
    ang = view(t, sway=0.18, base=0.5)
    floor_grid(draw, ang, half=320, step=80)
    box(draw, -150, 0, 200, 160, 230, ang, CYAN, 26)
    box(draw, 150, 0, 200, 160, 230, ang, WATER[:3] + (190,), 120)
    a, b = pt(-250, 330, 0, ang), pt(-150, 140, 0, ang)
    draw.line((*a, *b), fill=_c(WHITE, 235), width=5)
    for i in range(14):
        th = (t * 0.6 + i * 0.5) % 6.28
        _dot(draw, *pt(-150 + 80 * math.cos(th + i), 130 + 70 * math.sin(th * 1.3 + i), 60 * math.sin(th + i * 2), ang), 5, _c(BLUE, 210))
    top = pt(120, 330, 0, ang)
    draw.line((*top, *pt(120, 330 - 250 * p, 0, ang)), fill=RED, width=6)
    draw.line((*pt(190, 330, 0, ang), *pt(190, 10, 0, ang)), fill=BLUE, width=6)
    _label(draw, pt(-150, 400, 0, ang), "sky: scattering", fonts, CYAN, "mm")
    _label(draw, pt(150, 400, 0, ang), "sea: absorption", fonts, CYAN, "mm")
    _label(draw, pt(0, 0, 220, ang), "two different effects", fonts, WHITE, "mm")


def sediment_colors(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    tints = [(40, 120, 215), (40, 170, 160), (80, 170, 80), (150, 120, 70)]
    pos = p * (len(tints) - 1)
    i = min(len(tints) - 2, int(pos))
    f = pos - i
    tint = tuple(int(tints[i][k] * (1 - f) + tints[i + 1][k] * f) for k in range(3))
    box(draw, 0, 0, 260, 180, 260, ang, CYAN, 36)
    box(draw, 0, 0, 250, 170, 220, ang, tint + (200,), 160, wire=False)
    for n in range(36):
        ph = (t * 0.2 + n * 0.07) % 1.0
        x, z = -110 + (n * 37) % 220, -70 + (n * 53) % 140
        _dot(draw, *pt(x, 220 - ph * 210, z, ang), 3 + n % 3, _c(WHITE, 170))
    _label(draw, pt(0, 330, 0, ang), "the colour shifts", fonts, WHITE, "mm")
    _label(draw, pt(0, 0, 200, ang), "with what the water carries", fonts, CYAN, "mm")


MOTIFS_3D_K = {name: fn for name, fn in (
    ("orbit_year", orbit_year), ("water_carry", water_carry), ("water_balance", water_balance),
    ("light_absorption", light_absorption), ("scattering_compare", scattering_compare),
    ("sediment_colors", sediment_colors))}
