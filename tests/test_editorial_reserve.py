import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_editorial_reserve_specs_are_owner_approved_but_require_source_verification():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    reserve = [item for item in library["production_specs"] if item["spec_path"].startswith("production/specs/") and item.get("editorial_approval_basis") == "explicit_project_owner_batch_approval"]
    assert len(reserve) == 14
    for record in reserve:
        if not record["source_passage_verification_required_before_publication"]:
            continue  # passage-checked topics are covered by the test below
        spec = json.loads((ROOT / record["spec_path"]).read_text(encoding="utf-8"))
        assert spec["editorial_approved"] is True
        assert record["editorial_approved"] is True
        assert record["status"] == "approved_ready"
        assert spec["source_passage_verification_required_before_publication"] is True
        assert len(spec["sources"]) >= 2
        assert all(source["url"].startswith("https://") for source in spec["sources"])
        assert all(source["review_status"] == "source_lead_requires_human_passage_check" for source in spec["sources"])

def test_editorial_reserve_has_unique_content_ids_and_spec_paths():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    reserve = [item for item in library["production_specs"] if item["spec_path"].startswith("production/specs/")]
    assert len({item["spec_path"] for item in reserve}) == len(reserve)
    assert len({item["content_id_prefix"] for item in reserve}) == len(reserve)


def test_new_sunset_spec_is_registered_after_source_passage_assessment():
    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    record = next(item for item in library["production_specs"] if item["spec_path"] == "production/specs/sunset-red.json")
    spec = json.loads((ROOT / record["spec_path"]).read_text(encoding="utf-8"))
    assert record["status"] == "approved_ready"
    assert record["source_passage_verification_required_before_publication"] is False
    assert spec["visual_profile"] == "sunset_red_v1"
    assert spec["source_passage_verification_required_before_publication"] is False
    assert len(spec["sources"]) == 2
    assert all(source["review_status"] == "passage_checked_supports_claim" for source in spec["sources"])


def test_today_noon_and_evening_slots_select_distinct_eligible_topics():
    from datetime import datetime, timezone
    from factflow.publishing_slots import is_publishable_spec, select_next_slot

    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    ledger = {}
    noon = select_next_slot(
        library, ledger, now=datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc)
    )
    from factflow.topic_interest import interest_of
    eligible = [i for i in library["production_specs"] if is_publishable_spec(i)]
    best = max(interest_of(i) for i in eligible)
    chosen = next(i for i in eligible if i["spec_path"] == noon["spec_path"])
    assert interest_of(chosen) == best  # the most interesting never-used topic goes first
    ledger[noon["content_id"]] = {"spec": noon["spec_path"], "due_at": noon["due_at"]}
    evening = select_next_slot(
        library, ledger, now=datetime(2026, 11, 16, 14, 30, tzinfo=timezone.utc)
    )
    assert evening["spec_path"] != noon["spec_path"]
    assert evening["content_id"] != noon["content_id"]


CHECKED = ["moon-phases", "ocean-blue", "lightning-hot-air", "clouds-form", "stars-twinkle",
    "tectonic-plates", "leaves-colour", "earth-shape", "mercury-day", "old-faithful"]
STILL_BLOCKED = ["venus-day", "aurora-lights", "sound-space", "olympus-mons"]


def test_passage_checked_reserve_topics_are_publishable_with_review_provenance():
    from factflow.publishing_slots import is_publishable_spec

    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    for slug in CHECKED:
        path = f"production/specs/{slug}.json"
        record = next(i for i in library["production_specs"] if i["spec_path"] == path)
        spec = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert record["source_passage_verification_required_before_publication"] is False
        assert spec["source_passage_verification_required_before_publication"] is False
        assert len(spec["sources"]) >= 2
        assert all(s["review_status"] == "passage_checked_supports_claim" and s["reviewed_at"] for s in spec["sources"])
        assert is_publishable_spec({**record, "sources": spec["sources"]})


def test_failed_source_checks_keep_topics_blocked():
    from factflow.publishing_slots import is_publishable_spec

    library = json.loads((ROOT / "production/topic-library.json").read_text(encoding="utf-8"))
    for slug in STILL_BLOCKED:
        record = next(i for i in library["production_specs"] if i["spec_path"] == f"production/specs/{slug}.json")
        assert not is_publishable_spec(record)
