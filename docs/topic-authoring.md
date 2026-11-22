# Automated topic authoring

QuantaTale writes its own new topics. No human approval step is involved; topics are accepted or discarded by automated gates.

## Pipeline (daily 01:30 UTC, or manual dispatch)
1. A language model proposes evergreen questions and candidate pages on registered publisher domains (`data/source_registry.json`).
2. Each page is fetched; unregistered, unreachable or too-short pages are dropped. At least **two independent publishers** must load.
3. The model writes a title, description, scene plan and a **script in its own words**, using only the fetched passages.
4. Automated gates (any failure discards the topic; it is never published):
   - every narration sentence cites a **verbatim quote** found in a fetched page (one opening question may be uncited);
   - every number in a sentence appears in its quote;
   - the script shares no run of 8 or more consecutive words with any source;
   - a second model pass must mark each sentence supported and report no conflicts;
   - a clickable title (20-70 characters, not a duplicate), a non-empty description, 60-170 words, 3-5 scenes.
5. Accepted specs are written to `production/specs/` and registered in the library with `passage_checked_supports_claim` and `review_method: automated_quote_grounding_and_model_entailment`.

These checks are automated and are **not complete fact verification**. Each spec says so in `source_assessment`.

## Free providers (tried in order)
1. **Groq** (`GROQ_API_KEY`)
2. **OVHcloud AI Endpoints** (anonymous, no key; very low rate limit)
3. **Cloudflare Workers AI** (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`)

A provider that is missing credentials, rate limited, down or returns unusable output is skipped. Free tiers, model names and endpoints can change; override with `GROQ_MODEL`, `GROQ_URL`, `OVH_MODEL`, `OVH_URL`, `CLOUDFLARE_MODEL`, `CLOUDFLARE_URL`. Limits apply per account or organization, not per key. Only public source text is sent. A local open-source model fallback is not implemented yet.

## Stock alert
After each run `quantatale topic-stock` counts never-used publishable topics. Fewer than 4 opens (once) the GitHub issue "QuantaTale topic stock is low". The authoring job fails visibly when every provider fails.

## Scene motifs

Each scene may carry a `motif` naming a small procedural animation in `src/factflow/visual_motifs.py`
(for example `evaporation`, `rising_cooling`, `moon_phases`, `plates_timelapse`). The renderer draws the
motif for the scene being narrated so the picture shows what the words say. Authored topics pick a motif
from that list; an unknown or missing motif (`none`) falls back to the generic description card.
Add a new motif by writing a draw function and registering it in `MOTIFS`; tests check every spec uses a valid one.

## Drafts written from an assistant session

Topics can also be added by committing a draft JSON (same fields as a model draft plus `source_urls`) to
`production/drafts/`. The workflow fetches the pages, requires a verbatim quote per sentence, no copied runs,
two independent publishers and a passing independent model check; then it turns the draft into a spec.
Rejected drafts move to `production/drafts/rejected/` with their reasons. If no provider can run the check,
the draft stays for the next run.

## Reading the exact page text

Run the "source page probe" workflow with space-separated page URLs. It prints, per page, the paragraphs the
evidence gates would see, or why the page could not be fetched (for example Britannica answers HTTP 403).
Quotes in drafts must be copied from that text.

## Every scene must be a 3D holographic figure

New topics, whether written by the automatic writer or in an assistant session, may only use motifs in
`HOLOGRAPHIC_3D` (`visual_motifs.py`). `check_shape` rejects a scene whose motif is flat, missing (`none`)
or unknown, and the writer is told to answer `request: <the 3D animation that is needed>` when nothing
listed fits, so a poor match is never used. A rejected draft stays visible in the run log with the reason,
which is the work queue for the next 3D motif. `quantatale motif-report` (also run in CI) counts 3D vs flat
motifs and lists the flat ones still used by existing topics, most-used first, so they can be converted.

To add a 3D motif: put the function in `visual_motifs_3d.py` (or name it `*_3d`), add it to `MOTIFS_3D`,
render a frame to check it, and make sure its on-screen text states only what the sources support.

## Numbers only when comparing

Narration does not state standalone numerical facts (a measurement, count, percentage or fraction). A number is used only when
the sentence compares two or more situations, for example the speed of light versus the speed of sound, or how long the first
10 cm of sea level rise took versus the next 10 cm. Years of events are fine. Otherwise the idea is said in words ("almost all",
"far larger").

`check_shape` enforces this with a heuristic (`lone_number_sentences`): a sentence with a number and no comparison word is
rejected, and the writer prompt states the rule. The heuristic cannot judge intent, so review borderline cases.
`python -m factflow.cli number-report` lists the sentences in existing topics that break the rule.

## Plain language for everyone

Videos are for the general public, not only scientists. The tone is warm, friendly and curious, with everyday words and short
sentences. A technical term is allowed only when it is explained in plain words straight away.

`check_shape` rejects sentences over 26 words and words of 14 or more letters (`hard_to_follow`), and the writer prompt asks for
plain language. `python -m factflow.cli language-report` lists existing sentences that fail.
