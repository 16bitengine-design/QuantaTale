"""Holographic 3D motifs, batch L: the last flat motifs (ozone, flares, twinkling, aurora, sleep, salt, heat, blood).

Same names as the flat motifs, so existing topics upgrade without a spec change. Words only on screen.
"""

from __future__ import annotations

import math
from typing import Any

from .holo3d import box, floor_grid, pt, view
from .visual_motifs import BLUE, CX, CYAN, GREEN, GREY, ORANGE, RED, WATER, WHITE, YELLOW, _c, _dot, _glow, _label
from .visual_motifs_3d import _solid
from .visual_motifs_3d_g import aurora_curtains_3d

ROCK = (150, 120, 90, 255)


def _lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


def _arr(draw: Any, a: tuple[float, float], b: tuple[float, float], color: Any, width: int = 4) -> None:
    draw.line((*a, *b), fill=color, width=width)
    th = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-0.5, 0.5):
        draw.line((*b, b[0] - 16 * math.cos(th + s), b[1] - 16 * math.sin(th + s)), fill=color, width=width)


def _setup(draw: Any, t: float, sway: float = 0.2, base: float = 0.5, half: float = 300, step: float = 75) -> float:
    ang = view(t, sway=sway, base=base)
    floor_grid(draw, ang, half=half, step=step)
    return ang


def interval_timeline(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    box(draw, 0, 0, 560, 24, 10, ang, GREY, 200, y0=100)
    for x in (-250, 20, 260):
        sx, sy = pt(x, 110, 0, ang)
        _glow(draw, sx, sy, 14, _c(CYAN, 230))
    k1, k2 = min(1.0, p * 2), max(0.0, min(1.0, p * 2 - 0.6))
    _arr(draw, pt(-245, 190, 0, ang), pt(_lerp(-245, 15, k1), 190, 0, ang), _c(YELLOW, 235), 5)
    _arr(draw, pt(30, 190, 0, ang), pt(_lerp(30, 255, k2), 190, 0, ang), _c(ORANGE, 235), 5)
    _label(draw, pt(-115, 260, 0, ang), "shorter wait", fonts, YELLOW, "mm")
    _label(draw, pt(140, 260, 0, ang), "longer wait", fonts, ORANGE, "mm")


def gravity_surface(draw, p, t, fonts, color):
    _setup(draw, t, half=1)
    cx, cy, R = CX, 640, 200
    rot = t * 0.4

    def rad(a: float, b: float) -> float:
        return R * (1 + 0.06 * math.sin(a * 5 + t) * math.cos(b * 3) + 0.04 * math.sin(a * 9 - t * 1.4 + b * 2))

    def proj(a: float, b: float):
        r = rad(a, b)
        x, y, z = r * math.cos(b) * math.cos(a + rot), r * math.sin(b), r * math.cos(b) * math.sin(a + rot)
        return cx + x, cy - y * 0.95 + z * 0.2, z
    _glow(draw, cx, cy, R, _c(BLUE, 70))
    draw.ellipse((cx - R * 0.9, cy - R * 0.9, cx + R * 0.9, cy + R * 0.9), fill=_c(BLUE, 70))
    for lat in range(-60, 61, 30):
        b = math.radians(lat)
        pts = [proj(i * math.pi / 24, b) for i in range(49)]
        for p0, p1 in zip(pts, pts[1:]):
            near = (p0[2] + p1[2]) > 0
            draw.line((p0[0], p0[1], p1[0], p1[1]), fill=_c(CYAN, 200 if near else 45), width=2 if near else 1)
    for lon in range(0, 180, 30):
        a = math.radians(lon)
        pts = [proj(a if i < 25 else a + math.pi, -math.pi / 2 + (i % 25) * math.pi / 24 if i < 25 else math.pi / 2 - (i - 25) * math.pi / 24) for i in range(49)]
        for p0, p1 in zip(pts, pts[1:]):
            near = (p0[2] + p1[2]) > 0
            draw.line((p0[0], p0[1], p1[0], p1[1]), fill=_c(CYAN, 200 if near else 45), width=2 if near else 1)
    _label(draw, (CX, 930), "mountains, trenches and gravity", fonts, CYAN, "mm")
    _label(draw, (CX, 965), "the real shape is irregular", fonts, WHITE, "mm")


def cfc_cycle(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    n = int(1 + 5 * min(1.0, p * 1.2))
    for k in range(5):
        x = -240 + k * 120
        alive = k >= n
        sx, sy = pt(x, 130, 0, ang)
        col = BLUE if alive else GREY
        _solid(draw, sx, sy, 24, col, 235 if alive else 90)
        for dx in (-22, 22):
            _solid(draw, sx + dx, sy + 14, 12, col, 235 if alive else 90)
        if alive:
            _label(draw, (sx, sy + 56), "ozone", fonts, WHITE, "mm")
    cx = -240 + min(4, n - 1) * 120
    sx, sy = pt(cx, 250 + 14 * math.sin(t * 6), 0, ang)
    _glow(draw, sx, sy, 26, _c(GREEN, 230))
    _solid(draw, sx, sy, 16, GREEN, 245)
    _label(draw, (sx, sy - 42), "chlorine", fonts, GREEN, "mm")
    _label(draw, pt(0, 400, 0, ang), "one chlorine atom, again and again", fonts, WHITE, "mm")


def ozone_hole_patch(draw, p, t, fonts, color):
    cx, cy, R = CX, 640, 150
    _setup(draw, t, half=1)
    _glow(draw, cx, cy, R + 40, _c(CYAN, 40))
    draw.ellipse((cx - R - 36, cy - R - 36, cx + R + 36, cy + R + 36), outline=_c(CYAN, 120), width=2)
    _solid(draw, cx, cy, R, (30, 90, 170, 240), 240)
    for k in range(5):
        a = t * 0.3 + k * math.pi / 5
        w = R * abs(math.cos(a))
        draw.ellipse((cx - w, cy - R, cx + w, cy + R), outline=_c(WHITE, 40), width=1)
    r = 30 + 90 * min(1.0, p * 1.3)
    py = cy + R * 0.82
    draw.ellipse((cx - r, py - r * 0.35, cx + r, py + r * 0.35), fill=_c(RED, 150), outline=_c(RED, 230), width=2)
    _label(draw, (cx, cy + 250), "a thin patch over Antarctica", fonts, RED, "mm")
    _label(draw, (cx, 430), "the ozone \"hole\" is a thinning", fonts, CYAN, "mm")


def flare_travel(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    sun = pt(-250, 200, 0, ang)
    _glow(draw, sun[0], sun[1], 64, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 44, YELLOW, 245)
    e = pt(250, 200, 0, ang)
    _solid(draw, e[0], e[1], 30, BLUE, 245)
    x = _lerp(-200, 220, p)
    a, b = pt(-200, 200, 0, ang), pt(x, 200, 0, ang)
    draw.line((*a, *b), fill=_c(WHITE, 200), width=4)
    _glow(draw, b[0], b[1], 12, _c(YELLOW, 240))
    _label(draw, pt(0, 540, 0, ang), "travelling at the speed of light", fonts, YELLOW, "mm")
    _label(draw, pt(0, 500, 0, ang), "the flare's energy reaches Earth", fonts, WHITE, "mm")


def star_beam(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    s = pt(0, 480, 0, ang)
    _glow(draw, s[0], s[1], 36, _c(YELLOW, 240))
    _solid(draw, s[0], s[1], 14, YELLOW, 250)
    draw.line((*pt(0, 460, 0, ang), *pt(0, 60, 0, ang)), fill=_c(YELLOW, 150), width=5)
    for k in range(3):
        sy = (t * 0.5 + k / 3) % 1.0
        _dot(draw, *pt(0, _lerp(460, 60, sy), 0, ang), 5, _c(WHITE, 230))
    box(draw, 0, 0, 40, 40, 30, ang, CYAN, 225)
    _label(draw, pt(0, 520, 0, ang), "a star's steady light", fonts, WHITE, "mm")


def star_twinkle(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    s = pt(0, 480, 0, ang)
    _glow(draw, s[0], s[1], 30, _c(YELLOW, 240))
    for k, y in enumerate((120, 190, 260)):
        box(draw, 0, 0, 340, 200, 8, ang, CYAN, 60, y0=y, wire=True)
    pts = [pt(0, 470, 0, ang)]
    x = 0.0
    for y in (330, 260, 190, 120, 40):
        x = 26 * math.sin(t * 7 + y * 0.05)
        pts.append(pt(x, y, 0, ang))
    draw.line(pts, fill=_c(YELLOW, 200), width=4)
    _glow(draw, pts[-1][0], pts[-1][1] + 6 * math.sin(t * 11), 10 + 3 * math.sin(t * 13), _c(WHITE, 240))
    _label(draw, pt(0, 540, 0, ang), "moving air bends the light", fonts, CYAN, "mm")


def twinkle_compare(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    box(draw, -150, 0, 200, 150, 8, ang, CYAN, 70, y0=150)
    gx = pt(-150 + 10 * math.sin(t * 9), 300 + 8 * math.cos(t * 11), 0, ang)
    _glow(draw, gx[0], gx[1], 12 + 4 * math.sin(t * 13), _c(WHITE, 240))
    sx = pt(150, 300, 0, ang)
    _glow(draw, sx[0], sx[1], 12, _c(WHITE, 240))
    _label(draw, pt(-150, 400, 0, ang), "from the ground", fonts, CYAN, "mm")
    _label(draw, pt(150, 400, 0, ang), "from space", fonts, CYAN, "mm")
    _label(draw, pt(-150, 60, 80, ang), "twinkles", fonts, YELLOW, "mm")
    _label(draw, pt(150, 60, 80, ang), "steady", fonts, GREEN, "mm")


def aurora_particles(draw, p, t, fonts, color):
    ang = _setup(draw, t, sway=0.15)
    sun = pt(-270, 300, 0, ang)
    _glow(draw, sun[0], sun[1], 46, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 32, YELLOW, 245)
    e = pt(210, 300, 0, ang)
    _solid(draw, e[0], e[1], 56, BLUE, 240)
    for k, rr in enumerate((80, 105, 130)):
        pts = [pt(210 - rr * 1.5 * math.sin(u) * 0.5, 300 + rr * 1.1 * math.cos(u), 0, ang) for u in [0.3 + 2.5 * i / 30 for i in range(31)]]
        draw.line(pts, fill=_c(CYAN, 130 - 25 * k), width=2)
    for k in range(10):
        s = (t * 0.4 + k / 10) % 1.0
        x = _lerp(-230, 150, s)
        y = 300 + (k % 5 - 2) * 30 * (1 - s)
        if s > 0.8:
            y = _lerp(y, 420, (s - 0.8) / 0.2)
        _dot(draw, *pt(x, y, (k % 3 - 1) * 30, ang), 5, _c(YELLOW, 225))
    for k in range(8):
        s = (t * 0.7 + k / 8) % 1.0
        _dot(draw, *pt(205, 360 + 90 * s, 0, ang), 4, _c(GREEN, int(230 * (1 - 0.4 * s))))
    _label(draw, pt(0, 520, 0, ang), "solar wind guided to the poles", fonts, WHITE, "mm")


aurora_colours = aurora_curtains_3d


def sleep_vitals(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    for row, (name, col, base) in enumerate((("heart rate", RED, 330), ("blood pressure", ORANGE, 160))):
        n = int(61 * min(1.0, p * 1.3 + 0.05))
        pts = [pt(-260 + 520 * i / 60, base - 50 * min(1.0, i / 60 * 1.4) + 8 * math.sin(i / 3 + t * 3 + row), (row - 0.5) * 120, ang) for i in range(n)]
        if len(pts) > 1:
            draw.line(pts, fill=_c(col, 235), width=5)
            _glow(draw, *pts[-1], 10, _c(col, 220))
        _label(draw, pt(-200, base + 60, (row - 0.5) * 120, ang), name, fonts, col, "mm")
    _label(draw, pt(0, 560, 0, ang), "both ease down during sleep", fonts, WHITE, "mm")


def sleep_memory(draw, p, t, fonts, color):
    ang = _setup(draw, t, sway=0.3)
    nodes = [(190 * math.cos(k * 0.9), 260 + 120 * math.sin(k * 1.3), 150 * math.sin(k * 0.7)) for k in range(12)]
    scr = [pt(x, y, z, ang) for x, y, z in nodes]
    lit = int(12 * min(1.0, p * 1.3))
    for i in range(lit):
        for j in range(i):
            if (i + j) % 3 == 0:
                draw.line((*scr[i], *scr[j]), fill=_c(CYAN, 120), width=2)
    for i, (x, y) in enumerate(scr):
        _glow(draw, x, y, 12, _c(YELLOW, 235) if i < lit else _c(GREY, 120))
    _label(draw, pt(0, 450, 0, ang), "and supports learning", fonts, WHITE, "mm")


def salt_sources(draw, p, t, fonts, color):
    ang = _setup(draw, t, sway=0.18)
    box(draw, 190, 0, 160, 220, 24, ang, WATER[:3] + (190,), 150)
    box(draw, -160, 0, 180, 220, 120, ang, ROCK, 235)
    for k in range(6):
        s = (t * 0.6 + k / 6) % 1.0
        _dot(draw, *pt(-210 + k * 20, 320 - 200 * s, (k % 3 - 1) * 40, ang), 3, _c(CYAN, 220))
    draw.line((*pt(-70, 100, 0, ang), *pt(110, 22, 0, ang)), fill=_c(BLUE, 230), width=5)
    for k in range(4):
        x = 150 + k * 28
        draw.line((*pt(x, 0, -40 + k * 25, ang), *pt(x, 20 + 18 * math.sin(t * 3 + k) + 20, -40 + k * 25, ang)), fill=_c(ORANGE, 220), width=5)
    for k in range(int(60 * p)):
        _dot(draw, *pt(130 + (k * 53) % 120, 8 + (k * 17) % 16, -100 + (k * 37) % 200, ang), 3, _c(WHITE, 220))
    _label(draw, pt(-160, 0, 150, ang), "rocks and rivers", fonts, WHITE, "mm")
    _label(draw, pt(190, 0, 150, ang), "seafloor vents", fonts, ORANGE, "mm")


def dense_float(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    box(draw, 0, 0, 520, 240, 120, ang, WATER[:3] + (190,), 140)
    bob = 6 * math.sin(t * 2)
    box(draw, 0, 0, 170, 40, 28, ang, ORANGE, 235, y0=100 + bob)
    _solid(draw, *pt(105, 130 + bob, 0, ang), 18, ORANGE, 235)
    for k in range(40):
        _dot(draw, *pt(-240 + (k * 71) % 480, 10 + (k * 43) % 100, -100 + (k * 29) % 200, ang), 3, _c(WHITE, 150))
    _label(draw, pt(0, 330, 0, ang), "the extremely salty Dead Sea", fonts, CYAN, "mm")
    _label(draw, pt(0, 290, 0, ang), "dense water holds you up like a mattress", fonts, WHITE, "mm")


def sweat_cooling(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    box(draw, 0, 0, 150, 90, 260, ang, ORANGE, 150)
    _solid(draw, *pt(0, 310, 0, ang), 36, ORANGE, 170)
    for k in range(10):
        a = (t * 0.7 + k / 10) % 1.0
        x = -55 + (k * 53) % 110
        z = -30 + (k * 31) % 60
        y = 50 + (k * 29) % 180
        sx, sy = pt(x, y + 40 * a, z + 50, ang)
        _dot(draw, sx, sy, 7 * (1 - a * 0.8), _c(CYAN, int(230 * (1 - a))))
        _arr(draw, pt(x, y, z, ang), pt(x + 80 * a, y + 50 * a, z, ang), _c(RED, int(200 * (1 - a))), 2)
    _label(draw, pt(0, 420, 0, ang), "your natural cooling system", fonts, WHITE, "mm")


def ac_relief(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    box(draw, 0, 0, 440, 280, 280, ang, BLUE, 28)
    box(draw, 0, -110, 240, 40, 50, ang, CYAN, 235, y0=220)
    for k in range(6):
        a = (t * 0.6 + k / 6) % 1.0
        x = -100 + k * 40
        _arr(draw, pt(x, 210, -90, ang), pt(x, 210 - 160 * a, -60, ang), _c(CYAN, int(230 * (1 - a))), 3)
    box(draw, 0, 0, 400, 240, 6, ang, BLUE, 90)
    _label(draw, pt(0, 340, 0, ang), "cool air brings relief", fonts, CYAN, "mm")


def blood_delivery(draw, p, t, fonts, color):
    ang = _setup(draw, t)
    a, b = pt(-190, 220, 0, ang), pt(190, 220, 0, ang)
    _glow(draw, a[0], a[1], 90, _c(CYAN, 45))
    _solid(draw, a[0], a[1], 62, (200, 60, 70, 230), 220)
    _glow(draw, b[0], b[1], 90, _c(GREEN, 45))
    _solid(draw, b[0], b[1], 62, GREEN, 220)
    draw.line((*pt(-130, 250, 0, ang), *pt(130, 250, 0, ang)), fill=_c(ORANGE, 100), width=3)
    draw.line((*pt(-130, 190, 0, ang), *pt(130, 190, 0, ang)), fill=_c(GREY, 100), width=3)
    for k in range(5):
        s = (t * 0.5 + k / 5) % 1.0
        _dot(draw, *pt(_lerp(-130, 130, s), 250, 0, ang), 7, _c(ORANGE, 240))
        _dot(draw, *pt(_lerp(130, -130, s), 190, 0, ang), 7, _c(GREY, 240))
    _label(draw, (a[0], a[1] + 90), "blood", fonts, WHITE, "mm")
    _label(draw, (b[0], b[1] + 90), "organs", fonts, WHITE, "mm")
    _label(draw, pt(0, 340, 0, ang), "oxygen and nutrients", fonts, ORANGE, "mm")
    _label(draw, pt(0, 20, 0, ang), "carbon dioxide heads for the lungs", fonts, GREY, "mm")


MOTIFS_3D_L = {name: fn for name, fn in (
    ("interval_timeline", interval_timeline), ("gravity_surface", gravity_surface), ("cfc_cycle", cfc_cycle),
    ("ozone_hole_patch", ozone_hole_patch), ("flare_travel", flare_travel), ("star_beam", star_beam),
    ("star_twinkle", star_twinkle), ("twinkle_compare", twinkle_compare), ("aurora_particles", aurora_particles),
    ("aurora_colours", aurora_colours), ("sleep_vitals", sleep_vitals), ("sleep_memory", sleep_memory),
    ("salt_sources", salt_sources), ("dense_float", dense_float), ("sweat_cooling", sweat_cooling),
    ("ac_relief", ac_relief), ("blood_delivery", blood_delivery))}
