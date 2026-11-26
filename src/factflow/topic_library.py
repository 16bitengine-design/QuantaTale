"""Persistent topic library for discovery leads and production specs."""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from factflow.publishing_slots import is_publishable_spec
from factflow.topic_interest import lead_is_low_interest, score_spec

DEFAULT_LIBRARY = Path("production/topic-library.json")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _normalise_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return value.strip()
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))

def _normalise_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

def load_library(path: str | Path = DEFAULT_LIBRARY) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"schema_version": 1, "updated_at": _now(), "production_specs": [], "discovery_leads": []}
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported or malformed topic library.")
    for key in ("production_specs", "discovery_leads"):
        if not isinstance(data.get(key), list):
            raise ValueError(f"Topic library field {key} must be a list.")
    return data

def save_library(library: dict[str, Any], path: str | Path = DEFAULT_LIBRARY) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    library["updated_at"] = _now()
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(library, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)

def register_production_spec(library: dict[str, Any], spec_path: str, spec: dict[str, Any]) -> bool:
    """Register a production spec, enabled by default unless explicitly disabled."""
    content_id = str(spec.get("content_id_prefix", "")).strip()
    title = str(spec.get("post_title") or spec.get("title") or "").strip()
    if not content_id or not title:
        raise ValueError("Production spec needs content_id_prefix and a title.")
    enabled = spec.get("publishing_enabled") is not False
    existing = next((item for item in library["production_specs"] if item.get("spec_path") == spec_path), None)
    record = {
        "spec_path": spec_path, "content_id_prefix": content_id, "title": title,
        "publish_time_local": spec.get("publish_time_local"),
        "publish_timezone": spec.get("publish_timezone"),
        "publishing_enabled": enabled,
        "status": "eligible_ready" if enabled else "disabled",
        "editorial_approved": spec.get("editorial_approved") is True,
        "editorial_approval_basis": "explicit_project_owner_approval" if spec.get("editorial_approved") is True else "automatic_topic_eligibility_policy",
        "registered_at": existing.get("registered_at", _now()) if existing else _now(),
        "source_passage_verification_required_before_publication": spec.get("source_passage_verification_required_before_publication") is True,
        "sources": [{"publisher": source.get("publisher"), "url": source.get("url"), "review_status": source.get("review_status")}
            for source in spec.get("sources", []) if isinstance(source, dict)],
    }
    interest = score_spec(spec)
    record["interest_score"] = interest["score"]
    record["interest_reasons"] = interest["reasons"]
    if existing:
        existing.update(record)
        return False
    library["production_specs"].append(record)
    return True

def add_discovery_report(library: dict[str, Any], report: dict[str, Any]) -> dict[str, int]:
    """Add RSS leads as research inputs with URL/title duplicate detection."""
    candidates = report.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("Discovery report candidates must be a list.")
    known_urls = {_normalise_url(str(item.get("url", ""))) for item in library["discovery_leads"]}
    known_titles = {_normalise_title(str(item.get("title", ""))) for item in library["discovery_leads"]}
    added = duplicates = skipped = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if lead_is_low_interest(candidate):
            skipped += 1
            continue
        title, url = str(candidate.get("title", "")).strip(), str(candidate.get("url", "")).strip()
        if not title or not url:
            continue
        normalized_url, normalized_title = _normalise_url(url), _normalise_title(title)
        if normalized_url in known_urls or normalized_title in known_titles:
            duplicates += 1
            continue
        library["discovery_leads"].append({
            "lead_id": f"lead-{len(library['discovery_leads']) + 1:06d}",
            "title": title, "url": url, "publisher_id": candidate.get("publisher_id"),
            "published": candidate.get("published"), "description": candidate.get("description", ""),
            "discovered_at": _now(), "status": "candidate_unreviewed",
            "editorial_review_required": False,
        })
        known_urls.add(normalized_url)
        known_titles.add(normalized_title)
        added += 1
    result = {"added": added, "duplicates": duplicates, "total_leads": len(library["discovery_leads"])}
    if skipped:
        result["skipped_low_interest"] = skipped
    return result

def library_summary(library: dict[str, Any]) -> dict[str, int]:
    specs = library["production_specs"]
    enabled = [item for item in specs if item.get("publishing_enabled") is not False]
    eligible = [item for item in specs if is_publishable_spec(item)]
    return {
        "production_specs": len(specs), "approved_ready": len(enabled),
        "eligible_for_publishing": len(eligible), "blocked_by_evidence": len(enabled) - len(eligible),
        "awaiting_editorial_review": 0, "discovery_leads": len(library["discovery_leads"]),
        "unreviewed_leads": sum(item.get("status") == "candidate_unreviewed" for item in library["discovery_leads"]),
    }
