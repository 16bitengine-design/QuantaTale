"""Reusable procedural science animations ("motifs") for authored topics.

Each motif draws one concept so that what appears on screen matches what the
narration says (for example water vapour rising, or red light fading with depth).
A scene selects a motif by name in its ``motif`` field. Unknown or missing names
fall back to the generic holographic core. Motifs draw into the centre area of
the frame (about y 380-940) and are driven only by scene progress ``p`` (0-1)
and elapsed seconds ``t``, so renders are reproducible.
"""
from __future__ import annotations

import math
from typing import Any, Callable

CX, CY = 360, 660
WHITE = (232, 246, 255, 235)
CYAN = (73, 226, 255, 230)
BLUE = (65, 155, 255, 230)
WATER = (40, 120, 215, 150)
ORANGE = (255, 160, 60, 230)
YELLOW = (255, 225, 90, 230)
RED = (255, 85, 85, 230)
GREEN = (90, 220, 130, 230)
GREY = (150, 175, 200, 200)


def _c(color: tuple, alpha: int) -> tuple:
    return (*color[:3], alpha)


def _label(draw: Any, xy: tuple[int, int], text: str, fonts: dict[str, Any], color: tuple = WHITE, anchor: str = "la") -> None:
    draw.text(xy, text, font=fonts["label"], fill=color, anchor=anchor, stroke_width=1, stroke_fill=(3, 20, 42, 210))


def _dot(draw: Any, x: float, y: float, r: float, color: tuple) -> None:
    draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _glow(draw: Any, x: float, y: float, r: float, color: tuple) -> None:
    for extra, alpha in ((r * 1.9, 28), (r * 1.4, 55), (r * 1.1, 95)):
        draw.ellipse((x - extra, y - extra, x + extra, y + extra), fill=_c(color, alpha))
    _dot(draw, x, y, r, color)


def _arrow(draw: Any, x0: float, y0: float, x1: float, y1: float, color: tuple, width: int = 4) -> None:
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    angle = math.atan2(y1 - y0, x1 - x0)
    for side in (-0.5, 0.5):
        draw.line((x1, y1, x1 - 16 * math.cos(angle + side), y1 - 16 * math.sin(angle + side)), fill=color, width=width)


def _gauge(draw: Any, x: int, y0: int, y1: int, level: float, color: tuple) -> None:
    draw.rounded_rectangle((x - 14, y0, x + 14, y1), radius=14, outline=GREY, width=3)
    top = y1 - (y1 - y0 - 8) * max(0.02, min(1.0, level))
    draw.rounded_rectangle((x - 9, top, x + 9, y1 - 5), radius=9, fill=color)


def _sun(draw: Any, x: int, y: int, r: int = 46) -> None:
    _glow(draw, x, y, r, YELLOW)


def _star_field_waves(draw: Any, y: int, amp: float, t: float, color: tuple, x0: int = 90, x1: int = 630) -> None:
    pts = [(x, y + amp * math.sin(x * 0.045 + t * 3)) for x in range(x0, x1, 12)]
    draw.line(pts, fill=color, width=3)


# --------------------------------------------------------------- clouds

def evaporation(draw, p, t, fonts, color):
    _sun(draw, 580, 430)
    draw.rectangle((90, 800, 630, 930), fill=WATER)
    _star_field_waves(draw, 800, 6, t, _c(CYAN, 200), 90, 630)
    for i in range(26):
        phase = (t * 0.35 + i * 0.137) % 1.0
        x = 120 + (i * 53) % 480 + 14 * math.sin(phase * 9 + i)
        y = 790 - phase * 360
        _dot(draw, x, y, 5 + 3 * phase, _c(WHITE, int(200 * (1 - phase * 0.6))))
    _label(draw, (CX, 880), "WATER", fonts, WHITE, "mm")


def rising_cooling(draw, p, t, fonts, color):
    y = 880 - 400 * p
    r = 34 + 56 * p
    _glow(draw, 300, y, r, _c(BLUE, 200))
    _arrow(draw, 300, 900, 300, 470, _c(WHITE, 160), 3)
    _gauge(draw, 560, 420, 920, 1.0 - 0.85 * p, _c(ORANGE if p < 0.5 else CYAN, 230))
    _label(draw, (560, 395), f"{int(25 - 40 * p)}°C", fonts, WHITE, "mm")
    _label(draw, (300, 935), "AIR RISES, EXPANDS, COOLS", fonts, CYAN, "mm")


def condensation(draw, p, t, fonts, color):
    nuclei = [(250, 640), (360, 700), (470, 630), (310, 780), (430, 790)]
    for i, (x, y) in enumerate(nuclei):
        _dot(draw, x, y, 7, GREY)
        for k in range(9):
            a = k * 0.7 + i
            start = (x + 190 * math.cos(a), y + 190 * math.sin(a))
            pos = (start[0] + (x - start[0]) * min(1, p * 1.3), start[1] + (y - start[1]) * min(1, p * 1.3))
            _dot(draw, pos[0], pos[1], 4, _c(WHITE, 190))
        radius = 14 + 46 * p
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=_c(CYAN, int(60 + 150 * p)), width=3,
                     fill=_c(WHITE, int(20 + 70 * p)))
    _label(draw, (CX, 900), "dust · sea salt · smoke", fonts, GREY, "mm")


# --------------------------------------------------------------- Moon

def moon_phases(draw, p, t, fonts, color):
    _sun(draw, 110, CY, 40)
    for k in range(5):
        draw.line((170, CY - 80 + k * 40, 600, CY - 80 + k * 40), fill=_c(YELLOW, 60), width=2)
    _glow(draw, CX, CY, 46, _c(BLUE, 220))
    angle = math.pi * 2 * p
    mx, my = CX + 200 * math.cos(angle + math.pi), CY + 200 * 0.45 * math.sin(angle + math.pi)
    _dot(draw, mx, my, 34, GREY)
    draw.pieslice((mx - 34, my - 34, mx + 34, my + 34), 90, 270, fill=WHITE)
    _label(draw, (CX, 850), "THE SUN ALWAYS LIGHTS HALF THE MOON", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "we see a changing part of that half", fonts, WHITE, "mm")


def eclipse_shadow(draw, p, t, fonts, color):
    _sun(draw, 110, CY, 40)
    _glow(draw, 340, CY, 52, _c(BLUE, 220))
    draw.polygon([(340, CY - 52), (620, CY - 26), (620, CY + 26), (340, CY + 52)], fill=(5, 10, 25, 150))
    mx = 640 - 230 * p
    _dot(draw, mx, CY, 30, GREY if p < 0.5 else (120, 50, 40, 230))
    _label(draw, (CX, 850), "ONLY IN A LUNAR ECLIPSE", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "does Earth's shadow fall on the Moon", fonts, WHITE, "mm")


# --------------------------------------------------------------- ocean

def light_absorption(draw, p, t, fonts, color):
    draw.rectangle((220, 460, 500, 930), fill=_c(WATER, 120))
    colours = [(RED, 560), (ORANGE, 640), (YELLOW, 720), (GREEN, 790), (BLUE, 910)]
    for i, (col, depth) in enumerate(colours):
        x = 255 + i * 52
        reach = min(depth - 460, (depth - 460) * min(1.0, p * 1.6)) + 40
        draw.line((x, 400, x, 460 + reach), fill=col, width=9)
    _label(draw, (CX, 380), "WHITE LIGHT ENTERS WATER", fonts, WHITE, "mm")
    _label(draw, (150, 560), "red fades", fonts, RED, "mm")
    _label(draw, (CX, 950), "blue travels deepest", fonts, BLUE, "mm")


def scattering_compare(draw, p, t, fonts, color):
    draw.line((CX, 400, CX, 930), fill=_c(GREY, 120), width=2)
    _label(draw, (210, 420), "SKY: SCATTERING", fonts, CYAN, "mm")
    _label(draw, (510, 420), "SEA: ABSORPTION", fonts, CYAN, "mm")
    for i in range(14):
        a = (t * 0.6 + i * 0.5) % 6.28
        _dot(draw, 210 + 110 * math.cos(a + i), 640 + 90 * math.sin(a * 1.3 + i), 6, _c(BLUE, 200))
    draw.line((90, 520, 210, 640), fill=WHITE, width=5)
    draw.rectangle((410, 560, 620, 920), fill=_c(WATER, 120))
    draw.line((470, 480, 470, 560 + 260 * p), fill=RED, width=6)
    draw.line((560, 480, 560, 920), fill=BLUE, width=6)
    _label(draw, (CX, 960), "two different effects", fonts, WHITE, "mm")


def sediment_colors(draw, p, t, fonts, color):
    tints = [(40, 120, 215), (40, 170, 160), (80, 170, 80), (150, 120, 70)]
    pos = p * (len(tints) - 1)
    i = min(len(tints) - 2, int(pos))
    f = pos - i
    tint = tuple(int(tints[i][k] * (1 - f) + tints[i + 1][k] * f) for k in range(3))
    draw.rounded_rectangle((220, 500, 500, 900), radius=24, fill=(*tint, 170), outline=_c(CYAN, 180), width=3)
    for n in range(30):
        phase = (t * 0.2 + n * 0.07) % 1.0
        _dot(draw, 240 + (n * 37) % 240, 520 + phase * 360, 3 + n % 3, _c(WHITE, 160))
    _label(draw, (CX, 940), "the colour shifts", fonts, WHITE, "mm")


# --------------------------------------------------------------- lightning

def _bolt(draw, x0, y0, y1, seed, color, width):
    pts = [(x0, y0)]
    y = y0
    k = 0
    while y < y1:
        y += 46
        k += 1
        pts.append((x0 + 46 * math.sin(seed + k * 1.9) + 18 * math.sin(k * 5.1), y))
    draw.line(pts, fill=color, width=width)
    return pts


def lightning_bolt(draw, p, t, fonts, color):
    draw.ellipse((150, 330, 570, 470), fill=_c(GREY, 120))
    flash = 0.5 + 0.5 * math.sin(t * 14)
    _bolt(draw, 360, 440, 900, 1.3, _c(WHITE, int(150 + 100 * flash)), 7)
    _bolt(draw, 360, 440, 900, 1.3, _c(CYAN, 90), 16)
    _label(draw, (CX, 950), "A LIGHTNING CHANNEL", fonts, CYAN, "mm")


def heat_halo(draw, p, t, fonts, color):
    pts = _bolt(draw, 360, 420, 900, 1.3, _c(WHITE, 240), 6)
    for r, a in ((190, 35), (140, 60), (95, 95)):
        draw.ellipse((360 - r, 660 - r * 1.4, 360 + r, 660 + r * 1.4), fill=_c(ORANGE, int(a * (0.6 + 0.4 * p))))
    _gauge(draw, 600, 420, 900, p, _c(RED, 230))
    _label(draw, (600, 395), f"{int(54000 * p):,}°F", fonts, WHITE, "mm")
    _label(draw, (CX, 950), "the AIR around the channel", fonts, ORANGE, "mm")


def pressure_wave(draw, p, t, fonts, color):
    _glow(draw, CX, 560, 20, _c(WHITE, 240))
    for k in range(4):
        r = ((p * 1.4 + k * 0.22) % 1.0) * 260
        draw.ellipse((CX - r, 560 - r, CX + r, 560 + r), outline=_c(CYAN, int(220 * (1 - r / 260))), width=4)
    pts = [(x, 850 + (60 * math.sin((x - 90) * 0.09 - t * 6) * min(1.0, p * 2)) * math.exp(-(x - 90) / 420)) for x in range(90, 630, 6)]
    draw.line(pts, fill=ORANGE, width=3)
    _label(draw, (CX, 930), "THE AIR EXPANDS · WE HEAR THUNDER", fonts, WHITE, "mm")


# --------------------------------------------------------------- stars

def star_beam(draw, p, t, fonts, color):
    _glow(draw, CX, 420, 18, _c(YELLOW, 240))
    draw.line((CX, 440, CX, 760), fill=_c(YELLOW, 150), width=5)
    draw.ellipse((120, 800, 600, 1150), outline=_c(BLUE, 200), width=4)
    _label(draw, (CX, 780), "steady light", fonts, WHITE, "mm")


def star_twinkle(draw, p, t, fonts, color):
    _glow(draw, CX, 420, 18, _c(YELLOW, 240))
    for k, y in enumerate((560, 640, 720)):
        _star_field_waves(draw, y, 9, t + k, _c(CYAN, 140))
    x = CX
    pts = [(x, 440)]
    for y in (560, 640, 720, 820):
        x = CX + 24 * math.sin(t * 7 + y * 0.05)
        pts.append((x, y))
    draw.line(pts, fill=_c(YELLOW, 190), width=4)
    _glow(draw, x, 840 + 6 * math.sin(t * 11), 10 + 3 * math.sin(t * 13), _c(WHITE, 240))
    _label(draw, (CX, 930), "MOVING AIR BENDS THE LIGHT", fonts, CYAN, "mm")


def twinkle_compare(draw, p, t, fonts, color):
    draw.line((CX, 400, CX, 930), fill=_c(GREY, 120), width=2)
    _label(draw, (210, 420), "FROM THE GROUND", fonts, CYAN, "mm")
    _label(draw, (510, 420), "FROM SPACE", fonts, CYAN, "mm")
    _glow(draw, 210 + 10 * math.sin(t * 9), 700 + 8 * math.cos(t * 11), 12 + 4 * math.sin(t * 13), _c(WHITE, 240))
    _glow(draw, 510, 700, 12, _c(WHITE, 240))
    _label(draw, (210, 880), "twinkles", fonts, YELLOW, "mm")
    _label(draw, (510, 880), "steady", fonts, GREEN, "mm")


# --------------------------------------------------------------- Earth

def plates_globe(draw, p, t, fonts, color):
    draw.ellipse((130, 430, 590, 890), fill=_c(BLUE, 70), outline=_c(CYAN, 200), width=3)
    shades = [GREEN, ORANGE, YELLOW, RED, CYAN, WHITE]
    for k in range(6):
        a0 = k * 60 + t * 6
        draw.pieslice((140, 440, 580, 880), a0, a0 + 56, fill=_c(shades[k], 85), outline=_c(WHITE, 200), width=2)
    _label(draw, (CX, 950), "EARTH'S SHELL IS BROKEN INTO PLATES", fonts, CYAN, "mm")


def plates_boundary(draw, p, t, fonts, color):
    shift = 40 * p
    draw.rectangle((90, 620, 340 + shift, 780), fill=_c(ORANGE, 150), outline=WHITE, width=2)
    draw.rectangle((380 - shift, 620, 630, 780), fill=_c(GREEN, 150), outline=WHITE, width=2)
    _arrow(draw, 150, 700, 150 + 70, 700, WHITE)
    _arrow(draw, 570, 700, 570 - 70, 700, WHITE)
    draw.line((120, 860, 600, 860), fill=GREY, width=3)
    for i in range(13):
        draw.line((120 + i * 40, 850, 120 + i * 40, 870), fill=GREY, width=2)
    _label(draw, (CX, 900), "a few centimetres per year", fonts, WHITE, "mm")


def plates_timelapse(draw, p, t, fonts, color):
    gap = 120 * (1 - p)
    draw.polygon([(90, 800), (90, 700), (320 - gap, 700), (320 - gap, 800)], fill=_c(ORANGE, 150))
    draw.polygon([(630, 800), (630, 700), (400 + gap, 700), (400 + gap, 800)], fill=_c(GREEN, 150))
    peak = 220 * p
    draw.polygon([(250, 700), (360, 700 - peak), (470, 700)], fill=_c(WHITE, int(60 + 140 * p)))
    _label(draw, (CX, 880), f"{int(p * 50)} MILLION YEARS", fonts, YELLOW, "mm")


def globe_bulge(draw, p, t, fonts, color):
    squash = 1.0 - 0.18 * min(1.0, p * 1.5)
    rx, ry = 230, 230 * squash
    draw.ellipse((CX - rx, CY - ry, CX + rx, CY + ry), fill=_c(BLUE, 90), outline=_c(CYAN, 220), width=4)
    for k in range(-2, 3):
        draw.arc((CX - rx, CY - ry * abs(math.cos(t * 0.7 + k * 0.6)), CX + rx, CY + ry * abs(math.cos(t * 0.7 + k * 0.6))), 0, 360, fill=_c(WHITE, 90), width=2)
    draw.line((CX - rx - 20, CY, CX + rx + 20, CY), fill=_c(YELLOW, 170), width=2)
    _label(draw, (CX, 900), "ROTATION MAKES THE EQUATOR BULGE", fonts, CYAN, "mm")


def gravity_surface(draw, p, t, fonts, color):
    pts = []
    for k in range(120):
        a = k / 120 * math.tau
        r = 220 + 14 * math.sin(a * 5 + t) + 9 * math.sin(a * 9 - t * 1.4)
        pts.append((CX + r * math.cos(a), CY + r * 0.92 * math.sin(a)))
    draw.polygon(pts, fill=_c(BLUE, 60), outline=_c(CYAN, 230))
    _label(draw, (CX, 900), "MOUNTAINS · TRENCHES · GRAVITY", fonts, CYAN, "mm")
    _label(draw, (CX, 935), "the real shape is irregular", fonts, WHITE, "mm")


# --------------------------------------------------------------- leaves

def leaf_pigments(draw, p, t, fonts, color):
    draw.ellipse((150, 480, 570, 880), fill=_c(GREEN, int(190 - 120 * p)), outline=_c(WHITE, 200), width=3)
    draw.line((150, 680, 570, 680), fill=_c(WHITE, 140), width=3)
    for k, (col, name) in enumerate(((GREEN, "green"), (YELLOW, "yellow"), (ORANGE, "orange"), (RED, "red"))):
        level = (1 - p) if k == 0 else (0.35 + 0.65 * p if k < 3 else p * 0.8)
        draw.rectangle((110 + k * 130, 960 - 70 * level, 190 + k * 130, 960), fill=col)
        _label(draw, (150 + k * 130, 985), name, fonts, WHITE, "mm")


def daylight_fade(draw, p, t, fonts, color):
    _sun(draw, 360, 560 + 100 * p, int(52 - 14 * p))
    draw.arc((120, 420, 600, 900), 200, 340, fill=_c(YELLOW, 150), width=3)
    draw.rectangle((140, 900, 580, 940), outline=GREY, width=3)
    draw.rectangle((144, 904, 144 + 432 * (1 - p), 936), fill=_c(GREEN, 220))
    _label(draw, (CX, 880), "SHORTER DAYS · LESS CHLOROPHYLL", fonts, CYAN, "mm")


# --------------------------------------------------------------- Mercury

def _orbit(draw, angle, planet_color):
    _sun(draw, CX, CY, 36)
    draw.ellipse((CX - 210, CY - 210, CX + 210, CY + 210), outline=_c(GREY, 110), width=2)
    _glow(draw, CX + 210 * math.cos(angle), CY + 210 * math.sin(angle), 15, planet_color)


def orbit_year(draw, p, t, fonts, color):
    _orbit(draw, p * math.tau - math.pi / 2, _c(ORANGE, 240))
    _label(draw, (CX, 440), f"DAY {int(88 * p)} OF 88", fonts, YELLOW, "mm")
    _label(draw, (CX, 940), "one Mercury year", fonts, WHITE, "mm")


def orbit_rotation(draw, p, t, fonts, color):
    _orbit(draw, p * 2 * math.tau - math.pi / 2, _c(ORANGE, 240))
    days = 176 * p
    _label(draw, (CX, 420), f"DAY {int(days)} · SPINS {days / 59:.1f} · ORBITS {days / 88:.1f}", fonts, CYAN, "mm")
    _label(draw, (CX, 455), "ONE SUNRISE-TO-SUNRISE = 176 DAYS", fonts, YELLOW, "mm")
    _label(draw, (CX, 940), "one solar day ≈ two Mercury years", fonts, WHITE, "mm")


# --------------------------------------------------------------- geyser

def geyser_eruption(draw, p, t, fonts, color):
    draw.polygon([(230, 900), (490, 900), (420, 830), (300, 830)], fill=_c(GREY, 150))
    height = 400 * math.sin(min(1.0, p * 1.2) * math.pi) ** 0.7
    for k in range(70):
        a = (k * 0.137 + t * 1.3) % 1.0
        reach = 0.45 + 0.55 * ((k * 37) % 10) / 10
        x = CX + (k % 9 - 4) * (5 + 16 * a)
        y = 830 - height * a * reach
        _dot(draw, x, y, 5 + 4 * (1 - a), _c(WHITE, int(230 * (1 - a * 0.55))))
    _label(draw, (CX, 430), f"NEXT ERUPTION IN ABOUT {60 + int(50 * p)} MIN", fonts, YELLOW, "mm")
    _label(draw, (CX, 950), "predictable, but not a clock", fonts, WHITE, "mm")


def interval_timeline(draw, p, t, fonts, color):
    draw.line((110, 700, 610, 700), fill=_c(GREY, 200), width=4)
    for i, (x, h, name) in enumerate(((140, 60, "short"), (330, 60, "long"), (560, 60, "next"))):
        _glow(draw, x, 700, 12, _c(CYAN, 230))
    _arrow(draw, 150, 640, 130 + 190 * min(1, p * 2), 640, YELLOW)
    _arrow(draw, 340, 640, 340 + 210 * max(0.0, min(1, p * 2 - 0.6)), 640, ORANGE)
    _label(draw, (235, 600), "shorter wait", fonts, YELLOW, "mm")
    _label(draw, (445, 600), "longer wait", fonts, ORANGE, "mm")


def geyser_cutaway(draw, p, t, fonts, color):
    draw.rectangle((190, 450, 530, 920), fill=_c(GREY, 60), outline=_c(WHITE, 160), width=2)
    draw.polygon([(340, 470), (380, 470), (390, 700), (430, 760), (430, 880), (290, 880), (290, 760), (330, 700)], fill=_c(WATER, 170))
    for k in range(14):
        a = (t * 0.5 + k * 0.17) % 1.0
        _dot(draw, 330 + (k % 5) * 18, 870 - a * 380 * (0.4 + 0.6 * p), 5, _c(WHITE, 190))
    draw.ellipse((300, 850, 420, 905), fill=_c(RED, int(80 + 120 * p)))


def tidal_pull(draw, p, t, fonts, color):
    r = 70
    draw.ellipse((CX - r - 38, CY - r, CX + r + 38, CY + r), fill=_c(WATER, 120))  # ocean bulged toward and away from the Moon
    _glow(draw, CX, CY, r - 14, _c(GREEN, 170))
    angle = math.pi * 2 * p * 0.5
    mx, my = CX + 250 * math.cos(angle), CY + 250 * 0.35 * math.sin(angle) - 40
    _dot(draw, mx, my, 28, GREY)
    _arrow(draw, CX + 80 * math.cos(angle), CY + 80 * 0.35 * math.sin(angle), mx - 40 * math.cos(angle), my + 10, YELLOW)
    _sun(draw, 80, 450, 34)
    _label(draw, (CX, 850), "THE MOON'S AND SUN'S PULL", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "raises the ocean on Earth", fonts, WHITE, "mm")


def tide_alignment(draw, p, t, fonts, color):
    _sun(draw, 90, CY, 40)
    _glow(draw, CX, CY, 46, _c(BLUE, 220))
    k = 0.4 + 0.6 * min(1.0, p * 1.6)
    draw.ellipse((CX - 60 - 40 * k, CY - 60, CX + 60 + 40 * k, CY + 60), fill=_c(WATER, 120))
    _dot(draw, 600, CY - 100 * (1 - min(1.0, p * 1.6)), 26, GREY)
    draw.line((120, CY, 580, CY), fill=_c(WHITE, 60), width=2)
    _label(draw, (CX, 850), "FULL OR NEW MOON: SPRING TIDES", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "Sun, Moon and Earth in a line", fonts, WHITE, "mm")


def tide_gauge(draw, p, t, fonts, color):
    days = 2 * p
    level = 0.5 + 0.5 * math.sin(2 * math.pi * 2 * days)  # about two high tides per day
    draw.line((140, 780, 600, 780), fill=GREY, width=3)
    pts = [(140 + 460 * (i / 80), 600 - 90 * math.sin(2 * math.pi * 2 * (2 * i / 80))) for i in range(81)]
    draw.line(pts, fill=_c(CYAN, 120), width=3)
    x = 140 + 460 * (days / 2)
    y = 600 - 90 * math.sin(2 * math.pi * 2 * days)
    _glow(draw, x, y, 12, YELLOW)
    _gauge(draw, 90, 480, 720, level, BLUE)
    _label(draw, (CX + 20, 830), f"HIGH TIDES SO FAR: {int(2 * days * 1.0 + 0.25)}", fonts, YELLOW, "mm")
    _label(draw, (CX + 20, 870), "tidal range = high minus low", fonts, WHITE, "mm")


def seafloor_quake(draw, p, t, fonts, color):
    draw.rectangle((100, 820, 620, 940), fill=(90, 70, 55, 230))
    shift = 14 * math.sin(t * 40) * max(0.0, 1 - p) if p < 0.5 else 0
    draw.polygon([(100, 820), (360 + shift, 820), (360 + shift, 940), (100, 940)], fill=(120, 95, 70, 235))
    draw.rectangle((100, 600, 620, 820), fill=_c(WATER, 110))
    for k in range(4):
        rr = 30 + 90 * ((p * 2 + k * 0.25) % 1.0)
        draw.arc((360 - rr, 820 - rr, 360 + rr, 820 + rr), 200, 340, fill=_c(YELLOW, int(220 * (1 - rr / 120))), width=4)
    lift = 34 * min(1.0, p * 2)
    draw.arc((160, 590 - lift, 560, 630 + lift), 190, 350, fill=WHITE, width=5)
    _label(draw, (CX, 470), "sets off a giant wave", fonts, WHITE, "mm")


def tsunami_deep(draw, p, t, fonts, color):
    draw.rectangle((80, 700, 640, 900), fill=_c(WATER, 90))
    pts = [(80 + 560 * i / 120, 700 - 18 * math.sin((i / 120) * 2 * math.pi * 1.4 - p * 16)) for i in range(121)]
    draw.line(pts, fill=WHITE, width=5)
    _glow(draw, 80 + 560 * ((p * 3) % 1.0), 640, 12, YELLOW)
    _label(draw, (CX, 470), "OUT AT SEA: LOW, FAST WAVES", fonts, YELLOW, "mm")
    _label(draw, (CX, 510), "they do not grow dramatically in height", fonts, WHITE, "mm")


def tsunami_shore(draw, p, t, fonts, color):
    draw.polygon([(80, 900), (640, 700 - 0), (640, 900)], fill=(120, 95, 70, 235))
    draw.polygon([(80, 760), (640, 700), (640, 900), (80, 900)], fill=_c(WATER, 70))
    x = 120 + 420 * p
    height = 18 + 90 * p
    width = 140 - 70 * p
    pts = [(x - width + 2 * width * i / 40, (760 - 60 * (x - 80) / 560) - height * math.exp(-(((i - 20) / 9) ** 2))) for i in range(41)]
    draw.line(pts, fill=WHITE, width=5)
    _label(draw, (CX, 510), "reaching farther inland than usual", fonts, WHITE, "mm")


def salt_sources(draw, p, t, fonts, color):
    draw.polygon([(60, 760), (60, 560), (260, 640), (330, 760)], fill=(110, 95, 75, 235))  # land
    draw.rectangle((60, 760, 660, 920), fill=_c(WATER, 120))
    for k in range(6):
        y = 470 + ((t * 120 + k * 45) % 150)
        draw.line((110 + k * 26, y, 104 + k * 26, y + 16), fill=_c(CYAN, 200), width=3)  # rain on the rocks
    draw.line((250, 640, 330, 760), fill=_c(BLUE, 220), width=5)  # river to the sea
    for k in range(4):
        draw.line((470 + k * 40, 920, 470 + k * 40, 870 - 20 * math.sin(t * 3 + k)), fill=_c(ORANGE, 200), width=5)  # seafloor vents
    for k in range(int(70 * p)):
        _dot(draw, 340 + (k * 53) % 300, 780 + (k * 37) % 120, 4, _c(WHITE, 220))
    _label(draw, (180, 520), "rocks + rivers", fonts, WHITE, "mm")
    _label(draw, (545, 840), "seafloor vents", fonts, ORANGE, "mm")


def salt_share(draw, p, t, fonts, color):
    draw.rectangle((80, 560, 640, 640), outline=GREY, width=3)
    width = 560 * 0.035 * min(1.0, p * 1.5)
    draw.rectangle((80, 560, 80 + max(4, width), 640), fill=WHITE)
    _label(draw, (CX, 520), "ABOUT 3.5% OF SEAWATER'S WEIGHT IS SALT", fonts, CYAN, "mm")
    draw.rectangle((80, 740, 640, 800), outline=GREY, width=3)
    draw.rectangle((80, 740, 80 + 560 * 0.85 * min(1.0, p * 1.5), 800), fill=_c(YELLOW, 200))
    _label(draw, (CX, 700), "SODIUM + CHLORIDE: ABOUT 85% OF DISSOLVED IONS", fonts, YELLOW, "mm")


def dense_float(draw, p, t, fonts, color):
    draw.rectangle((60, 700, 660, 940), fill=_c(WATER, 140))
    bob = 6 * math.sin(t * 2)
    draw.rounded_rectangle((250, 665 + bob, 470, 705 + bob), radius=18, fill=_c(ORANGE, 230))
    _dot(draw, 480, 668 + bob, 22, _c(ORANGE, 230))
    for k in range(40):
        _dot(draw, 80 + (k * 71) % 560, 720 + (k * 43) % 200, 3, _c(WHITE, 150))
    _label(draw, (CX, 520), "THE EXTREMELY SALTY DEAD SEA", fonts, CYAN, "mm")
    _label(draw, (CX, 560), "dense water holds you up like a mattress", fonts, WHITE, "mm")


def enso_winds(draw, p, t, fonts, color):
    draw.rectangle((60, 700, 660, 880), fill=_c(WATER, 110))
    shift = max(0.0, min(1.0, (p - 0.45) * 2.2))
    bx = 190 + 340 * shift
    for extra, alpha in ((120, 60), (85, 110), (55, 170)):
        draw.ellipse((bx - extra, 760 - extra * 0.5, bx + extra, 760 + extra * 0.5), fill=_c(ORANGE, alpha))
    strength = 1 - shift
    for k in range(4):
        x = 150 + k * 130
        if shift < 0.5:
            _arrow(draw, x + 90, 620, x, 620, _c(WHITE, 230), 3 + int(2 * strength))
        else:
            _arrow(draw, x, 620, x + 40, 620, _c(WHITE, 110), 2)
    _label(draw, (110, 930), "INDONESIA", fonts, WHITE, "mm")
    _label(draw, (610, 930), "S. AMERICA", fonts, WHITE, "mm")
    _label(draw, (CX, 470), "NORMAL: WINDS PUSH WARM WATER WEST" if shift < 0.5 else "EL NIÑO: WINDS WEAKEN", fonts, CYAN, "mm")
    if shift >= 0.5:
        _label(draw, (CX, 510), "warm water piles up near South America", fonts, WHITE, "mm")


def jet_stream_shift(draw, p, t, fonts, color):
    y0 = 560 + 150 * min(1.0, p * 1.4)
    pts = [(60 + 600 * i / 80, y0 + 28 * math.sin(i / 7 + t * 2)) for i in range(81)]
    draw.line(pts, fill=_c(CYAN, 230), width=6)
    draw.ellipse((330, 820, 650, 900), fill=_c(ORANGE, 150))
    for k in range(5):
        _dot(draw, 440 + k * 38, 780 - 8 * (k % 2), 26, _c(GREY, 210))
    for k in range(6):
        y = 790 + ((t * 110 + k * 40) % 90)
        draw.line((430 + k * 36, y, 426 + k * 36, y + 14), fill=_c(BLUE, 210), width=3)
    _label(draw, (CX, 490), "much more rain in some places, drought in others", fonts, WHITE, "mm")


def upwelling(draw, p, t, fonts, color):
    draw.rectangle((100, 560, 620, 920), fill=_c(WATER, 110))
    strength = 1 - min(1.0, p * 1.3)
    for k in range(5):
        x = 170 + k * 95
        rise = 200 * strength
        if rise > 6:
            _arrow(draw, x, 900, x, 900 - rise, _c(CYAN, int(60 + 170 * strength)), 4)
    for k in range(int(12 * strength)):
        _dot(draw, 130 + (k * 83) % 460, 640 + (k * 47) % 180, 4, _c(GREEN, 220))
    _label(draw, (CX, 500), "COLD, NUTRIENT-RICH WATER RISES", fonts, CYAN, "mm")
    _label(draw, (CX, 960), "in El Niño, upwelling weakens or stops", fonts, WHITE, "mm")


def hurricane_engine(draw, p, t, fonts, color):
    draw.rectangle((60, 800, 660, 940), fill=_c(WATER, 140))
    for k in range(10):
        a = (t * 0.5 + k / 10) % 1.0
        x = 150 + 420 * ((k * 0.37) % 1.0)
        y = 800 - 240 * a
        _arrow(draw, x, y + 40, x, y, _c(RED, 210), 3)
    for k in range(int(6 * p) + 1):
        _dot(draw, 200 + k * 60, 575 - 12 * (k % 2), 40, _c(WHITE, 190))
    _label(draw, (CX, 470), "rising air cools and forms clouds", fonts, WHITE, "mm")


def hurricane_spin(draw, p, t, fonts, color):
    for arm in range(4):
        pts = []
        for i in range(60):
            r = 30 + i * 4.2
            a = -t * 1.2 + arm * math.pi / 2 - i * 0.09
            pts.append((CX + r * math.cos(a), CY + r * 0.9 * math.sin(a)))
        draw.line(pts, fill=_c(WHITE, 200), width=9)
    _glow(draw, CX, CY, 24, _c(CYAN, 120))
    _label(draw, (CX, CY), "EYE", fonts, WHITE, "mm")
    _label(draw, (CX, 930), "south of it: clockwise · calm, clear eye", fonts, WHITE, "mm")


def hurricane_landfall(draw, p, t, fonts, color):
    draw.rectangle((60, 760, 380, 920), fill=_c(WATER, 140))
    draw.rectangle((380, 760, 660, 920), fill=(110, 95, 75, 235))
    x = 150 + 400 * p
    size = 120 if x < 380 else max(30, 120 - (x - 380) * 0.6)
    alpha = 220 if x < 380 else int(max(60, 220 - (x - 380) * 0.8))
    for arm in range(3):
        pts = [(x + (size * i / 40) * math.cos(-t * 1.5 + arm * 2.1 - i * 0.18), 640 + (size * i / 40) * 0.8 * math.sin(-t * 1.5 + arm * 2.1 - i * 0.18)) for i in range(40)]
        draw.line(pts, fill=_c(WHITE, alpha), width=7)
    _gauge(draw, 90, 450, 700, 0.9 if x < 380 else max(0.1, 0.9 - (x - 380) / 300), RED)
    _label(draw, (CX + 30, 450), "74 MPH WINDS = HURRICANE", fonts, CYAN, "mm")
    _label(draw, (CX + 30, 500), "over land it loses its ocean fuel", fonts, WHITE, "mm")


def sleep_vitals(draw, p, t, fonts, color):
    for row, (name, col, base) in enumerate((("HEART RATE", RED, 560), ("BLOOD PRESSURE", ORANGE, 760))):
        pts = [(100 + 520 * i / 60, base - 60 + 50 * min(1.0, i / 60 * 1.4) + 8 * math.sin(i / 3 + t * 3 + row)) for i in range(int(61 * min(1.0, p * 1.3 + 0.05)))]
        if len(pts) > 1:
            draw.line(pts, fill=_c(col, 230), width=5)
        _label(draw, (110, base - 90), name, fonts, col, "la")


def sleep_memory(draw, p, t, fonts, color):
    nodes = [(CX + 190 * math.cos(k * 0.9), CY + 150 * math.sin(k * 1.3)) for k in range(12)]
    lit = int(12 * min(1.0, p * 1.3))
    for i in range(lit):
        for j in range(i):
            if (i + j) % 3 == 0:
                draw.line((*nodes[i], *nodes[j]), fill=_c(CYAN, 110), width=2)
    for i, (x, y) in enumerate(nodes):
        _glow(draw, x, y, 10, YELLOW if i < lit else _c(GREY, 120))
    _label(draw, (CX, 930), "and supports learning", fonts, WHITE, "mm")


def sleep_ages(draw, p, t, fonts, color):
    draw.line((100, 820, 620, 820), fill=GREY, width=3)
    for k in range(7):
        h = 260 - 22 * k
        draw.rectangle((130 + k * 70, 820 - h, 170 + k * 70, 820), fill=_c(BLUE, 120))
    i = min(6, int(p * 7))
    h = 260 - 22 * i
    draw.rectangle((130 + i * 70, 820 - h, 170 + i * 70, 820), fill=_c(YELLOW, 230))
    _label(draw, (CX, 860), "AGE  →", fonts, WHITE, "mm")


def _earth(draw, x, y, r):
    _glow(draw, x, y, r, _c(BLUE, 230))
    draw.ellipse((x - r * 0.55, y - r * 0.35, x - r * 0.1, y + r * 0.2), fill=_c(GREEN, 200))


def ear_signal(draw, p, t, fonts, color):
    for k in range(4):
        x = 70 + ((t * 120 + k * 45) % 180)
        draw.arc((x - 18, CY - 40, x + 18, CY + 40), -60, 60, fill=_c(CYAN, 220), width=4)
    draw.arc((250, CY - 90, 340, CY + 90), 90, 270, fill=_c(WHITE, 230), width=8)
    _label(draw, (295, CY + 120), "EAR", fonts, WHITE, "mm")
    draw.line((340, CY, 520, CY), fill=_c(GREY, 200), width=4)
    for k in range(5):
        a = (t * 0.7 + k / 5) % 1.0
        _dot(draw, 340 + 180 * a, CY, 6, _c(YELLOW, 240))
    _label(draw, (430, CY - 40), "auditory nerve", fonts, YELLOW, "mm")
    draw.ellipse((520, CY - 80, 660, CY + 80), outline=_c(CYAN, 230), width=4)
    _label(draw, (590, CY), "BRAIN", fonts, WHITE, "mm")
    _label(draw, (180, CY + 120), "sound waves", fonts, CYAN, "mm")


def noise_gauge(draw, p, t, fonts, color):
    level = 0.25 + 0.65 * min(1.0, p * 1.4)
    _gauge(draw, 150, 480, 880, level, ORANGE if level > 0.7 else GREEN)
    y = 880 - (880 - 480) * 0.7
    draw.line((120, y, 260, y), fill=_c(RED, 240), width=4)
    _label(draw, (290, y), "85 dBA: HAZARDOUS", fonts, RED, "lm")
    _label(draw, (290, 760), "below: safer", fonts, GREEN, "lm")


def hearing_protect(draw, p, t, fonts, color):
    draw.arc((220, CY - 150, 500, CY + 90), 180, 360, fill=_c(WHITE, 230), width=10)
    for x in (210, 510):
        draw.rounded_rectangle((x - 35, CY - 40, x + 35, CY + 70), 14, fill=_c(CYAN, 210))
    _label(draw, (CX, CY + 140), "NEARLY ALWAYS PREVENTABLE", fonts, GREEN, "mm")
    _label(draw, (CX, CY + 190), "get a hearing test every year if noise is hazardous", fonts, WHITE, "mm")


def heart_pump(draw, p, t, fonts, color):
    beat = 1.0 + 0.08 * math.sin(t * 6.0)
    r = 80 * beat
    draw.ellipse((CX - r - 20, CY - r, CX + 20, CY + r), fill=_c(RED, 220))
    draw.ellipse((CX - 20, CY - r, CX + r + 20, CY + r), fill=_c(RED, 220))
    draw.polygon([(CX - r - 15, CY + 15), (CX + r + 15, CY + 15), (CX, CY + r * 1.9)], fill=_c(RED, 220))
    for k in range(6):
        a = (t * 0.5 + k / 6) % 1.0
        ang = 2 * math.pi * a
        _dot(draw, CX + 240 * math.cos(ang), CY + 20 + 170 * math.sin(ang), 7, _c(ORANGE, 230))
    draw.ellipse((CX - 255, CY - 160, CX + 255, CY + 200), outline=_c(RED, 110), width=3)
    _label(draw, (CX, CY + 250), "valves keep blood flowing one way", fonts, WHITE, "mm")


def blood_delivery(draw, p, t, fonts, color):
    draw.ellipse((90, CY - 90, 250, CY + 90), outline=_c(CYAN, 220), width=4)
    _label(draw, (170, CY), "BLOOD", fonts, WHITE, "mm")
    draw.ellipse((470, CY - 90, 630, CY + 90), outline=_c(GREEN, 220), width=4)
    _label(draw, (550, CY), "ORGANS", fonts, WHITE, "mm")
    for k in range(5):
        a = (t * 0.5 + k / 5) % 1.0
        _dot(draw, 260 + 200 * a, CY - 40, 7, _c(ORANGE, 240))
        _dot(draw, 460 - 200 * a, CY + 40, 7, _c(GREY, 240))
    _label(draw, (CX, CY - 80), "oxygen + nutrients", fonts, ORANGE, "mm")
    _label(draw, (CX, CY + 90), "carbon dioxide, on its way to the lungs", fonts, GREY, "mm")


def heart_risks(draw, p, t, fonts, color):
    for k, name in enumerate(("HIGH BLOOD PRESSURE", "HIGH BLOOD CHOLESTEROL", "SMOKING")):
        y = 520 + k * 110
        on = p * 3 > k
        draw.rounded_rectangle((120, y, 600, y + 70), 12, outline=_c(RED if on else GREY, 230), width=3)
        _label(draw, (CX, y + 35), name, fonts, WHITE, "mm")
    _label(draw, (CX, 880), "47% OF PEOPLE IN THE US HAVE AT LEAST ONE", fonts, YELLOW, "mm")


def ozone_shield(draw, p, t, fonts, color):
    draw.arc((-200, 760, 920, 1900), 205, 335, fill=_c(CYAN, 150), width=22)  # the planet's limb
    draw.arc((-120, 700, 840, 1760), 215, 325, fill=_c(PURPLE if "PURPLE" in globals() else BLUE, 170), width=18)  # ozone layer
    for k in range(7):
        x = 110 + k * 82
        y = 430 + ((t * 160 + k * 60) % 230)
        blocked = y > 640
        draw.line((x, y - 40, x, y), fill=_c(YELLOW, 60 if blocked else 230), width=4)
    _label(draw, (CX, 930), "a sunscreen for the planet", fonts, WHITE, "mm")


def cfc_cycle(draw, p, t, fonts, color):
    n = int(1 + 5 * min(1.0, p * 1.2))
    for k in range(5):
        x = 130 + k * 115
        alive = k >= n
        _dot(draw, x, 760, 26, _c(BLUE, 230) if alive else _c(GREY, 80))
        _label(draw, (x, 760), "O3" if alive else "", fonts, WHITE, "mm")
    cx = 130 + min(4, n - 1) * 115
    _glow(draw, cx, 640 + 12 * math.sin(t * 6), 18, _c(GREEN, 230))
    _label(draw, (cx, 590), "Cl", fonts, GREEN, "mm")
    _label(draw, (CX, 490), "up to 100,000 times", fonts, WHITE, "mm")


def ozone_hole_patch(draw, p, t, fonts, color):
    _earth(draw, CX, CY, 140)
    r = 20 + 70 * min(1.0, p * 1.3)
    draw.ellipse((CX - r * 0.6, CY + 100 - r * 0.35, CX + r * 0.6, CY + 100 + r * 0.35), fill=_c(RED, 150))
    _label(draw, (CX, CY + 200), "THIN PATCH OVER ANTARCTICA", fonts, RED, "mm")
    _label(draw, (CX, 450), "THE OZONE \"HOLE\" IS A THINNING", fonts, CYAN, "mm")


def flare_burst(draw, p, t, fonts, color):
    _glow(draw, CX, CY + 100, 150, _c(YELLOW, 230))
    for k in range(3):
        a = 0.6 + k * 0.9
        pts = [(CX + (130 + 40 * math.sin(i / 8 * math.pi)) * math.cos(a + i * 0.02 * (1 + p)), CY + 100 - (130 + 40 * math.sin(i / 8 * math.pi)) * math.sin(a + i * 0.02 * (1 + p))) for i in range(9)]
        draw.line(pts, fill=_c(RED, 220), width=5)
    if p > 0.5:
        for k in range(12):
            a = 0.2 + k * 0.17
            L = 220 * (p - 0.5) * 2
            draw.line((CX + 150 * math.cos(a), CY + 100 - 150 * math.sin(a), CX + (150 + L) * math.cos(a), CY + 100 - (150 + L) * math.sin(a)), fill=_c(WHITE, 220), width=4)


def flare_travel(draw, p, t, fonts, color):
    _glow(draw, 120, CY + 60, 60, _c(YELLOW, 230))
    _earth(draw, 600, CY + 60, 34)
    x = 120 + 480 * p
    draw.line((180, CY + 60, x, CY + 60), fill=_c(WHITE, 200), width=4)
    _glow(draw, x, CY + 60, 9, YELLOW)
    _label(draw, (CX, 470), f"AT LIGHT SPEED: {int(8 * p)} / 8 MINUTES", fonts, YELLOW, "mm")
    _label(draw, (CX, 510), "the flare's energy reaches Earth", fonts, WHITE, "mm")


def geodynamo(draw, p, t, fonts, color):
    draw.ellipse((CX - 200, CY - 200, CX + 200, CY + 200), fill=_c(BLUE, 90))
    draw.ellipse((CX - 110, CY - 110, CX + 110, CY + 110), fill=_c(ORANGE, 170))
    for k in range(8):
        a = t * 1.3 + k * math.pi / 4
        _dot(draw, CX + 150 * math.cos(a), CY + 150 * 0.8 * math.sin(a), 8, _c(YELLOW, 230))
    for k in range(5):
        x = CX - 90 + k * 45
        draw.arc((x - 140, CY - 300, x + 140, CY - 100), 200, 340, fill=_c(CYAN, 120), width=3)
    _label(draw, (CX, 940), "the geodynamo makes the field", fonts, WHITE, "mm")


def magnetosphere(draw, p, t, fonts, color):
    _earth(draw, CX + 40, CY, 55)
    for k, w in enumerate((100, 150, 210, 280)):
        draw.arc((CX + 40 - w, CY - w * 0.8, CX + 40 + w, CY + w * 0.8), 100, 260, fill=_c(CYAN, 190 - 30 * k), width=3)
    for k in range(8):
        y = 360 + k * 85
        x = 40 + ((t * 120 + k * 50) % 220)
        deflect = 0 if x < 190 else min(1.0, (x - 190) / 40)
        _dot(draw, x if deflect == 0 else 200 + 20 * deflect, y - 60 * deflect * (1 if y < CY else -1), 5, _c(YELLOW, 220))
    _label(draw, (CX, 330), "THE MAGNETOSPHERE DEFLECTS THE SOLAR WIND", fonts, CYAN, "mm")


def pole_flip(draw, p, t, fonts, color):
    flip = p > 0.5
    draw.rounded_rectangle((CX - 40, 560, CX + 40, 880), radius=10, fill=_c(GREY, 90))
    top, bottom = (RED, BLUE) if not flip else (BLUE, RED)
    draw.rectangle((CX - 40, 560, CX + 40, 720), fill=_c(top, 210))
    draw.rectangle((CX - 40, 720, CX + 40, 880), fill=_c(bottom, 210))
    _label(draw, (CX, 530), "N" if not flip else "S", fonts, WHITE, "mm")
    _label(draw, (CX, 910), "S" if not flip else "N", fonts, WHITE, "mm")


def magma_rise(draw, p, t, fonts, color):
    draw.polygon([(120, 940), (300, 600), (420, 600), (600, 940)], fill=(110, 95, 75, 235))
    draw.ellipse((260, 800, 460, 900), fill=_c(ORANGE, 200))
    top = 800 - 200 * min(1.0, p * 1.4)
    draw.rectangle((350, top, 370, 820), fill=_c(ORANGE, 230))
    if p > 0.7:
        for k in range(10):
            a = (t * 1.5 + k / 10) % 1.0
            _dot(draw, 360 + (k % 5 - 2) * 14 * a, 600 - 120 * a, 6, _c(ORANGE, int(230 * (1 - a))))


def gas_pressure(draw, p, t, fonts, color):
    for side, (cx, name, explosive) in enumerate(((190, "THIN, RUNNY: FLOWS", False), (530, "THICK, STICKY: EXPLODES", True))):
        draw.rounded_rectangle((cx - 110, 620, cx + 110, 860), radius=20, fill=_c(ORANGE, 150))
        for k in range(9):
            a = (t * 0.6 + k / 9) % 1.0
            if explosive:
                _dot(draw, cx - 80 + (k * 37) % 160, 840 - 40 * a * min(1.0, p), 6, _c(WHITE, 200))
            else:
                _dot(draw, cx - 80 + (k * 37) % 160, 840 - 210 * a, 6, _c(WHITE, int(220 * (1 - a))))
        if explosive and p > 0.7:
            for k in range(14):
                a = (t * 2 + k / 14) % 1.0
                _dot(draw, cx + (k % 7 - 3) * 28 * a, 620 - 190 * a, 7, _c(GREY, int(230 * (1 - a))))
        _label(draw, (cx, 560), name, fonts, WHITE, "mm")


def sweat_cooling(draw, p, t, fonts, color):
    draw.rounded_rectangle((200, 560, 520, 900), radius=60, fill=_c(ORANGE, 120))
    for k in range(10):
        a = (t * 0.7 + k / 10) % 1.0
        x = 230 + (k * 53) % 260
        _dot(draw, x, 700 + (k * 29) % 160, 7 * (1 - a * 0.8), _c(CYAN, int(230 * (1 - a))))
        _arrow(draw, x, 690 + (k * 29) % 160, x + 6, 600 - 60 * a, _c(RED, int(200 * (1 - a))), 2)
    _label(draw, (CX, 940), "your natural cooling system", fonts, WHITE, "mm")


def heat_stroke_gauge(draw, p, t, fonts, color):
    level = 0.35 + 0.6 * min(1.0, p * 1.3)
    _gauge(draw, 150, 500, 760, level, RED)
    draw.line((330, 700, 560, 700), fill=_c(GREY, 120), width=3)
    ok = level < 0.8
    _label(draw, (440, 640), "SWEATING WORKS" if ok else "SWEATING FAILS", fonts, GREEN if ok else RED, "mm")
    _label(draw, (440, 760), "body temperature rises rapidly", fonts, WHITE, "mm")


def ac_relief(draw, p, t, fonts, color):
    draw.rounded_rectangle((140, 560, 580, 650), radius=18, fill=_c(CYAN, 150))
    for k in range(6):
        a = (t * 0.6 + k / 6) % 1.0
        _arrow(draw, 180 + k * 70, 670, 180 + k * 70, 670 + 130 * a, _c(CYAN, int(220 * (1 - a))), 3)
    draw.rectangle((140, 850, 580, 920), fill=_c(BLUE, 90))


def water_share_bars(draw, p, t, fonts, color):
    rows = (("ADULT BODY", 60), ("BONES", 31), ("BRAIN + HEART", 73), ("LUNGS", 83), ("BABY AT BIRTH", 78))
    for k, (name, pct) in enumerate(rows):
        y = 520 + k * 85
        grow = min(1.0, max(0.0, p * 1.6 - k * 0.15))
        draw.rectangle((220, y, 640, y + 40), outline=GREY, width=2)
        draw.rectangle((220, y, 220 + 420 * pct / 100 * grow, y + 40), fill=_c(BLUE, 210))
        _label(draw, (205, y + 20), name, fonts, WHITE, "rm")
        _label(draw, (225 + 420 * pct / 100 * grow, y + 20), f"{int(pct * grow)}%", fonts, YELLOW, "lm")


def water_carry(draw, p, t, fonts, color):
    draw.ellipse((CX - 130, CY - 120, CX + 130, CY + 120), outline=_c(CYAN, 220), width=5)
    for k in range(8):
        a = (t * 0.5 + k / 8) % 1.0
        _dot(draw, 60 + a * (CX - 190), CY - 80 + (k % 4) * 50, 7, _c(GREEN, 230))
        _dot(draw, CX + 140 + a * (CX - 190), CY - 80 + (k % 4) * 50, 7, _c(ORANGE, 230))
    _label(draw, (120, CY - 130), "nutrients in", fonts, GREEN, "mm")
    _label(draw, (600, CY - 130), "waste out", fonts, ORANGE, "mm")


def water_balance(draw, p, t, fonts, color):
    level = 0.8 - 0.35 * min(1.0, p * 1.3)
    if p > 0.75:
        level += 0.4 * (p - 0.75)
    _gauge(draw, 140, 520, 860, level, BLUE)
    for k, name in enumerate(("sweat", "bathroom", "breath")):
        _arrow(draw, 300, 640 + k * 70, 520, 640 + k * 70, _c(ORANGE, 220), 3)
        _label(draw, (560, 640 + k * 70), name, fonts, ORANGE, "lm")


def aurora_particles(draw, p, t, fonts, color):
    _glow(draw, 90, CY, 50, _c(YELLOW, 230))
    _earth(draw, 560, CY, 70)
    for k in range(5):
        draw.arc((560 - 150 - 20 * k, CY - 180 - 20 * k, 560 + 150 + 20 * k, CY + 180 + 20 * k), 100, 260, fill=_c(CYAN, 110), width=3)
    for k in range(8):
        a = (t * 0.5 + k / 8) % 1.0
        _dot(draw, 150 + a * 300, CY - 160 + k * 45, 5, _c(YELLOW, 220))
    for k in range(10):
        a = (t * 0.8 + k / 10) % 1.0
        _dot(draw, 560 + 10 * math.sin(k), CY - 70 - 100 * a, 4, _c(GREEN, int(230 * (1 - a * 0.3))))


def aurora_colours(draw, p, t, fonts, color):
    for y0, y1, col, label in ((520, 620, RED, "RED: OXYGEN, HIGHEST"), (620, 760, GREEN, "GREEN: OXYGEN, MOST COMMON"), (760, 860, BLUE, "BLUE: NITROGEN")):
        for k in range(24):
            x = 90 + k * 25
            h = (y1 - y0) * (0.6 + 0.4 * math.sin(t * 2 + k * 0.5))
            draw.line((x, y1, x, y1 - h), fill=_c(col, 130), width=18)
        _label(draw, (CX, (y0 + y1) / 2), label, fonts, WHITE, "mm")
    draw.rectangle((60, 880, 660, 940), fill=_c(GREEN, 40))


def aurora_twin(draw, p, t, fonts, color):
    _earth(draw, CX, CY, 110)
    for sign, name in ((-1, "NORTH"), (1, "SOUTH")):
        pts = [(CX - 90 + 180 * i / 30, CY + sign * (150 + 14 * math.sin(i / 3 + t * 2 * -sign))) for i in range(31)]
        draw.line(pts, fill=_c(GREEN, 220), width=8)
        _label(draw, (CX, CY + sign * 215), name, fonts, WHITE, "mm")


def fault_stick_slip(draw, p, t, fonts, color):
    stress = min(1.0, p * 1.6)
    slip = 0 if p < 0.6 else 28 * min(1.0, (p - 0.6) * 4)
    draw.rectangle((90, 620, 350, 860), fill=(110, 95, 75, 235))
    draw.rectangle((370 + 0, 620 - slip, 630, 860 - slip), fill=(130, 105, 80, 235))
    draw.line((360, 620, 360, 860), fill=_c(RED, 220), width=3)
    _arrow(draw, 250, 560, 250, 560 + 40 * (1 - 0.0), _c(YELLOW, 220), 3)
    _gauge(draw, 70, 520, 860, stress if p < 0.6 else max(0.05, 1.0 - (p - 0.6) * 2.5), YELLOW)
    if p >= 0.6:
        for k in range(3):
            r = 40 + 130 * (((p - 0.6) * 2 + k * 0.25) % 1.0)
            draw.arc((360 - r, 740 - r, 360 + r, 740 + r), 0, 360, fill=_c(WHITE, 150), width=3)


def seismograph_trace(draw, p, t, fonts, color):
    pts = []
    for i in range(120):
        x = 80 + 560 * i / 120
        env = 0.0 if i < 40 else math.exp(-(i - 40) / 25)
        pts.append((x, 700 + 150 * env * math.sin(i * 1.3)))
        if i / 120 > p * 1.2:
            break
    draw.line(pts, fill=_c(CYAN, 230), width=3)
    _label(draw, (CX, 900), "no one can predict when the next one will happen", fonts, WHITE, "mm")


def atom_jump(draw, p, t, fonts, color):
    _glow(draw, CX, CY + 40, 30, _c(RED, 230))
    for r in (80, 140):
        draw.ellipse((CX - r, CY + 40 - r, CX + r, CY + 40 + r), outline=_c(GREY, 130), width=2)
    jump = p > 0.5
    a = t * 2
    r = 140 if jump else 80
    _dot(draw, CX + r * math.cos(a), CY + 40 + r * math.sin(a), 9, YELLOW)
    _label(draw, (CX, 910), "only at exactly the right frequency", fonts, WHITE, "mm")


def cycle_counter(draw, p, t, fonts, color):
    pts = [(80 + 560 * i / 120, 600 + 70 * math.sin(i / 120 * 2 * math.pi * 14 - p * 30)) for i in range(121)]
    draw.line(pts, fill=_c(CYAN, 230), width=4)
    count = int(9192631770 * min(1.0, p * 1.1))
    _label(draw, (CX, 780), f"{count:,}", fonts, YELLOW, "mm")
    _label(draw, (CX, 830), "CYCLES = ONE SECOND", fonts, WHITE, "mm")


def clock_drift(draw, p, t, fonts, color):
    for k, (name, width, col) in enumerate((("QUARTZ WRISTWATCH: ~15 SECONDS A MONTH", 360, ORANGE), ("BEST CESIUM CLOCK: ~1/300,000,000 SECOND A YEAR", 4, GREEN))):
        y = 620 + k * 150
        draw.rectangle((100, y, 620, y + 40), outline=GREY, width=2)
        draw.rectangle((100, y, 100 + max(4, width * min(1.0, p * 1.5)), y + 40), fill=_c(col, 220))
        _label(draw, (CX, y - 28), name, fonts, WHITE, "mm")


def glacier_form(draw, p, t, fonts, color):
    layers = 1 + int(5 * min(1.0, p * 1.2))
    for k in range(layers):
        y = 860 - k * 36 * (1.0 - 0.07 * k)
        h = max(10, 34 - k * 4 * (1.0 if p > 0.5 else 0.2))
        col = _c(WHITE, 230 - k * 14) if k >= layers - 2 else _c(CYAN, 200)
        draw.rectangle((140, y - h, 580, y), fill=col)
    for k in range(10):
        a = (t * 0.4 + k / 10) % 1.0
        _dot(draw, 160 + (k * 71) % 400, 430 + a * 160, 4, _c(WHITE, 230))


def glacier_flow(draw, p, t, fonts, color):
    draw.polygon([(60, 640), (660, 860), (660, 940), (60, 940)], fill=(110, 95, 75, 235))
    shift = 20 * p
    draw.polygon([(80 + shift, 640 - 10), (640 + shift, 850 - 10), (640 + shift, 810), (80 + shift, 610)], fill=_c(CYAN, 190))
    for k in range(5):
        _arrow(draw, 150 + k * 100 + shift, 640 + k * 38, 190 + k * 100 + shift, 655 + k * 38, _c(WHITE, 210), 3)
    _dot(draw, 650, 860, 14 + 6 * p, _c(GREY, 220))


def glacier_share(draw, p, t, fonts, color):
    for k, (name, pct) in enumerate((("OF THE WORLD'S LAND: ABOUT 10%", 10), ("OF FRESH WATER: ABOUT 69%", 69))):
        y = 600 + k * 150
        draw.rectangle((100, y, 620, y + 44), outline=GREY, width=2)
        draw.rectangle((100, y, 100 + 520 * pct / 100 * min(1.0, p * 1.5), y + 44), fill=_c(CYAN, 220))
        _label(draw, (CX, y - 28), name, fonts, WHITE, "mm")


# ---------------------------------------------------------------- 3D layer (pure code, no assets)

def _rot(pt, yaw, tilt):
    """Rotate a 3D point around the vertical axis, then tilt towards the viewer."""
    x, y, z = pt
    x, z = x * math.cos(yaw) + z * math.sin(yaw), -x * math.sin(yaw) + z * math.cos(yaw)
    y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
    return x, y, z


def _proj(pt, cx, cy, r, yaw, tilt):
    """Orthographic projection with mild perspective; returns (x, y, depth)."""
    x, y, z = _rot(pt, yaw, tilt)
    k = 1.0 + 0.12 * z
    return cx + x * r * k, cy - y * r * k, z


def _globe3d(draw, cx, cy, r, yaw, tilt=0.35, color=CYAN, lines=True):
    """Wireframe sphere with depth shading: far side dim, near side bright."""
    _glow(draw, cx, cy, r, _c(BLUE, 120))
    steps = 48
    rings = [("lat", math.radians(a)) for a in range(-60, 61, 30)] + [("lon", math.radians(a)) for a in range(0, 180, 30)]
    for kind, a in rings:
        pts = []
        for i in range(steps + 1):
            u = 2 * math.pi * i / steps
            pt = (math.cos(a) * math.cos(u), math.sin(a), math.cos(a) * math.sin(u)) if kind == "lat" else (math.cos(u) * math.cos(a), math.sin(u), math.cos(u) * math.sin(a))
            pts.append(_proj(pt, cx, cy, r, yaw, tilt))
        for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
            near = (z0 + z1) / 2 > 0
            draw.line((x0, y0, x1, y1), fill=_c(color, 200 if near else 55), width=2 if near else 1)


def _orbit3d(draw, cx, cy, r, yaw, tilt, phase, color=YELLOW, radius=1.7, incl=1.1):
    """Circular orbit around the globe; returns the body's projected (x, y, depth)."""
    prev = None
    for i in range(65):
        u = 2 * math.pi * i / 64
        pt = (radius * math.cos(u), radius * math.sin(u) * math.sin(incl), radius * math.sin(u) * math.cos(incl))
        cur = _proj(pt, cx, cy, r, yaw, tilt)
        if prev:
            draw.line((prev[0], prev[1], cur[0], cur[1]), fill=_c(color, 150 if cur[2] > 0 else 45), width=2)
        prev = cur
    u = phase * 2 * math.pi
    body = _proj((radius * math.cos(u), radius * math.sin(u) * math.sin(incl), radius * math.sin(u) * math.cos(incl)), cx, cy, r, yaw, tilt)
    _dot(draw, body[0], body[1], 9 if body[2] > 0 else 6, _c(color, 255 if body[2] > 0 else 120))
    return body


def _dipole3d(draw, cx, cy, r, yaw, tilt, color=CYAN):
    """Dipole field lines (r = L cos^2 latitude) in 3D around the globe."""
    for lon in range(0, 360, 90):
        for L in (1.8, 2.6):
            pts = []
            for i in range(-80, 81):
                lat = math.radians(i * 0.95)
                rr = L * math.cos(lat) ** 2
                if rr < 1.02:
                    continue
                lo = math.radians(lon)
                pts.append(_proj((rr * math.cos(lat) * math.cos(lo), rr * math.sin(lat), rr * math.cos(lat) * math.sin(lo)), cx, cy, r, yaw, tilt))
            for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
                draw.line((x0, y0, x1, y1), fill=_c(color, 170 if (z0 + z1) > 0 else 50), width=2)


def globe_spin_3d(draw, p, t, fonts, color):
    _globe3d(draw, CX, CY + 10, 190, t * 0.6)


def orbit_3d(draw, p, t, fonts, color):
    _globe3d(draw, CX, CY + 10, 130, t * 0.3, 0.5)
    _orbit3d(draw, CX, CY + 10, 130, t * 0.3, 0.5, (t * 0.15) % 1.0)


def field_lines_3d(draw, p, t, fonts, color):
    _globe3d(draw, CX, CY + 10, 120, t * 0.4)
    _dipole3d(draw, CX, CY + 10, 120, t * 0.4, 0.35)


MOTIFS: dict[str, Callable[..., None]] = {
    name: fn for name, fn in {
        "evaporation": evaporation, "rising_cooling": rising_cooling, "condensation": condensation,
        "moon_phases": moon_phases, "eclipse_shadow": eclipse_shadow,
        "light_absorption": light_absorption, "scattering_compare": scattering_compare, "sediment_colors": sediment_colors,
        "lightning_bolt": lightning_bolt, "heat_halo": heat_halo, "pressure_wave": pressure_wave,
        "star_beam": star_beam, "star_twinkle": star_twinkle, "twinkle_compare": twinkle_compare,
        
        "ear_signal": ear_signal, "noise_gauge": noise_gauge, "hearing_protect": hearing_protect, "heart_pump": heart_pump, "blood_delivery": blood_delivery, "heart_risks": heart_risks,
        "plates_globe": plates_globe, "plates_boundary": plates_boundary, "plates_timelapse": plates_timelapse,
        "globe_bulge": globe_bulge, "gravity_surface": gravity_surface,
        "leaf_pigments": leaf_pigments, "daylight_fade": daylight_fade,
        "orbit_year": orbit_year, "orbit_rotation": orbit_rotation,
        "tidal_pull": tidal_pull, "tide_alignment": tide_alignment, "tide_gauge": tide_gauge,
        "seafloor_quake": seafloor_quake, "tsunami_deep": tsunami_deep, "tsunami_shore": tsunami_shore,
        
        "salt_sources": salt_sources, "salt_share": salt_share, "dense_float": dense_float, "enso_winds": enso_winds, "jet_stream_shift": jet_stream_shift, "upwelling": upwelling, "hurricane_engine": hurricane_engine, "hurricane_spin": hurricane_spin, "hurricane_landfall": hurricane_landfall, "sleep_vitals": sleep_vitals, "sleep_memory": sleep_memory, "sleep_ages": sleep_ages,
        
        "ozone_shield": ozone_shield, "cfc_cycle": cfc_cycle, "ozone_hole_patch": ozone_hole_patch, "flare_burst": flare_burst, "flare_travel": flare_travel, "geodynamo": geodynamo, "magnetosphere": magnetosphere, "pole_flip": pole_flip, "magma_rise": magma_rise, "gas_pressure": gas_pressure, "sweat_cooling": sweat_cooling, "heat_stroke_gauge": heat_stroke_gauge, "ac_relief": ac_relief,
        
        "water_share_bars": water_share_bars, "water_carry": water_carry, "water_balance": water_balance, "aurora_particles": aurora_particles, "aurora_colours": aurora_colours, "aurora_twin": aurora_twin, "fault_stick_slip": fault_stick_slip, "seismograph_trace": seismograph_trace, "atom_jump": atom_jump, "cycle_counter": cycle_counter, "clock_drift": clock_drift, "glacier_form": glacier_form, "glacier_flow": glacier_flow, "glacier_share": glacier_share,
        "globe_spin_3d": globe_spin_3d, "orbit_3d": orbit_3d, "field_lines_3d": field_lines_3d,
        "geyser_eruption": geyser_eruption, "interval_timeline": interval_timeline, "geyser_cutaway": geyser_cutaway,
    }.items()
}


def draw_motif(name: str | None, draw: Any, progress: float, seconds: float, fonts: dict[str, Any], color: tuple = CYAN) -> bool:
    """Draw a named motif; return False when the name is unknown (caller falls back)."""
    fn = MOTIFS.get(str(name or ""))
    if fn is None:
        return False
    fn(draw, max(0.0, min(1.0, progress)), seconds, fonts, color)
    return True


from .visual_motifs_3d import MOTIFS_3D  # noqa: E402  (3D versions replace the flat ones of the same name)
from .visual_motifs_3d_b import MOTIFS_3D_B  # noqa: E402
from .visual_motifs_3d_c import MOTIFS_3D_C  # noqa: E402
from .visual_motifs_3d_d import MOTIFS_3D_D  # noqa: E402
from .visual_motifs_3d_e import MOTIFS_3D_E  # noqa: E402
from .visual_motifs_3d_f import MOTIFS_3D_F  # noqa: E402
from .visual_motifs_3d_g import MOTIFS_3D_G  # noqa: E402

MOTIFS_3D = {**MOTIFS_3D, **MOTIFS_3D_B, **MOTIFS_3D_C, **MOTIFS_3D_D, **MOTIFS_3D_E, **MOTIFS_3D_F, **MOTIFS_3D_G}
MOTIFS.update(MOTIFS_3D)

# Motifs that show the idea as a holographic 3D figure. New topics may use only these.
HOLOGRAPHIC_3D = frozenset(name for name in MOTIFS if name in MOTIFS_3D or name.endswith("_3d"))
