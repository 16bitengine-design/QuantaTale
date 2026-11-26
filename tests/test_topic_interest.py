from datetime import datetime, timezone

from factflow.publishing_slots import (
    NoInterestingTopicError, select_immediate_slot, select_next_slot, unused_topic_count)
from factflow.topic_interest import (
    DEFAULT_MIN_INTEREST, clears_interest_bar, lead_is_low_interest, score_spec)
from factflow.topic_library import add_discovery_report, load_library, register_production_spec

GOOD = {
    "title": "Can You Get Sunburnt on a Cloudy Day?",
    "narration": "Can you really get sunburnt on a cloudy day? Yes, up to 80 percent of UV passes through thin cloud, "
                 "and it hits your skin just like sunlight does.",
    "scenes": [{"motif": "uv_filter_3d"}, {"motif": "cloud_3d"}, {"motif": "skin_3d"}],
}
DRY = {
    "title": "Agency Announces Reporting Standard Methodology",
    "narration": "The committee announces a standard protocol for administrative regulation.",
    "scenes": [{}],
}


def _item(path, score=None, prefix="qt-x"):
    item = {"spec_path": path, "content_id_prefix": prefix, "title": path, "publish_timezone": "Africa/Kampala",
            "publishing_enabled": True, "sources": []}
    if score is not None:
        item["interest_score"] = score
    return item


def test_engaging_topic_outscores_dry_topic():
    good, dry = score_spec(GOOD), score_spec(DRY)
    assert good["score"] >= 60 > DEFAULT_MIN_INTEREST > dry["score"]
    assert good["reasons"]


def test_score_is_deterministic_and_bounded():
    assert score_spec(GOOD) == score_spec(GOOD)
    assert 0 <= score_spec({})["score"] <= 100


def test_unscored_legacy_entries_stay_eligible():
    assert clears_interest_bar(_item("a.json"))


def test_register_stores_score_and_reasons():
    library = {"production_specs": [], "discovery_leads": []}
    spec = dict(GOOD, content_id_prefix="qt-sun", publish_timezone="Africa/Kampala")
    register_production_spec(library, "s.json", spec)
    record = library["production_specs"][0]
    assert record["interest_score"] >= DEFAULT_MIN_INTEREST and record["interest_reasons"]


def test_leads_filter_drops_administrative_items():
    assert lead_is_low_interest({"title": "Agency appoints new deputy director"})
    assert lead_is_low_interest({"title": "Webinar schedule announced"})
    assert not lead_is_low_interest({"title": "Scientists find water ice beneath the Moon's surface"})
    library = {"production_specs": [], "discovery_leads": []}
    report = {"candidates": [
        {"title": "Agency appoints new deputy director", "url": "https://a.example/1"},
        {"title": "Scientists find water ice on the Moon", "url": "https://a.example/2"}]}
    result = add_discovery_report(library, report)
    assert result["added"] == 1 and result["skipped_low_interest"] == 1


def test_higher_interest_topic_is_chosen_first():
    library = {"production_specs": [_item("low.json", 45, "qt-low"), _item("high.json", 90, "qt-high")]}
    picked = select_immediate_slot(library, {}, now=datetime(2026, 11, 26, 9, tzinfo=timezone.utc))
    assert picked["spec_path"] == "high.json"


def test_low_interest_topics_are_never_posted():
    library = {"production_specs": [_item("meh.json", 10, "qt-meh")]}
    now = datetime(2026, 11, 26, 8, 30, tzinfo=timezone.utc)  # 11:30 Kampala, noon slot in window
    assert select_next_slot(library, {}, now=now) is None
    try:
        select_immediate_slot(library, {}, now=now)
    except NoInterestingTopicError:
        pass
    else:
        raise AssertionError("expected a deliberate skip")


def test_stock_count_ignores_low_interest_topics():
    library = {"production_specs": [_item("a.json", 80, "qt-a"), _item("b.json", 5, "qt-b")]}
    assert unused_topic_count(library, {}) == 1


def test_existing_library_is_scored_and_mostly_clears_bar():
    library = load_library("production/topic-library.json")
    scored = [i for i in library["production_specs"] if "interest_score" in i]
    assert scored and sum(clears_interest_bar(i) for i in scored) >= len(scored) * 0.8
