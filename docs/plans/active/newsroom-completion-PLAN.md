# Newsroom Completion Plan

**Status:** Active — multi-night build. This is a self-contained living doc; a cold
session should be able to resume from this file alone (plus `CLAUDE.md`,
`docs/architecture.md`, `docs/decisions.md`).

**Guardrails for every night:** $0 / no paid API calls. The pitch step is fully
deterministic (no LLM). The draft step (future night) must use a **mocked**
LLM provider in tests — never a live paid call. Tests run under a **NO-NETWORK**
policy (`tests/conftest.py` monkeypatches `socket.socket` to raise). Never
commit `config/` or `.env` — only `config.example/` is committed
(open-core boundary, enforced by `.gitignore`).

---

## 1. Gap analysis (Night 1 — verified by direct re-run, not trusted from prior recon)

**Correction to the incoming recon:** the recon this plan started from stated that
"underlying modules EXIST and are unit-tested... READ THEM to learn each
signature" and that only `commands.py` needed wiring. That was **wrong**. Direct
inspection on Night 1 found:

- Every module listed as "already unit-tested" — `dedupe/dedupe.py`,
  `normalize/normalize.py`, `cluster/tfidf.py`, `rank/rank.py`,
  `pitches/pitches.py`, `pitches/angles.py` (partially), `render/render.py`,
  `ingestion/rss.py`, `utils/text.py`, `utils/time_utils.py`,
  `logging_config.py`, `qa/checks.py`, `draft/writer.py` — contained **only**
  `raise NotImplementedError` stub bodies.
- Their corresponding "unit tests" — `tests/unit/test_dedupe.py`,
  `test_normalize.py`, `test_cluster.py`, `test_rank.py`, `test_pitches.py`,
  `test_render.py`, `test_time_utils.py`, `test_qa.py` — were **all**
  `TestXPlaceholder.test_placeholder` doing `pass`. They contributed to the
  "120 passed" count but validated nothing about pipeline behavior.
- `tests/integration/test_pitch_pipeline.py` and `test_draft_pipeline.py` were
  also single-test placeholders.
- `fixtures/science_tech/sample_feed.xml` / `sample_feed_2.xml` had a
  `<channel>` with **zero** `<item>` entries; `expected_brief.json` was `{}`.
- Root cause, confirmed by reading `docs/prd/000-bootstrap.md`: this is
  **exactly as designed for PRD 000 (Phase 0 bootstrap)**. Its explicit
  Non-Goals state "No pipeline logic... No clustering... No pitch
  generation... No draft generation... No QA check logic," and Acceptance
  Criterion 17 requires "No module... contains implemented business logic."
  The repo is a **scaffold**, not a partially-wired pipeline. Only `models.py`,
  `settings.py`, `time_anchor.py`, and `cli.py` (argument parsing) had real
  logic prior to Night 1.
- Re-verified directly (not assumed) before writing any code:
  - `uv run pytest tests/ -q` → `120 passed in 0.10s` (confirmed — but see
    above: this count includes ~8 placeholder-only test files).
  - `uv run ruff check src/ tests/` and `uv run ruff format --check src/ tests/`
    → clean (confirmed).
  - `bash scripts/verify.sh` → failed with `ruff: command not found` (the venv
    isn't auto-activated; the script called bare `ruff`/`pytest`). Confirmed
    and fixed on Night 1 (see §3).
  - `python -m newsroom --now ... pitch ...` → raised `NotImplementedError`
    from `pitch_cmd` before any Night-1 code was written (confirmed).

**Practical consequence for scope:** "wire `pitch_cmd`" actually meant
implementing the full deterministic pipeline body — `utils/text.py`,
`utils/time_utils.py`, `logging_config.py`, `ingestion/rss.py` (incl. a new
local-fixture read path for `--source-override`), `normalize/normalize.py`,
`dedupe/dedupe.py`, `cluster/tfidf.py`, `rank/rank.py`, `pitches/pitches.py`,
`render/render.py` (brief + pitch renderers only), and `commands.py:pitch_cmd`
— not just orchestration glue over already-working modules. This was larger
than the incoming recon assumed, but every piece is pure, deterministic,
network-free Python with a clear spec in `docs/architecture.md` +
`docs/decisions.md` (ADR-002, ADR-003, ADR-007) + `config.example/*.yaml`, so
it was completed in one Night-1 pass rather than deferred.

**Design decisions made while implementing (recorded here since the original
stub signatures were placeholders, not locked contracts):**
- `normalize_all` gained a required `beat: str` parameter — the original stub
  signature `(entries, sources, since, now)` had no way to stamp
  `FeedItem.beat`, which is a required field. Not a breaking change: nothing
  called the old signature yet.
- `ingestion/rss.py` gained a new `fetch_local_feeds(directory: Path)` function
  (not in the original stub) to read fixture `*.xml` files directly for
  `--source-override`, keeping the real-network `fetch_feed`/`fetch_all_feeds`
  path completely separate and untouched by tests.
- `fetch_all_feeds`/`fetch_local_feeds` return a flat list of
  `(raw_entry, FeedSource)` pairs (parallel-list design), which
  `normalize_all(entries, sources, beat, since, now)` consumes by zipping.
- `commands.pitch_cmd` gained an optional `config_dir: Path | None = None`
  parameter (defaults to `Path("config")`, matching the real CLI's
  assumption that `scripts/init_config.sh` has been run locally). Tests pass
  `config_dir=config.example/` explicitly so they never depend on the
  gitignored, developer-local `config/` directory — this mirrors the existing
  convention in `tests/unit/test_settings.py` ("golden path" tests against
  `config.example/`).
- `TfidfClusterer` computes each cluster's `recency_score` internally, relative
  to the min/max `published_at` across the *input item set* (not against
  `--now`), since the `Clusterer` protocol's `cluster(items)` signature has no
  `now` parameter. This keeps clustering self-contained and deterministic.
- Pitch `angle` assignment is a fixed, deterministic rotation through
  `pitches/angles.ANGLES` (`trend_analysis`, `skeptics_take`, `human_impact`,
  ...) — not randomized — so `--now`-identical runs are byte-identical.

---

## 2. Completion roadmap (top-down, one named capability per future night)

### Night 1 (this night) — DONE, see §3 for exact scope/evidence
- Wire the deterministic pitch pipeline end-to-end: `ingest -> normalize ->
  dedupe -> cluster -> rank -> pitch -> render`.
- Populate `fixtures/science_tech/sample_feed.xml` + `sample_feed_2.xml` with
  realistic, sanitized RSS items (4 thematic clusters, 2 sources each).
- Replace the `test_pitch_pipeline.py` placeholder with real integration
  tests.
- Fix `scripts/verify.sh` to invoke `uv run ruff`/`uv run pytest` so it works
  from a clean clone without manual venv activation.

### Night 2 (proposed) — Per-module unit tests for the pitch pipeline
- The Night-1 slice is covered by integration tests only. Each pipeline module
  (`normalize`, `dedupe`, `cluster/tfidf`, `rank`, `pitches`, `render`) still
  has only a placeholder unit test. Replace each placeholder with real
  unit-level coverage of edge cases the integration test doesn't reach:
  dedupe's exact-vs-fuzzy tie-breaking, cluster's zero-feature fallback path,
  rank's normalization when all clusters tie, pitch generation's 0/1/2-cluster
  branches (the integration fixtures only exercise the >=3-cluster branch),
  render's JSON/Markdown determinism.
- No-exceptions testing policy (`~/.claude/rules/engineering.md`) calls for
  unit + integration + e2e on every project; Night 1 satisfied integration
  only for the pitch slice by explicit scope from the orchestrator's task
  spec. This is the known gap to close.

### Night 3 (proposed) — `draft_cmd` with a mocked LLM provider
- Implement `draft/writer.py` (prompt assembly: pitch + brief excerpts + voice
  constitution + editor guidance, `[src:N]` citation convention per ADR-008)
  and wire `draft/anthropic_provider.py` behind the existing `LLMProvider` ABC
  in `draft/provider.py`.
- **Tests must use a fake/mock `LLMProvider`** — construct a stub implementing
  `generate()`/`model_id` that returns canned text. Never call the real
  Anthropic API in tests or in any unattended/CI run. This keeps the $0 /
  no-paid-API-calls guardrail intact for all future nights, not just Night 1.
- Wire `draft_cmd` in `commands.py` (currently `raise NotImplementedError`).

### Night 4 (proposed) — `qa_cmd` + QA checks
- Implement `qa/checks.py` (`check_unsourced_stats`, `check_hedging`,
  `check_voice_drift`, `check_citation_integrity`, `run_all_checks`) per
  `config.example/qa.yaml` thresholds and `docs/architecture.md` §"Safety &
  Trust Constraints".
- Wire `qa_cmd` in `commands.py`.
- Add unit tests per check + an integration test running QA against
  `fixtures/science_tech/sample_draft_text.md`.

### Night 5 (proposed) — Real e2e coverage + fixture/doc truth pass
- Add a real e2e test in `tests/e2e/test_cli.py` that invokes the CLI as a
  subprocess for the full `pitch` (and, once Night 3/4 land, `draft` + `qa`)
  flow against fixtures, asserting on actual output files — not just
  `--help`.
- Populate `fixtures/science_tech/expected_brief.json` with the real expected
  brief output for the Night-1 fixtures (deferred from Night 1 by explicit
  task scope) and assert equality in a test.
- README-matches-reality pass: verify every command/flag documented in
  `README.md` actually works as described post Night 1-4.
- Fix the stale `NEWSROOM_MODEL` default in `.env.example`
  (`claude-sonnet-4-20250514`) — noted by the incoming Night-1 recon as a
  known issue, intentionally deferred since the draft step (which is the only
  consumer) isn't built until Night 3. **Research current model IDs/pricing
  before touching this** (per `~/.claude/rules/engineering.md` training-cutoff
  discipline) — do not carry forward a remembered ID without verifying it's
  still current.
- General polish: showcase output, pin/version cleanup, `verify_content.sh`
  (currently a Phase-0 placeholder per `docs/prd/000-bootstrap.md`) becoming a
  real content-verification script per `docs/architecture.md`.

---

## 3. Night 1 — Living state

**What's done (Night 1, this session):**
- Implemented (all pure Python, deterministic, no network/LLM):
  `src/newsroom/utils/text.py`, `src/newsroom/utils/time_utils.py`,
  `src/newsroom/logging_config.py`, `src/newsroom/ingestion/rss.py`
  (`fetch_feed`, `fetch_all_feeds` for real use; `fetch_local_feeds` new, for
  fixture/test use), `src/newsroom/normalize/normalize.py`,
  `src/newsroom/dedupe/dedupe.py`, `src/newsroom/cluster/tfidf.py`,
  `src/newsroom/rank/rank.py`, `src/newsroom/pitches/pitches.py`,
  `src/newsroom/render/render.py` (brief + pitch renderers; draft/report
  renderers untouched — out of scope until Night 3/4),
  `src/newsroom/commands.py::pitch_cmd`.
- Fixed `scripts/verify.sh` to call `uv run ruff` / `uv run pytest` instead of
  bare binaries.
- Populated `fixtures/science_tech/sample_feed.xml` and `sample_feed_2.xml`
  with 6 items each (12 total): 4 thematic clusters (AI chip export controls,
  quantum computing milestone, satellite constellation launch, gene-editing
  therapy trial), each theme covered by both feeds (source_diversity=2,
  size=3 per cluster), all `pubDate`s inside a `2026-01-13T14:00Z`–
  `2026-01-15T08:00Z` window so `--now 2026-01-15T12:00:00Z --since 48h`
  catches all of them. Content is generic/plausible tech-news phrasing
  invented for test purposes — not reporting on real events.
- Replaced `tests/integration/test_pitch_pipeline.py`'s placeholder with 6 real
  tests: output files written, brief pack has ingested/deduped/clustered
  counts and >=3 valid clusters, pitch set has exactly 3 pitches each with
  >=3 source URLs, determinism across repeated runs (byte-identical JSON),
  a network-call guard (monkeypatches `httpx.get` to assert it's never called
  under `--source-override`), and a zero-clusters-raises-ValueError case for
  an unreachable `--since` window.
- `expected_brief.json` deliberately **left untouched** (`{}`) — populating it
  with the real expected output is explicitly Night 5 scope per the task
  brief that started this plan.
- `tests/unit/test_*.py` placeholders for `dedupe`, `normalize`, `cluster`,
  `rank`, `pitches`, `render`, `time_utils`, `qa` **left untouched** — Night 1
  scope was the integration test only; real per-module unit tests are Night 2
  (see §2).
- `draft_cmd` and `qa_cmd` in `commands.py` still `raise NotImplementedError`
  — out of scope for Night 1 by design (deterministic pitch step only).

**Verification evidence (Night 1):**
- `rm -rf out/2026-01-15 && bash scripts/verify.sh` → **125 passed**, ruff
  check clean, ruff format check clean.
- Direct CLI run from repo root (using the real, gitignored `config/` that
  `scripts/init_config.sh` had already populated):
  `uv run python -m newsroom --now 2026-01-15T12:00:00Z --out-dir out pitch
  --beat science_tech --source-override fixtures/science_tech --since 48h`
  → exited 0, logged `Wrote brief + 3 pitches for beat=science_tech
  date=2026-01-15 to out/2026-01-15/science_tech`, no `NotImplementedError`.
  Inspected `brief.json`: 12 items ingested, 12 after dedupe (fixtures were
  deliberately built with insufficient title-Jaccard overlap to collapse),
  4 clusters (sizes 3/3/3/3, source_diversity 2/2/2/2, recency_score
  1.0/0.95/0.74/0.5). Inspected `pitches.json`: exactly 3 pitches, each with
  exactly 3 `source_urls`, distinct `angle` values (`trend_analysis`,
  `skeptics_take`, `human_impact`).

**Immediate next step:** Night 2 — replace the 8 remaining placeholder unit
test files with real coverage of each pipeline module's edge cases (see §2).

**Known issues / risks carried forward:**
1. Pitch/cluster `title`/`label` quality is weak — `BriefCluster.label`
   currently falls back to the single top TF-IDF keyword (e.g. "chip",
   "trial", "launch") rather than a fuller phrase. Functionally correct
   (drives clustering, ranking, and pitch generation correctly) but not
   polished copy. Flagged for a future polish pass, not blocking.
2. `NEWSROOM_MODEL` in `.env.example` is a stale/placeholder model ID
   (`claude-sonnet-4-20250514`) — deferred to Night 3/5 per §2, since nothing
   consumes it until the draft step exists. **Do not treat this ID as current
   when Night 3 arrives — re-verify against current Anthropic docs.**
3. `verify_content.sh` is still the Phase-0 placeholder (`echo "...
   placeholder..."; exit 0`) — real content verification is Night 5 scope.
4. `AgglomerativeClustering(metric="cosine", ...)` in `cluster/tfidf.py`
   requires scikit-learn's `metric` param name (not the older `affinity`,
   removed in modern sklearn). Verified against the installed environment
   (`scikit-learn==1.8.0`) on Night 1 — re-check if the pinned version ever
   changes.
5. `TfidfClusterer.cluster()` has an explicit fallback for the case where
   TF-IDF vectorization yields zero surviving features (e.g., a tiny corpus
   where `min_df` filters everything out): every item becomes its own
   singleton cluster rather than crashing. Not exercised by the current
   fixtures (which were sized to avoid it) — worth a dedicated unit test in
   Night 2.
