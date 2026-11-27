"""Choose a visual profile and scene motif for a topic (pipeline stage 7, scene planning).

The low-poly diorama suits physical, earth, weather and space mechanics. Health, safety and
abstract topics stay on the holographic profile. The choice is deterministic and recorded in the spec.
"""
from __future__ import annotations

import re
from typing import Any

LOWPOLY = "lowpoly_diorama_v1"
HOLOGRAPHIC = "holographic_science_v1"

# First match wins, and only the TITLE is matched: a diorama must depict the subject itself, because
# visuals explain the narration, they do not decorate it. Anything unclear stays holographic.
_MOTIF_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lp_volcano", ("volcano", "volcanoes", "volcanic", "lava")),
    ("lp_plates", ("tectonic", "continental drift", "plate boundar")),
    ("lp_seasons", ("seasons", "equinox", "solstice")),
    ("lp_water_cycle", ("water cycle", "rain", "evaporation")),
    ("lp_sky_scatter", ("the sky", "sunset", "sunrise")),
)
# Topics where a toy-like diorama would trivialise real harm, or that cannot be shown as a physical scene.
_SENSITIVE = ("health", "disease", "virus", "vaccine", "cancer", "death", "drug", "medicine", "brain", "heart",
              "mental", "infection", "pandemic", "poison", "toxic", "earthquake", "tsunami", "hurricane", "tornado",
              "flood", "war", "nuclear", "radiation", "suicide", "injury")


# The diorama shows Earth (trees, houses, a blue sky), so other worlds would be shown wrongly.
_OFF_EARTH = ("mars", "venus", "mercury", "jupiter", "saturn", "moon", "exoplanet", "titan", "io")


def _has(text: str, words: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}", text) for w in words)


def choose_visual_style(spec: dict[str, Any]) -> tuple[str, str | None]:
    """Return (visual_profile, motif). The motif is None for the holographic profile."""
    title = str(spec.get("title", "")).casefold()
    text = f"{title} {spec.get('narration', '')}".casefold()
    if _has(text, _SENSITIVE) or _has(title, _OFF_EARTH):
        return HOLOGRAPHIC, None
    for motif, words in _MOTIF_RULES:
        if _has(title, words):
            return LOWPOLY, motif
    return HOLOGRAPHIC, None


def apply_visual_style(spec: dict[str, Any]) -> dict[str, Any]:
    """Set the profile on a spec in place; low-poly scenes keep the holographic motif for fallback."""
    profile, motif = choose_visual_style(spec)
    spec["visual_profile"] = profile
    if profile == LOWPOLY:
        for scene in spec.get("scenes", []):
            scene["holographic_motif"] = scene.get("motif", "none")
            scene["motif"] = motif
    return spec
