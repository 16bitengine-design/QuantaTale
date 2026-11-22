"""Holographic 3D motifs, batch E: earthquakes, tsunamis, plates and volcanoes.

These replace the flat motifs of the same names, so topics that already use them become 3D without any spec change.
Labels never state a lone number.
"""

from __future__ import annotations

import math
from typing import Any

from .holo3d import box, floor_grid, pt, view
from .visual_motifs import (BLUE, CX, CY, CYAN, GREEN, GREY, ORANGE, RED, WATER, WHITE, YELLOW, _arrow, _c, _dot, _glow,
                            _label, _proj)
from .visual_motifs_3d import _solid

ROCK = (125, 100, 75, 235)
SAND = (170, 140, 95, 235)


def _smooth(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _ring(draw, cx, y, r, ang, color, width=3, cz=0.0):
    pts = [pt(cx + r * math.cos(u), y, cz + r * math.sin(u), ang) for u in [math.tau * i / 40 for i in range(41)]]
    draw.line(pts, fill=color, width=width)


def _arrow3(draw, a, b, ang, color, width=4):
    _arrow(draw, *pt(*a, ang), *pt(*b, ang), color, width)


def _cone(draw, ang, radius_base, radius_top, height, color, alpha=190, cx=0.0, cz=0.0, y0=0.0, sides=28):
    base = [pt(cx + radius_base * math.cos(u), y0, cz + radius_base * math.sin(u), ang) for u in [math.tau * i / sides for i in range(sides + 1)]]
    top = [pt(cx + radius_top * math.cos(u), y0 + height, cz + radius_top * math.sin(u), ang) for u in [math.tau * i / sides for i in range(sides + 1)]]
    quads = []
    for i in range(sides):
        quad = [base[i], base[i + 1], top[i + 1], top[i]]
        quads.append((sum(q[1] for q in quad), quad, i))
    for _, quad, i in sorted(quads):
        shade = 0.55 + 0.25 * math.sin(i / sides * math.tau)
        draw.polygon(quad, fill=_c(tuple(int(ch * max(0.35, shade)) for ch in color[:3]), alpha))
    draw.line(top, fill=_c(WHITE, 120), width=2)


def _two_line(draw, xy, text, fonts, color):
    top, _, bottom = text.partition("|")
    _label(draw, (xy[0], xy[1] - 14), top, fonts, color, "mm")
    if bottom:
        _label(draw, (xy[0], xy[1] + 16), bottom, fonts, color, "mm")


def seafloor_quake(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.55)
    floor_grid(draw, ang, half=300, step=75)
    jitter = 7 * math.sin(t * 40) * max(0.0, 1 - p * 2)
    box(draw, -155, 0, 290, 260, 60, ang, ROCK, 235)
    box(draw, 155, 0, 290, 260, 60, ang, SAND, 235, y0=jitter)
    box(draw, 0, 0, 600, 260, 200, ang, WATER, 55, y0=60)
    for k in range(4):
        r = 30 + 200 * ((p * 1.6 + k * 0.25) % 1.0)
        _ring(draw, 0, 62, r, ang, _c(YELLOW, int(230 * (1 - r / 230))), 3)
    lift = 60 * _smooth(p * 1.6)
    for z in (-90, -30, 30, 90):
        pts = [pt(x, 260 + lift * math.exp(-((x / 140.0) ** 2)), z, ang) for x in range(-290, 291, 20)]
        draw.line(pts, fill=_c(WHITE, 220), width=3)
    sx, sy = pt(0, 360, 0, ang)
    _label(draw, (sx, sy), "sets off a giant wave", fonts, WHITE, "mm")


def tsunami_deep(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 620, 260, 190, ang, WATER, 70)
    for z in (-110, -55, 0, 55, 110):
        pts = [pt(x, 190 + 16 * math.sin(x / 95.0 - t * 2.4 - z / 160.0), z, ang) for x in range(-300, 301, 12)]
        draw.line(pts, fill=_c(WHITE, 230), width=3)
    run = (t * 0.3) % 1.0
    sx, sy = pt(-300 + 600 * run, 190 + 16 * math.sin((-300 + 600 * run) / 95.0 - t * 2.4), 0, ang)
    _glow(draw, sx, sy - 14, 11, _c(YELLOW, 240))
    bx, by = pt(60, 206, 40, ang)
    draw.polygon([(bx - 22, by), (bx + 22, by), (bx + 12, by + 12), (bx - 12, by + 12)], fill=_c(WHITE, 240))
    _label(draw, (CX, 640), "OUT AT SEA: LOW, FAST WAVES", fonts, YELLOW, "mm")
    _label(draw, (CX, 680), "barely a bump on the surface", fonts, WHITE, "mm")


def tsunami_shore(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.55)
    floor_grid(draw, ang, half=300, step=75)

    def ground(x):
        return max(0.0, (x + 300) * 170 / 600)
    for z0, z1 in ((-130, 130),):
        slope = [pt(-300, 0, z0, ang), pt(300, 170, z0, ang), pt(300, 170, z1, ang), pt(-300, 0, z1, ang)]
        draw.polygon(slope, fill=SAND)
        draw.polygon([pt(-300, 0, z1, ang), pt(300, 170, z1, ang), pt(300, 0, z1, ang)], fill=_c(ROCK, 235))
        draw.line(slope + [slope[0]], fill=_c(WHITE, 120), width=2)
    xc = -230 + 470 * p
    height = 20 + 100 * p
    for z in range(-130, 131, 26):
        pts = []
        for x in range(-300, 301, 10):
            base = max(ground(x), 56.0) if x < xc + 40 else ground(x)
            crest = height * math.exp(-(((x - xc) / (70 - 25 * p)) ** 2)) if x <= xc + 60 else 0.0
            if base > ground(x) or crest > 0:
                pts.append(pt(x, base + crest + 3, z, ang))
        if len(pts) > 1:
            draw.line(pts, fill=_c(WHITE, 225), width=3)
    sx, sy = pt(0, 300, 0, ang)
    _label(draw, (sx, sy), "reaching farther inland than usual", fonts, WHITE, "mm")


def seismograph_trace(draw, p, t, fonts, color):
    ang = view(t, sway=0.25, base=0.9)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 620, 200, 8, ang, WHITE, 45)
    shown = _smooth(p * 1.2)
    for off, alpha, width in ((0, 235, 4), (3, 120, 2)):
        pts = []
        for i in range(0, 121):
            if i / 120 > shown:
                break
            x = -300 + 600 * i / 120
            env = 0.0 if i < 40 else math.exp(-(i - 40) / 25)
            pts.append(pt(x, 10 + off, 80 * env * math.sin(i * 1.3), ang))
        if len(pts) > 1:
            draw.line(pts, fill=_c(CYAN, alpha), width=width)
    if shown > 0.3:
        px, py = pt(-300, 10, 0, ang)
        _dot(draw, px, py, 7, _c(YELLOW, 240))
    sx, sy = pt(0, 260, 0, ang)
    _label(draw, (sx, sy), "no one can predict the next one", fonts, WHITE, "mm")


def fault_stick_slip(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.6)
    floor_grid(draw, ang, half=300, step=75)
    stress = min(1.0, p * 1.6)
    slip = 0.0 if p < 0.6 else 70 * _smooth((p - 0.6) * 4)
    shake = 3 * math.sin(t * 40) if 0.6 <= p < 0.8 else 0.0
    box(draw, -135, 0, 270, 240, 150, ang, ROCK, 235)
    box(draw, 135, slip, 270, 240, 150, ang, SAND, 235, y0=shake)
    seam_a, seam_b = pt(0, 150, -125, ang), pt(0, 150, 125, ang)
    draw.line((*seam_a, *seam_b), fill=_c(RED, 235), width=4)
    if p < 0.6:
        _arrow3(draw, (-135, 170, -90), (-135, 170, 10), ang, _c(YELLOW, 235))
        _arrow3(draw, (135, 170, 90), (135, 170, -10), ang, _c(YELLOW, 235))
    box(draw, -280, -170, 30, 30, 30 + 190 * (stress if p < 0.6 else max(0.04, 1.0 - (p - 0.6) * 2.5)), ang, YELLOW, 230)
    sx, sy = pt(-280, 255, -170, ang)
    _label(draw, (sx, sy), "STRESS", fonts, YELLOW, "mm")
    if p >= 0.6:
        for k in range(3):
            r = 40 + 160 * (((p - 0.6) * 2 + k * 0.25) % 1.0)
            _ring(draw, 0, 154, r, ang, _c(WHITE, 160), 3)


def plates_globe(draw, p, t, fonts, color):
    r = 215
    yaw, tilt = t * 0.3, 0.35
    cells = []
    for la in range(-75, 90, 15):
        for lo in range(0, 360, 15):
            corners = []
            for dla, dlo in ((0, 0), (0, 15), (15, 15), (15, 0)):
                a, b = math.radians(la + dla), math.radians(lo + dlo)
                corners.append(_proj((math.cos(a) * math.cos(b), math.sin(a), math.cos(a) * math.sin(b)), CX, CY, r, yaw, tilt))
            depth = sum(c[2] for c in corners) / 4
            plate = (int((lo + 20 * math.sin(math.radians(la * 3))) // 60) + (3 if la >= 0 else 0)) % 6
            cells.append((depth, corners, plate))
    shades = [GREEN, ORANGE, YELLOW, RED, CYAN, WHITE]
    for depth, corners, plate in sorted(cells, key=lambda c: c[0]):
        if depth > 0:
            draw.polygon([(c[0], c[1]) for c in corners], fill=_c(shades[plate], 105), outline=_c(shades[plate], 150))
    draw.ellipse((CX - r, CY - r, CX + r, CY + r), outline=_c(CYAN, 210), width=3)
    _label(draw, (CX, CY + r + 50), "EARTH'S SHELL IS BROKEN INTO PLATES", fonts, CYAN, "mm")


def _pyramid(draw, cx, cz, base, height, ang, color, alpha=235, y0=0.0):
    pts = [(cx - base, cz - base), (cx + base, cz - base), (cx + base, cz + base), (cx - base, cz + base)]
    low = [pt(x, y0, z, ang) for x, z in pts]
    apex = pt(cx, y0 + height, cz, ang)
    faces = [(sum(q[1] for q in (low[i], low[(i + 1) % 4], apex)), [low[i], low[(i + 1) % 4], apex], i) for i in range(4)]
    for _, face, i in sorted(faces):
        draw.polygon(face, fill=_c(tuple(int(ch * (0.6 + 0.15 * (i % 2))) for ch in color[:3]), alpha))
        draw.line(face + [face[0]], fill=_c(WHITE, 100), width=1)


def plates_boundary(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.55)
    floor_grid(draw, ang, half=300, step=75)
    shift = 40 * p
    box(draw, -175 + shift, 0, 290, 220, 70, ang, _c(ORANGE, 220), 220)
    box(draw, 175 - shift, 0, 290, 220, 70, ang, _c(GREEN, 220), 220)
    _arrow3(draw, (-235, 95, 0), (-150, 95, 0), ang, WHITE)
    _arrow3(draw, (235, 95, 0), (150, 95, 0), ang, WHITE)
    if p > 0.5:
        _pyramid(draw, 0, 0, 40, 90 * (p - 0.5) * 2, ang, WHITE, 230, y0=70)
    sx, sy = pt(0, 250, 0, ang)
    _label(draw, (sx, sy), "slow, steady push", fonts, WHITE, "mm")


def plates_timelapse(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.55)
    floor_grid(draw, ang, half=300, step=75)
    gap = 110 * (1 - p)
    box(draw, -190 - gap / 2, 0, 270, 220, 70, ang, _c(ORANGE, 220), 220)
    box(draw, 190 + gap / 2, 0, 270, 220, 70, ang, _c(GREEN, 220), 220)
    _pyramid(draw, 0, 0, 70 * min(1.0, p * 1.4) + 8, 210 * p, ang, WHITE, int(90 + 140 * p), y0=70)
    sx, sy = pt(0, 330, 0, ang)
    _label(draw, (sx, sy), "OVER MILLIONS OF YEARS", fonts, YELLOW, "mm")


def magma_rise(draw, p, t, fonts, color):
    ang = view(t, sway=0.25, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    _cone(draw, ang, 260, 55, 250, ROCK, 120)
    cx, cy = pt(0, 70, 0, ang)
    _glow(draw, cx, cy, 70, _c(ORANGE, 150))
    _solid(draw, cx, cy, 52, ORANGE, 230)
    top = 70 + 180 * min(1.0, p * 1.4)
    a, b = pt(0, 100, 0, ang), pt(0, top, 0, ang)
    draw.line((*a, *b), fill=_c(ORANGE, 240), width=14)
    draw.line((*a, *b), fill=_c(YELLOW, 220), width=5)
    if p > 0.7:
        for k in range(12):
            s = (t * 1.5 + k / 12) % 1.0
            sx, sy = pt((k % 6 - 2.5) * 22 * s, 320 + 150 * s, (k % 3 - 1) * 18 * s, ang)
            _dot(draw, sx, sy, 6, _c(ORANGE, int(230 * (1 - s))))
    sx, sy = pt(0, 560, 0, ang)
    _label(draw, (sx, sy), "molten rock climbs from below", fonts, WHITE, "mm")


def gas_pressure(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.45)
    floor_grid(draw, ang, half=300, step=75)
    for side, (x, name, sticky) in enumerate(((-190, "THIN, RUNNY|FLOWS", False), (190, "THICK, STICKY|EXPLODES", True))):
        box(draw, x, 0, 170, 170, 230, ang, (150, 70, 40) if sticky else ORANGE, 120)
        for k in range(10):
            a = (t * (0.35 if sticky else 0.6) + k / 10) % 1.0
            bx = x - 70 + (k * 37) % 140
            bz = (k * 53) % 120 - 60
            if sticky:
                y = 30 + 90 * a * (0.3 + 0.7 * min(1.0, p))
            else:
                y = 30 + 200 * a
            sx, sy = pt(bx, y, bz, ang)
            _dot(draw, sx, sy, 6, _c(WHITE, 210 if sticky else int(230 * (1 - a * 0.6))))
        if sticky and p > 0.7:
            for k in range(14):
                a = (t * 2 + k / 14) % 1.0
                sx, sy = pt(x + (k % 7 - 3) * 28 * a, 240 + 170 * a, (k % 3 - 1) * 30 * a, ang)
                _dot(draw, sx, sy, 7, _c(GREY, int(230 * (1 - a))))
            sx, sy = pt(x, 235, 0, ang)
            _glow(draw, sx, sy, 24, _c(RED, 160))
        sx, sy = pt(x, 330, 0, ang)
        _two_line(draw, (sx, sy - 60), name, fonts, WHITE)


MOTIFS_3D_E = {name: fn for name, fn in (
    ("seafloor_quake", seafloor_quake), ("tsunami_deep", tsunami_deep), ("tsunami_shore", tsunami_shore),
    ("seismograph_trace", seismograph_trace), ("fault_stick_slip", fault_stick_slip), ("plates_globe", plates_globe),
    ("plates_boundary", plates_boundary), ("plates_timelapse", plates_timelapse), ("magma_rise", magma_rise),
    ("gas_pressure", gas_pressure))}
