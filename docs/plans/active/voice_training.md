# Voice Training for Science/Tech Beat

## Context

Newsroom has voice infrastructure in place — a hand-written `VoiceConstitution` (qualitative editorial rules) and `VoiceDriftConfig` (hand-tuned sentence length thresholds) — but no way to learn a voice from actual writing samples. The goal is to add a `newsroom train` command that ingests a corpus of markdown writing samples, extracts stylometric features, and produces a serialized `VoiceProfile` JSON. This profile complements the existing voice constitution with empirical measurements, and feeds into QA drift checks.

The training feature is independent of the draft pipeline (which is still stubbed). No new dependencies required — scikit-learn and numpy are already present.

### ML Review Summary

Plan reviewed by ML engineer and data scientist agents. Key corrections incorporated:
- **Percentile-based thresholds** replace mean±2σ (sentence lengths are right-skewed, not normal)
- **Length-normalized TTR** replaces naive TTR (eliminates text-length bias)
- **Raw frequency counts** replace TF-IDF for n-grams (IDF is meaningless at 5-15 documents)
- **Markdown stripping** added as preprocessing step before feature extraction
- **Schema versioning** added to VoiceProfile model
- **Tiered confidence** for small corpus: N<5 report-only, N=5-10 warnings, N>10 full enforcement

## Sample Format Recommendation

**Plain markdown files, one per sample, in `config/samples/{beat}/`.**

- Markdown is the native draft output format (`Draft.body_md`)
- One file per sample = trivial corpus management
- `config/` is gitignored (open-core); `config.example/samples/` gets synthetic examples
- No metadata headers needed — beat determined by directory, no dates needed for stylometrics
- Naming: `{slug}.md` (e.g., `ai-regulation-policy.md`)
- Minimum corpus: 5 samples for meaningful stats (warn below, don't error)

---

## Phase 1: Corpus Management (Small)

**New files:**
- `src/newsroom/voice/__init__.py` — Voice training subpackage
- `src/newsroom/voice/corpus.py` — `load_corpus(beat, config_dir) -> list[str]`
- `config.example/samples/science_tech/` — 3 synthetic example samples (~500 words each)
- `tests/unit/test_corpus.py`

**Modify:**
- `src/newsroom/settings.py` — Add `load_corpus()` facade (follows `load_voice()` pattern)

**Corpus reader** (`voice/corpus.py`):
- Reads all `.md` files from `config_dir/samples/{beat}/`
- Returns list of raw text strings, sorted alphabetically (deterministic)
- Raises `ConfigError` on missing dir or no `.md` files
- Logs warning if `< min_samples` files found

**Reuse:** `settings.ConfigError`, `settings._read_yaml` pattern

## Phase 2: Feature Extraction (Medium)

**New files:**
- `src/newsroom/voice/analyze.py` — Pure stylometric functions, no I/O
- `src/newsroom/voice/profiler.py` — `build_profile(beat, texts, now) -> VoiceProfile`
- `tests/unit/test_analyze.py`
- `tests/unit/test_profiler.py`

**Modify:**
- `src/newsroom/models.py` — Add ~50 LOC (330 → ~380, under 400 limit):

```python
class SentenceStats(BaseModel):
    median: float
    p10: float
    p90: float
    p95: float
    iqr: float              # interquartile range for robust spread

class VocabularyStats(BaseModel):
    avg_word_length: float
    type_token_ratio: float       # length-normalized (truncated to min sample length)
    contraction_ratio: float

class RhetoricalStats(BaseModel):
    question_ratio: float
    exclamation_ratio: float
    passive_voice_estimate: float  # approximate, regex-based
    avg_paragraph_length: float    # median sentences per paragraph

class VoiceProfile(BaseModel):
    schema_version: str = "1.0.0"  # forward compatibility
    beat: str
    sample_count: int
    total_words: int
    sentence_stats: SentenceStats
    vocabulary: VocabularyStats
    rhetorical: RhetoricalStats
    top_unigrams: list[tuple[str, int]]   # raw count from CountVectorizer, not TF-IDF
    top_bigrams: list[tuple[str, int]]
    top_trigrams: list[tuple[str, int]]
    generated_at: datetime
```

### Preprocessing: Markdown Stripping

Before any feature extraction, strip markdown syntax from raw text:
- Remove link markup `[text](url)` → keep `text`
- Remove headers (`#`, `##`, etc.)
- Remove code blocks (fenced and inline)
- Remove image references
- Remove emphasis markers (`*`, `_`, `**`, `__`)
- Preserve paragraph breaks (double newlines)

Add `strip_markdown(text: str) -> str` to `analyze.py` (or `utils/text.py` if it fits better with existing `strip_html()`).

### V1 Feature Set (`analyze.py`):

| Feature | Method | Integration Point |
|---------|--------|-------------------|
| Sentence length distribution (median, p10, p90, p95, IQR) | Regex sentence splitter + numpy | Drift threshold derivation (percentile-based) |
| Avg word length | Whitespace tokenizer | Vocabulary complexity signal |
| Length-normalized TTR | Truncate samples to min length, then unique/total | LLM prompt hint (eliminates length bias) |
| Contraction ratio | Regex `\w+'\w+` | Formality signal |
| Question/exclamation ratios | Sentence-ending punctuation | Rhetorical pattern |
| Passive voice estimate | `was/were/been + past participle` regex (~60-70% accuracy) | Directional signal only |
| Paragraph length (median, IQR) | Double-newline split | Structural pacing |
| Top n-grams (uni/bi/tri) | `CountVectorizer` raw frequencies (no IDF) | Characteristic phrases for LLM prompt |

**Key design decisions (from ML review):**
- **Percentiles over mean±std**: Sentence lengths are right-skewed. Percentiles are distribution-agnostic and robust to outliers with small N.
- **Length-normalized TTR**: Truncate each sample to `min(len(sample_words))` before computing ratio. Eliminates the inverse correlation between TTR and text length.
- **Raw counts over TF-IDF**: With 5-15 documents, IDF has only 3-5 possible values and provides no discriminative power. `CountVectorizer` with `min_df=2` captures actual phrase habits.
- **Passive voice kept but labeled**: ~60-70% regex accuracy is acceptable for a directional estimate. Named `passive_voice_estimate` with documented limitations.

**Key functions in `analyze.py`:** `strip_markdown()`, `split_sentences()`, `split_paragraphs()`, `tokenize_words()`, `compute_sentence_stats()`, `compute_vocabulary_stats()`, `compute_rhetorical_stats()`, `compute_ngrams()`

**Reuse:** `numpy` (percentiles), `sklearn.feature_extraction.text.CountVectorizer`, existing `utils/text.py` patterns

## Phase 3: CLI + Persistence (Medium)

**New files:**
- `src/newsroom/voice/persistence.py` — `save_profile()` / `load_profile()`
- `config.example/voices/science_tech_profile.json` — Pre-generated example
- `tests/unit/test_persistence.py`
- `tests/unit/test_train_cmd.py`
- `tests/integration/test_train_pipeline.py`

**Modify:**
- `src/newsroom/cli.py` — Add `train` subparser: `--beat` (required), `--config-dir`, `--min-samples`, `--now`, `--verbose`
- `src/newsroom/commands.py` — Add `train_cmd()`: load corpus → build profile → save profile → print summary
- `tests/e2e/test_cli.py` — Verify `train` in help output + full E2E

**CLI:**
```
newsroom train --beat science_tech [--config-dir config/] [--min-samples 5] [--now ISO8601] [--verbose]
```
Output: `config/voices/science_tech_profile.json`

**Reuse:** `time_anchor.resolve_now()`, Pydantic `.model_dump_json()` / `.model_validate_json()`

## Phase 4: QA Integration (Medium)

**New files:**
- `src/newsroom/voice/thresholds.py` — `derive_drift_config(profile) -> VoiceDriftConfig`
- `tests/unit/test_voice_drift.py`
- `tests/unit/test_thresholds.py`

**Modify:**
- `src/newsroom/qa/checks.py` — Implement `check_voice_drift()` with optional `VoiceProfile` param

**`check_voice_drift()` logic:**
1. **Taboo phrases** (from `VoiceConstitution`): case-insensitive scan → error-severity findings
2. **Sentence length** (from `VoiceProfile` or `VoiceDriftConfig` fallback): extract sentences from draft, compare against profile percentiles → warning-severity findings
3. **Optional profile-derived checks** (when profile present): vocabulary richness drift (TTR), contraction usage drift → info-severity findings

**Threshold derivation** (`thresholds.py`) — percentile-based, not mean±σ:
- `max_avg_sentence_length = round(profile.sentence_stats.p90)`
- `min_avg_sentence_length = max(5, round(profile.sentence_stats.p10))`
- `max_sentence_length = round(profile.sentence_stats.p95 * 1.1)`

**Tiered enforcement by corpus size:**
- `N < 5`: Report percentile ranks only, no pass/fail thresholds
- `N = 5-10`: Warning-severity findings only (no blocking errors)
- `N > 10`: Full enforcement with error-severity for extreme drift

**Reuse:** `voice/analyze.py` sentence splitting + markdown stripping, existing `QAFinding`/`VoiceDriftConfig` models

## Phase 5: Draft Integration (Deferred)

Blocked by `writer.py` `NotImplementedError`. Design documented for when writer is implemented:
- `src/newsroom/voice/prompt.py` — `format_profile_for_prompt(profile) -> str`
- Renders stats into natural language for the LLM system prompt
- Falls back gracefully if no profile exists

---

## Dependency Graph

```
Phase 1 (Corpus)  ←→  Phase 2 (Analysis)   [parallelizable]
         ↘              ↙
      Phase 3 (CLI + Persistence)
                ↓
      Phase 4 (QA Integration)
                ↓
      Phase 5 (Draft Integration)  [deferred]
```

## Constitution Compliance

| Principle | Status |
|-----------|--------|
| I. Determinism | Sorted file listing, fixed `--now`, deterministic CountVectorizer |
| II. Test-First | TDD per phase, NO NETWORK (tmp_path fixtures) |
| III. Human Authority | `train` is explicit human action, profile is advisory |
| IV. Truth & Attribution | Profile derived from human-written samples |
| V. Open-Core | Samples in `config/` (gitignored), examples in `config.example/` |
| VI. Simplicity | No new deps, small modules, pure functions |

## Verification

```bash
# After each phase:
bash scripts/verify.sh          # lint + format + tests

# After Phase 3 (full E2E):
python -m newsroom train --beat science_tech --config-dir config.example/
cat config.example/voices/science_tech_profile.json

# After Phase 4:
python -m pytest tests/unit/test_voice_drift.py tests/unit/test_thresholds.py -v
```

## Risks

1. **Sentence splitting edge cases** (abbreviations, URLs, decimals) — mitigated by comprehensive test fixtures, negative lookbehind for common abbreviations (Dr., Mr., U.S.), and URL stripping
2. **Small corpus instability** (<5 samples) — mitigated by tiered enforcement: report-only below 5, warnings at 5-10, full enforcement above 10
3. **models.py approaching LOC limit** (~380 after changes) — monitor, split if future features push past 400
4. **Passive voice regex is approximate** (~60-70% accuracy) — named `passive_voice_estimate`, documented as directional, not used for blocking decisions
5. **Markdown noise in features** — mitigated by `strip_markdown()` preprocessing before all analysis
