"""Author new evidence-gated topics automatically (no human approval step).

A language model proposes evergreen questions and candidate pages on registered
publisher domains. Pages are fetched and must load. The model then writes a short
script in its own words using only those passages. A topic is accepted only when
every automated gate passes:

* every narration sentence is tied to a verbatim quote from a fetched page,
* every number in a sentence appears in its quote,
* the script copies no long word sequence from the sources,
* a second model pass confirms each sentence is supported and nothing conflicts,
* there is a clickable title, a description, and at least two independent publishers.

These gates are automated checks, not complete fact verification, and each spec
records that. A topic that fails any gate is discarded and never published.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from factflow.fact_research import _ArticleParser, _publisher_for_url, fetch_article
from factflow.llm_providers import AllProvidersFailed, ProviderChain
from factflow.topic_library import register_production_spec
from factflow.visual_motifs import HOLOGRAPHIC_3D, MOTIFS

MIN_WORDS, MAX_WORDS = 50, 110  # fewer ideas, more time on each: the audience is entertained, not lectured
MIN_TITLE, MAX_TITLE = 20, 70
COPY_RUN_WORDS = 8
MAX_UNCITED_QUESTIONS = 1
VISUAL_STYLES = {"hybrid", "3d", "procedural_2d_holographic"}
Fetcher = Callable[[str, dict[str, Any]], dict[str, Any]]


def _norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    cleaned = " ".join(re.sub(r"[^a-z0-9%.' ]+", " ", text.lower()).split())
    # Web pages often render a linked term as "word ." with a space before the stop.
    return re.sub(r" \.", ".", cleaned)


def _words(text: str) -> list[str]:
    return _norm(text).split()


def _numbers(text: str) -> list[str]:
    return [n.rstrip(".") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text.replace(",", ""))]


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def slugify(title: str, limit: int = 22) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    parts = [p for p in base.split("-") if p not in {"a", "an", "the", "why", "how", "does", "do", "is", "are", "of"}]
    slug = "-".join(parts[:3]) or base
    return slug[:limit].strip("-") or "topic"


def default_fetcher(url: str, publisher: dict[str, Any]) -> dict[str, Any]:
    return fetch_article(url, publisher)


def fetch_passages(url: str, registry: dict[str, Any], fetcher: Fetcher = default_fetcher,
                   why: list[str] | None = None) -> dict[str, Any] | None:
    """Fetch one registered-publisher page; None if it is unregistered or fails."""
    publisher = _publisher_for_url(url, registry)
    if publisher is None:
        if why is not None:
            why.append(f"{url}: publisher not in the registry")
        return None
    try:
        page = fetcher(url, publisher)
    except Exception as exc:  # network, redirect, size or type problems all mean "unusable source"
        if why is not None:
            why.append(f"{url}: {type(exc).__name__}: {str(exc)[:120]}")
        return None
    parser = _ArticleParser()
    parser.feed(page["html"])
    title, paragraphs = parser.result()
    paragraphs = [p for p in paragraphs if len(p.split()) >= 8][:40]
    if len(paragraphs) < 2:
        if why is not None:
            why.append(f"{url}: only {len(paragraphs)} usable paragraph(s) found in {len(page['html'])} bytes of HTML")
        return None
    return {"url": page.get("final_url") or url, "title": title, "paragraphs": paragraphs,
            "publisher": publisher.get("name") or publisher.get("id"),
            "publisher_id": publisher.get("id"),
            "group": publisher.get("independence_group") or publisher.get("id")}


# ---------------------------------------------------------------- gates

def check_grounding(narration: str, claims: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[str]:
    """Every sentence needs a verbatim quote from a page; numbers must match."""
    problems: list[str] = []
    corpus = [_norm(" ".join(s["paragraphs"])) for s in sources]
    by_sentence = {_norm(str(c.get("sentence", ""))): c for c in claims if isinstance(c, dict)}
    uncited_questions = 0
    for sentence in split_sentences(narration):
        claim = by_sentence.get(_norm(sentence))
        if claim is None:
            if sentence.endswith("?") and uncited_questions < MAX_UNCITED_QUESTIONS:
                uncited_questions += 1
                continue
            problems.append(f"sentence has no cited quote: {sentence[:80]!r}")
            continue
        quote, index = _norm(str(claim.get("quote", ""))), claim.get("source")
        if not isinstance(index, int) or not 0 <= index < len(sources):
            problems.append(f"bad source index for: {sentence[:60]!r}")
        elif len(quote.split()) < 4 or quote not in corpus[index]:
            problems.append(f"quote not found verbatim in source {index}: {sentence[:60]!r}")
        else:
            missing = [n for n in _numbers(sentence) if n not in _numbers(str(claim.get("quote", "")))]
            if missing:
                problems.append(f"number(s) {missing} not in the cited quote: {sentence[:60]!r}")
    return problems


_TITLE_STOP = frozenset("a an and are as at by do does for how in into is it its of on or our that the their this to what when where which who why with you your".split())


def _title_tokens(title: str) -> set[str]:
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in _norm(title).split() if w not in _TITLE_STOP}


def check_duplicate_subject(title: str, existing_titles: set[str], threshold: float = 0.5) -> list[str]:
    """Reject a topic whose title says nearly the same thing as an existing one (different wording, same subject)."""
    mine = _title_tokens(title)
    for other in existing_titles:
        theirs = _title_tokens(other)
        if mine and theirs and len(mine & theirs) / len(mine | theirs) >= threshold:
            return [f"same subject as an existing topic: {other!r}"]
    return []


def check_source_coverage(claims: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[str]:
    """The cited quotes must come from at least two independent publisher groups, not just one page plus a bystander."""
    groups = set()
    for claim in claims:
        index = claim.get("source") if isinstance(claim, dict) else None
        if isinstance(index, int) and 0 <= index < len(sources):
            groups.add(sources[index].get("group"))
    if len(groups) < 2:
        return ["quotes come from fewer than two independent publisher groups, so nothing is corroborated"]
    return []


def check_originality(narration: str, sources: list[dict[str, Any]], run: int = COPY_RUN_WORDS) -> list[str]:
    """Reject a script that copies a long word run from any source."""
    words = _words(narration)
    grams = {" ".join(words[i:i + run]) for i in range(max(0, len(words) - run + 1))}
    for number, source in enumerate(sources):
        text = " " + _norm(" ".join(source["paragraphs"])) + " "
        for gram in grams:
            if f" {gram} " in text:
                return [f"copies {run}+ consecutive words from source {number}: {gram!r}"]
    return []


_NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?(?![\w])|\b(?:thousand|hundred|million|billion|trillion|percent|per cent|third|thirds)\b", re.I)
_YEAR = re.compile(r"^(1[0-9]{3}|20[0-9]{2})$")
_COMPARE = re.compile(
    r"\b(than|compared|versus|vs|while|whereas|but|unlike|twice|double|triple|times|faster|slower|larger|smaller|bigger|"
    r"longer|shorter|higher|lower|heavier|lighter|hotter|colder|more|less|fewer|greater|further|closer|older|younger|"
    r"stronger|weaker|both|instead|whereas)\b", re.I)


def lone_number_sentences(narration: str) -> list[str]:
    """Sentences that state a number without comparing two or more situations (channel rule: numbers only to compare)."""
    found = []
    for sentence in re.split(r"(?<=[.!?])\s+", narration.strip()):
        numbers = [m.group(0) for m in _NUMBER.finditer(sentence) if not _YEAR.match(m.group(0))]
        if numbers and not _COMPARE.search(sentence):
            found.append(sentence)
    return found


MAX_SENTENCE_WORDS = 18
MAX_WORD_LETTERS = 12
# Textbook words that lose a general audience. Say it the everyday way instead ("leans" for "tilts", "pushing" for "force").
JARGON = {
    "synchronous", "tidally", "nucleus", "nuclei", "proton", "protons", "neutron", "neutrons", "kinetic", "hemisphere",
    "hemispheres", "perturbation", "perturbations", "thermal", "electromagnetic", "stratosphere", "troposphere",
    "isotope", "isotopes", "trajectory", "momentum", "ionosphere", "photosynthesis", "precipitation", "evaporates",
    "condensation", "sedimentary", "convection", "dissipated", "sidereal", "antibodies", "antigen", "pathogen",
}


def hard_to_follow(narration: str) -> list[str]:
    """Sentences a general audience will struggle with: very long sentences or very long words (jargon)."""
    found = []
    for sentence in re.split(r"(?<=[.!?])\s+", narration.strip()):
        words = sentence.split()
        long_word = next((w for w in words for part in w.split("-") if len(re.sub(r"[^A-Za-z]", "", part)) >= MAX_WORD_LETTERS), "")
        if len(words) > MAX_SENTENCE_WORDS:
            found.append(f"{len(words)} words (max {MAX_SENTENCE_WORDS}): {sentence[:60]}")
        elif long_word:
            found.append(f"long word {long_word!r}: {sentence[:60]}")
        else:
            term = next((w for w in re.findall(r"[a-z]+", sentence.lower()) if w in JARGON), "")
            if term:
                found.append(f"textbook word {term!r}: {sentence[:60]}")
    return found


def check_shape(draft: dict[str, Any], existing_titles: set[str]) -> list[str]:
    problems: list[str] = []
    title = str(draft.get("title", "")).strip()
    if not MIN_TITLE <= len(title) <= MAX_TITLE:
        problems.append(f"title must be {MIN_TITLE}-{MAX_TITLE} characters")
    if _norm(title) in existing_titles:
        problems.append("title duplicates an existing topic")
    count = len(str(draft.get("narration", "")).split())
    if not MIN_WORDS <= count <= MAX_WORDS:
        problems.append(f"narration must be {MIN_WORDS}-{MAX_WORDS} words, got {count}")
    if not str(draft.get("description", "")).strip():
        problems.append("description is empty")
    for sentence in lone_number_sentences(str(draft.get("narration", ""))):
        problems.append(f"states a number without comparing situations (say it in words): {sentence[:70]!r}")
    if not (split_sentences(str(draft.get("narration", ""))) or [""])[0].endswith("?"):
        problems.append("open with a friendly question that makes people curious")
    for note in hard_to_follow(str(draft.get("narration", ""))):
        problems.append(f"hard for a general audience, simplify: {note}")
    scenes = draft.get("scenes")
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= 5 or not all(
            isinstance(s, dict) and s.get("visual_description") for s in scenes):
        problems.append("need 3-5 scenes with visual descriptions")
    else:
        for number, scene in enumerate(scenes, 1):
            motif = str(scene.get("motif", "none"))
            if motif not in HOLOGRAPHIC_3D:
                problems.append(f"scene {number} needs a 3D holographic motif, got {motif[:90]!r}")
    return problems


ENTAIL_SYSTEM = ("You are a strict fact checker. Use ONLY the source passages. Reply with JSON only: "
                 '{"results":[{"i":0,"supported":true}],"conflicts":["..."]}. '
                 "supported is true only if the quoted passage clearly states or directly implies the sentence.")


def check_entailment(chain: ProviderChain, claims: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[str]:
    items = "\n".join(f"{i}. SENTENCE: {c['sentence']}\n   QUOTE: {c['quote']}" for i, c in enumerate(claims))
    passages = "\n\n".join(f"[Source {i}] " + " ".join(s["paragraphs"])[:3500] for i, s in enumerate(sources))
    reply = chain.complete_json(ENTAIL_SYSTEM, f"{passages}\n\nCheck each sentence:\n{items}\n"
                                "Also list any sentence that any passage contradicts under conflicts.", max_tokens=1200, temperature=0)
    results = {r.get("i"): r.get("supported") for r in reply.get("results", []) if isinstance(r, dict)}
    problems = [f"not supported: {claims[i]['sentence'][:70]!r}" for i in range(len(claims)) if results.get(i) is not True]
    problems += [f"conflict reported: {str(c)[:100]}" for c in reply.get("conflicts", []) if c]
    return problems


# ---------------------------------------------------------------- model steps

PROPOSE_SYSTEM = ("You propose evergreen educational science questions for 40-second videos. Reply with JSON only: "
                  '{"topics":[{"question":"...","category":"...","source_urls":["https://..."]}]}. '
                  "Give 2-3 real page URLs per topic from DIFFERENT official publishers (e.g. nasa.gov, noaa.gov, usgs.gov, "
                  "esa.int, nps.gov, nist.gov, who.int, universities). Only URLs you are confident exist.")

WRITE_SYSTEM = ("You write a short educational video script in your OWN WORDS using ONLY the supplied source passages. "
                "Never copy phrases; never add facts that are not in the passages. Reply with JSON only: "
                '{"title":"clickable curiosity title, 25-65 characters","narration":"60-100 words, plain sentences, starting with a curious question",'
                '"description":"1-2 sentence hook for the post","category":"...",'
                '"claims":[{"sentence":"exact narration sentence","quote":"verbatim 6+ word excerpt from a passage","source":0}],'
                '"scenes":[{"narration_segment":"...","visual_description":"...","visual_style":"hybrid","motif":"<name or none>"}]}. '
                "Every narration sentence must have a claim whose quote is copied exactly from the passage with that source index. "
                "This is an ENTERTAINMENT channel, not a classroom. Write for the general public, never for scientists: sound like a warm, curious friend telling a fascinating story, with a little wonder and humour. Open with a question that makes people curious. Teach ONE main idea and give it room: at most six short sentences, each under 16 words, one thought per sentence, so the narrator never rushes. Use everyday words (say \"leans\", not \"tilts its axis\"; \"pushes\", not \"exerts force\"). Avoid textbook terms; if one is unavoidable, explain it in plain words right away. Never lecture or talk down. "
                "Do not state numbers (measurements, counts, percentages, fractions) unless the sentence compares two or more situations, such as the speed of light versus the speed of sound; otherwise describe the idea in words. Years of events are fine. visual_style is one of hybrid, 3d, procedural_2d_holographic. 3-4 scenes. motif must be one of these 3D holographic animations: " + ", ".join(sorted(HOLOGRAPHIC_3D)) + ". Choose the one that literally shows what that part of the narration says. If none does, write \"request: <the 3D animation that is needed>\" instead of picking a poor match.")


SEEDED_PROPOSE_SYSTEM = ("You propose evergreen educational science questions for 40-second videos. Reply with JSON only: "
                         '{"topics":[{"question":"...","category":"...","source_urls":["https://..."]}]}. '
                         "You may ONLY use URLs from the supplied list, copied exactly. Each topic needs 2-3 URLs from DIFFERENT "
                         "groups (the group is shown beside each URL) whose pages are about the same subject as the question. "
                         "Skip a topic if no two pages from different groups fit it.")


def load_seeds(path: Path | str) -> list[dict[str, str]]:
    """Verified page URLs the automatic writer may use; empty when the file is missing."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [p for p in data.get("pages", []) if isinstance(p, dict) and p.get("url") and p.get("group")]


def used_source_urls(specs_dir: Path) -> set[str]:
    """Every source URL already behind a topic, so new topics start from fresh pages."""
    used: set[str] = set()
    for path in Path(specs_dir).glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        used.update(str(src.get("url")) for src in data.get("sources", []) if isinstance(src, dict) and src.get("url"))
    return used


def propose_topics(chain: ProviderChain, existing_titles: list[str], count: int,
                   seeds: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    avoid = "; ".join(existing_titles[-60:])
    if seeds:
        listing = "\n".join(f"{s['group']} {s['url']}" for s in seeds)
        reply = chain.complete_json(SEEDED_PROPOSE_SYSTEM,
                                    f"Propose {count} NEW topics. Do not repeat these: {avoid}\n\nAllowed pages:\n{listing}",
                                    max_tokens=1800, temperature=0.7)
        allowed = {s["url"] for s in seeds}
        topics = reply.get("topics", [])
        for t in topics:
            if isinstance(t, dict) and isinstance(t.get("source_urls"), list):
                t["source_urls"] = [u for u in t["source_urls"] if u in allowed]
        return [t for t in topics if isinstance(t, dict) and t.get("question") and isinstance(t.get("source_urls"), list)]
    reply = chain.complete_json(PROPOSE_SYSTEM, f"Propose {count} NEW topics. Do not repeat these: {avoid}", max_tokens=1500, temperature=0.8)
    topics = reply.get("topics", [])
    return [t for t in topics if isinstance(t, dict) and t.get("question") and isinstance(t.get("source_urls"), list)]


def write_draft(chain: ProviderChain, question: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    passages = "\n\n".join(f"[Source {i}] ({s['publisher']}) " + " ".join(s["paragraphs"])[:3500] for i, s in enumerate(sources))
    return chain.complete_json(WRITE_SYSTEM, f"Question: {question}\n\n{passages}", max_tokens=1800, temperature=0.4)


# ---------------------------------------------------------------- orchestration

def build_spec(draft: dict[str, Any], sources: list[dict[str, Any]], today: str) -> dict[str, Any]:
    title = draft["title"].strip()
    urls = " and ".join(f"{s['publisher']} {s['url']}" for s in sources[:2])
    claims = draft["claims"]
    supports: dict[int, list[str]] = {}
    for claim in claims:
        if isinstance(claim.get("source"), int):
            supports.setdefault(claim["source"], []).append(str(claim["quote"]))
    return {
        "title": title, "category": str(draft.get("category") or "science"), "voice": "af_heart",
        "production_label": "QUANTATALE ORIGINAL", "post_title": f"{title} | QuantaTale",
        "post_description": f"{draft['description'].strip()} Sources: {urls} #Science #ScienceFacts #QuantaTale",
        "content_id_prefix": f"qt-{slugify(title)}", "publish_timezone": "Africa/Kampala",
        "editorial_approved": True, "editorial_status": "automated_gate_passed",
        "editorial_review_required": False, "narration": draft["narration"].strip(),
        "sources": [{
            "publisher": s["publisher"], "title": s["title"], "url": s["url"],
            "supports": " | ".join(supports.get(i, []))[:600],
            "review_status": "passage_checked_supports_claim",
            "review_method": "automated_quote_grounding_and_model_entailment", "reviewed_at": today,
        } for i, s in enumerate(sources)],
        "scenes": [{"narration_segment": str(s.get("narration_segment", "")),
                    "visual_description": str(s["visual_description"]),
                    "visual_style": s.get("visual_style") if s.get("visual_style") in VISUAL_STYLES else "hybrid",
                    "motif": s.get("motif") if s.get("motif") in MOTIFS else "none"}
                   for s in draft["scenes"]],
        "visual_profile": "holographic_science_v1",
        "source_passage_verification_required_before_publication": False,
        "source_assessment": ("Automated gates passed on " + today + ": each sentence tied to a verbatim source quote, numbers matched, "
                              "no copied word runs, model entailment check passed, independent publishers. "
                              "Not complete fact verification."),
        "authored_by": "automated_topic_authoring",
    }


def author_topics(chain: ProviderChain, library: dict[str, Any], registry: dict[str, Any], specs_dir: Path, *,
                  count: int = 3, fetcher: Fetcher = default_fetcher, today: str | None = None,
                  max_attempts: int | None = None, seeds: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Create up to ``count`` gated specs; returns a report of accepted and rejected topics."""
    today = today or datetime.now(timezone.utc).date().isoformat()
    specs_dir.mkdir(parents=True, exist_ok=True)
    existing = {_norm(str(i.get("title", "")).replace("| QuantaTale", "")) for i in library.get("production_specs", [])}
    existing_prefixes = {str(i.get("content_id_prefix", "")) for i in library.get("production_specs", [])}
    report: dict[str, Any] = {"accepted": [], "rejected": [], "provider_usage": {}}
    budget = max_attempts or count * 3
    if seeds is not None:
        used = used_source_urls(specs_dir)
        seeds = [x for x in seeds if x["url"] not in used]
        if len({x["group"] for x in seeds}) < 2:
            report["note"] = "no unused verified pages left in production/source-seeds.json; run the source probe and add more"
            return report
    try:
        proposals = propose_topics(chain, sorted(existing), budget, seeds)
    except AllProvidersFailed as exc:
        report["error"] = str(exc)
        return report
    for proposal in proposals[:budget]:
        if len(report["accepted"]) >= count:
            break
        question = str(proposal["question"])
        sources, groups = [], set()
        for url in proposal["source_urls"][:4]:
            page = fetch_passages(str(url), registry, fetcher)
            if page and page["url"] not in {s["url"] for s in sources}:
                sources.append(page)
                groups.add(page["group"])
        if len(groups) < 2:
            report["rejected"].append({"question": question, "reason": "fewer than two independent publisher pages loaded"})
            continue
        try:
            draft = write_draft(chain, question, sources)
            problems = check_shape(draft, existing)
            claims = draft.get("claims") if isinstance(draft.get("claims"), list) else []
            if not problems:
                problems += check_grounding(str(draft.get("narration", "")), claims, sources)
                problems += check_originality(str(draft.get("narration", "")), sources)
                problems += check_source_coverage(claims, sources)
                problems += check_duplicate_subject(str(draft.get("title", "")), existing)
            if not problems:
                problems += check_entailment(chain, claims, sources)
        except AllProvidersFailed as exc:
            report["error"] = str(exc)
            break
        except (KeyError, TypeError, ValueError) as exc:
            problems = [f"malformed draft: {exc}"]
        if problems:
            report["rejected"].append({"question": question, "reason": "; ".join(problems)[:400]})
            continue
        spec = build_spec(draft, sources, today)
        if spec["content_id_prefix"] in existing_prefixes:
            spec["content_id_prefix"] += "-2"
        path = specs_dir / f"{spec['content_id_prefix'][3:]}.json"
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        register_production_spec(library, str(path.as_posix()), spec)
        existing.add(_norm(spec["title"]))
        existing_prefixes.add(spec["content_id_prefix"])
        report["accepted"].append({"title": spec["title"], "spec_path": str(path.as_posix())})
    report["provider_usage"] = dict(chain.usage)
    return report


# ---------------------------------------------------------------- drafts written outside the automated chain

def ingest_drafts(chain: ProviderChain, library: dict[str, Any], registry: dict[str, Any], specs_dir: Path,
                  drafts_dir: Path, *, fetcher: Fetcher = default_fetcher, today: str | None = None,
                  locked_specs: set[str] | None = None) -> dict[str, Any]:
    """Run drafts written by an assistant session through exactly the same gates as model-authored topics.

    A draft is JSON with the fields of a model draft plus ``source_urls``. Pages are fetched fresh, every
    sentence must be tied to a verbatim quote, and the independent model entailment pass must succeed. Accepted drafts
    become specs and are removed; rejected ones move to ``rejected/`` with their reasons so they are never retried silently.

    A draft may carry ``"replaces": "<spec file name without .json>"`` to rewrite a topic that has not been scheduled yet
    (for a friendlier tone, say). It passes every gate again and then overwrites that spec in place; specs listed in
    ``locked_specs`` (already scheduled or published) can never be replaced.
    """
    today = today or datetime.now(timezone.utc).date().isoformat()
    report: dict[str, Any] = {"accepted": [], "rejected": [], "deferred": []}
    specs_dir.mkdir(parents=True, exist_ok=True)
    existing = {_norm(str(i.get("title", "")).replace("| QuantaTale", "")) for i in library.get("production_specs", [])}
    prefixes = {str(i.get("content_id_prefix", "")) for i in library.get("production_specs", [])}
    for path in sorted(drafts_dir.glob("*.json")):
        draft = json.loads(path.read_text(encoding="utf-8"))
        sources, groups, why = [], set(), []
        for url in draft.get("source_urls", [])[:4]:
            page = fetch_passages(str(url), registry, fetcher, why)
            if page and page["url"] not in {s["url"] for s in sources}:
                sources.append(page)
                groups.add(page["group"])
        problems: list[str] = []
        replaces = str(draft.get("replaces", "")).strip()
        old = next((i for i in library["production_specs"] if Path(str(i.get("spec_path", ""))).stem == replaces), None) if replaces else None
        others = existing - {_norm(str(old.get("title", "")).replace("| QuantaTale", ""))} if old else existing
        if replaces and old is None:
            problems.append(f"replaces unknown topic {replaces!r}")
        elif old is not None and str(old.get("spec_path")) in (locked_specs or set()):
            problems.append(f"{replaces!r} is already scheduled or published and cannot be replaced")
        if len(groups) < 2:
            problems.append("fewer than two independent publisher pages loaded: " + " | ".join(why))
        try:
            claims = draft.get("claims") if isinstance(draft.get("claims"), list) else []
            if not problems:
                problems += check_shape(draft, others)
            if not problems:
                problems += check_grounding(str(draft.get("narration", "")), claims, sources)
                problems += check_originality(str(draft.get("narration", "")), sources)
                problems += check_source_coverage(claims, sources)
                problems += check_duplicate_subject(str(draft.get("title", "")), others)
            if not problems:
                problems += check_entailment(chain, claims, sources)
        except AllProvidersFailed as exc:
            report["deferred"].append({"draft": path.name, "reason": str(exc)[:300]})
            continue  # no independent checker was reachable: keep the draft for the next run
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"malformed draft: {exc}")
        if problems:
            rejected = drafts_dir / "rejected"
            rejected.mkdir(exist_ok=True)
            draft["rejection_reasons"] = problems
            (rejected / path.name).write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            path.unlink()
            # The paragraphs the gates actually saw, so a rewrite can quote the page exactly.
            report["rejected"].append({"draft": path.name, "reason": "; ".join(problems)[:400],
                                       "source_text": {s["url"]: [q[:900] for q in s["paragraphs"][:25]] for s in sources}})
            continue
        spec = build_spec(draft, sources, today)
        spec["authored_by"] = "assistant_session_draft_then_automated_gates"
        if old is not None:
            spec["content_id_prefix"] = str(old["content_id_prefix"])
            spec["replaced_at"] = today
            existing.discard(_norm(str(old.get("title", "")).replace("| QuantaTale", "")))
            spec_path = Path(str(old["spec_path"]))
        else:
            if spec["content_id_prefix"] in prefixes:
                spec["content_id_prefix"] += "-2"
            spec_path = specs_dir / f"{spec['content_id_prefix'][3:]}.json"
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        register_production_spec(library, str(spec_path.as_posix()), spec)
        existing.add(_norm(spec["title"]))
        prefixes.add(spec["content_id_prefix"])
        path.unlink()
        report["accepted"].append({"title": spec["title"], "spec_path": str(spec_path.as_posix())})
    return report
