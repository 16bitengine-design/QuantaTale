# QuantaTale

**KNOW MORE. SEE DIFFERENTLY.**

QuantaTale is a free, open-source, cloud-first production engine for turning reliable research into engaging narrated explainers, quick facts and educational videos across science, history, nature, technology, geography, health, engineering, mathematics and virtually any other subject.

Its signature presentation is **cinematic, code-generated holographic storytelling**: animated scientific diagrams, procedural 2D/3D scenes, simulations, luminous interfaces, motion graphics and visual effects. QuantaTale is designed to create its visuals with code and open-source tools—not stock footage or paid AI-video services.

## Brand identity

- **Name:** QuantaTale
- **Tagline:** KNOW MORE. SEE DIFFERENTLY.
- **Positioning:** Immersive, evidence-led explanations of fascinating facts, complex ideas and the world around us.
- **Personality:** Curious, intelligent, cinematic, clear and trustworthy.
- **Visual direction:** Deep midnight navy backgrounds, luminous cyan holographic elements, restrained violet accents, crisp white typography and a geometric QT-inspired symbol.
- **Content promise:** Make complex things easier to understand without compromising factual accuracy.

## Non-negotiable principles

- **Zero-cost core:** no paid APIs, subscriptions, credits or commercial generation services are mandatory.
- **Cloud-only execution:** production runs through GitHub Actions; no local rendering or installation is required.
- **Code-generated visuals:** scenes are created with open-source tools and project code.
- **Narration-first storytelling:** every video has a strong hook, clear explanation and memorable ending.
- **Evidence before publication:** factual claims must be traceable to reputable sources and reviewed before rendering.
- **Reproducible builds:** inputs, settings and outputs are versioned or recorded.
- **Honest limits:** free runners have time, storage and resource limits. QuantaTale must report these rather than promise unlimited production.

## Production flow

1. **Discover:** identify engaging topics and define the audience and learning objective.
2. **Research:** collect source-backed claims and preserve structured evidence.
3. **Assess:** examine publisher registration, source relevance, independent corroboration and uncertainty; require editorial review.
4. **Write:** prepare concise narration with a hook, explanation and memorable close.
5. **Plan scenes:** map each narration segment to an original explanatory visual.
6. **Generate voice:** use an open-source, cloud-runnable text-to-speech engine.
7. **Animate:** create 2D motion graphics and procedural 3D/holographic scenes with code.
8. **Assemble:** synchronize narration, visuals, captions and sound.
9. **Quality-check:** validate evidence status, timing, audio, captions, dimensions and render integrity.
10. **Export:** prepare platform-ready videos and publishing metadata for Shorts and longer formats.

## Cloud-only, zero-cost operating model

The initial execution target is GitHub Actions on GitHub-hosted runners. The repository prioritizes open-source tools and free public-repository runner capacity where available. Workflows must be efficient, avoid unnecessary repeated renders and respect free compute and storage limits.

**Important:** "100% free" means the core project must not require paid services or subscriptions. It does not mean unlimited compute, storage, bandwidth or guaranteed availability. GitHub and upstream projects can change their free-tier policies. QuantaTale will report resource limits clearly and fail safely when a job cannot complete.

No API keys or paid-provider credentials should be required for the core workflow.

## Repository layout

The current Python import package and legacy command remain `factflow` for compatibility with existing code and workflows. The supported product command is `quantatale`.

```text
.
├── .github/workflows/ci.yml
├── data/
│   ├── discovery_feeds.json
│   └── source_registry.json
├── examples/topics/why-the-sky-is-blue.json
├── src/factflow/
│   ├── __init__.py
│   ├── cli.py
│   ├── discovery.py
│   ├── fact_research.py
│   ├── evidence_dossier.py
│   ├── scholarly_discovery.py
│   ├── scholarly_fulltext.py
│   ├── research.py
│   └── topic.py
├── tests/
└── pyproject.toml
```

## Stage 1: project foundation

The first milestone established a Python package, a topic JSON specification, a command-line validator, automated tests and a GitHub Actions workflow.

## Stage 2: evidence and fact assessment

QuantaTale has a curated starting registry of reputable publishers, including scientific, government, health, historical, educational and statistical institutions. The registry is stored in `data/source_registry.json`.

Each factual claim records structured evidence:
- `publisher_id`: publisher identifier from the curated registry.
- `url`: page containing the evidence.
- `title`: source page title.
- `accessed_on`: date the source was reviewed.
- `evidence_summary`: editor's summary of the relevant material.
- `supports_claim`: set to `true` only after an editor confirms the source directly supports the claim.

Generate an evidence report:

```bash
quantatale research-report examples/topics/why-the-sky-is-blue.json
```

Add `--check-links` to check whether source URLs respond. A reachable page is not necessarily accurate, authoritative or relevant.

Evidence statuses are workflow signals, not truth scores. Even two independent registered publishers marked as supporting a claim do not automatically approve it. An editor must read the cited material, check wording and context, and approve the claim before publication.

## Stage 3: automated topic discovery

QuantaTale collects candidate story leads from a curated set of public RSS and Atom feeds. The configuration is in `data/discovery_feeds.json`; every feed and article URL must match the registered domains for its publisher.

Run discovery:

```bash
quantatale discover --limit 30 --output build/discovery-candidates.json
```

The GitHub Actions workflow runs this command automatically and uploads JSON reports as an artifact named `quantatale-research-reports` (retained for seven days). Open the repository's **Actions** tab, select the latest successful workflow run, and download the artifact.

Each result is labeled `candidate_unreviewed`. QuantaTale stores the headline, source URL, publication date when provided, and a short feed description. It does **not** turn a headline into a factual claim, copy feed descriptions into narration, or mark a source as supporting a claim. The original article must be opened and reviewed before claims are extracted.

Feed availability, formats, rate limits and terms can change. A failed feed is reported without silently substituting an unapproved source. Discovery is best-effort and the workflow can still complete when one configured feed is unavailable.

## Stage 4A: source retrieval and claim-candidate extraction

QuantaTale fetches a limited number of discovered article pages from their registered publisher domains and extracts sentence-shaped claim candidates from article paragraphs. Each candidate retains its original source passage, publisher ID, original and final URL, page title and extraction timestamp.

Run it after Stage 3 discovery:

```bash
quantatale research-candidates build/discovery-candidates.json --limit 10 --output build/research-candidates.json
```

The implementation uses deterministic Python standard-library parsing and requires no AI API, paid search service or additional package. It applies a page-size limit, checks publisher domains and rejects redirects outside the registered publisher domains. CI uploads the report with the other research artifacts.

**Important:** extracted sentences are unreviewed candidates, not verified claims. Extraction does not establish truth, source relevance, support, corroboration or contradiction. Human review of the original source remains mandatory. Stage 4B adds a separate, heuristic evidence-discovery and review-dossier workflow.

## Current limits

- Topic discovery is currently feed-based, not a general-purpose search engine.
- Feed metadata is only a lead; it is not evidence verification.
- Extracted claim candidates still require source review and structured evidence assessment.
- Feed-based evidence dossiers, heuristic possible-difference flags, Crossref/Europe PMC metadata discovery and bounded Europe PMC open-access passage retrieval are implemented. None establishes corroboration or verifies claims.
- Automatic narration, voice generation, animation and MP4 rendering have not yet been implemented.

## Development roadmap

- [x] Establish repository foundation and cloud CI.
- [x] Define and validate the first topic specification.
- [x] Add a curated publisher registry and evidence-assessment workflow.
- [x] Add curated RSS/Atom topic discovery and candidate collection.
- [x] Retrieve source pages and extract unreviewed claim candidates.
- [x] Add initial feed-based evidence discovery, source grouping and heuristic conflict-review dossiers.
- [x] Add free Crossref and Europe PMC scholarly metadata discovery; leads remain unreviewed.
- [x] Retrieve bounded Europe PMC open-access passages for human review; passages remain unreviewed.
- [ ] Expand discovery coverage and add topic scoring/diversity controls.
- [ ] Generate narration scripts and scene plans.
- [ ] Add fully cloud-runnable, open-source text-to-speech.
- [ ] Build reusable code-generated 2D animation components.
- [ ] Add procedural 3D holographic-style scenes.
- [ ] Assemble audio, animation and captions with FFmpeg.
- [ ] Add render profiles, quality gates and artifact exports.
- [ ] Add optional publishing integrations only if they remain free and do not become core dependencies.

## License

A project license will be selected and added before public code reuse is encouraged. Individual dependencies and downloaded voice models may have separate licenses; QuantaTale must record and respect them.


## Stage 4B: independent-feed evidence discovery and review dossiers

The first Stage 4B increment searches the configured public RSS/Atom feeds for articles whose titles or descriptions overlap with Stage 4A claim candidates. It retrieves a bounded number of matching pages from registered publisher domains, extracts additional unreviewed passages, groups records by the registry's publisher independence group, and flags possible wording/polarity or numerical differences.

Run it after Stage 4A:

```bash
quantatale evidence-dossier build/research-candidates.json --feed-limit 100 --article-limit 20 --output build/evidence-dossiers.json
```

The output is `build/evidence-dossiers.json`. CI includes this report in the seven-day research artifact.

**Important limitations:** feed discovery searches configured feeds, not the entire web. Matching uses deterministic keyword overlap and can miss relevant evidence or retrieve false matches. Independence groups are registry metadata, not proof of institutional independence. Difference flags are heuristic review signals, not confirmed contradictions. Human reviewers must compare full passages, dates, methods, definitions and units. Every dossier remains blocked from publication pending editorial review.

### Stage 4B-2: free scholarly metadata discovery

QuantaTale also searches the public Crossref REST API and Europe PMC REST API for bibliographic records related to Stage 4A candidates. Both services expose public metadata endpoints without a mandatory paid API subscription. Crossref records metadata deposited by its members; Europe PMC indexes biomedical and life-sciences publications. See the [Crossref REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) and [Europe PMC REST API documentation](https://dev.europepmc.org/RestfulWebService).

Run the search:

```bash
quantatale scholarly-discover build/research-candidates.json --claim-limit 20 --results-per-provider 5 --output build/scholarly-leads.json
```

The output contains metadata leads, DOI/PMID/PMCID identifiers when available, dates, journal metadata, API provenance and provider errors. Metadata leads are not source passages, verified publishers, supporting evidence or corroboration. Publisher identity and the original full text must be checked before a record can enter an evidence dossier. API failures are recorded per provider and do not discard successful results from the other provider.


### Stage 4B-3: bounded open-access full-text passage retrieval

QuantaTale can now retrieve full-text XML from Europe PMC for scholarly metadata leads that include a valid PMCID and are explicitly marked open access by Europe PMC. The retrieval stage is bounded by article count, response size, timeout and passage count. It extracts abstract/body paragraphs with section context while skipping reference lists and common non-evidence sections. Invalid PMCID values are never inserted into request URLs; XML document/entity declarations are rejected.

Run it after Stage 4B-2:

```bash
quantatale scholarly-retrieve build/scholarly-leads.json --article-limit 20 --passages-per-article 40 --output build/scholarly-passages.json
```

The output is `build/scholarly-passages.json` and is uploaded with the other CI research reports. Provider errors are recorded per article without discarding successful retrievals. Records without a PMCID or without an explicit open-access flag are skipped.

**Important limitations:** Europe PMC's open-access metadata flag is not a substitute for checking the article's actual license and reuse terms. The API provider is not necessarily the publisher. Extracted passages remain unreviewed; source attribution, license, methods, relevance, context and claim support require human verification. No passage is counted as corroboration, automatically assigned as supporting or opposing evidence, or approved for narration. Full-text retrieval is limited to the Europe PMC open-access collection; Crossref metadata alone does not grant full-text access.


### Stage 4B-4: claim-to-passage evidence comparison

QuantaTale now compares the collected Stage 4B-3 scholarly passages and Stage 4B feed-dossier passages against their assigned Stage 4A claim candidates. It records lexical relevance, possible polarity differences, qualifying language, numeric mentions with surrounding context, source identifiers and registry independence-group metadata.

Run the comparison after the previous research stages:

```bash
quantatale evidence-compare build/research-candidates.json --scholarly build/scholarly-passages.json --dossiers build/evidence-dossiers.json --passage-limit-per-claim 100 --output build/evidence-comparisons.json
```

The scholarly and dossier reports are optional inputs; without them, the command still emits a blocked review report for each candidate. The CI workflow runs this comparison and includes `evidence-comparisons.json` in the research artifact.

**Important limitations:** relation labels such as `possible_support_signal` and `possible_opposition_signal` are deterministic text signals, not judgments that a source supports or refutes a claim. Negation detection is incomplete and lexical overlap can be misleading. Numeric differences preserve nearby context, but matching units do not make values comparable: reviewers must check dates, populations, definitions, methods, precision and measurement context. Scholarly metadata providers are not assumed to be publishers. Only publisher group metadata from the curated registry is reported, and it is not proof of independence. All comparisons remain unreviewed and publication-blocked.


## Sample video rendering

QuantaTale includes an optional, cloud-runnable procedural short-video renderer. The first demonstration explains why the sky appears blue. It uses original Python/Pillow motion graphics, Kokoro-82M narration, FFmpeg encoding and burned-in captions; it does not use stock footage, paid APIs or external generation services. The animation is organized as three distinct explanatory shots, with moving light particles, animated scattering rays, expanding wavefronts and visibly changing scene emphasis. Kokoro runs on CPU-only GitHub-hosted runners; its open model files are cached between workflow runs when GitHub cache is available.

The sample is a **9:16 vertical video at 720×1280 and 24 fps**. Its script references NASA Space Place and NOAA. The renderer also creates a WAV narration track, SRT captions, thumbnail and machine-readable metadata. Every sample is explicitly marked `sample_not_approved_for_publication`; the demo does not bypass the human editorial gate.

### Run in GitHub Actions

Open **Actions → Render QuantaTale sample video → Run workflow**. The workflow installs the free Ubuntu packages `ffmpeg`, `espeak-ng` (phonemization only) and `fonts-dejavu-core`, installs CPU-only PyTorch, Kokoro and the optional Pillow extra, renders the video, verifies the MP4 with `ffprobe`, and uploads the output as a downloadable workflow artifact.

### Optional command

On a compatible Linux runner with the listed system tools installed:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ".[render,tts]"
quantatale render-sample examples/videos/why-the-sky-is-blue.json --output-dir build/sample-video
```

Rendering requires FFmpeg/ffprobe, eSpeak NG for Kokoro phonemization, DejaVu fonts, Pillow, CPU PyTorch and Kokoro model weights. Kokoro's model and weights are open-weight and Apache-2.0 licensed. GitHub Actions cache availability is not guaranteed. The core research installation remains dependency-free; Pillow is an optional extra. GitHub-hosted runner time, CPU, artifact storage and retention remain subject to GitHub's current limits.

The first renderer is a vertical proof of the production pipeline, not yet the complete hybrid 2D/3D animation system. Horizontal 16:9 rendering, richer scene planning, advanced motion design and audio mixing remain future upgrades.


## Buffer publishing integration (draft-only test)

QuantaTale includes a manually triggered integration check that renders the sample video, uploads it to Cloudinary, verifies that the resulting HTTPS video URL is publicly reachable, and creates a **Buffer draft** for the selected connected channel(s). It does not schedule or publish posts. YouTube drafts are explicitly marked private and use the Education category by default (category ID 27); the optional repository variable `BUFFER_YOUTUBE_CATEGORY_ID` can override that category.

Configure these GitHub Actions secrets in **Settings → Secrets and variables → Actions**:

- `BUFFER_API_KEY`
- `BUFFER_YOUTUBE_CHANNEL_ID`
- `BUFFER_TIKTOK_CHANNEL_ID`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Optionally configure the repository variable `BUFFER_YOUTUBE_CATEGORY_ID`. The integration never prints secret values. Do not put credentials in workflow files, source code, issue comments or chat messages.

To run the test, open **Actions → QuantaTale Buffer draft integration test → Run workflow**, choose `both`, `youtube` or `tiktok`, and start the run. Check the job output for a successful draft ID and then inspect the corresponding draft in Buffer. A successful run proves that the selected channel accepted a video draft; it does not prove that the social network will accept or publish every future video. Publishing remains disabled until the editorial approval and scheduling workflow is separately implemented and tested.

Buffer requires video media to be hosted at a direct, public, stable HTTPS URL. The Cloudinary delivery URL is public so Buffer can retrieve it; never use an expiring signed delivery URL. The sample's draft description is explicitly marked as an integration test. Re-running the workflow creates new drafts and new Cloudinary assets; remove test drafts in Buffer when finished.

The workflow uses the current Buffer GraphQL API and Cloudinary's signed server-side upload SDK. See the [Buffer video-post example](https://developers.buffer.com/examples/create-video-post.html), [Buffer draft-post example](https://developers.buffer.com/examples/create-draft-post.html), [Buffer media-hosting requirements](https://developers.buffer.com/guides/hosting-media.html), and [Cloudinary Upload API](https://cloudinary.com/documentation/upload_images).


## Global audiovisual production standards

Every topic and production workflow follows the shared [visual and narration standards](docs/visual-production-standards.md). The renderer enforces the Kokoro voice policy (default `af_heart`; eSpeak is phonemization-only) and records the shared standards in render metadata. New storyboards must map every important narration beat to a scientifically accurate, animated holographic visual. A topic must never inherit another topic's storyboard. Automated checks and human editorial approval are required before public release.

## Public-interest gate

Pipeline stage 5 ranks topics by likely public interest (`src/factflow/topic_interest.py`): curiosity hook, everyday relevance, visual explainability and concreteness, scored 0-100 with recorded reasons. It is a free, deterministic heuristic and never replaces evidence gates.

- Each registered spec stores `interest_score` and `interest_reasons` in `production/topic-library.json`; `quantatale score-library` rescores existing specs.
- Slots pick the highest-scoring unused topic (least recently used breaks ties).
- Topics below `DEFAULT_MIN_INTEREST` (40) are never posted: the slot is skipped rather than filled with low-appeal content, and they are excluded from the low-stock alert count.
- Administrative or personnel discovery leads (appointments, webinars, budgets, meetings) are not added to the leads list.
- The score is a heuristic, not audience data. Tune the threshold once real watch-time results exist.

## Low-poly diorama style (`lowpoly_diorama_v1`)

An opt-in visual profile: flat-shaded low-poly miniature dioramas on a swaying platform, muted palette, cool twilight lighting with a faint cyan edge glow, gentle pop-in animation, drawn entirely with Pillow (`lowpoly.py` primitives, `lowpoly_scenes.py` motifs). Set `"visual_profile": "lowpoly_diorama_v1"` in a spec and use scene motifs `lp_sky_scatter`, `lp_water_cycle`, `lp_volcano`, `lp_seasons` or `lp_plates`; unknown motifs fall back to a generic village. The holographic profile is unchanged and remains the default for authored topics.
