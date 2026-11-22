"""Holographic 3D motifs, batch F: evaporation and clouds, hurricanes, glaciers, upwelling and geysers.

They replace the flat motifs of the same names, so existing topics upgrade without a spec change.
Labels never state a lone number.
"""

from __future__ import annotations

import math

from .holo3d import box, floor_grid, pt, view
from .visual_motifs import (BLUE, CX, CYAN, GREEN, GREY, ORANGE, RED, WATER, WHITE, YELLOW, _c, _dot, _glow, _label)
from .visual_motifs_3d import _solid
from .visual_motifs_3d_e import ROCK, SAND, _arrow3, _ring, _smooth


def _scene(t, sway=0.22, base=0.5):
    return view(t, sway=sway, base=base)


def evaporation(draw, p, t, fonts, color):
    ang = _scene(t)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 620, 260, 50, ang, WATER, 150)
    sx, sy = pt(240, 470, -60, ang)
    _glow(draw, sx, sy, 34, _c(YELLOW, 235))
    for i in range(26):
        s = (t * 0.3 + i * 0.137) % 1.0
        x, z = -280 + (i * 53) % 560, -100 + (i * 37) % 200
        px, py = pt(x + 16 * math.sin(s * 9 + i), 50 + 330 * s, z, ang)
        _dot(draw, px, py, 4 + 3 * s, _c(WHITE, int(220 * (1 - 0.6 * s))))
    lx, ly = pt(0, 10, 150, ang)
    _label(draw, (lx, ly + 36), "WATER", fonts, WHITE, "mm")


def rising_cooling(draw, p, t, fonts, color):
    ang = _scene(t, base=0.35)
    floor_grid(draw, ang, half=300, step=75)
    y = 60 + 330 * p
    r = 30 + 50 * p
    a, b = pt(-110, 30, 0, ang), pt(-110, 420, 0, ang)
    draw.line((*a, *b), fill=_c(WHITE, 150), width=3)
    sx, sy = pt(-110, y, 0, ang)
    _glow(draw, sx, sy, r + 14, _c(BLUE, 140))
    _solid(draw, sx, sy, r, BLUE, 215)
    hot = (255, 160, 60)
    cold = (90, 200, 255)
    mix = tuple(int(h + (c - h) * p) for h, c in zip(hot, cold))
    box(draw, 190, 0, 46, 46, 60 + 300 * (1 - 0.85 * p), ang, mix, 230)
    tx, ty = pt(190, 20, 0, ang)
    _label(draw, (tx, ty + 44), "TEMPERATURE", fonts, WHITE, "mm")
    _label(draw, (CX, 900), "AIR RISES, EXPANDS, COOLS", fonts, CYAN, "mm")


def condensation(draw, p, t, fonts, color):
    ang = _scene(t, base=0.4)
    floor_grid(draw, ang, half=300, step=75)
    nuclei = [(-150, 160, -60), (0, 230, 40), (150, 150, -30), (-80, 90, 80), (90, 80, -90)]
    k = min(1.0, p * 1.3)
    for i, (x, y, z) in enumerate(nuclei):
        sx, sy = pt(x, y, z, ang)
        r = 14 + 46 * p
        _solid(draw, sx, sy, r, (190, 230, 255), int(30 + 90 * p))
        draw.ellipse((sx - r, sy - r, sx + r, sy + r), outline=_c(CYAN, int(70 + 150 * p)), width=3)
        _dot(draw, sx, sy, 7, GREY)
        for j in range(8):
            a = j * 0.8 + i
            sx0, sy0 = pt(x + 170 * math.cos(a), y + 80 * math.sin(a * 1.3), z + 170 * math.sin(a), ang)
            _dot(draw, sx0 + (sx - sx0) * k, sy0 + (sy - sy0) * k, 4, _c(WHITE, 190))
    _label(draw, (CX, 900), "dust · sea salt · smoke", fonts, GREY, "mm")


def hurricane_engine(draw, p, t, fonts, color):
    ang = _scene(t, base=0.45)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 620, 260, 50, ang, WATER, 160)
    for k in range(12):
        s = (t * 0.45 + k / 12) % 1.0
        x, z = -250 + (k * 47) % 500, -90 + (k * 61) % 180
        a, b = pt(x, 50 + 230 * s, z, ang), pt(x, 90 + 230 * s, z, ang)
        draw.line((*b, *a), fill=_c(RED, 215), width=3)
        _dot(draw, b[0], b[1], 4, _c(RED, 235))
    for j in range(int(6 * p) + 1):
        sx, sy = pt(-250 + j * 100, 330 + 14 * (j % 2), (j % 3 - 1) * 40, ang)
        _solid(draw, sx, sy, 34, WHITE, 215)
    sx, sy = pt(0, 520, 0, ang)
    _label(draw, (sx, sy), "rising air cools and forms clouds", fonts, WHITE, "mm")


def hurricane_landfall(draw, p, t, fonts, color):
    ang = _scene(t, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, -165, 0, 330, 260, 40, ang, WATER, 170)
    box(draw, 165, 0, 300, 260, 40, ang, ROCK, 235)
    x = -200 + 400 * p
    over_land = x > 15
    size = 110 if not over_land else max(30.0, 110 - (x - 15) * 0.35)
    alpha = 225 if not over_land else int(max(70, 225 - (x - 15) * 0.5))
    for arm in range(3):
        pts = []
        for i in range(41):
            r = size * i / 40
            a = -t * 1.5 + arm * 2.1 - i * 0.18
            pts.append(pt(x + r * math.cos(a), 120, r * math.sin(a), ang))
        draw.line(pts, fill=_c(WHITE, alpha), width=7)
    ex, ey = pt(x, 120, 0, ang)
    _glow(draw, ex, ey, 10, _c(CYAN, 120))
    strength = 0.9 if not over_land else max(0.1, 0.9 - (x - 15) / 320)
    box(draw, -285, -150, 30, 30, 20 + 240 * strength, ang, RED, 230)
    _label(draw, (CX + 30, 560), "strong winds make it a hurricane", fonts, CYAN, "mm")
    _label(draw, (CX + 30, 600), "over land it loses its ocean fuel", fonts, WHITE, "mm")


def glacier_form(draw, p, t, fonts, color):
    ang = _scene(t, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    layers = 1 + int(5 * min(1.0, p * 1.2))
    y = 0.0
    for k in range(layers):
        h = max(12.0, 40 - k * 5 * (1.0 if p > 0.5 else 0.2))
        col = (235, 245, 255) if k >= layers - 2 else (150, 215, 255)
        box(draw, 0, 0, 440, 240, h, ang, col, 230 - k * 8, y0=y)
        y += h
    for k in range(12):
        s = (t * 0.4 + k / 12) % 1.0
        sx, sy = pt(-190 + (k * 71) % 380, y + 260 - 260 * s, -100 + (k * 41) % 200, ang)
        _dot(draw, sx, sy, 4, _c(WHITE, 230))
    sx, sy = pt(0, 420, 0, ang)
    _label(draw, (sx, sy), "snow piles up and packs into ice", fonts, WHITE, "mm")


def glacier_flow(draw, p, t, fonts, color):
    ang = _scene(t, base=0.7)
    floor_grid(draw, ang, half=300, step=75)

    def ground(x):
        return 40 + (300 - x) * 0.45

    slope = [pt(-300, ground(-300), -120, ang), pt(300, ground(300), -120, ang), pt(300, ground(300), 120, ang), pt(-300, ground(-300), 120, ang)]
    draw.polygon(slope, fill=ROCK)
    draw.polygon([pt(300, 0, -120, ang), pt(300, ground(300), -120, ang), pt(-300, ground(-300), -120, ang), pt(-300, 0, -120, ang)], fill=_c(SAND, 235))
    draw.line(slope + [slope[0]], fill=_c(WHITE, 120), width=2)
    shift = 40 * p
    xs = (-250 + shift, 200 + shift)
    quad = [pt(xs[0], ground(xs[0]) + 6, -100, ang), pt(xs[1], ground(xs[1]) + 6, -100, ang),
            pt(xs[1], ground(xs[1]) + 6, 100, ang), pt(xs[0], ground(xs[0]) + 6, 100, ang)]
    top = [pt(xs[0], ground(xs[0]) + 46, -100, ang), pt(xs[1], ground(xs[1]) + 46, -100, ang),
           pt(xs[1], ground(xs[1]) + 46, 100, ang), pt(xs[0], ground(xs[0]) + 46, 100, ang)]
    draw.polygon([quad[0], quad[1], top[1], top[0]], fill=_c((150, 215, 255), 200))
    draw.polygon(top, fill=_c((225, 245, 255), 215), outline=_c(WHITE, 160))
    for k in range(5):
        x0 = -200 + k * 90 + shift
        a, b = pt(x0, ground(x0) + 52, 0, ang), pt(x0 + 40, ground(x0 + 40) + 52, 0, ang)
        draw.line((*a, *b), fill=_c(WHITE, 230), width=4)
    for k in range(6):
        s = (t * 0.3 + k / 6) % 1.0
        sx, sy = pt(xs[1] + 10 + 50 * s, ground(xs[1] + 10 + 50 * s) + 6, (k % 3 - 1) * 40, ang)
        _dot(draw, sx, sy, 5, _c(GREY, 230))
    sx, sy = pt(0, 480, 0, ang)
    _label(draw, (sx, sy), "ice creeps downhill and grinds the ground", fonts, WHITE, "mm")


def upwelling(draw, p, t, fonts, color):
    ang = _scene(t, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 620, 260, 230, ang, WATER, 80)
    box(draw, -330, 0, 40, 260, 250, ang, ROCK, 235)
    strength = 1 - min(1.0, p * 1.3)
    for k in range(5):
        x = -200 + k * 100
        rise = 190 * strength
        if rise > 6:
            _arrow3(draw, (x, 20, 0), (x, 20 + rise, 0), ang, _c(CYAN, int(70 + 170 * strength)), 4)
    for k in range(int(14 * strength)):
        s = (t * 0.5 + k * 0.11) % 1.0
        sx, sy = pt(-250 + (k * 83) % 500, 30 + 190 * s, -100 + (k * 47) % 200, ang)
        _dot(draw, sx, sy, 4, _c(GREEN, 225))
    _arrow3(draw, (-260, 250, 100), (-60, 250, 100), ang, _c(WHITE, 220), 3)
    sx, sy = pt(0, 340, 0, ang)
    _label(draw, (sx, sy), "COLD, NUTRIENT-RICH WATER RISES", fonts, CYAN, "mm")
    _label(draw, (CX, 960), "in El Niño, upwelling weakens or stops", fonts, WHITE, "mm")


def geyser_eruption(draw, p, t, fonts, color):
    ang = _scene(t, base=0.45)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 340, 340, 26, ang, GREY, 170)
    height = 420 * math.sin(min(1.0, p * 1.2) * math.pi) ** 0.7
    for k in range(80):
        a = (k * 0.137 + t * 1.3) % 1.0
        reach = 0.45 + 0.55 * ((k * 37) % 10) / 10
        spread = 5 + 18 * a
        sx, sy = pt((k % 9 - 4) * spread, 26 + height * a * reach, ((k * 7) % 9 - 4) * spread, ang)
        _dot(draw, sx, sy, 5 + 4 * (1 - a), _c(WHITE, int(230 * (1 - a * 0.55))))
    sx, sy = pt(0, 560, 0, ang)
    _label(draw, (sx, sy), "predictable, but not a clock", fonts, YELLOW, "mm")


def geyser_cutaway(draw, p, t, fonts, color):
    ang = _scene(t, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 420, 240, 440, ang, GREY, 55)
    box(draw, 0, 0, 40, 40, 330, ang, WATER, 190, y0=110)
    box(draw, 0, 0, 170, 120, 100, ang, WATER, 190, y0=10)
    for k in range(14):
        s = (t * 0.5 + k * 0.17) % 1.0
        sx, sy = pt(-20 + (k % 5) * 10, 30 + s * 400 * (0.4 + 0.6 * p), (k % 3 - 1) * 12, ang)
        _dot(draw, sx, sy, 5, _c(WHITE, 200))
    hx, hy = pt(0, 20, 0, ang)
    _glow(draw, hx, hy, 46, _c(RED, int(70 + 130 * p)))
    sx, sy = pt(0, 520, 0, ang)
    _label(draw, (sx, sy), "heat below boils water that is trapped above", fonts, WHITE, "mm")


MOTIFS_3D_F = {name: fn for name, fn in (
    ("evaporation", evaporation), ("rising_cooling", rising_cooling), ("condensation", condensation),
    ("hurricane_engine", hurricane_engine), ("hurricane_landfall", hurricane_landfall), ("glacier_form", glacier_form),
    ("glacier_flow", glacier_flow), ("upwelling", upwelling), ("geyser_eruption", geyser_eruption),
    ("geyser_cutaway", geyser_cutaway))}
