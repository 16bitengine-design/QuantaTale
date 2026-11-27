import pytest

pytest.importorskip("PIL")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from factflow.toybox import ease_out_back, shade  # noqa: E402
from factflow.toybox_scenes import TOYBOX_MOTIFS, toy_generic  # noqa: E402
from factflow.video_render import _draw_frame, validate_sample_spec  # noqa: E402

SPEC = {
    "title": "Why Is the Sky Blue?", "visual_profile": "toybox_diorama_v1",
    "narration": "Why is the sky blue? Sunlight is made of many colours. Air scatters blue light the most. "
                 "So blue reaches your eyes from every direction of the sky.",
    "sources": [{"publisher": "NASA", "url": "https://science.nasa.gov/"}],
    "scenes": [{"motif": "toy_sky_scatter"}, {"motif": "toy_sky_scatter"}, {"motif": "toy_unknown"}],
}


def _fonts():
    f = ImageFont.load_default()
    return {k: f for k in ("title", "small", "label", "caption", "tiny", "heading")}


def _frame(spec=SPEC, t=3.0):
    return _draw_frame(spec, t, 12.0, "caption", _fonts(), [])


def test_profile_is_accepted_by_validation():
    validate_sample_spec(SPEC)


def test_every_motif_draws_something_and_is_deterministic():
    for name, fn in list(TOYBOX_MOTIFS.items()) + [("generic", toy_generic)]:
        images = []
        for _ in range(2):
            im = Image.new("RGB", (720, 1280), (0, 0, 0))
            fn(ImageDraw.Draw(im, "RGBA"), 0.7, 1.5, 0.6)
            images.append(im)
        assert images[0].tobytes() == images[1].tobytes(), name
        assert images[0].getbbox() is not None, name


def test_frame_uses_light_toybox_background_not_dark_hologram():
    px = _frame().getpixel((20, 300))
    assert sum(px) > 450  # warm light sky, not the navy chamber


def test_frames_animate_and_unknown_motif_falls_back():
    assert _frame(t=1.0).tobytes() != _frame(t=4.0).tobytes()
    spec = dict(SPEC, scenes=[{"motif": "does_not_exist"}] * 3)
    assert _frame(spec).getbbox() is not None


def test_easing_and_shading_bounds():
    assert abs(ease_out_back(0)) < 1e-9 and abs(ease_out_back(1) - 1) < 1e-9
    assert max(ease_out_back(i / 20) for i in range(21)) > 1.0  # overshoot = bounce
    assert all(0 <= c <= 255 for c in shade((250, 250, 250), 1.0))
