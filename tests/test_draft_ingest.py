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
             "narration": " ".join(["Warm oceans send up vapour."] + ["Air cools high above."] * 12 + ["Clouds then form."] * 6),
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
