import json

from factflow.llm_providers import ProviderChain
from factflow.research import load_source_registry
from factflow.topic_authoring import (author_topics, check_grounding, check_originality, check_shape, check_duplicate_subject, check_source_coverage, hard_to_follow, lone_number_sentences,
                                      slugify)

P1 = ["Clouds form when water vapor in rising air cools and condenses onto tiny particles in the sky.",
      "These tiny particles are called cloud condensation nuclei and include dust and sea salt grains."]
P2 = ["Air that rises expands and cools until it becomes saturated with 100 percent relative humidity.",
      "A cloud is a large collection of water droplets or ice crystals that float in the atmosphere."]


def _page(paragraphs):
    return "<html><title>T</title><main>" + "".join(f"<p>{p}</p>" for p in paragraphs) + "</main></html>"


def fetcher(url, publisher):
    return {"final_url": url, "html": _page(P1 if "nasa" in url else P2), "content_type": "text/html"}


NARRATION = ("Why do clouds exist at all? Rising air cools and its invisible vapour starts turning into liquid. "
             "That change needs microscopic specks such as dust or salt to gather on. "
             "When the air is fully saturated at 100 percent humidity, but not before, droplets build up around the specks. "
             "A cloud is really a crowd of tiny drops or ice crystals floating in the atmosphere.")
CLAIMS = [
    {"sentence": "Rising air cools and its invisible vapour starts turning into liquid.",
     "quote": "water vapor in rising air cools and condenses onto tiny particles", "source": 0},
    {"sentence": "That change needs microscopic specks such as dust or salt to gather on.",
     "quote": "include dust and sea salt grains", "source": 0},
    {"sentence": "When the air is fully saturated at 100 percent humidity, but not before, droplets build up around the specks.",
     "quote": "saturated with 100 percent relative humidity", "source": 1},
    {"sentence": "A cloud is really a crowd of tiny drops or ice crystals floating in the atmosphere.",
     "quote": "collection of water droplets or ice crystals that float in the atmosphere", "source": 1},
]
DRAFT = {"title": "Why Clouds Need Dust to Exist", "narration": NARRATION, "description": "A cloud starts with a speck.",
         "category": "weather", "claims": CLAIMS,
         "scenes": [{"narration_segment": "a", "visual_description": "vapour rises", "visual_style": "hybrid", "motif": "orbit_3d"}] * 3}
PROPOSAL = {"topics": [{"question": "How do clouds form?", "category": "weather",
                        "source_urls": ["https://science.nasa.gov/x", "https://www.noaa.gov/y"]}]}
OK = {"results": [{"i": i, "supported": True} for i in range(4)], "conflicts": []}


class FakeChain(ProviderChain):
    def __init__(self, replies):
        super().__init__([])
        self.replies = list(replies)

    def complete_json(self, system, user, **kw):
        self.usage["fake"] = self.usage.get("fake", 0) + 1
        return self.replies.pop(0)


def _run(tmp_path, draft=DRAFT, entail=OK, proposal=PROPOSAL, fetch=fetcher):
    lib = {"production_specs": [], "discovery_leads": []}
    report = author_topics(FakeChain([proposal, draft, entail]), lib, load_source_registry(), tmp_path / "specs",
                           count=1, fetcher=fetch, today="2026-11-18")
    return lib, report


def test_accepts_topic_and_writes_spec_with_title_description_and_sources(tmp_path):
    lib, report = _run(tmp_path)
    assert len(report["accepted"]) == 1, report
    spec = json.loads((tmp_path / "specs" / "clouds-need-dust.json").read_text())
    assert spec["post_title"] == "Why Clouds Need Dust to Exist | QuantaTale"
    assert spec["post_description"].startswith("A cloud starts with a speck.") and "https://" in spec["post_description"]
    assert spec["source_passage_verification_required_before_publication"] is False
    assert len(spec["sources"]) == 2 and all(s["supports"] for s in spec["sources"])
    assert lib["production_specs"][0]["content_id_prefix"] == spec["content_id_prefix"]


def test_rejects_when_only_one_publisher_loads(tmp_path):
    def one(url, publisher):
        if "noaa" in url:
            raise OSError("down")
        return fetcher(url, publisher)
    lib, report = _run(tmp_path, fetch=one)
    assert not report["accepted"] and "independent" in report["rejected"][0]["reason"] and not lib["production_specs"]


def test_rejects_quote_not_in_source():
    bad = [dict(CLAIMS[0], quote="clouds are made of cotton candy")] + CLAIMS[1:]
    srcs = [{"paragraphs": P1}, {"paragraphs": P2}]
    assert any("not found verbatim" in p for p in check_grounding(NARRATION, bad, srcs))


def test_rejects_number_not_in_quote():
    srcs = [{"paragraphs": P1}, {"paragraphs": P2}]
    changed = NARRATION.replace("100 percent", "90 percent")
    claims = [dict(c, sentence=c["sentence"].replace("100 percent", "90 percent")) for c in CLAIMS]
    assert any("number" in p for p in check_grounding(changed, claims, srcs))


def test_uncited_sentence_rejected_but_one_opening_question_allowed():
    srcs = [{"paragraphs": P1}, {"paragraphs": P2}]
    assert check_grounding(NARRATION, CLAIMS, srcs) == []
    assert check_grounding(NARRATION + " Extra claim here.", CLAIMS, srcs)


def test_copied_text_is_rejected():
    copied = "Clouds form when water vapor in rising air cools and condenses onto tiny particles in the sky."
    assert check_originality(copied, [{"paragraphs": P1}])
    assert not check_originality(NARRATION, [{"paragraphs": P1}, {"paragraphs": P2}])


def test_entailment_failure_blocks_topic(tmp_path):
    lib, report = _run(tmp_path, entail={"results": [{"i": 0, "supported": False}], "conflicts": []})
    assert not report["accepted"] and "not supported" in report["rejected"][0]["reason"]


def test_reported_conflict_blocks_topic(tmp_path):
    lib, report = _run(tmp_path, entail={**OK, "conflicts": ["sources disagree on 100 percent"]})
    assert not report["accepted"] and "conflict" in report["rejected"][0]["reason"]


def test_shape_requires_title_description_length_and_unique_title():
    assert check_shape(DRAFT, set()) == []
    assert check_shape({**DRAFT, "title": "Short"}, set())
    assert check_shape({**DRAFT, "description": " "}, set())
    assert check_shape({**DRAFT, "narration": "Too short."}, set())
    assert check_shape(DRAFT, {"why clouds need dust to exist"})


def test_slugify_is_short_and_safe():
    assert slugify("Why Clouds Need Dust to Exist") == "clouds-need-dust"


def test_seeded_proposals_only_keep_listed_urls_and_seed_file_loads(tmp_path):
    from factflow.topic_authoring import load_seeds

    seeds = [{"url": "https://science.nasa.gov/x", "group": "NASA"}, {"url": "https://www.noaa.gov/y", "group": "NOAA"}]
    proposal = {"topics": [{"question": "How do clouds form?", "category": "weather",
                            "source_urls": ["https://science.nasa.gov/x", "https://invented.example/z", "https://www.noaa.gov/y"]}]}
    lib = {"production_specs": [], "discovery_leads": []}
    chain = FakeChain([proposal, DRAFT, OK])
    seen = {}
    original = chain.complete_json

    def spy(system, user, **kw):
        seen.setdefault("first", (system, user))
        return original(system, user, **kw)

    chain.complete_json = spy
    report = author_topics(chain, lib, load_source_registry(), tmp_path / "specs", count=1, fetcher=fetcher,
                           today="2026-11-18", seeds=seeds)
    assert len(report["accepted"]) == 1, report
    assert "Allowed pages" in seen["first"][1] and "invented.example" not in seen["first"][1]
    assert report["accepted"][0]["spec_path"].endswith(".json")
    assert load_seeds(tmp_path / "missing.json") == []
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"pages": seeds}))
    assert load_seeds(path) == seeds


def test_seeds_already_used_by_a_topic_are_not_offered_again(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "old.json").write_text(json.dumps({"sources": [{"url": "https://science.nasa.gov/x"}]}))
    seeds = [{"url": "https://science.nasa.gov/x", "group": "NASA"}, {"url": "https://www.noaa.gov/y", "group": "NOAA"}]
    lib = {"production_specs": [], "discovery_leads": []}
    chain = FakeChain([])  # must not be called: only one group is left
    report = author_topics(chain, lib, load_source_registry(), specs, count=1, fetcher=fetcher, today="2026-11-18", seeds=seeds)
    assert report["accepted"] == [] and "no unused verified pages" in report["note"]


def test_flat_or_missing_motifs_are_rejected_and_prompt_lists_only_3d(monkeypatch):
    from factflow.topic_authoring import WRITE_SYSTEM  # the writer's instructions
    from factflow.visual_motifs import HOLOGRAPHIC_3D, MOTIFS

    flat = "flat_demo"  # every shipped motif is 3D now, so register a flat one for this check
    monkeypatch.setitem(MOTIFS, flat, lambda *args: None)
    assert flat not in HOLOGRAPHIC_3D
    draft = dict(DRAFT)
    draft["scenes"] = [{"visual_description": "x", "motif": flat}, {"visual_description": "y", "motif": "none"},
                       {"visual_description": "z", "motif": "request: a 3D cutaway of a cell"}]
    problems = [p for p in check_shape(draft, set()) if "3D holographic motif" in p]
    assert len(problems) == 3
    assert flat not in WRITE_SYSTEM and "orbit_3d" in WRITE_SYSTEM and "request:" in WRITE_SYSTEM
    ok = dict(DRAFT)
    ok["scenes"] = [{"visual_description": "x", "motif": "heart_pump"}] * 3
    assert not [p for p in check_shape(ok, set()) if "motif" in p]


def test_lone_number_sentences_flag_numbers_not_used_to_compare():
    text = ("Sound travels about 343 meters per second in air. Light is far faster than sound, so lightning is seen before thunder. "
            "In 2019 a telescope captured the first image. Roughly 3.5 percent of seawater is salt. The first 10 cm took 90 years, "
            "but the next 10 cm took 30 years. Two forces act on the Moon.")
    flagged = lone_number_sentences(text)
    assert flagged == ["Sound travels about 343 meters per second in air.", "Roughly 3.5 percent of seawater is salt."]


def test_shape_rejects_a_lone_number_sentence():
    draft = {**DRAFT, "narration": NARRATION.replace(", but not before,", "")}
    assert any("without comparing situations" in p for p in check_shape(draft, set()))
    assert not any("without comparing situations" in p for p in check_shape(DRAFT, set()))


def test_hard_to_follow_flags_long_sentences_and_jargon_but_not_hyphenated_compounds():
    long_sentence = " ".join(["word"] * 30) + "."
    text = f"Light is an electromagnetic wave. A sunrise-to-sunrise day is easy. {long_sentence} Short and clear."
    notes = hard_to_follow(text)
    assert len(notes) == 2
    assert "electromagnetic" in notes[0] and notes[1].startswith("30 words")


def test_shape_asks_for_plainer_language():
    draft = {**DRAFT, "narration": NARRATION + " The electromagnetic spectrum is wide."}
    assert any("general audience" in p for p in check_shape(draft, set()))
    assert not any("general audience" in p for p in check_shape(DRAFT, set()))


def test_duplicate_subject_is_rejected_even_when_worded_differently():
    existing = {"how your eyes turn light into sight"}
    assert check_duplicate_subject("How Your Eye Turns Light into Pictures", existing)
    assert not check_duplicate_subject("How Vaccines Train Your Immune System", existing)


def test_quotes_must_come_from_two_independent_groups():
    sources = [{"group": "NIH", "paragraphs": []}, {"group": "NASA", "paragraphs": []}]
    one_group = [{"source": 0, "quote": "a"}, {"source": 0, "quote": "b"}]
    two_groups = [{"source": 0, "quote": "a"}, {"source": 1, "quote": "b"}]
    assert check_source_coverage(one_group, sources)
    assert check_source_coverage(two_groups, sources) == []
