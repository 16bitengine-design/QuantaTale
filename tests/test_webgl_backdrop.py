import os

import pytest

from factflow import video_render
from factflow.webgl_render import WebGLBackdrop, WebGLUnavailable


def test_non_lowpoly_profiles_never_start_the_3d_backend():
    assert video_render._open_backdrop({"visual_profile": "holographic_science_v1"}) == (None, None)


def test_falls_back_to_pillow_when_3d_backend_is_unavailable(monkeypatch):
    def boom(self):
        raise WebGLUnavailable("no chromium")
    monkeypatch.setattr(WebGLBackdrop, "__enter__", boom)
    assert video_render._open_backdrop({"visual_profile": "lowpoly_diorama_v1"}) == (None, None)


def test_real_3d_frame_when_chromium_is_present():
    pytest.importorskip("playwright")
    pytest.importorskip("PIL")
    try:
        backdrop = WebGLBackdrop(360, 640).__enter__()
    except WebGLUnavailable as exc:
        if os.environ.get("QUANTATALE_REQUIRE_WEBGL"):  # the 3D CI workflow must not hide a broken backend
            raise
        pytest.skip(f"Chromium not available: {exc}")
    try:
        a = backdrop.frame("lp_seasons", 1.0, 0.2)
        b = backdrop.frame("lp_seasons", 1.0, 0.2)
        c = backdrop.frame("unknown_motif", 2.0, 0.5)  # falls back to the generic village
    finally:
        backdrop.__exit__(None, None, None)
    assert a.size == (360, 640)
    assert a.tobytes() == b.tobytes()  # deterministic
    assert a.getextrema() != ((0, 0),) * 3 and a.tobytes() != c.tobytes()


def test_every_motif_has_a_distinct_3d_scene_when_chromium_is_present():
    pytest.importorskip("playwright")
    pytest.importorskip("PIL")
    try:
        backdrop = WebGLBackdrop(240, 426).__enter__()
    except WebGLUnavailable as exc:
        if os.environ.get("QUANTATALE_REQUIRE_WEBGL"):  # the 3D CI workflow must not hide a broken backend
            raise
        pytest.skip(f"Chromium not available: {exc}")
    try:
        frames = {m: backdrop.frame(m, 3.0, 0.6).tobytes()
                  for m in ("lp_seasons", "lp_sky_scatter", "lp_water_cycle", "lp_volcano", "lp_plates", "generic")}
    finally:
        backdrop.__exit__(None, None, None)
    assert len(set(frames.values())) == len(frames)
