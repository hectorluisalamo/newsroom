# PRD 001: Core Data Models (Pydantic)

## Goal

Define all eight core Pydantic models specified in the Blueprint (§ Phase 1)
inside `src/newsroom/models.py`. These models form the shared vocabulary for
every pipeline stage. This PRD delivers purely declarative data classes — no
ingestion, clustering, ranking, or business logic of any kind.

## User Stories

- As a pipeline module author, I can import a well-typed `FeedItem` and know
  every field, its type, and its constraints without reading the Blueprint.
- As a test author, I can instantiate any model with example data and
  assert round-trip serialization (model → JSON → model).
- As a downstream consumer, I can trust that `Pitch.source_urls` always
  contains 3–10 URLs and that all datetimes are UTC-aware, because the
  models enforce these invariants at construction time.

## Non-Goals

- No RSS fetching, parsing, or normalization logic.
- No clustering, ranking, or pitch-generation logic.
- No CLI changes (current stubs remain as-is).
- No config loading or settings changes.
- No `LLMResponse` model (already lives in `src/newsroom/draft/provider.py`).
- No business-logic methods on models (ADR-004: purely declarative).

## Constraints

- Pydantic version: v2.x (required). Validators must use `@field_validator` /
  `@model_validator` syntax. Serialization uses `.model_dump_json()` /
  `.model_validate_json()`.
- All models in a single file: `src/newsroom/models.py` (ADR-004).
- No new dependencies — Pydantic is already in `pyproject.toml`.
- All `datetime` fields must be UTC-aware (ADR-007). Implement a single
  reusable validator function applied to all datetime fields (no duplicated
  logic).
- All `HttpUrl` fields use `pydantic.HttpUrl`.
- `item_id` = SHA-256 of canonical URL (generation is caller's responsibility;
  model stores the string).
- `cluster_id` = SHA-256 of sorted `item_ids` (same: caller generates, model
  stores).
- `Draft.word_count` is informational only; no validation is enforced at the
  model layer. Word-count policy belongs to editorial/QA checks, not data
  models.
- No `TODO`, `FIXME`, or temporal comments.
- Preserve existing ABOUTME header and module docstring in `models.py`.

## Sources & Data

- Model specifications: `docs/BLUEPRINT.md` §§ Phase 1, Data Models.
- Design decisions: `docs/decisions.md` ADR-004, ADR-007, ADR-008.
- No config file changes, no fixture updates, no new output artifacts.

## Models to Implement

### 1. FeedItem
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `item_id` | `str` | SHA-256 hex string |
| `title` | `str` | — |
| `url` | `HttpUrl` | — |
| `source_name` | `str` | — |
| `source_feed_url` | `HttpUrl` | — |
| `published_at` | `datetime` | UTC-aware (validated) |
| `summary` | `str` | max 500 chars |
| `raw_tags` | `list[str]` | `[]` |
| `beat` | `str` | — |

### 2. BriefCluster
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `cluster_id` | `str` | SHA-256 hex string |
| `label` | `str` | — |
| `items` | `list[FeedItem]` | — |
| `centroid_keywords` | `list[str]` | top 5 TF-IDF terms |
| `recency_score` | `float` | 0.0–1.0 (validated) |
| `source_diversity` | `int` | count of unique sources |
| `size` | `int` | number of items |

### 3. BriefPack
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `beat` | `str` | — |
| `date` | `date` | — |
| `since` | `str` | e.g. `"48h"` |
| `total_items_ingested` | `int` | — |
| `total_items_after_dedupe` | `int` | — |
| `clusters` | `list[BriefCluster]` | ranked |
| `generated_at` | `datetime` | UTC-aware (validated) |

### 4. Pitch
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `pitch_id` | `str` | `{beat}-{date}-{index}` |
| `title` | `str` | — |
| `thesis_angle` | `str` | 1–2 sentences |
| `why_now` | `str` | 1–2 sentences |
| `key_points` | `list[str]` | 3–5 bullets |
| `source_urls` | `list[HttpUrl]` | min 3, max 10 (validator) |
| `risk_flags` | `list[str]` | — |
| `cluster_id` | `str` | ref to BriefCluster |
| `angle` | `str` | angle template name |

### 5. PitchSet
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `beat` | `str` | — |
| `date` | `date` | — |
| `pitches` | `list[Pitch]` | exactly 3 (validated) |
| `brief_pack_ref` | `str` | path to brief.json |
| `generated_at` | `datetime` | UTC-aware (validated) |

### 6. Draft
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `beat` | `str` | — |
| `date` | `date` | — |
| `pitch_id` | `str` | ref to Pitch |
| `title` | `str` | — |
| `body_md` | `str` | ~700 words, `[src:N]` markers |
| `word_count` | `int` | informational; no validation |
| `sources` | `list[HttpUrl]` | ordered, matches `[src:N]` |
| `guidance_used` | `str` | writer guidance/prompt |
| `model_id` | `str` | LLM model ID |
| `generated_at` | `datetime` | UTC-aware (validated) |
| `token_usage` | `dict[str, int] \| None` | `None` default |

### 7. QAFinding
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `check_name` | `str` | — |
| `severity` | `Literal["error", "warning", "info"]` | — |
| `location` | `str` | paragraph / line range |
| `message` | `str` | human-readable |
| `details` | `dict[str, Any]` | `{}` default |

### 8. QAReport
| Field | Type | Default / Constraint |
|-------|------|----------------------|
| `beat` | `str` | — |
| `date` | `date` | — |
| `pitch_id` | `str` | ref to Pitch |
| `passed` | `bool` | `True` iff no error-severity findings |
| `findings` | `list[QAFinding]` | — |
| `checks_run` | `list[str]` | names of checks executed |
| `generated_at` | `datetime` | UTC-aware (validated) |

## Validators to Implement

1. **UTC-aware datetime** — implement a single reusable validator function;
   apply it to all `datetime` fields across all models. Reject naive
   datetimes with a clear error message.
2. **Pitch.source_urls** — min length 3; if `len > 10`, truncate to the
   first 10 in original order without raising.
3. **PitchSet.pitches** — exactly 3 items.
4. **BriefCluster.recency_score** — `0.0 <= value <= 1.0`.
5. **FeedItem.summary** — max 500 characters.

## Acceptance Criteria

1. `from newsroom.models import FeedItem, BriefCluster, BriefPack, Pitch, PitchSet, Draft, QAFinding, QAReport` succeeds.
2. Each model can be instantiated with valid example data without error.
3. Each model round-trips through `.model_dump_json()` → `Model.model_validate_json()`.
4. `FeedItem` rejects a naive (non-UTC-aware) `published_at`.
5. `FeedItem` rejects a `summary` longer than 500 characters.
6. `Pitch` with fewer than 3 `source_urls` raises `ValidationError`.
7. `Pitch` with more than 10 `source_urls` truncates to the first 10 in original order without raising.
8. `PitchSet` with ≠ 3 pitches raises `ValidationError`.
9. `BriefCluster` with `recency_score` outside 0.0–1.0 raises `ValidationError`.
10. All `datetime` fields across all models reject naive datetimes.
11. `QAFinding.severity` rejects values outside `{"error", "warning", "info"}`.
12. `tests/unit/test_models.py` replaces the placeholder with real tests covering criteria 1–11.
13. `bash scripts/verify.sh` passes (lint + format + tests).

## Definition of Done

- `scripts/verify.sh` passes.
- `tests/unit/test_models.py` covers all acceptance criteria above.
- No unrelated changes to other modules.
- No business logic in `models.py`.
- Existing ABOUTME header and module docstring preserved.
