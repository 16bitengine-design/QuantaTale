"""Holographic 3D motifs, batch D: the water cycle and rising sea level."""

from __future__ import annotations

import math
from typing import Any

from .holo3d import box, columns, floor_grid, pt, view
from .visual_motifs import BLUE, CYAN, GREEN, GREY, ORANGE, RED, WATER, WHITE, YELLOW, _c, _dot, _glow, _label
from .visual_motifs_3d import _solid


def _lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


def water_cycle_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, -165, 0, 270, 250, 40, ang, BLUE, 150)
    box(draw, 170, 0, 260, 250, 70, ang, GREEN, 215)
    box(draw, 215, 0, 110, 110, 70, ang, GREY, 230, y0=70)
    box(draw, 215, 0, 54, 54, 22, ang, WHITE, 235, y0=140)
    sun = pt(-270, 430, 0, ang)
    _glow(draw, sun[0], sun[1], 30, _c(YELLOW, 235))
    for i in range(9):
        s = (t * 0.28 + i * 0.111) % 1.0
        x, z = -270 + (i % 3) * 100, -80 + (i // 3) * 80
        sx, sy = pt(x + 30 * s, 40 + 300 * s, z, ang)
        _dot(draw, sx, sy, 4, _c(CYAN, int(230 * (1 - 0.6 * s))))
    for dx, dy, dz, r in ((-40, 360, -30, 34), (10, 380, 10, 42), (60, 360, 30, 34), (-10, 395, 40, 30), (30, 350, -40, 28)):
        sx, sy = pt(dx, dy, dz, ang)
        _solid(draw, sx, sy, r, WHITE, 215)
    for i in range(10):
        s = (t * 0.45 + i * 0.1) % 1.0
        x, z = 90 + (i % 5) * 45, -60 + (i // 5) * 90
        sx, sy = pt(x, 340 - 270 * s, z, ang)
        draw.line((sx, sy, sx, sy + 12), fill=_c(BLUE, 235), width=3)
    for i in range(6):
        s = (t * 0.22 + i * 0.17) % 1.0
        sx, sy = pt(_lerp(240, -60, s), _lerp(76, 44, s), (i - 2.5) * 12, ang)
        _dot(draw, sx, sy, 4, _c(WATER, 240))
    for text, x, y, col in (("evaporation", -250, 230, CYAN), ("condensation", 0, 470, WHITE), ("rain + snow", 200, 310, BLUE), ("runoff", 40, 20, WHITE)):
        sx, sy = pt(x, y, 0, ang)
        _label(draw, (sx, sy), text, fonts, col, "mm")


moisture_sources = columns([
    ("EVAPORATION", 90, CYAN, "NEARLY 90%"), ("PLANTS", 10, GREEN, "MOST OF THE REST")], rise=1.3)

water_stores = columns([
    ("OCEANS", 96.5, BLUE, "ABOUT 96.5%"), ("ICE", 1.7, WHITE, "1.7%"), ("GROUND + FRESH", 1.7, CYAN, "1.7%")], rise=1.3)

sea_level_causes = columns([
    ("OCEAN WARMING", 33, ORANGE, "ABOUT 1/3"), ("MELTING LAND ICE", 66, CYAN, "ABOUT 2/3")], rise=1.3)

sea_level_pace = columns([
    ("FIRST 10 CM: 1902–1992", 90, BLUE, "90 YEARS"), ("NEXT 10 CM: 1993–2023", 30, RED, "30 YEARS")], rise=1.3)


def ocean_expansion_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.6)
    floor_grid(draw, ang, half=300, step=75)
    warm = min(1.0, p / 0.5)
    melt = max(0.0, (p - 0.5) / 0.5)
    level = 150 + 55 * warm + 55 * melt
    box(draw, -60, 0, 360, 220, 330, ang, BLUE, 38)
    water = tuple(int(_lerp(a, b, warm)) for a, b in zip(WATER[:3], (255, 150, 70)))
    box(draw, -60, 0, 346, 206, level, ang, water, 170, wire=False)
    sx, sy = pt(-60, 150, 0, ang)
    top = pt(-60, level, 0, ang)
    draw.line((sx + 190, sy, sx + 190, top[1]), fill=_c(YELLOW, 220), width=3)
    _label(draw, (sx + 190, top[1] - 16), "level", fonts, YELLOW, "mm")
    box(draw, -120, 40, 70, 70, 32, ang, WHITE, 215, y0=level - 6)
    ice_h = 150 * (1 - melt)
    box(draw, 235, 0, 110, 150, 30, ang, GREEN, 215)
    if ice_h > 2:
        box(draw, 235, 0, 90, 130, ice_h, ang, WHITE, 230, y0=30)
    for i in range(6):
        s = (t * 0.5 + i * 0.17) % 1.0
        if melt > 0.05:
            sx, sy = pt(_lerp(190, 100, s), _lerp(60, level, s), (i - 2.5) * 20, ang)
            _dot(draw, sx, sy, 5, _c(CYAN, 235))
    for i in range(7):
        s = (t * 0.3 + i * 0.14) % 1.0
        if warm > 0.2:
            sx, sy = pt(-200 + i * 45, level - 20 + 40 * s, (i % 3 - 1) * 50, ang)
            _dot(draw, sx, sy, 4, _c(ORANGE, int(220 * warm)))
    msg = "warm water expands" if p < 0.5 else "land ice melts into the ocean"
    sx, sy = pt(-60, 380, 0, ang)
    _label(draw, (sx, sy), msg, fonts, ORANGE if p < 0.5 else CYAN, "mm")


MOTIFS_3D_D = {name: fn for name, fn in (
    ("water_cycle_3d", water_cycle_3d), ("moisture_sources", moisture_sources), ("water_stores", water_stores),
    ("sea_level_causes", sea_level_causes), ("sea_level_pace", sea_level_pace), ("ocean_expansion_3d", ocean_expansion_3d))}
