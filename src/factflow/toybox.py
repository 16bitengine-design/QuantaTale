"""Low-poly "toy-box diorama" toolkit (visual profile ``toybox_diorama_v1``).

Pure Pillow, no GPU. Objects are flat-shaded polygon meshes: each face is lit by one fixed light,
faces are painted back to front, and the camera sways slowly so the scene reads as a small
tabletop diorama of painted toys. Everything is a function of progress and elapsed time, so
renders are reproducible.
"""
from __future__ import annotations

import math
from typing import Any


# Warm, limited toy palette (RGB).
CREAM, SKY, SKY_LOW = (255, 244, 222), (150, 205, 245), (255, 226, 190)
GRASS, SOIL, STONE = (118, 200, 120), (150, 105, 78), (170, 170, 185)
SUN, RED, ORANGE = (255, 205, 70), (238, 88, 80), (255, 150, 60)
BLUE, WATER, WHITE = (80, 150, 235), (70, 170, 225), (250, 250, 252)
WOOD, LEAF, PINK = (190, 130, 85), (70, 170, 100), (245, 150, 180)
INK = (62, 44, 40)

_LIGHT = (-0.45, 0.8, -0.4)
Vec = tuple[float, float, float]
CX_DEFAULT = 360


def pt(x: float, y: float, z: float, ang: float, cx: float = CX_DEFAULT, cy: float = 930) -> tuple[float, float]:
    """x right, y up, z depth -> screen. Same projection as the holographic toolkit, kept separate on purpose."""
    return cx + x * math.cos(ang) - z * math.sin(ang), cy - y + (x * math.sin(ang) + z * math.cos(ang)) * 0.38


def view(t: float, sway: float = 0.3, base: float = 0.6) -> float:
    return base + sway * math.sin(t * 0.5)


def _norm(v: Vec) -> Vec:
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return v[0] / n, v[1] / n, v[2] / n


_L = _norm(_LIGHT)


def shade(color: tuple, intensity: float) -> tuple[int, int, int]:
    """Scale a base colour; 0.55 ambient plus up to 0.45 directional light."""
    k = 0.72 + 0.4 * max(0.0, min(1.0, intensity))
    return tuple(max(0, min(255, int(ch * k))) for ch in color[:3])  # type: ignore[return-value]


def _normal(face: list[Vec]) -> Vec:
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = face[0], face[1], face[2]
    u, v = (bx - ax, by - ay, bz - az), (cx - ax, cy - ay, cz - az)
    return _norm((u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]))


def ease_out_back(p: float) -> float:
    """Bouncy pop-in: overshoots slightly then settles. 0 -> 0, 1 -> 1."""
    p = max(0.0, min(1.0, p))
    c1 = 1.70158
    return 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2


def bob(t: float, phase: float = 0.0, amount: float = 8.0) -> float:
    return amount * math.sin(t * 2.4 + phase)


def draw_mesh(draw: Any, faces: list[tuple[list[Vec], tuple]], ang: float, cx: float = 360, cy: float = 930,
              outline: bool = True) -> None:
    """Paint flat-shaded faces back to front. Each face is (vertices, base colour)."""
    items = []
    for verts, color in faces:
        n = _normal(verts)
        # Orient the normal outward from the mesh centre of this face set later via sign of y/centroid.
        depth = sum(x * math.sin(ang) + z * math.cos(ang) for x, _, z in verts) / len(verts)
        items.append((depth, verts, color, n))
    for depth, verts, color, n in sorted(items, key=lambda i: i[0]):
        light = abs(n[0] * _L[0] + n[1] * _L[1] + n[2] * _L[2])
        poly = [pt(x, y, z, ang, cx, cy) for x, y, z in verts]
        draw.polygon(poly, fill=(*shade(color, light), 255),
                     outline=(*shade(color, light * 0.4), 255) if outline else None)


def prism_faces(x: float, z: float, w: float, d: float, h: float, color: tuple, y0: float = 0.0) -> list[tuple[list[Vec], tuple]]:
    x0, x1, z0, z1, y1 = x - w / 2, x + w / 2, z - d / 2, z + d / 2, y0 + h
    return [
        ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], color),
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], color),
        ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], color),
        ([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], color),
        ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], color),
    ]


def pyramid_faces(x: float, z: float, r: float, h: float, color: tuple, y0: float = 0.0, sides: int = 6,
                  top_r: float = 0.0) -> list[tuple[list[Vec], tuple]]:
    """Faceted cone (or frustum when top_r > 0)."""
    faces: list[tuple[list[Vec], tuple]] = []
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        base = [(x + r * math.cos(a0), y0, z + r * math.sin(a0)), (x + r * math.cos(a1), y0, z + r * math.sin(a1))]
        top = [(x + top_r * math.cos(a1), y0 + h, z + top_r * math.sin(a1)), (x + top_r * math.cos(a0), y0 + h, z + top_r * math.sin(a0))]
        faces.append((base + top if top_r > 0 else base + [(x, y0 + h, z)], color))
    if top_r > 0:
        faces.append(([(x + top_r * math.cos(2 * math.pi * i / sides), y0 + h, z + top_r * math.sin(2 * math.pi * i / sides))
                       for i in range(sides)], color))
    return faces


def ball_faces(x: float, y: float, z: float, r: float, color: tuple, bands: int = 3, sides: int = 8) -> list[tuple[list[Vec], tuple]]:
    """Low-poly sphere from latitude bands."""
    faces: list[tuple[list[Vec], tuple]] = []
    for b in range(bands):
        lat0, lat1 = math.pi * (b / bands - 0.5), math.pi * ((b + 1) / bands - 0.5)
        for i in range(sides):
            a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
            p = lambda lat, a: (x + r * math.cos(lat) * math.cos(a), y + r * math.sin(lat), z + r * math.cos(lat) * math.sin(a))
            quad = [p(lat0, a0), p(lat0, a1), p(lat1, a1), p(lat1, a0)]
            faces.append((quad if b not in (0, bands - 1) else _dedupe(quad), color))
    return faces


def _dedupe(poly: list[Vec]) -> list[Vec]:
    out: list[Vec] = []
    for v in poly:
        if not out or max(abs(v[i] - out[-1][i]) for i in range(3)) > 1e-6:
            out.append(v)
    if len(out) > 1 and max(abs(out[0][i] - out[-1][i]) for i in range(3)) <= 1e-6:
        out.pop()
    return out if len(out) >= 3 else poly


def platform(draw: Any, ang: float, top: tuple = GRASS, cy: float = 930, radius: float = 300) -> None:
    """Octagonal diorama base: soil slab with a grass top and a soft shadow under it."""
    cx = 360
    sh = [pt(radius * 1.05 * math.cos(2 * math.pi * i / 8), -34, radius * 1.05 * math.sin(2 * math.pi * i / 8), ang, cx, cy + 14)
          for i in range(8)]
    draw.polygon(sh, fill=(60, 40, 30, 60))
    faces = pyramid_faces(0, 0, radius, 26, SOIL, y0=-26, sides=8, top_r=radius)
    faces = [([(x, y, z) for x, y, z in v], c) for v, c in faces]
    draw_mesh(draw, faces, ang, cx, cy)
    top_face = [(radius * math.cos(2 * math.pi * i / 8), 0, radius * math.sin(2 * math.pi * i / 8)) for i in range(8)]
    draw.polygon([pt(x, y, z, ang, cx, cy) for x, y, z in top_face], fill=(*shade(top, 1.0), 255),
                 outline=(*shade(top, 0.3), 255))


def shadow(draw: Any, x: float, z: float, r: float, ang: float, cy: float = 930) -> None:
    pts = [pt(x + r * math.cos(a), 0.5, z + r * math.sin(a), ang, 360, cy) for a in [i * math.pi / 6 for i in range(12)]]
    draw.polygon(pts, fill=(50, 70, 50, 70))


def tree(x: float, z: float, scale: float = 1.0, color: tuple = LEAF) -> list[tuple[list[Vec], tuple]]:
    s = scale
    return (prism_faces(x, z, 14 * s, 14 * s, 36 * s, WOOD)
            + pyramid_faces(x, z, 40 * s, 60 * s, color, y0=30 * s, sides=5)
            + pyramid_faces(x, z, 30 * s, 50 * s, color, y0=62 * s, sides=5))


def house(x: float, z: float, scale: float = 1.0) -> list[tuple[list[Vec], tuple]]:
    s = scale
    return prism_faces(x, z, 70 * s, 60 * s, 50 * s, PINK) + pyramid_faces(x, z, 56 * s, 38 * s, RED, y0=50 * s, sides=4)


def background(draw: Any, width: int, height: int, seconds: float) -> None:
    """Soft sky-to-cream gradient with a few drifting low-poly clouds."""
    for y in range(0, height, 4):
        f = y / height
        col = tuple(int(SKY[i] * (1 - f) + SKY_LOW[i] * f) for i in range(3))
        draw.rectangle((0, y, width, y + 4), fill=(*col, 255))
    for k in range(4):
        x = (k * 230 + seconds * (12 + 5 * k)) % (width + 200) - 100
        y = 230 + k * 95
        for dx, dw in ((-34, 60), (0, 84), (40, 56)):
            draw.rounded_rectangle((x + dx - dw / 2, y - 16, x + dx + dw / 2, y + 14), radius=14, fill=(255, 255, 255, 150))
