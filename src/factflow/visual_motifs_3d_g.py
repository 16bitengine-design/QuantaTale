"""Holographic 3D motifs, batch G: aurora, Olympus Mons, sound in space, sunset colours and the Venus day.

No on-screen numbers: every label is a word or a comparison.
"""

from __future__ import annotations

import math
from typing import Any

from .holo3d import box, columns, floor_grid, pt, view
from .visual_motifs import BLUE, CX, CYAN, GREEN, GREY, ORANGE, RED, WHITE, YELLOW, _c, _dot, _glow, _label
from .visual_motifs_3d import _solid

PINK = (255, 130, 190, 230)
VIOLET = (170, 120, 255, 230)
ROCK = (190, 120, 80, 230)


def _lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


def _frustum(draw: Any, x: float, z: float, rb: float, rt: float, h: float, ang: float, color: Any,
             alpha: int = 215, y0: float = 0.0, n: int = 28) -> None:
    """Shaded cone or mound with a flat top, standing on the floor."""
    quads = []
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        low = [pt(x + rb * math.cos(a), y0, z + rb * math.sin(a), ang) for a in (a0, a1)]
        high = [pt(x + rt * math.cos(a), y0 + h, z + rt * math.sin(a), ang) for a in (a1, a0)]
        quad = low + high
        quads.append((sum(q[1] for q in quad), quad, 0.5 + 0.35 * (0.5 + 0.5 * math.cos(a0 - 2.2))))
    for _, quad, shade in sorted(quads, key=lambda q: q[0]):
        draw.polygon(quad, fill=_c(tuple(int(ch * shade) for ch in color[:3]), alpha))
    top = [pt(x + rt * math.cos(2 * math.pi * i / n), y0 + h, z + rt * math.sin(2 * math.pi * i / n), ang) for i in range(n)]
    draw.polygon(top, fill=_c(tuple(min(255, int(ch * 1.1 + 20)) for ch in color[:3]), alpha))
    for k in range(0, n, 4):
        a = 2 * math.pi * k / n
        p0 = pt(x + rb * math.cos(a), y0, z + rb * math.sin(a), ang)
        p1 = pt(x + rt * math.cos(a), y0 + h, z + rt * math.sin(a), ang)
        draw.line((*p0, *p1), fill=_c(WHITE, 60), width=1)


# ---------------------------------------------------------------- aurora

def solar_wind_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    sun = pt(-250, 300, 0, ang)
    _glow(draw, sun[0], sun[1], 52, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 40, YELLOW, 240)
    earth = pt(250, 300, 0, ang)
    _solid(draw, earth[0], earth[1], 56, BLUE, 240)
    for i in range(24):
        s = (t * 0.35 + i / 24) % 1.0
        x = _lerp(-200, 190, s)
        spread = 20 + 110 * s
        y = 300 + math.sin(i * 2.1) * spread * 0.6
        z = math.cos(i * 1.7) * spread
        if s > 0.9:
            y += (s - 0.9) * 600 * (1 if i % 2 else -1)
        sx, sy = pt(x, y, z, ang)
        _dot(draw, sx, sy, 4, _c(YELLOW, int(230 * (1 - 0.3 * s))))
    _label(draw, (sun[0], sun[1] - 80), "the Sun", fonts, YELLOW, "mm")
    _label(draw, (earth[0], earth[1] + 90), "Earth", fonts, CYAN, "mm")
    sx, sy = pt(0, 420, 0, ang)
    _label(draw, (sx, sy), "solar wind", fonts, WHITE, "mm")


def field_lines_3d(draw, p, t, fonts, color):
    cx, cy, r = CX, 640, 105
    _glow(draw, cx, cy, r, _c(BLUE, 110))
    _solid(draw, cx, cy, r, BLUE, 215)
    rot = t * 0.35
    for side in (-1, 1):
        for li, L in enumerate((1.9, 2.6, 3.4)):
            pts = []
            for i in range(41):
                th = 0.22 + (math.pi - 0.44) * i / 40
                rad = L * math.sin(th) ** 2
                x = side * rad * math.sin(th) * r * math.cos(rot)
                y = rad * math.cos(th) * r
                pts.append((cx + x, cy - y))
            draw.line(pts, fill=_c(CYAN, 150 - 25 * li), width=2)
            s = (t * 0.25 + li * 0.3 + (0.5 if side > 0 else 0)) % 1.0
            px, py = pts[int(s * 40)]
            _dot(draw, px, py, 5, _c(YELLOW, 240))
    for sign in (-1, 1):
        _glow(draw, cx, cy - sign * r * 1.02, 22, _c(GREEN, int(120 + 100 * math.sin(t * 3) ** 2)))
    _label(draw, (cx, cy - 330), "magnetic field", fonts, CYAN, "mm")
    _label(draw, (cx, cy + 330), "guides particles to the poles", fonts, WHITE, "mm")


def aurora_curtains_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.25, base=0.45)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 560, 200, 360, ang, BLUE, 28, wire=False)
    for k in range(26):
        x = -270 + k * 21
        z = 70 * math.sin(k * 0.35 + t * 0.8)
        h = 110 + 60 * math.sin(t * 2 + k * 0.5)
        for y0, y1, col, a in ((120, 120 + h, GREEN, 150), (120 + h, 150 + h + 60, RED, 95), (80, 120, VIOLET, 110)):
            a0, a1 = pt(x, y0, z, ang), pt(x, y1, z, ang)
            draw.line((*a0, *a1), fill=_c(col, int(a * min(1, p * 3 + 0.4))), width=16)
    for text, y, col in (("higher: red", 330, RED), ("oxygen: green", 220, GREEN), ("nitrogen: blue", 100, VIOLET)):
        sx, sy = pt(260, y, 120, ang)
        _label(draw, (sx - 40, sy), text, fonts, col, "mm")
    sx, sy = pt(0, 470, 0, ang)
    _label(draw, (sx, sy), "glowing curtains of light", fonts, WHITE, "mm")


# ---------------------------------------------------------------- Olympus Mons

def mars_volcano_3d(draw, p, t, fonts, color):
    cx, cy, r = CX, 640, 190
    _glow(draw, cx, cy, r, _c(ORANGE, 70))
    _solid(draw, cx, cy, r, (210, 100, 60, 240), 235)
    rot = t * 0.5
    for k in range(6):
        a = rot + k * math.pi / 6
        w = r * abs(math.cos(a))
        draw.ellipse((cx - w, cy - r, cx + w, cy + r), outline=_c(WHITE, 40), width=1)
    lon, lat = (rot * 0.6) % (2 * math.pi), 0.35
    x = math.sin(lon) * math.cos(lat)
    zz = math.cos(lon) * math.cos(lat)
    y = math.sin(lat)
    if zz > 0.1:
        rise = 0.25 + 0.75 * min(1, p * 2)
        bx, by = cx + x * r, cy - y * r
        tx, ty = cx + x * r * (1 + 0.24 * rise), cy - y * r * (1 + 0.24 * rise)
        nx, ny = -(ty - by), tx - bx
        ln = math.hypot(nx, ny) or 1
        wdt = 40 * zz
        draw.polygon([(bx + nx / ln * wdt, by + ny / ln * wdt), (tx + nx / ln * 8, ty + ny / ln * 8),
                      (tx - nx / ln * 8, ty - ny / ln * 8), (bx - nx / ln * wdt, by - ny / ln * wdt)],
                     fill=_c((240, 150, 90), 240))
        _label(draw, (tx + (60 if x > 0 else -60), ty - 30), "Olympus Mons", fonts, YELLOW, "mm")
    _label(draw, (cx, cy + 270), "Mars", fonts, ORANGE, "mm")


def volcano_scale_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.45)
    floor_grid(draw, ang, half=320, step=80)
    k = min(1.0, 0.25 + p * 1.5)
    _frustum(draw, 70, 0, 250, 90, 170 * k, ang, ROCK, 225)
    _frustum(draw, -250, 20, 46, 4, 62 * k, ang, WHITE, 235)
    a, b = pt(-250, 62 * k, 20, ang), pt(-250, 170 * k, 20, ang)
    draw.line((*a, *pt(70, 62 * k, 0, ang)), fill=_c(YELLOW, 120), width=1)
    draw.line((*pt(-250, 170 * k, 20, ang), *pt(70, 170 * k, 0, ang)), fill=_c(YELLOW, 170), width=2)
    sx, sy = pt(-250, 100, 20, ang)
    _label(draw, (sx, sy - 90), "Mount Everest", fonts, WHITE, "mm")
    sx, sy = pt(70, 170 * k + 60, 0, ang)
    _label(draw, (sx, sy), "Olympus Mons", fonts, YELLOW, "mm")
    sx, sy = pt(60, 0, 300, ang)
    _label(draw, (sx, sy), "much taller and far wider", fonts, CYAN, "mm")


def shield_cutaway_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    layers = 6
    shown = 1 + int(p * (layers - 1) + 0.999)
    cols = (GREY, RED, ORANGE, GREY, RED, ORANGE)
    prof = lambda i, z: [pt(-(280 - i * 38) + 2 * (280 - i * 38) * j / 24, (70 + i * 22) * (1 - ((j - 12) / 12) ** 2) ** 0.8, z, ang) for j in range(25)]
    for z, a, k in ((50, 120, 0.55), (-50, 225, 0.95)):
        for i in range(min(layers, shown)):
            W = 280 - i * 38
            draw.polygon(prof(i, z) + [pt(W, 0, z, ang), pt(-W, 0, z, ang)], fill=_c(tuple(int(c * k) for c in cols[i][:3]), a))
            if z < 0:
                draw.line(prof(i, z), fill=_c(WHITE, 110), width=1)
    for i in range(8):
        s = (t * 0.4 + i * 0.125) % 1.0
        sx, sy = pt(-30 + 60 * s * (1 if i % 2 else -1), 160 + 50 * s, -50, ang)
        _dot(draw, sx, sy, 4, _c(ORANGE, int(230 * (1 - s))))
    sx, sy = pt(0, 340, 0, ang)
    _label(draw, (sx, sy), "lava flow on lava flow", fonts, ORANGE, "mm")
    sx, sy = pt(0, 0, 160, ang)
    _label(draw, (sx, sy), "a broad, gently sloping shield", fonts, WHITE, "mm")


# ---------------------------------------------------------------- sound in space

def silent_blast_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, -210, 0, 120, 60, 44, ang, GREY, 230, y0=240)
    box(draw, -130, 0, 40, 36, 24, ang, CYAN, 230, y0=250)
    box(draw, -260, 0, 18, 80, 8, ang, BLUE, 230, y0=258)
    fx, fy = pt(150, 270, 0, ang)
    pulse = (t * 0.6) % 1.0
    _glow(draw, fx, fy, 30 + 90 * pulse, _c(YELLOW, int(235 * (1 - pulse))))
    _glow(draw, fx, fy, 24, _c(WHITE, 240))
    for i in range(14):
        a = i * math.pi * 2 / 14
        ln = 40 + 160 * pulse
        draw.line((fx, fy, fx + ln * math.cos(a), fy + ln * math.sin(a)), fill=_c(YELLOW, int(150 * (1 - pulse))), width=2)
    _label(draw, (fx, fy + 150), "bright flash", fonts, YELLOW, "mm")
    sx, sy = pt(-210, 330, 0, ang)
    _label(draw, (sx, sy), "spacecraft: no boom", fonts, WHITE, "mm")


def vacuum_rings_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.55)
    floor_grid(draw, ang, half=320, step=80)
    box(draw, 120, 0, 240, 520, 260, ang, (20, 30, 60, 255), 60, wire=True)
    src = (-190, 0)
    for k in range(4):
        s = (t * 0.3 + k / 4) % 1.0
        r = s * 310
        pts = [pt(src[0] + r * math.cos(a), 6, src[1] + r * math.sin(a), ang) for a in [i * math.pi / 30 for i in range(61)]]
        seg = []
        for i, a in enumerate([j * math.pi / 30 for j in range(61)]):
            if src[0] + r * math.cos(a) <= 0:
                seg.append(pts[i])
            elif len(seg) > 1:
                draw.line(seg, fill=_c(CYAN, int(220 * (1 - s))), width=3)
                seg = []
            else:
                seg = []
        if len(seg) > 1:
            draw.line(seg, fill=_c(CYAN, int(220 * (1 - s))), width=3)
    sx, sy = pt(src[0], 20, src[1], ang)
    _glow(draw, sx, sy, 16, _c(WHITE, 235))
    for i in range(6):
        s = (t * 0.5 + i / 6) % 1.0
        x, z = _lerp(-190, 230, s), (i - 2.5) * 28
        gx, gy = pt(x, 30, z, ang)
        _dot(draw, gx, gy, 4, _c(YELLOW, 235))
    for text, x, col in (("air: sound travels", -190, CYAN), ("vacuum: no sound", 110, GREY)):
        sx, sy = pt(x, 330, 0, ang)
        _label(draw, (sx, sy), text, fonts, col, "mm")
    sx, sy = pt(110, 90, 0, ang)
    _label(draw, (sx, sy), "light keeps going", fonts, YELLOW, "mm")


def cabin_sound_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.55)
    floor_grid(draw, ang, half=300, step=75)
    W, D = 440, 260
    box(draw, 0, 0, W, D, 150, ang, BLUE, 40)
    box(draw, -150, 0, 30, 30, 36, ang, ORANGE, 235)
    box(draw, 150, 40, 30, 30, 60, ang, WHITE, 235)
    _solid(draw, *pt(150, 100, 40, ang), 15, WHITE, 235)
    for k in range(4):
        s = (t * 0.35 + k / 4) % 1.0
        r = s * 340
        a_list = [i * math.pi / 32 for i in range(65)]
        seg = []
        for a in a_list:
            x, z = -150 + r * math.cos(a), r * math.sin(a)
            if abs(x) <= W / 2 and abs(z) <= D / 2:
                seg.append(pt(x, 40, z, ang))
            else:
                if len(seg) > 1:
                    draw.line(seg, fill=_c(CYAN, int(230 * (1 - s))), width=3)
                seg = []
        if len(seg) > 1:
            draw.line(seg, fill=_c(CYAN, int(230 * (1 - s))), width=3)
    sx, sy = pt(0, 250, 0, ang)
    _label(draw, (sx, sy), "cabin air carries sound", fonts, CYAN, "mm")
    sx, sy = pt(0, 0, 220, ang)
    _label(draw, (sx, sy), "outside: silent space", fonts, GREY, "mm")


# ---------------------------------------------------------------- sunset colours

def _earth_arc(draw: Any, cx: float, cy: float, r: float, t: float) -> None:
    draw.ellipse((cx - r - 70, cy - r - 70, cx + r + 70, cy + r + 70), fill=_c(CYAN, 18), outline=_c(CYAN, 70), width=2)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_c((10, 40, 90), 235), outline=_c(BLUE, 220), width=3)
    for k in range(6):
        a = t * 0.3 + k * math.pi / 6
        w = r * abs(math.cos(a))
        draw.ellipse((cx - w, cy - r, cx + w, cy + r), outline=_c(CYAN, 40), width=1)


def sunset_path_3d(draw, p, t, fonts, color):
    cx, cy, r = CX, 1230, 400
    _earth_arc(draw, cx, cy, r, t)
    ox, oy = cx, cy - r
    _dot(draw, ox, oy, 8, _c(WHITE, 240))
    mid = (cx, 440)
    _glow(draw, mid[0], mid[1], 30, _c(YELLOW, 235))
    draw.line((*mid, ox, oy - 4), fill=_c(YELLOW, 200), width=4)
    sun = (70, 760)
    _glow(draw, sun[0], sun[1], 34, _c(ORANGE, 235))
    for i in range(12):
        s = (t * 0.4 + i / 12) % 1.0
        _dot(draw, _lerp(sun[0], ox, s), _lerp(sun[1], oy - 4, s), 4, _c(ORANGE, 230))
    draw.line((*sun, ox, oy - 4), fill=_c(ORANGE, 120), width=2)
    _label(draw, (mid[0], mid[1] - 60), "midday: short path", fonts, YELLOW, "mm")
    _label(draw, (210, 690), "sunset: long path", fonts, ORANGE, "mm")
    _label(draw, (ox + 120, oy - 40), "you", fonts, WHITE, "mm")


def _beam_scene(draw, t, fonts, show_arrival: float) -> None:
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    box(draw, 0, 0, 560, 220, 210, ang, BLUE, 26, wire=False)
    for i in range(36):
        x, y, z = -250 + (i * 83) % 520, 30 + (i * 47) % 170, -90 + (i * 61) % 180
        sx, sy = pt(x, y, z, ang)
        _dot(draw, sx, sy, 3, _c(WHITE, 130))
    sun = pt(-285, 110, 0, ang)
    _glow(draw, sun[0], sun[1], 34, _c(ORANGE, 235))
    for i in range(10):
        s = (t * 0.35 + i / 10) % 1.0
        sx, sy = pt(_lerp(-265, 250, s), 110, (i - 4.5) * 4, ang)
        _dot(draw, sx, sy, 4, _c(ORANGE, 235))
    for i in range(14):
        s = (t * 0.3 + i / 14) % 1.0
        x = _lerp(-220, 120, (i * 0.37) % 1.0) + s * 40
        dirn = 1 if i % 2 else -1
        sx, sy = pt(x, 110 + dirn * 140 * s, dirn * 90 * s * (1 if i % 3 else -1), ang)
        _dot(draw, sx, sy, 4, _c(BLUE, int(235 * (1 - s))))
    if show_arrival:
        eye = pt(270, 110, 0, ang)
        _glow(draw, eye[0], eye[1], 24 + 12 * math.sin(t * 4), _c(ORANGE, int(200 * show_arrival)))
        _solid(draw, eye[0], eye[1], 14, WHITE, 235)
    return ang


def blue_scatter_3d(draw, p, t, fonts, color):
    ang = _beam_scene(draw, t, fonts, 0.0)
    sx, sy = pt(-40, 300, 0, ang)
    _label(draw, (sx, sy), "air bounces blue light aside", fonts, BLUE, "mm")
    sx, sy = pt(50, 20, 0, ang)
    _label(draw, (sx, sy + 20), "red and orange carry on", fonts, ORANGE, "mm")


def red_reach_3d(draw, p, t, fonts, color):
    ang = _beam_scene(draw, t, fonts, min(1.0, 0.3 + p))
    sx, sy = pt(0, 300, 0, ang)
    _label(draw, (sx, sy), "warm light reaches your eyes", fonts, ORANGE, "mm")


def sunset_horizon_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.18, base=0.4)
    floor_grid(draw, ang, half=320, step=80, color=BLUE)
    bands = ((RED, 70), (ORANGE, 70), (PINK, 70), (VIOLET, 70), (BLUE, 70))
    for i, (col, hh) in enumerate(bands):
        box(draw, 0, -160, 640, 30, hh, ang, col, 120, y0=i * hh * 0.8, wire=False)
    sun = pt(0, 50 + 12 * math.sin(t), -160, ang)
    _glow(draw, sun[0], sun[1], 60, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 34, YELLOW, 245)
    for i in range(9):
        a = pt(-45 + i * 11, 4, -150 + i * 20, ang)
        b = pt(-45 + i * 11 + 15, 4, -150 + i * 20, ang)
        draw.line((*a, *b), fill=_c(YELLOW, 120), width=2)
    sx, sy = pt(0, 420, -160, ang)
    _label(draw, (sx, sy), "red, orange and pink", fonts, ORANGE, "mm")


# ---------------------------------------------------------------- Venus

def venus_spin_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.15, base=0.5)
    floor_grid(draw, ang, half=320, step=80)
    sun = pt(0, 150, 0, ang)
    _glow(draw, sun[0], sun[1], 40, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 26, YELLOW, 245)
    R = 230
    ring = [pt(R * math.cos(a), 150, R * math.sin(a), ang) for a in [i * math.pi / 30 for i in range(61)]]
    draw.line(ring, fill=_c(CYAN, 90), width=2)
    u = t * 0.9
    vx, vy = pt(R * math.cos(u), 150, R * math.sin(u), ang)
    _solid(draw, vx, vy, 36, (240, 190, 100, 240), 240)
    sp = -t * 0.25
    draw.ellipse((vx + 22 * math.cos(sp) - 5, vy + 14 * math.sin(sp) - 5, vx + 22 * math.cos(sp) + 5, vy + 14 * math.sin(sp) + 5),
                 fill=_c(RED, 240))
    _label(draw, (vx, vy - 64), "Venus", fonts, ORANGE, "mm")
    _label(draw, (CX, 470), "orbit: quicker  /  spin: slower", fonts, WHITE, "mm")


venus_counters = columns([
    ("ONE SPIN", 243, ORANGE, "LONGER"), ("ONE ORBIT", 225, CYAN, "SHORTER")], ref=250, rise=1.3)


def venus_sunrise_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.12, base=0.4)
    floor_grid(draw, ang, half=320, step=80)
    rise = (t * 0.2) % 1.0
    sx, sy = pt(-220, 20 + 220 * rise, -60, ang)
    _glow(draw, sx, sy, 50, _c(YELLOW, 230))
    _solid(draw, sx, sy, 30, YELLOW, 245)
    a0, a1 = pt(-220, 20, -60, ang), pt(-220, 280, -60, ang)
    draw.line((*a0, *a1), fill=_c(ORANGE, 140), width=3)
    for dx in range(-3, 4):
        pa, pb = pt(dx * 40, 0, 40, ang), pt(dx * 40, 36, 40, ang)
        draw.line((*pa, *pb), fill=_c(GREY, 150), width=3)
    a, b = pt(220, 380, 0, ang), pt(-220, 380, 0, ang)
    draw.line((*a, *b), fill=_c(CYAN, 220), width=4)
    draw.polygon([(b[0], b[1]), (b[0] + 24, b[1] - 12), (b[0] + 24, b[1] + 12)], fill=_c(CYAN, 230))
    _label(draw, pt(-250, 0, 100, ang), "west", fonts, ORANGE, "mm")
    _label(draw, pt(250, 0, 100, ang), "east", fonts, GREY, "mm")
    _label(draw, (CX, pt(0, 440, 0, ang)[1]), "the Sun rises in the west", fonts, WHITE, "mm")


MOTIFS_3D_G = {name: fn for name, fn in (
    ("solar_wind_3d", solar_wind_3d), ("field_lines_3d", field_lines_3d), ("aurora_curtains_3d", aurora_curtains_3d),
    ("mars_volcano_3d", mars_volcano_3d), ("volcano_scale_3d", volcano_scale_3d), ("shield_cutaway_3d", shield_cutaway_3d),
    ("silent_blast_3d", silent_blast_3d), ("vacuum_rings_3d", vacuum_rings_3d), ("cabin_sound_3d", cabin_sound_3d),
    ("sunset_path_3d", sunset_path_3d), ("blue_scatter_3d", blue_scatter_3d), ("red_reach_3d", red_reach_3d),
    ("sunset_horizon_3d", sunset_horizon_3d), ("venus_spin_3d", venus_spin_3d), ("venus_counters", venus_counters),
    ("venus_sunrise_3d", venus_sunrise_3d))}
