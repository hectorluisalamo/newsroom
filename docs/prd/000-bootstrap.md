# PRD: Project Bootstrap — Newsroom CLI

> **Historical note:** References to `newsroom-config`, `sync_private_config.sh`, and BLUEPRINT.md in this PRD are historical. The private config repo and speckit governance were removed per ADR-012.

**PRD ID**: `000-bootstrap`
**Phase**: 0

## Goal

Scaffold the Newsroom CLI repository (public, open-core) so that every subsequent PRD can begin from a consistent, verified foundation. This PRD creates the directory structure, tooling configuration, verification scripts, repo-local rules, placeholder modules (signatures and docstrings only), example config files, fixture stubs, and documentation skeletons defined in BLUEPRINT.md Phase 0.

The repository follows an open-core model: example configs are committed under `config.example/`, while runtime configs under `config/` are gitignored and generated locally via `scripts/init_config.sh`. A companion private repo (`newsroom-config`) holds production configs; it is not required and must not be referenced as a dependency.

No feature logic, business logic, network calls, or LLM usage is introduced.

## User Stories

- As a developer, I can clone the repo, run `uv sync` and `scripts/init_config.sh`, and have a working Python 3.12 environment with all dependencies installed and example config in place.
- As a developer, I can run `scripts/verify.sh` and see it pass cleanly (lint, format check, and test suite all green).
- As a developer, I can run `python -m newsroom --help` and see the CLI entry point with subcommand stubs.
- As a developer, I can read any module under `src/newsroom/` and find function signatures with docstrings that describe the module's future responsibility.
- As a developer, I can find all project governance documents (`CLAUDE.md`, `docs/decisions.md`, `docs/architecture.md`, `docs/agent-notes.md`, `docs/prd/prd-template.md`) in their canonical locations.
- As a developer, I can review `config.example/sources.yaml`, `config.example/qa.yaml`, `config.example/cluster.yaml`, and `config.example/voices/science_tech.md` with the content specified in BLUEPRINT.md.
- As a developer with access to the private config repo, I can overlay production config into `config/` via `scripts/sync_private_config.sh`.

## Non-Goals

- **No pipeline logic.** No RSS fetching, HTTP calls, or feed parsing beyond stub signatures.
- **No RSS ingestion.** `ingestion/rss.py` contains only function signatures and docstrings.
- **No clustering.** `cluster/tfidf.py` contains only the class skeleton implementing the `Clusterer` protocol with `NotImplementedError`.
- **No pitch generation.** `pitches/pitches.py` and `pitches/angles.py` contain only signatures.
- **No draft generation.** `draft/writer.py`, `draft/provider.py`, and `draft/anthropic_provider.py` contain only signatures and ABCs.
- **No QA check logic.** `qa/checks.py` contains only function signatures.
- **No LLM usage of any kind.**
- **No network calls of any kind.**
- **No Pydantic model field definitions** beyond what is needed for imports to resolve. (Models are Phase 1.)
- **No requirement that the private repo (`newsroom-config`) exists.** No git submodules, no automation that clones repos, no code that depends on private config fields beyond what's in example configs.

## Constraints

- **Stack**: Python 3.12+, uv, Ruff, pytest. All runtime and dev dependencies per BLUEPRINT.md § Dependencies.
- **Package name**: `newsroom` (under `src/newsroom/`). The repo directory name (`crash_log`) is irrelevant to the package.
- **Open-core config boundary**:
  - Example config files live under `config.example/` and are committed to the public repo.
  - Runtime config lives under `config/` and is gitignored. The entire `config/` directory is ignored.
  - `scripts/init_config.sh` copies `config.example/` into `config/` for local dev and demo runs.
  - `scripts/sync_private_config.sh` optionally overlays private config from a sibling repo path if present; exits nonzero with a friendly message if the private repo is not found.
  - No code may depend on config fields that exist only in the private repo and not in example configs.
- **ABOUTME header**: Every new Python file must begin with a two-line comment, each line prefixed with `ABOUTME: `, describing what the file does. This rule is defined in the global `~/.claude/CLAUDE.md` and must also be captured in the repo-local `CLAUDE.md` created by this PRD.
- **Stub modules**: Every `.py` file listed in BLUEPRINT.md Phase 0 § Directory Structure must exist. Each stub must contain:
  - The `ABOUTME:` two-line header comment.
  - Function/class signatures matching BLUEPRINT.md exactly.
  - Docstrings describing the function's responsibility.
  - `raise NotImplementedError` or `pass` as the body. No real logic.
- **Config example files**: `config.example/sources.yaml`, `config.example/qa.yaml`, `config.example/cluster.yaml`, and `config.example/voices/science_tech.md` must contain the exact content specified in BLUEPRINT.md §§ Phase 2.
- **Verification scripts**: `scripts/verify.sh` and `scripts/verify_content.sh` must exist. `verify.sh` must be runnable and pass. `verify_content.sh` must be a placeholder that prints a clear message explaining it is a placeholder (e.g., `echo "verify_content.sh is a placeholder; content verification begins in Phase 7"`) and exits 0. It must not be silently empty.
- **`.env.example`**: Must contain `ANTHROPIC_API_KEY=`, `NEWSROOM_MODEL=claude-sonnet-4-20250514`, `NEWSROOM_NOW=`.
- **`.python-version`**: Must contain `3.12`.
- **`.gitignore`**: Must cover `out/`, `.env`, `.env.*`, `__pycache__/`, `.ruff_cache/`, `*.egg-info/`, `.venv/`, `dist/`, and the entire `config/` directory.
- **No temporal or aspirational comments.** No comments referring to temporal context (e.g., "new", "recently added", "will be implemented later"). No `TODO`, `FIXME`, or `HACK` comments. Comments must be evergreen and describe the code as it is.
- **No dependencies beyond those listed in BLUEPRINT.md § Dependencies.**
- **Never commit `config/` or `.env`.** Only `config.example/` is committed. This must be documented as a repo-local rule in `CLAUDE.md`.

## Sources & Data

- **Source list**: `config.example/sources.yaml` — content per BLUEPRINT.md § Phase 2 (`science_tech` beat with 5 RSS feeds: Ars Technica, MIT Technology Review, Nature News, Hacker News Best, The Verge). No feeds are added or removed by this PRD.
- **Fixture stubs**: `fixtures/science_tech/` directory must exist with empty placeholder files: `sample_feed.xml`, `sample_feed_2.xml`, `expected_brief.json`, `sample_draft_text.md`. These files may be empty or contain minimal valid structure (e.g., empty XML root, empty JSON object). Fixture content will be populated by subsequent PRDs.
- **Caching assumptions**: None. No caching is introduced.
- **Expected output artifacts**: No runtime output artifacts. The `out/` directory is gitignored and created at runtime by future phases.

## Acceptance Criteria

1. `uv sync` completes without errors on a clean checkout.
2. `scripts/verify.sh` exits 0: Ruff lint passes, Ruff format check passes, `pytest tests/ -v` passes (with at least one test in `tests/` that asserts the package is importable).
3. `python -m newsroom --help` exits 0 and prints usage text showing `pitch`, `draft`, and `qa` subcommands. Invoking subcommands without required arguments may error; only `--help` behavior is required.
4. Every Python file listed in BLUEPRINT.md Phase 0 § Directory Structure exists under `src/newsroom/` and is importable without error.
5. Every Python file under `src/newsroom/` starts with a two-line `ABOUTME:` comment.
6. Every public function/class signature listed in BLUEPRINT.md for the corresponding module exists as a stub with a docstring.
7. `config.example/sources.yaml` is valid YAML and contains 5 RSS feed entries under `science_tech.rss`.
8. `config.example/qa.yaml` is valid YAML and contains `hedging`, `source_attribution`, and `voice_drift` sections.
9. `config.example/cluster.yaml` is valid YAML and contains `tfidf`, `clustering`, and `keywords` sections.
10. `config.example/voices/science_tech.md` exists and contains `## Beliefs`, `## Tone`, `## Forbidden Moves`, `## Taboo Phrases`, and `## Required Habits` sections.
11. `docs/decisions.md` exists and contains the 10 resolved design decisions from BLUEPRINT.md.
12. `docs/architecture.md` exists (may be a skeleton with section headers).
13. `docs/agent-notes.md` exists (may be initialized with a single entry noting Phase 0 bootstrap).
14. `docs/prd/prd-template.md` exists and contains the canonical PRD template from AGENTIC_DEV_PLAYBOOK.md § 2.
15. `.env.example`, `.python-version`, `.gitignore` exist with content per Constraints above.
16. `fixtures/science_tech/` directory exists with the four placeholder files.
17. No module under `src/newsroom/` contains implemented business logic (no real parsing, no HTTP calls, no clustering math, no LLM calls). All function bodies are `raise NotImplementedError`, `pass`, or trivially return placeholder values needed only for CLI `--help` to work.
18. `pyproject.toml` declares all runtime and dev dependencies listed in BLUEPRINT.md § Dependencies.
19. No `TODO`, `FIXME`, or `HACK` comments exist anywhere in the codebase.
20. `scripts/verify_content.sh` prints a human-readable placeholder message and exits 0 (not silently empty).
21. `scripts/init_config.sh` copies `config.example/` into `config/`, is idempotent (skips if `config/` already has content), and does not modify `config.example/`.
22. `scripts/sync_private_config.sh` overlays config from a sibling `newsroom-config` repo path if present, and exits nonzero with a friendly message if the path does not exist.
23. `config/` contents are gitignored. `git status` shows no tracked files under `config/` after running `scripts/init_config.sh`.
24. `README.md` contains a section explaining the open-core config model, how to initialize example config, and how to overlay private config.

## Definition of Done

- [ ] `scripts/verify.sh` passes with exit code 0.
- [ ] All 24 Acceptance Criteria above are met.
- [ ] No unrelated changes (this commit contains only Phase 0 scaffolding).
- [ ] `docs/agent-notes.md` updated with Phase 0 completion note.
- [ ] Single commit with message referencing PRD `000-bootstrap`.
