"""Public-interest scoring for QuantaTale topics and discovery leads.

Pipeline stage 5 (topic ranking). The score is a transparent, deterministic
heuristic (no paid API, no model call). It estimates how likely an ordinary
viewer is to stop, watch and share a short explainer. It never judges truth:
evidence gates remain separate and mandatory, and a high score cannot make an
unverified topic publishable.
"""
from __future__ import annotations
import re
from typing import Any

# Topics scoring below this are not selected for a publishing slot. The slot is
# skipped rather than filled with low-appeal content.
DEFAULT_MIN_INTEREST = 40
NEUTRAL_SCORE = 50  # legacy library entries with no stored score

_COUNTER = ("not", "n't", "isn't", "doesn't", "aren't", "really", "actually", "myth",
            "wrong", "surprising", "secret", "hidden", "only", "never", "yet", "but")
_SUPERLATIVE = ("largest", "biggest", "hottest", "coldest", "fastest", "deepest", "oldest",
                "tallest", "strongest", "longest", "most ", "ever", "impossible")
_EVERYDAY = ("you", "your", "body", "brain", "heart", "sleep", "eyes", "skin", "sun", "sky",
             "weather", "storm", "water", "food", "sound", "light", "phone", "heat", "cold",
             "sick", "health", "age", "money", "earth", "moon", "space", "ocean", "animal")
_BIG_QUESTIONS = ("black hole", "universe", "death", "alien", "dinosaur", "volcano",
                  "earthquake", "tsunami", "asteroid", "vaccine", "climate", "ai ")
_NUMBER = re.compile(r"\b\d[\d,.]*\s*(?:%|percent|times|minutes?|hours?|years?|days?|km|miles?|degrees?|seconds?)?", re.I)
_DRY = ("definition of", "standard", "protocol", "committee", "framework", "methodology",
        "regulation", "administrative", "appointment", "announces", "press release")


def _text(spec: dict[str, Any]) -> str:
    narration = str(spec.get("narration") or "")
    title = str(spec.get("post_title") or spec.get("title") or "")
    return f"{title}. {narration}".casefold()


def _hits(text: str, words: tuple[str, ...]) -> list[str]:
    return [w.strip() for w in words if w in text]


def score_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Return {"score": 0-100, "reasons": [...]} for a production spec."""
    text = _text(spec)
    reasons: list[str] = []
    score = 0
    narration = str(spec.get("narration") or "").strip()

    # Curiosity-gap hook (max 30).
    hook = 0
    if narration.split("?")[0] != narration and narration.find("?") < 120:
        hook += 12
        reasons.append("opens with a question")
    counter = _hits(text, _COUNTER)
    if counter:
        hook += min(10, 5 * len(counter))
        reasons.append("challenges an assumption")
    if _hits(text, _SUPERLATIVE):
        hook += 8
        reasons.append("extreme or record claim")
    score += min(30, hook)

    # Everyday relevance (max 30).
    everyday = _hits(text, _EVERYDAY)
    relevance = min(20, 4 * len(everyday))
    if "you" in text.split() or "your" in text.split():
        relevance += 5
    if _hits(text, _BIG_QUESTIONS):
        relevance += 5
        reasons.append("big-question subject")
    if everyday:
        reasons.append("touches everyday life")
    score += min(30, relevance)

    # Visual explainability (max 25).
    scenes = [s for s in spec.get("scenes", []) if isinstance(s, dict)]
    visual = 0
    if len(scenes) >= 3:
        visual += 10
    visual += min(15, 5 * sum(1 for s in scenes if s.get("motif")))
    if visual >= 15:
        reasons.append("strong visual explanation")
    score += min(25, visual)

    # Concreteness (max 15): a number or comparison viewers can picture.
    if _NUMBER.search(narration):
        score += 10
        reasons.append("concrete number")
    if " than " in text or " times " in text or " like " in text:
        score += 5

    dry = _hits(text, _DRY)
    if dry:
        score -= 15 * len(dry)
        reasons.append("dry or administrative wording")

    score = max(0, min(100, score))
    return {"score": score, "reasons": reasons}


# Discovery leads that are about institutions, not phenomena.
_LEAD_SKIP = re.compile(
    r"\b(appoint\w*|names new|hires?|hired|retire\w*|resign\w*|joins|contract award\w*|"
    r"award\w* (?:a )?(?:contract|grant)|budget\w*|hearing\w*|webinar\w*|press kit|media advisory|"
    r"call for proposals|funding opportunit\w*|schedule\w*|reminder|job opening\w*|holiday\w*|"
    r"closure\w*|workshop\w*|meeting\w*)\b", re.I)


def lead_is_low_interest(lead: dict[str, Any]) -> bool:
    """True for administrative or personnel items that are poor video topics."""
    return bool(_LEAD_SKIP.search(f"{lead.get('title', '')} {lead.get('description', '')}"))


def interest_of(item: dict[str, Any]) -> int:
    """Stored interest score of a library entry, neutral if never scored."""
    value = item.get("interest_score")
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else NEUTRAL_SCORE


def clears_interest_bar(item: dict[str, Any], minimum: int = DEFAULT_MIN_INTEREST) -> bool:
    return interest_of(item) >= minimum
