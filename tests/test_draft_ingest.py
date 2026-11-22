import json
from pathlib import Path

from factflow.llm_providers import AllProvidersFailed
from factflow.topic_authoring import ingest_drafts


class FakeChain:
    def __init__(self, supported=True, fail=False):
        self.supported, self.fail = supported, fail

    def complete_json(self, *a, **k):
        if self.fail:
            raise AllProvidersFailed({"x": "down"})
        return {"results": [{"i": i, "supported": self.supported} for i in range(5)], "conflicts": []}


def _setup(tmp_path, monkeypatch, narration_ok=True):
    from factflow import topic_authoring as ta

    page = lambda url, group: {"url": url, "title": "t", "group": group, "publisher": group, "publisher_id": group,
                               "paragraphs": ["Water vapour rises from warm oceans and cools into clouds high in the sky today."] * 3}
    monkeypatch.setattr(ta, "fetch_passages", lambda url, reg, f=None, why=None: page(url, "g1" if "a." in url else "g2"))
    draft = {"title": "Why clouds look white from above", "description": "d", "category": "science",
             "source_urls": ["https://a.example/1", "https://b.example/2"],
             "narration": " ".join(["Why do warm oceans send up vapour?"] + ["Air cools high above."] * 12 + ["Clouds then form."] * 6),
             "claims": [], "scenes": [{"visual_description": "x", "motif": "orbit_3d"}] * 3}
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "one.json").write_text(json.dumps(draft))
    return drafts


def test_bad_draft_is_rejected_and_moved(tmp_path, monkeypatch):
    drafts = _setup(tmp_path, monkeypatch)
    report = ingest_drafts(FakeChain(), {"production_specs": []}, {}, tmp_path / "specs", drafts)
    assert report["accepted"] == [] and len(report["rejected"]) == 1
    assert (drafts / "rejected" / "one.json").exists() and not (drafts / "one.json").exists()


def test_draft_stays_when_no_checker_is_reachable(tmp_path, monkeypatch):
    drafts = _setup(tmp_path, monkeypatch)
    draft = json.loads((drafts / "one.json").read_text())
    from factflow import topic_authoring as ta
    monkeypatch.setattr(ta, "check_grounding", lambda *a: [])
    monkeypatch.setattr(ta, "check_originality", lambda *a: [])
    monkeypatch.setattr(ta, "check_source_coverage", lambda *a: [])
    report = ingest_drafts(FakeChain(fail=True), {"production_specs": []}, {}, tmp_path / "specs", drafts)
    assert len(report["deferred"]) == 1 and (drafts / "one.json").exists()


def test_quote_matches_page_text_with_space_before_full_stop():
    from factflow.topic_authoring import check_grounding

    sources = [{"paragraphs": ["Earthquakes are recorded by instruments called seismographs . The recording is a seismogram ."]}]
    claims = [{"sentence": "Seismographs record the shaking.", "quote": "Earthquakes are recorded by instruments called seismographs.", "source": 0}]
    assert check_grounding("Seismographs record the shaking.", claims, sources) == []


def _replace_setup(tmp_path, monkeypatch, replaces="clouds-white"):
    drafts = _setup(tmp_path, monkeypatch)
    from factflow import topic_authoring as ta
    for name in ("check_grounding", "check_originality", "check_source_coverage"):
        monkeypatch.setattr(ta, name, lambda *a: [])
    draft = json.loads((drafts / "one.json").read_text())
    draft.update({"replaces": replaces, "claims": [{"sentence": "x", "quote": "y", "source": 0}]})
    (drafts / "one.json").write_text(json.dumps(draft))
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "clouds-white.json").write_text(json.dumps({"title": "old"}))
    library = {"production_specs": [{"spec_path": (specs / "clouds-white.json").as_posix(), "content_id_prefix": "qt-clouds-white",
                                     "title": "Why clouds look white from above | QuantaTale"}]}
    return drafts, specs, library


def test_replaces_rewrites_an_unscheduled_topic_in_place(tmp_path, monkeypatch):
    drafts, specs, library = _replace_setup(tmp_path, monkeypatch)
    report = ingest_drafts(FakeChain(), library, {}, specs, drafts)
    assert len(report["accepted"]) == 1 and not (drafts / "one.json").exists()
    spec = json.loads((specs / "clouds-white.json").read_text())
    assert spec["content_id_prefix"] == "qt-clouds-white" and spec["narration"].startswith("Why do warm oceans")
    assert len(library["production_specs"]) == 1 and not list(specs.glob("*-2.json"))


def test_replaces_refuses_scheduled_or_unknown_topics(tmp_path, monkeypatch):
    drafts, specs, library = _replace_setup(tmp_path, monkeypatch)
    locked = {library["production_specs"][0]["spec_path"]}
    report = ingest_drafts(FakeChain(), library, {}, specs, drafts, locked_specs=locked)
    assert report["accepted"] == [] and "already scheduled" in report["rejected"][0]["reason"]
    assert json.loads((specs / "clouds-white.json").read_text()) == {"title": "old"}
    drafts2, specs2, library2 = _replace_setup((tmp_path / "b").mkdir() or tmp_path / "b", monkeypatch, replaces="nope")
    report2 = ingest_drafts(FakeChain(), library2, {}, specs2, drafts2)
    assert "unknown topic" in report2["rejected"][0]["reason"]
