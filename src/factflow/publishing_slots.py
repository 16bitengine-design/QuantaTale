"""Select distinct topics for QuantaTale's daily publishing slots."""
from __future__ import annotations
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

from factflow.topic_interest import DEFAULT_MIN_INTEREST, clears_interest_bar, interest_of

DEFAULT_PUBLISH_SLOTS = ("12:00", "18:00")
# A slot becomes selectable up to 2.5 hours ahead so delayed or dropped GitHub
# cron events still land inside the window, and stays selectable until 15
# minutes before it is due so rendering and upload fit before Buffer's
# five-minute minimum scheduling lead.
DEFAULT_MIN_LEAD = timedelta(minutes=15)
DEFAULT_MAX_LEAD = timedelta(minutes=150)

class NoInterestingTopicError(ValueError):
    """Evidence-eligible topics exist but none clears the public-interest bar.

    Callers treat this as a deliberate skipped slot, not a failure.
    """


def is_publishable_spec(item: dict[str, Any]) -> bool:
    """Check default topic enablement and retain independent evidence safeguards."""
    if item.get("publishing_enabled") is False:
        return False
    if item.get("source_passage_verification_required_before_publication") is True:
        return False
    sources = item.get("sources", [])
    if not isinstance(sources, list):
        return False
    return not any(
        isinstance(source, dict)
        and str(source.get("review_status", "")).startswith("source_lead_requires_human")
        for source in sources
    )


def _ever_used_specs(ledger: dict[str, Any]) -> set[str]:
    """Specs that already have a reservation or post. A topic is never reused.

    Only entries explicitly cancelled before any public post (status starting
    with "cancelled") free a topic again.
    """
    used: set[str] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("spec"):
            continue
        if str(entry.get("status", "")).startswith("cancelled"):
            continue
        used.add(str(entry["spec"]))
    return used


def unused_topic_count(library: dict[str, Any], ledger: dict[str, Any],
                       min_interest: int = DEFAULT_MIN_INTEREST) -> int:
    """Number of publishable, interesting topics that have never been used."""
    used = _ever_used_specs(ledger)
    return sum(1 for item in library.get("production_specs", [])
               if isinstance(item, dict) and is_publishable_spec(item)
               and clears_interest_bar(item, min_interest) and str(item.get("spec_path", "")) not in used)


def _last_used_by_spec(ledger: dict[str, Any]) -> dict[str, datetime]:
    """Return the most recent recorded use of each spec, normalized to UTC."""
    last_used: dict[str, datetime] = {}
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("spec") or not entry.get("due_at"):
            continue
        try:
            due = _parse_datetime(entry["due_at"]).astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue
        spec_path = str(entry["spec"])
        if spec_path not in last_used or due > last_used[spec_path]:
            last_used[spec_path] = due
    return last_used


def _least_recently_used(candidates: list[dict[str, Any]], ledger: dict[str, Any]) -> dict[str, Any]:
    """Choose the most interesting spec; ties go to the least recently used."""
    last_used = _last_used_by_spec(ledger)
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(
        candidates,
        key=lambda item: (
            -interest_of(item),
            last_used.get(str(item.get("spec_path", "")), oldest),
            str(item.get("spec_path", "")),
        ),
    )[0]


def select_immediate_slot(library: dict[str, Any], ledger: dict[str, Any], *,
    now: datetime | None = None, lead_time: timedelta = timedelta(minutes=20),
    min_interest: int = DEFAULT_MIN_INTEREST
) -> dict[str, str]:
    """Select an unused evidence-eligible topic for an operator-triggered ASAP post.

    The lead time gives rendering and upload enough room before Buffer's
    five-minute minimum scheduling boundary. Normal noon/evening slots are
    unchanged; this path is only used by an explicit manual dispatch input.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if lead_time < timedelta(minutes=10):
        raise ValueError("lead_time must be at least ten minutes")
    eligible = [item for item in library.get("production_specs", [])
        if isinstance(item, dict) and is_publishable_spec(item)]
    if not eligible:
        raise ValueError("No enabled production specs clear the evidence safety gates.")
    used_today: set[str] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("spec") or not entry.get("due_at"):
            continue
        try:
            due = _parse_datetime(entry["due_at"])
        except (TypeError, ValueError):
            continue
        zone_name = entry.get("publish_timezone")
        if zone_name:
            local_date = due.astimezone(ZoneInfo(zone_name)).date()
        else:
            local_date = due.date()
        if local_date == current.astimezone(ZoneInfo("Africa/Kampala")).date():
            used_today.add(str(entry["spec"]))
    ever_used = _ever_used_specs(ledger)
    candidates = [item for item in eligible if str(item.get("spec_path", "")) not in used_today
        and str(item.get("spec_path", "")) not in ever_used]
    if not candidates:
        raise ValueError("No never-used eligible topic remains; topics are never repeated. Add and verify new topics.")
    interesting = [item for item in candidates if clears_interest_bar(item, min_interest)]
    if not interesting:
        raise NoInterestingTopicError("No unused topic clears the public-interest bar; skipping instead of posting low-appeal content.")
    candidates = interesting
    spec = _least_recently_used(candidates, ledger)
    zone_name = str(spec.get("publish_timezone") or "Africa/Kampala")
    zone = ZoneInfo(zone_name)
    due_local = (current.astimezone(timezone.utc) + lead_time).astimezone(zone)
    prefix = str(spec.get("content_id_prefix", "")).strip()
    if not prefix:
        raise ValueError(f"Eligible spec {spec.get('spec_path')} has no content_id_prefix.")
    return {
        "spec_path": str(spec["spec_path"]),
        "content_id": f"{prefix}-{due_local:%Y%m%d}-{due_local:%H%M}",
        "due_at": due_local.isoformat(timespec="seconds"),
        "post_title": str(spec.get("post_title") or spec.get("title") or ""),
        "post_description": str(spec.get("post_description") or ""),
        "publish_timezone": zone.key,
        "slot_local": due_local.strftime("%Y-%m-%d %H:%M"),
    }

def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Datetime must include a timezone: {value!r}")
    return parsed

def select_next_slot(library: dict[str, Any], ledger: dict[str, Any], *,
    now: datetime | None = None, slot_times: tuple[str, ...] = DEFAULT_PUBLISH_SLOTS,
    min_lead: timedelta = DEFAULT_MIN_LEAD, max_lead: timedelta = DEFAULT_MAX_LEAD,
    min_interest: int = DEFAULT_MIN_INTEREST
) -> dict[str, str] | None:
    """Return the next imminent slot and an unused enabled spec, or None.

    Specs are enabled by default unless explicitly disabled. Evidence checks
    remain mandatory. A spec cannot be reused twice on one local calendar day.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    current_utc = current.astimezone(timezone.utc)
    eligible_specs = [item for item in library.get("production_specs", [])
        if isinstance(item, dict) and is_publishable_spec(item)]
    if not eligible_specs:
        raise ValueError("No enabled production specs clear the evidence safety gates.")
    occupied_slots: set[datetime] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("due_at"):
            continue
        try:
            occupied_slots.add(_parse_datetime(entry["due_at"]).astimezone(timezone.utc))
        except (TypeError, ValueError):
            continue
    candidates: list[tuple[datetime, dict[str, Any]]] = []
    for spec in eligible_specs:
        zone_name = spec.get("publish_timezone")
        if not zone_name:
            raise ValueError(f"Eligible spec {spec.get('spec_path')} has no publish_timezone.")
        zone = ZoneInfo(zone_name)
        local_now = current_utc.astimezone(zone)
        for offset in (0, 1):
            slot_date = local_now.date() + timedelta(days=offset)
            for slot_text in slot_times:
                local_slot = datetime.combine(slot_date, time.fromisoformat(slot_text), tzinfo=zone)
                slot_utc = local_slot.astimezone(timezone.utc)
                lead = slot_utc - current_utc
                if min_lead < lead <= max_lead and slot_utc not in occupied_slots:
                    candidates.append((slot_utc, spec))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    slot_utc = candidates[0][0]
    chosen_specs = [spec for due, spec in candidates if due == slot_utc]
    zone = ZoneInfo(chosen_specs[0]["publish_timezone"])
    local_slot = slot_utc.astimezone(zone)
    used_spec_paths: set[str] = set()
    for entry in ledger.values():
        if not isinstance(entry, dict) or not entry.get("spec") or not entry.get("due_at"):
            continue
        try:
            prior_due = _parse_datetime(entry["due_at"]).astimezone(zone)
        except (TypeError, ValueError):
            continue
        if prior_due.date() == local_slot.date():
            used_spec_paths.add(str(entry["spec"]))
    ever_used = _ever_used_specs(ledger)
    unused = [spec for spec in chosen_specs if str(spec.get("spec_path", "")) not in used_spec_paths
        and str(spec.get("spec_path", "")) not in ever_used]
    if unused and not any(clears_interest_bar(spec, min_interest) for spec in unused):
        return None  # deliberate skip: nothing left clears the public-interest bar
    unused = [spec for spec in unused if clears_interest_bar(spec, min_interest)] or unused
    if not unused:
        raise ValueError(f"No unused eligible topic remains for the {local_slot:%Y-%m-%d %H:%M} {zone.key} publishing slot; topics are never repeated. Add and verify new topics.")
    spec = _least_recently_used(unused, ledger)
    prefix = str(spec.get("content_id_prefix", "")).strip()
    if not prefix:
        raise ValueError(f"Eligible spec {spec.get('spec_path')} has no content_id_prefix.")
    return {
        "spec_path": str(spec["spec_path"]),
        "content_id": f"{prefix}-{local_slot:%Y%m%d}-{local_slot:%H%M}",
        "due_at": local_slot.isoformat(timespec="seconds"),
        "post_title": str(spec.get("post_title") or spec.get("title") or ""),
        "post_description": str(spec.get("post_description") or ""),
        "publish_timezone": zone.key,
        "slot_local": local_slot.strftime("%Y-%m-%d %H:%M"),
    }
