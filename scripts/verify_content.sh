#!/usr/bin/env bash
# ABOUTME: Content verification — runs pitch against fixtures, validates the
# ABOUTME: brief.json schema and golden output, and asserts determinism.
set -euo pipefail

# Scope: the deterministic `pitch` step only (no LLM calls, no network —
# `--source-override` forces fixture reads). `draft`/`qa` content
# verification (which would require NEWSROOM_FAKE_LLM=1 to stay LLM-call
# free) is not yet covered here; see docs/architecture.md's Verification
# section for the full intended scope of this script.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FIXED_NOW="2026-01-15T12:00:00Z"
BEAT="science_tech"
FIXTURE_DIR="fixtures/science_tech"
GOLDEN_BRIEF="$FIXTURE_DIR/expected_brief.json"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

RUN_A_DIR="$TMP_DIR/run_a"
RUN_B_DIR="$TMP_DIR/run_b"

echo "Running pitch (run A) against $FIXTURE_DIR..."
timeout 60 uv run python -m newsroom \
  --now "$FIXED_NOW" \
  --out-dir "$RUN_A_DIR" \
  pitch --beat "$BEAT" --since 48h --source-override "$FIXTURE_DIR"

echo "Running pitch (run B) against $FIXTURE_DIR..."
timeout 60 uv run python -m newsroom \
  --now "$FIXED_NOW" \
  --out-dir "$RUN_B_DIR" \
  pitch --beat "$BEAT" --since 48h --source-override "$FIXTURE_DIR"

BEAT_SUBPATH="2026-01-15/$BEAT"
BRIEF_A="$RUN_A_DIR/$BEAT_SUBPATH/brief.json"
BRIEF_B="$RUN_B_DIR/$BEAT_SUBPATH/brief.json"
PITCHES_A="$RUN_A_DIR/$BEAT_SUBPATH/pitches.json"
PITCHES_B="$RUN_B_DIR/$BEAT_SUBPATH/pitches.json"

for f in "$BRIEF_A" "$BRIEF_B" "$PITCHES_A" "$PITCHES_B"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: expected output file missing: $f" >&2
    exit 1
  fi
done

echo "Validating brief.json schema and golden equality..."
timeout 30 uv run python - "$BRIEF_A" "$GOLDEN_BRIEF" <<'PY'
import json
import sys

from newsroom.models import BriefPack

actual_path, golden_path = sys.argv[1], sys.argv[2]

actual_text = open(actual_path, encoding="utf-8").read()

# Schema-valid: must parse into the real BriefPack model, not just be JSON.
try:
    BriefPack.model_validate_json(actual_text)
except Exception as exc:  # noqa: BLE001 - re-raised as a clear failure below
    print(f"FAIL: brief.json failed BriefPack schema validation: {exc}", file=sys.stderr)
    sys.exit(1)

actual = json.loads(actual_text)
golden = json.loads(open(golden_path, encoding="utf-8").read())

if actual != golden:
    print("FAIL: brief.json does not match the golden fixture.", file=sys.stderr)
    print(f"  actual:  {actual_path}", file=sys.stderr)
    print(f"  golden:  {golden_path}", file=sys.stderr)
    sys.exit(1)

print("OK: brief.json is schema-valid and matches the golden fixture.")
PY

echo "Asserting determinism across repeated runs..."
if ! diff -q "$BRIEF_A" "$BRIEF_B" > /dev/null; then
  echo "FAIL: brief.json differs between two runs with the same --now and fixtures." >&2
  diff "$BRIEF_A" "$BRIEF_B" >&2 || true
  exit 1
fi
if ! diff -q "$PITCHES_A" "$PITCHES_B" > /dev/null; then
  echo "FAIL: pitches.json differs between two runs with the same --now and fixtures." >&2
  diff "$PITCHES_A" "$PITCHES_B" >&2 || true
  exit 1
fi
echo "OK: pitch output is deterministic across repeated runs."

echo "verify_content.sh: all content checks passed."
