"""Command-line interface for QuantaTale."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from factflow.discovery import discover_candidates, load_feed_config
from factflow.evidence_dossier import build_evidence_dossier
from factflow.evidence_comparison import compare_evidence
from factflow.fact_research import research_discovery_candidates
from factflow.research import build_research_report, load_source_registry
from factflow.scholarly_discovery import discover_scholarly_metadata
from factflow.scholarly_fulltext import retrieve_open_access_passages
from factflow.topic import TopicValidationError, load_topic
from factflow.topic_library import add_discovery_report, load_library, save_library, library_summary, register_production_spec
from factflow.video_render import render_sample_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quantatale", description="QuantaTale production tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a topic JSON file.")
    validate_parser.add_argument("topic_file", help="Path to the topic JSON file.")

    research_parser = subparsers.add_parser(
        "research-report", help="Assess registered evidence for each topic claim."
    )
    research_parser.add_argument("topic_file", help="Path to the topic JSON file.")
    research_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    research_parser.add_argument("--check-links", action="store_true", help="Check source URL reachability.")
    research_parser.add_argument("--output", default=None, help="Optional path for the JSON report.")

    discover_parser = subparsers.add_parser(
        "discover", help="Collect candidate story leads from curated public RSS/Atom feeds."
    )
    discover_parser.add_argument("--feeds", default=None, help="Optional discovery feed configuration.")
    discover_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    discover_parser.add_argument("--limit", type=int, default=30, help="Maximum candidate leads (1-200).")
    discover_parser.add_argument("--output", default="build/discovery-candidates.json", help="JSON output path.")

    candidates_parser = subparsers.add_parser(
        "research-candidates", help="Fetch discovered articles and extract unreviewed claim candidates."
    )
    candidates_parser.add_argument("discovery_report", help="Stage 3 discovery-candidates JSON file.")
    candidates_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    candidates_parser.add_argument("--limit", type=int, default=10, help="Maximum article pages to retrieve (1-50).")
    candidates_parser.add_argument("--max-candidates-per-source", type=int, default=12)
    candidates_parser.add_argument("--output", default="build/research-candidates.json", help="JSON output path.")

    dossier_parser = subparsers.add_parser(
        "evidence-dossier", help="Discover related feed evidence and flag possible differences for review."
    )
    dossier_parser.add_argument("research_report", help="Stage 4A research-candidates JSON file.")
    dossier_parser.add_argument("--feeds", default=None, help="Optional discovery feed configuration.")
    dossier_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    dossier_parser.add_argument("--feed-limit", type=int, default=100, help="Maximum feed leads to inspect (1-200).")
    dossier_parser.add_argument("--article-limit", type=int, default=20, help="Maximum related pages to retrieve (1-50).")
    dossier_parser.add_argument("--output", default="build/evidence-dossiers.json", help="JSON output path.")
    scholarly_parser = subparsers.add_parser(
        "scholarly-discover", help="Find unreviewed scholarly metadata leads via free Crossref and Europe PMC APIs."
    )
    scholarly_parser.add_argument("research_report", help="Stage 4A research-candidates JSON file.")
    scholarly_parser.add_argument("--claim-limit", type=int, default=20, help="Maximum claim candidates to search (1-50).")
    scholarly_parser.add_argument("--results-per-provider", type=int, default=5, help="Results per API and claim (1-10).")
    scholarly_parser.add_argument("--output", default="build/scholarly-leads.json", help="JSON output path.")

    comparison_parser = subparsers.add_parser(
        "evidence-compare", help="Compare collected passages with claim candidates and produce human-review signals."
    )
    comparison_parser.add_argument("research_report", help="Stage 4A research-candidates JSON file.")
    comparison_parser.add_argument("--scholarly", default=None, help="Optional Stage 4B-3 scholarly-passages JSON file.")
    comparison_parser.add_argument("--dossiers", default=None, help="Optional Stage 4B feed evidence-dossiers JSON file.")
    comparison_parser.add_argument("--passage-limit-per-claim", type=int, default=100, help="Maximum passages compared per claim (1-250).")
    comparison_parser.add_argument("--output", default="build/evidence-comparisons.json", help="JSON output path.")

    fulltext_parser = subparsers.add_parser(
        "scholarly-retrieve", help="Retrieve bounded full-text passages from explicitly open-access Europe PMC records."
    )
    fulltext_parser.add_argument("scholarly_report", help="Stage 4B-2 scholarly-leads JSON file.")
    fulltext_parser.add_argument("--article-limit", type=int, default=20, help="Maximum OA articles to retrieve (1-50).")
    fulltext_parser.add_argument("--passages-per-article", type=int, default=40, help="Maximum passages per article (1-40).")
    fulltext_parser.add_argument("--output", default="build/scholarly-passages.json", help="JSON output path.")
    library_parser = subparsers.add_parser(
        "library-add-discovery", help="Persist discovered story leads without approving them for production."
    )
    library_parser.add_argument("discovery_report", help="Discovery-candidates JSON report.")
    library_parser.add_argument("--library", default="production/topic-library.json", help="Persistent topic library JSON.")

    register_parser = subparsers.add_parser(
        "library-register-spec", help="Register a production spec; only explicitly approved specs become selectable."
    )
    register_parser.add_argument("spec_file", help="Reviewed production specification JSON.")
    register_parser.add_argument("--library", default="production/topic-library.json", help="Persistent topic library JSON.")

    author_parser = subparsers.add_parser(
        "author-topics", help="Automatically write and gate new topics with the free LLM provider chain.")
    author_parser.add_argument("--count", type=int, default=3, help="Maximum topics to accept this run.")
    author_parser.add_argument("--library", default="production/topic-library.json", help="Persistent topic library JSON.")
    author_parser.add_argument("--specs-dir", default="production/specs", help="Directory for new specs.")
    author_parser.add_argument("--registry", default=None, help="Optional publisher registry JSON.")
    author_parser.add_argument("--seeds", default="production/source-seeds.json", help="Verified source pages the writer may use.")
    author_parser.add_argument("--output", default="build/topic-authoring.json", help="JSON report path.")

    ingest_parser = subparsers.add_parser(
        "ingest-drafts", help="Gate assistant-written topic drafts and add the accepted ones to the library.")
    ingest_parser.add_argument("--drafts-dir", default="production/drafts", help="Directory of draft JSON files.")
    ingest_parser.add_argument("--library", default="production/topic-library.json")
    ingest_parser.add_argument("--specs-dir", default="production/specs")
    ingest_parser.add_argument("--registry", default=None)
    ingest_parser.add_argument("--ledger", default="production/publishing-ledger.json",
                               help="Publishing ledger; topics listed there are locked and cannot be rewritten.")
    ingest_parser.add_argument("--output", default="build/draft-ingest.json")

    probe_parser = subparsers.add_parser("source-text", help="Print the paragraphs the evidence gates would see for page URLs.")
    probe_parser.add_argument("urls", nargs="+")
    probe_parser.add_argument("--registry", default=None)
    probe_parser.add_argument("--max-paragraphs", type=int, default=16)

    motif_parser = subparsers.add_parser("motif-report", help="Count 3D vs flat animations and list flat ones still used by topics.")
    motif_parser.add_argument("--specs-dir", default="production/specs")

    number_parser = subparsers.add_parser("number-report", help="List narration sentences that state a number without comparing situations.")
    number_parser.add_argument("--specs-dir", default="production/specs")

    language_parser = subparsers.add_parser("language-report", help="List narration sentences that are hard for a general audience.")
    language_parser.add_argument("--specs-dir", default="production/specs")

    stock_parser = subparsers.add_parser("topic-stock", help="Report never-used publishable topics.")
    stock_parser.add_argument("--library", default="production/topic-library.json")
    stock_parser.add_argument("--ledger", default="production/publishing-ledger.json")
    stock_parser.add_argument("--minimum", type=int, default=4)
    stock_parser.add_argument("--output", default="build/topic-stock.json")

    interest_parser = subparsers.add_parser(
        "score-library", help="Score every production spec for public interest and store the result.")
    interest_parser.add_argument("--library", default="production/topic-library.json")

    status_parser = subparsers.add_parser(
        "library-status", help="Report approved topic reserve health without approving candidates."
    )
    status_parser.add_argument("--library", default="production/topic-library.json", help="Persistent topic library JSON.")
    status_parser.add_argument("--minimum-ready", type=int, default=14, help="Target approved-ready topic reserve.")
    status_parser.add_argument("--output", default="build/topic-library-status.json", help="JSON status report path.")

    render_parser = subparsers.add_parser(
        "render-sample", help="Render a sourced sample short using free procedural graphics, TTS and FFmpeg."
    )
    render_parser.add_argument("spec_file", help="Sample video specification JSON.")
    render_parser.add_argument("--output-dir", default="build/sample-video", help="Directory for MP4 and sidecar files.")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "library-register-spec":
        try:
            spec = json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
            library = load_library(args.library)
            added = register_production_spec(library, args.spec_file, spec)
            save_library(library, args.library)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"TOPIC LIBRARY ERROR: {exc}", file=sys.stderr)
            return 1
        print(("Registered" if added else "Updated") + f" production spec: {args.spec_file}")
        print("Selection status: " + ("approved_ready" if spec.get("editorial_approved") is True else "awaiting_editorial_review"))
        return 0

    if args.command == "library-add-discovery":
        try:
            report = json.loads(Path(args.discovery_report).read_text(encoding="utf-8"))
            library = load_library(args.library)
            result = add_discovery_report(library, report)
            save_library(library, args.library)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"TOPIC LIBRARY ERROR: {exc}", file=sys.stderr)
            return 1
        summary = library_summary(library)
        print(f"Added {result['added']} leads; skipped {result['duplicates']} duplicates.")
        print(f"Library totals: {summary}")
        print("All discovered leads remain unreviewed and blocked from production.")
        return 0

    if args.command == "motif-report":
        import json as _json
        from collections import Counter
        from factflow.visual_motifs import HOLOGRAPHIC_3D, MOTIFS
        used: Counter[str] = Counter()
        for path in sorted(Path(args.specs_dir).glob("*.json")):
            spec = _json.loads(path.read_text(encoding="utf-8"))
            for scene in spec.get("scenes", []):
                used[str(scene.get("motif", "none"))] += 1
        flat_used = {name: n for name, n in used.items() if name not in HOLOGRAPHIC_3D}
        print(f"Motifs: {len(HOLOGRAPHIC_3D)} holographic 3D of {len(MOTIFS)} total")
        print(f"Scenes in topics: {sum(used.values())}; still flat: {sum(flat_used.values())}")
        for name, n in sorted(flat_used.items(), key=lambda kv: -kv[1]):
            print(f"  flat: {name} x{n}")
        return 0

    if args.command == "number-report":
        import json as _json
        from factflow.topic_authoring import lone_number_sentences
        total = 0
        for path in sorted(Path(args.specs_dir).glob("*.json")):
            spec = _json.loads(path.read_text(encoding="utf-8"))
            for sentence in lone_number_sentences(str(spec.get("narration", ""))):
                total += 1
                print(f"  {path.stem}: {sentence[:110]}")
        print(f"Sentences stating a lone number: {total}")
        return 0

    if args.command == "language-report":
        import json as _json
        from factflow.topic_authoring import MAX_WORDS, hard_to_follow, split_sentences
        total, rewrite = 0, []
        for path in sorted(Path(args.specs_dir).glob("*.json")):
            spec = _json.loads(path.read_text(encoding="utf-8"))
            narration = str(spec.get("narration", ""))
            notes = hard_to_follow(narration)
            if len(narration.split()) > MAX_WORDS:
                notes.append(f"{len(narration.split())} words, too many ideas for a relaxed pace (max {MAX_WORDS})")
            if not (split_sentences(narration) or [""])[0].endswith("?"):
                notes.append("does not open with a friendly question")
            for note in notes:
                total += 1
                print(f"  {path.stem}: {note}")
            if notes:
                rewrite.append(path.stem)
        print(f"Sentences hard for a general audience: {total}")
        print(f"Topics to rewrite for a friendlier, slower pace: {len(rewrite)}")
        return 0

    if args.command == "source-text":
        from factflow.topic_authoring import fetch_passages
        registry = load_source_registry(args.registry) if args.registry else load_source_registry()
        for url in args.urls:
            why: list[str] = []
            page = fetch_passages(url, registry, why=why)
            if page is None:
                print(f"=== FAILED {url}: {' | '.join(why)}")
                continue
            print(f"=== OK {url} (publisher {page['publisher']}, group {page['group']})")
            for number, paragraph in enumerate(page["paragraphs"][:args.max_paragraphs]):
                print(f"[{number}] {paragraph[:700]}")
        return 0

    if args.command == "ingest-drafts":
        from factflow.llm_providers import ProviderChain
        from factflow.topic_authoring import ingest_drafts
        try:
            library = load_library(args.library)
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            chain = ProviderChain()
            ledger_path = Path(args.ledger)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
            locked = {str(v.get("spec")) for v in ledger.values() if isinstance(v, dict) and v.get("spec")}
            report = ingest_drafts(chain, library, registry, Path(args.specs_dir), Path(args.drafts_dir), locked_specs=locked)
            report["provider_failures"] = chain.failures[:40]
            if report["accepted"]:
                save_library(library, args.library)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"DRAFT INGEST ERROR: {exc}", file=sys.stderr)
            return 1
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for failure in report["provider_failures"]:
            print(f"  provider skipped: {failure}")
        for item in report["rejected"] + report["deferred"]:
            print(f"  not accepted: { {k: v for k, v in item.items() if k != 'source_text'} }")
            for url, paragraphs in item.get("source_text", {}).items():
                for number, paragraph in enumerate(paragraphs):
                    print(f"    page text {url} [{number}]: {paragraph}")
        print(f"Ingested {len(report['accepted'])}, rejected {len(report['rejected'])}, deferred {len(report['deferred'])}")
        return 0

    if args.command == "author-topics":
        from factflow.llm_providers import ProviderChain
        from factflow.topic_authoring import author_topics, load_seeds
        try:
            library = load_library(args.library)
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            chain = ProviderChain()
            report = author_topics(chain, library, registry, Path(args.specs_dir), count=args.count, seeds=load_seeds(args.seeds))
            report["provider_failures"] = chain.failures[:40]
            if report["accepted"]:
                save_library(library, args.library)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"TOPIC AUTHORING ERROR: {exc}", file=sys.stderr)
            return 1
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for failure in report.get("provider_failures", []):
            print(f"  provider skipped: {failure}")
        print(f"Accepted {len(report['accepted'])}, rejected {len(report['rejected'])}; providers used: {report['provider_usage']}")
        for item in report["rejected"]:
            print(f"  rejected: {item['question'][:70]} -> {item['reason'][:160]}")
        if report.get("note"):
            print(f"  note: {report['note']}")
        if report.get("error"):
            print(f"TOPIC AUTHORING ERROR: {report['error']}", file=sys.stderr)
            return 1
        return 0

    if args.command == "score-library":
        from factflow.topic_interest import score_spec
        library = load_library(args.library)
        scored = 0
        for item in library["production_specs"]:
            try:
                spec = json.loads(Path(item["spec_path"]).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, KeyError):
                print(f"  could not read {item.get('spec_path')}; left unscored")
                continue
            result = score_spec(spec)
            item["interest_score"], item["interest_reasons"] = result["score"], result["reasons"]
            scored += 1
        save_library(library, args.library)
        print(f"Scored {scored} of {len(library['production_specs'])} specs.")
        return 0

    if args.command == "topic-stock":
        from factflow.publishing_slots import unused_topic_count
        library = load_library(args.library)
        ledger_path = Path(args.ledger)
        ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
        unused = unused_topic_count(library, ledger)
        result = {"unused_publishable_topics": unused, "minimum": args.minimum, "low": unused < args.minimum}
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Unused publishable topics: {unused} (minimum {args.minimum})")
        return 0

    if args.command == "library-status":
        if args.minimum_ready < 1:
            print("TOPIC LIBRARY STATUS ERROR: minimum-ready must be at least 1.", file=sys.stderr)
            return 1
        try:
            library = load_library(args.library)
            summary = library_summary(library)
            report = {
                "schema_version": 1,
                "minimum_ready_target": args.minimum_ready,
                "approved_ready": summary["approved_ready"],
                "eligible_for_publishing": summary["eligible_for_publishing"],
                "blocked_by_evidence": summary["blocked_by_evidence"],
                "needs_replenishment": summary["eligible_for_publishing"] < args.minimum_ready,
                "summary": summary,
                "publication_gate": "only_explicitly_human_approved_specs_are_selectable",
            }
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"TOPIC LIBRARY STATUS ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"Editorially approved topics: {summary['approved_ready']}")
        print(f"Eligible for publishing: {summary['eligible_for_publishing']} / target {args.minimum_ready}")
        print(f"Blocked by evidence checks: {summary['blocked_by_evidence']}")
        print(f"Unreviewed candidates: {summary['unreviewed_leads']}")
        print(f"Status report: {output_path}")
        if report["needs_replenishment"]:
            print("WARNING: approved topic reserve is below target; editorial review and approval are required.")
        return 0

    if args.command == "render-sample":
        try:
            result = render_sample_video(args.spec_file, args.output_dir)
        except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
            print(f"SAMPLE RENDER ERROR: {exc}", file=sys.stderr)
            return 1
        print("SAMPLE VIDEO RENDERED AND QUALITY-CHECKED")
        print(f"Video: {result['video']}")
        print(f"Duration: {result['duration_seconds']} seconds")
        print(f"Format: {result['width']}x{result['height']} at {result['fps']} fps")
        print(f"File size: {result['size_bytes']} bytes")
        print(f"Metadata: {result['metadata']}")
        return 0

    if args.command == "evidence-compare":
        if not 1 <= args.passage_limit_per_claim <= 250:
            print("EVIDENCE COMPARISON ERROR: passage limit must be between 1 and 250.", file=sys.stderr)
            return 1
        try:
            research = json.loads(Path(args.research_report).read_text(encoding="utf-8"))
            scholarly = json.loads(Path(args.scholarly).read_text(encoding="utf-8")) if args.scholarly else {}
            dossiers = json.loads(Path(args.dossiers).read_text(encoding="utf-8")) if args.dossiers else {}
            report = compare_evidence(
                research, scholarly, dossiers,
                passage_limit_per_claim=args.passage_limit_per_claim,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"EVIDENCE COMPARISON ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Compared passages for {report['candidate_count']} claim candidates; all signals remain unreviewed.")
        print(f"Evidence comparison report: {output_path}")
        return 0

    if args.command == "scholarly-retrieve":
        if not 1 <= args.article_limit <= 50 or not 1 <= args.passages_per_article <= 40:
            print("SCHOLARLY RETRIEVAL ERROR: limits out of range.", file=sys.stderr)
            return 1
        try:
            scholarly = json.loads(Path(args.scholarly_report).read_text(encoding="utf-8"))
            report = retrieve_open_access_passages(
                scholarly, article_limit=args.article_limit,
                passages_per_article=args.passages_per_article,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"SCHOLARLY RETRIEVAL ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Retrieved {report['passage_count']} unreviewed passages from {report['retrieved_article_count']} open-access articles.")
        print(f"Scholarly passage report: {output_path}")
        return 0

    if args.command == "scholarly-discover":
        if not 1 <= args.claim_limit <= 50 or not 1 <= args.results_per_provider <= 10:
            print("SCHOLARLY DISCOVERY ERROR: limits out of range.", file=sys.stderr)
            return 1
        try:
            research = json.loads(Path(args.research_report).read_text(encoding="utf-8"))
            report = discover_scholarly_metadata(research, claim_limit=args.claim_limit,
                                                 results_per_provider=args.results_per_provider)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"SCHOLARLY DISCOVERY ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Collected {report['lead_count']} unreviewed scholarly metadata leads.")
        print(f"Scholarly discovery report: {output_path}")
        return 0

    if args.command == "evidence-dossier":
        if not 1 <= args.feed_limit <= 200 or not 1 <= args.article_limit <= 50:
            print("DOSSIER ERROR: feed-limit must be 1-200 and article-limit must be 1-50.", file=sys.stderr)
            return 1
        try:
            research = json.loads(Path(args.research_report).read_text(encoding="utf-8"))
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            feeds = load_feed_config(args.feeds) if args.feeds else load_feed_config()
            report = build_evidence_dossier(
                research, registry, feeds,
                feed_limit=args.feed_limit, article_limit=args.article_limit,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"DOSSIER ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        discovery = report["discovery"]
        print(
            f"Built {report['dossier_count']} evidence dossiers; "
            f"retrieved {discovery['retrieved_article_count']} related articles."
        )
        print(f"Evidence dossier report: {output_path}")
        return 0

    if args.command == "research-candidates":
        if not 1 <= args.limit <= 50:
            print("RESEARCH ERROR: --limit must be between 1 and 50.", file=sys.stderr)
            return 1
        try:
            discovery = json.loads(Path(args.discovery_report).read_text(encoding="utf-8"))
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            report = research_discovery_candidates(
                discovery, registry, limit=args.limit,
                max_candidates_per_source=args.max_candidates_per_source,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"RESEARCH ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Extracted {report['claim_candidate_count']} unreviewed claim candidates from {report['source_count']} sources.")
        print(f"Research candidate report: {output_path}")
        return 0
    if args.command == "discover":
        if not 1 <= args.limit <= 200:
            print("DISCOVERY ERROR: --limit must be between 1 and 200.", file=sys.stderr)
            return 1
        try:
            config = load_feed_config(args.feeds) if args.feeds else load_feed_config()
            registry = load_source_registry(args.registry) if args.registry else load_source_registry()
            report = discover_candidates(config, registry, limit=args.limit)
        except ValueError as exc:
            print(f"DISCOVERY ERROR: {exc}", file=sys.stderr)
            return 1
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Discovered {report['candidate_count']} candidate leads; report: {output_path}")
        for result in report["feed_results"]:
            print(f"- {result['publisher_id']}: {result['status']}")
        return 0

    try:
        topic = load_topic(args.topic_file)
    except TopicValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        print(f"VALID: {topic['title']} ({topic['id']})")
        print(f"Claims: {len(topic['claims'])} | Scenes: {len(topic['scenes'])}")
        return 0

    try:
        registry = load_source_registry(args.registry) if args.registry else load_source_registry()
    except ValueError as exc:
        print(f"RESEARCH ERROR: {exc}", file=sys.stderr)
        return 1

    report = build_research_report(topic, registry, check_links=args.check_links)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Research report written to {output_path}")
    else:
        print(rendered)

    if any(item["status"] == "unsupported_or_unregistered" for item in report["claim_statuses"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
