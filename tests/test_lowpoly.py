import pytest

pytest.importorskip("PIL")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from factflow.lowpoly import ease_out_back, shade  # noqa: E402
from factflow.lowpoly_scenes import LOWPOLY_MOTIFS, lp_generic  # noqa: E402
from factflow.video_render import _draw_frame, validate_sample_spec  # noqa: E402

SPEC = {
    "title": "Why Is the Sky Blue?", "visual_profile": "lowpoly_diorama_v1",
    "narration": "Why is the sky blue? Sunlight is made of many colours. Air scatters blue light the most. "
                 "So blue reaches your eyes from every direction of the sky.",
    "sources": [{"publisher": "NASA", "url": "https://science.nasa.gov/"}],
    "scenes": [{"motif": "lp_sky_scatter"}, {"motif": "lp_sky_scatter"}, {"motif": "lp_unknown"}],
}


def _fonts():
    f = ImageFont.load_default()
    return {k: f for k in ("title", "small", "label", "caption", "tiny", "heading")}


def _frame(spec=SPEC, t=3.0):
    return _draw_frame(spec, t, 12.0, "caption", _fonts(), [])


def test_profile_is_accepted_by_validation():
    validate_sample_spec(SPEC)


def test_every_motif_draws_something_and_is_deterministic():
    for name, fn in list(LOWPOLY_MOTIFS.items()) + [("generic", lp_generic)]:
        images = []
        for _ in range(2):
            im = Image.new("RGB", (720, 1280), (0, 0, 0))
            fn(ImageDraw.Draw(im, "RGBA"), 0.7, 1.5, 0.6)
            images.append(im)
        assert images[0].tobytes() == images[1].tobytes(), name
        assert images[0].getbbox() is not None, name


def test_frame_uses_muted_dark_palette_not_pastel():
    frame = _frame()
    assert sum(frame.getpixel((20, 300))) < 330  # twilight sky, not a bright pastel one
    assert sum(frame.getpixel((20, 700))) > sum(frame.getpixel((20, 250)))  # gradient brightens toward the horizon


def test_frames_animate_and_unknown_motif_falls_back():
    assert _frame(t=1.0).tobytes() != _frame(t=4.0).tobytes()
    spec = dict(SPEC, scenes=[{"motif": "does_not_exist"}] * 3)
    assert _frame(spec).getbbox() is not None


def test_easing_and_shading_bounds():
    assert abs(ease_out_back(0)) < 1e-9 and abs(ease_out_back(1) - 1) < 1e-9
    assert max(ease_out_back(i / 20) for i in range(21)) > 1.0  # overshoot = bounce
    assert all(0 <= c <= 255 for c in shade((250, 250, 250), 1.0))


def test_lowpoly_frames_carry_little_text_and_short_captions():
    from factflow.video_render import _caption_segments

    long = "In the Northern Hemisphere, winter arrives while Earth is nearest the Sun, and summer arrives when it is farthest."
    chunks = [t for _, _, t in _caption_segments(long, 20.0, None, max_words=5, max_chars=30)]
    assert all(len(c.split()) <= 5 and len(c) <= 30 for c in chunks)
    early, late = _frame(t=1.0), _frame(t=9.0)
    # the title fades away after the first seconds, so the top band differs
    assert early.crop((0, 80, 720, 150)).tobytes() != late.crop((0, 80, 720, 150)).tobytes()


def test_cue_follows_the_spoken_sentence():
    from factflow.video_render import _cue_at

    spec = {"cues": ["a", "b", "c"]}
    spans = [(0.0, 2.0), (2.5, 4.0), (4.5, 6.0)]
    name, progress = _cue_at(spec, spans, 1.0, 7.0)
    assert name == "a" and abs(progress - 0.4) < 1e-9  # sentence a runs until the next one starts at 2.5
    assert _cue_at(spec, spans, 5.0, 7.0)[0] == "c"
    assert _cue_at({}, spans, 1.0, 7.0) == (None, 0.0)
    assert _cue_at({"cues": ["a"]}, spans, 1.0, 7.0) == (None, 0.0)  # mismatched cue list is ignored safely
