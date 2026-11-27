"""Toy-box diorama motifs and the scene renderer for visual profile ``toybox_diorama_v1``.

Each motif is ``fn(draw, p, t, ang)``: ``p`` is 0-1 progress inside the scene and ``t`` elapsed
seconds. Motifs only illustrate the narrated idea; they print no text.
"""
from __future__ import annotations

import math
from typing import Any, Callable

from .toybox import (BLUE, GRASS, ORANGE, RED, SOIL, STONE, SUN, WATER, WHITE, background, ball_faces, bob, draw_mesh,
                     ease_out_back, house, platform, prism_faces, pt, pyramid_faces, shadow, tree, view)

Faces = list


def _sun(x: float, y: float, z: float, t: float, r: float = 34) -> Faces:
    return ball_faces(x, y + bob(t, 0, 6), z, r, SUN, bands=4, sides=8)


def toy_sky_scatter(draw: Any, p: float, t: float, ang: float) -> None:
    """Sunlight meets air: blue toy specks scatter across the sky while a house sits below."""
    platform(draw, ang)
    faces = tree(-130, 70) + house(110, -50) + _sun(-150, 330, -80, t)
    for i in range(10):  # blue air molecules pop in one by one
        pop = ease_out_back(p * 10 - i)
        if pop <= 0.02:
            continue
        a = i * 0.9 + t * 0.35
        x, z = 150 * math.cos(a) * (0.4 + 0.1 * i % 0.6), 90 * math.sin(a)
        faces += prism_faces(x, z, 22 * pop, 22 * pop, 22 * pop, BLUE, y0=170 + (i % 4) * 36 + bob(t, i, 7))
    # warm beam of small cubes from the sun toward the ground
    for k in range(6):
        f = (k / 6 + t * 0.4) % 1
        faces += prism_faces(-150 + 190 * f, -80 + 80 * f, 12, 12, 12, SUN, y0=330 - 330 * f)
    draw_mesh(draw, faces, ang)


def toy_water_cycle(draw: Any, p: float, t: float, ang: float) -> None:
    """Sea, mountain, cloud and rain: water rises, gathers, falls."""
    platform(draw, ang)
    faces = prism_faces(-110, 90, 170, 120, 8, WATER) + pyramid_faces(120, -40, 110, 150, STONE, sides=5)
    faces += tree(60, 100, 0.8)
    cloud_x = -60 + 190 * min(1.0, p * 1.2)
    for dx, dy, s in ((-30, 0, 46), (0, 14, 58), (34, 0, 44)):
        faces += prism_faces(cloud_x + dx, -20, s, 40, 26, WHITE, y0=250 + dy + bob(t, dx, 5))
    for i in range(7):  # vapour rises first, then rain falls later in the scene
        f = (t * 0.5 + i / 7) % 1
        if p < 0.5:
            faces += prism_faces(-130 + i * 14, 90, 10, 10, 10, WHITE, y0=10 + 240 * f)
        else:
            faces += prism_faces(cloud_x - 40 + i * 14, -20, 9, 9, 14, BLUE, y0=240 - 230 * f)
    draw_mesh(draw, faces, ang)


def toy_volcano(draw: Any, p: float, t: float, ang: float) -> None:
    """Faceted volcano that blows lava cubes in arcs as the scene progresses."""
    platform(draw, ang)
    faces = pyramid_faces(0, 0, 170, 200, SOIL, sides=7, top_r=40) + tree(-210, 80, 0.8) + tree(200, 60, 0.7)
    for i in range(int(2 + 10 * p)):
        f = (t * 0.6 + i * 0.173) % 1
        a = i * 2.4
        r = 150 * f
        faces += prism_faces(r * math.cos(a), r * math.sin(a), 16, 16, 16, ORANGE if i % 2 else RED,
                             y0=200 + 260 * f * (1 - f) * 4 - 30 * f)
    draw_mesh(draw, faces, ang)


def toy_seasons(draw: Any, p: float, t: float, ang: float) -> None:
    """A tilted toy Earth circles a sun; the tilt, not the distance, changes the seasons."""
    platform(draw, ang)
    faces = ball_faces(0, 120, 0, 46, SUN, bands=4, sides=8)
    a = p * 2 * math.pi * 0.75 + 0.4
    ex, ez = 190 * math.cos(a), 190 * math.sin(a)
    faces += ball_faces(ex, 120, ez, 24, BLUE, bands=4, sides=8)
    faces += prism_faces(ex + 6, ez, 5, 5, 70, WHITE, y0=96)  # tilted-looking axis stick
    for k in range(24):  # orbit track
        b = k * math.pi / 12
        faces += prism_faces(190 * math.cos(b), 190 * math.sin(b), 5, 5, 3, STONE, y0=118)
    draw_mesh(draw, faces, ang)


def toy_plates(draw: Any, p: float, t: float, ang: float) -> None:
    """Two ground slabs push together and crumple a mountain between them."""
    platform(draw, ang)
    shift = 120 * (1 - p)
    faces = prism_faces(-150 - shift * 0.5, 0, 170, 260, 30, GRASS) + prism_faces(150 + shift * 0.5, 0, 170, 260, 30, SOIL)
    faces += pyramid_faces(0, 0, 80 + 40 * p, 20 + 180 * p, STONE, sides=5)
    draw_mesh(draw, faces, ang)


def toy_generic(draw: Any, p: float, t: float, ang: float) -> None:
    """Fallback diorama: a little village whose pieces pop in as the scene advances."""
    platform(draw, ang)
    faces = tree(-150, 60) + tree(160, 80, 0.8)
    for i, (x, z) in enumerate(((-30, -40), (120, -80), (-120, -90))):
        s = ease_out_back(p * 3 - i)
        if s > 0.02:
            faces += house(x, z, max(0.05, s))
    faces += _sun(0, 340, 0, t, 26)
    draw_mesh(draw, faces, ang)


TOYBOX_MOTIFS: dict[str, Callable[..., None]] = {
    "toy_sky_scatter": toy_sky_scatter, "toy_water_cycle": toy_water_cycle, "toy_volcano": toy_volcano,
    "toy_seasons": toy_seasons, "toy_plates": toy_plates,
}


def draw_toybox_scene(draw: Any, width: int, height: int, seconds: float, scenes: list[dict[str, Any]],
                      narration: str, duration: float) -> None:
    """Draw the diorama for the scene being narrated at ``seconds``."""
    from .holographic_scenes import scene_position

    background(draw, width, height, seconds)
    count = max(1, len(scenes))
    position, local = (scene_position(narration, scenes, seconds, duration) if narration and duration and scenes else (0, 0.0))
    position = min(count - 1, position)
    name = str(scenes[position].get("motif", "")) if scenes else ""
    TOYBOX_MOTIFS.get(name, toy_generic)(draw, local, seconds, view(seconds))
