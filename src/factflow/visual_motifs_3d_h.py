"""Holographic 3D motifs, batch H: moon phases, a locked planet orbit, an Earth that bulges, autumn leaf colours.

These use the same names as the flat motifs, so existing topics upgrade without a spec change.
No on-screen numbers: labels are words.
"""

from __future__ import annotations

import math
from typing import Any

from .holo3d import box, floor_grid, pt, view
from .visual_motifs import BLUE, CX, CYAN, GREEN, GREY, ORANGE, RED, WHITE, YELLOW, _c, _dot, _glow, _label
from .visual_motifs_3d import _solid


def _lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


def _phase_disc(draw: Any, cx: float, cy: float, r: float, phi: float) -> None:
    """The Moon as seen from Earth. phi = 0 new, pi full; waxing lit on the right."""
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_c((25, 35, 55), 240), outline=_c(GREY, 160), width=2)
    side = 1 if math.sin(phi) >= 0 else -1
    k = math.cos(phi)
    n = int(r)
    for i in range(-n, n + 1):
        w = math.sqrt(max(0.0, r * r - i * i))
        xt = k * w
        a, b = (xt, w) if side > 0 else (-w, -xt)
        if b > a:
            draw.line((cx + a, cy + i, cx + b, cy + i), fill=_c((235, 235, 215), 245), width=1)


def moon_phases(draw, p, t, fonts, color):
    ang = view(t, sway=0.12, base=0.45)
    floor_grid(draw, ang, half=300, step=75)
    sun = pt(-270, 220, 0, ang)
    _glow(draw, sun[0], sun[1], 50, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 36, YELLOW, 245)
    for k in range(5):
        a, b = pt(-215, 220 + (k - 2) * 38, 0, ang), pt(240, 220 + (k - 2) * 38, 0, ang)
        draw.line((*a, *b), fill=_c(YELLOW, 45), width=2)
    earth = pt(0, 220, 0, ang)
    R = 170
    ring = [pt(R * math.cos(a), 220, R * math.sin(a), ang) for a in [i * math.pi / 30 for i in range(61)]]
    draw.line(ring, fill=_c(CYAN, 80), width=1)
    _solid(draw, earth[0], earth[1], 34, BLUE, 240)
    alpha = 2 * math.pi * p
    mx, my = pt(R * math.cos(alpha), 220, R * math.sin(alpha), ang)
    _solid(draw, mx, my, 22, GREY, 240)
    sdx, sdy = sun[0] - mx, sun[1] - my
    th = math.degrees(math.atan2(sdy, sdx))
    draw.pieslice((mx - 22, my - 22, mx + 22, my + 22), th - 90, th + 90, fill=_c((245, 245, 225), 245))
    _phase_disc(draw, CX, 960, 58, (alpha - math.pi) % (2 * math.pi))
    _label(draw, (CX, 1050), "what we see from Earth", fonts, WHITE, "mm")
    _label(draw, (CX, 420), "the Sun always lights half the Moon", fonts, CYAN, "mm")
    _label(draw, (CX, 455), "we see a changing part of that half", fonts, WHITE, "mm")


def orbit_rotation(draw, p, t, fonts, color):
    ang = view(t, sway=0.15, base=0.5)
    floor_grid(draw, ang, half=320, step=80)
    sun = pt(0, 150, 0, ang)
    _glow(draw, sun[0], sun[1], 46, _c(YELLOW, 235))
    _solid(draw, sun[0], sun[1], 30, YELLOW, 245)
    R = 230
    draw.line([pt(R * math.cos(a), 150, R * math.sin(a), ang) for a in [i * math.pi / 30 for i in range(61)]],
              fill=_c(CYAN, 90), width=2)
    u = p * 4 * math.pi - math.pi / 2
    px, py = pt(R * math.cos(u), 150, R * math.sin(u), ang)
    _solid(draw, px, py, 32, (190, 160, 140, 240), 240)
    toward = math.atan2(sun[1] - py, sun[0] - px)
    draw.pieslice((px - 32, py - 32, px + 32, py + 32), math.degrees(toward) - 90, math.degrees(toward) + 90,
                  fill=_c(YELLOW, 70))
    spin = 1.5 * u
    mx, my = px + 22 * math.cos(spin), py + 14 * math.sin(spin)
    _dot(draw, mx, my, 5, _c(RED, 245))
    _label(draw, (CX, 440), "spin and orbit are locked together", fonts, CYAN, "mm")
    _label(draw, (CX, 475), "sunrise to sunrise takes two Mercury years", fonts, YELLOW, "mm")
    _label(draw, (px, py - 58), "Mercury", fonts, WHITE, "mm")


def globe_bulge(draw, p, t, fonts, color):
    cx, cy, R = CX, 640, 215
    squash = 1.0 - 0.16 * min(1.0, p * 1.5)
    rx, ry = R, R * squash
    tilt = 0.32
    rot = t * 0.6

    def proj(x, y, z):
        return cx + x, cy - y * math.cos(tilt) + z * math.sin(tilt) * 0.6

    _glow(draw, cx, cy, R, _c(BLUE, 80))
    draw.ellipse((cx - R, cy - R, cx + R, cy + R), outline=_c(WHITE, 90), width=2)
    for lon in range(0, 180, 30):
        lam = math.radians(lon) + rot
        pts = [(math.cos(v) * rx * math.cos(lam), ry * math.sin(v), math.cos(v) * rx * math.sin(lam)) for v in [i * math.pi / 24 for i in range(49)]]
        for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
            a, b = proj(x0, y0, z0), proj(x1, y1, z1)
            draw.line((*a, *b), fill=_c(CYAN, 190 if (z0 + z1) > 0 else 50), width=2 if (z0 + z1) > 0 else 1)
    for lat in (-60, -30, 0, 30, 60):
        la = math.radians(lat)
        pts = [(math.cos(la) * rx * math.cos(u), math.sin(la) * ry, math.cos(la) * rx * math.sin(u)) for u in [i * math.pi / 24 for i in range(49)]]
        col = YELLOW if lat == 0 else CYAN
        for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
            a, b = proj(x0, y0, z0), proj(x1, y1, z1)
            near = (z0 + z1) > 0
            draw.line((*a, *b), fill=_c(col, (230 if lat == 0 else 150) if near else 45), width=3 if lat == 0 else 1)
    draw.line((cx, cy - ry * 1.18, cx, cy + ry * 1.18), fill=_c(WHITE, 120), width=2)
    for k in range(3):
        s = (t * 0.5 + k / 3) % 1.0
        a = -0.6 + 1.2 * s
        _dot(draw, cx + (rx + 40) * math.sin(a), cy - ry * 1.28 * math.cos(a) + 40, 5, _c(YELLOW, 220))
    _label(draw, (cx, cy + 300), "spinning makes the equator bulge", fonts, CYAN, "mm")
    _label(draw, (cx, cy - 300), "a little wider than tall", fonts, WHITE, "mm")


def leaf_pigments(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.5)
    floor_grid(draw, ang, half=300, step=75)
    n = 24
    outline = []
    for i in range(n + 1):
        s = i / n
        outline.append((-170 + 340 * s, 70 * math.sin(math.pi * s) ** 0.8))
    top = [pt(x, 230, w + 0, ang) for x, w in outline]
    bot = [pt(x, 230, -w, ang) for x, w in reversed(outline)]
    green = int(210 * (1 - p) + 60)
    col = (int(_lerp(60, 230, p)), int(_lerp(200, 140, p)), int(_lerp(100, 40, p)), 235)
    draw.polygon(top + bot, fill=_c(col[:3], 235))
    draw.line([pt(-170, 230, 0, ang), pt(170, 230, 0, ang)], fill=_c(WHITE, 160), width=3)
    for i in range(-3, 4):
        if i:
            draw.line([pt(i * 40, 230, 0, ang), pt(i * 40 + 30, 230, 45 * (1 if i > 0 else -1) * 0.9 + 0, ang)], fill=_c(WHITE, 90), width=1)
    items = (("green", GREEN, 1 - p), ("yellow", YELLOW, 0.5 + 0.2 * p), ("orange", ORANGE, 0.4 + 0.4 * p), ("red", RED, 0.1 + 0.7 * p))
    for k, (name, c, level) in enumerate(items):
        x = -195 + k * 130
        box(draw, x, 130, 60, 60, max(6, 150 * level), ang, c, 225)
        sx, sy = pt(x, 0, 205, ang)
        _label(draw, (sx, sy), name, fonts, WHITE, "mm")
    sx, sy = pt(0, 360, 0, ang)
    _label(draw, (sx, sy), "green fades, other colours show", fonts, WHITE, "mm")


MOTIFS_3D_H = {name: fn for name, fn in (
    ("moon_phases", moon_phases), ("orbit_rotation", orbit_rotation),
    ("globe_bulge", globe_bulge), ("leaf_pigments", leaf_pigments))}
