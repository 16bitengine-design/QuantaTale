from factflow.visual_style import HOLOGRAPHIC, LOWPOLY, apply_visual_style, choose_visual_style


def _spec(title, narration="", n=3):
    return {"title": title, "narration": narration,
            "scenes": [{"motif": "uv_filter_3d", "visual_description": "x"} for _ in range(n)]}


def test_physical_earth_topics_get_the_low_poly_style_with_the_right_scene():
    cases = {
        "Why Earth Has Seasons": "lp_seasons",
        "How Volcanoes Erupt": "lp_volcano",
        "How Plate Tectonics Build Mountains": "lp_plates",
        "How Rain Forms": "lp_water_cycle",
        "Why the Sky Is Blue": "lp_sky_scatter",
    }
    for title, motif in cases.items():
        spec = _spec(title, title)
        assert choose_visual_style(spec) == (LOWPOLY, motif), title


def test_loose_matches_do_not_get_a_diorama_that_does_not_depict_them():
    for title in ("Stars Don't Really Twinkle", "The Moon's Phases Aren't Earth's Shadow",
                  "What Makes the Northern Lights Glow", "A Day on Mercury Lasts Two Mercury Years",
                  "Old Faithful Doesn't Erupt Like Clockwork", "Mars Has the Solar System's Largest Volcano", "Autumn Leaves Reveal Hidden Colours"):
        assert choose_visual_style(_spec(title, "sunlight atmosphere cloud season"))[0] == HOLOGRAPHIC, title


def test_sensitive_or_abstract_topics_stay_holographic():
    for title in ("How Vaccines Train Your Immune System", "Why Tsunamis Are So Dangerous",
                  "How a Black Hole Bends Time", "What Is Entropy"):
        assert choose_visual_style(_spec(title))[0] == HOLOGRAPHIC, title


def test_sensitive_words_win_over_physical_ones():
    assert choose_visual_style(_spec("Why Volcanic Ash Harms Your Health"))[0] == HOLOGRAPHIC


def test_apply_keeps_holographic_motif_for_fallback_and_sets_profile():
    spec = apply_visual_style(_spec("Why Earth Has Seasons"))
    assert spec["visual_profile"] == LOWPOLY
    assert all(s["motif"] == "lp_seasons" and s["holographic_motif"] == "uv_filter_3d" for s in spec["scenes"])
    holo = apply_visual_style(_spec("What Is Entropy"))
    assert holo["visual_profile"] == HOLOGRAPHIC and holo["scenes"][0]["motif"] == "uv_filter_3d"
