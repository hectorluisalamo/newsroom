# Newsroom

A Python CLI that produces Substack-ready opinion columns from beat-specific research briefs and writer voices. V0 covers the `science_tech` beat end-to-end.

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize local config from examples
bash scripts/init_config.sh

# See available commands
python -m newsroom --help
```

## Configuration

This repository is **open-core**. Production configuration is intentionally excluded from the public repo.

- **Example configs** live in `config.example/` and are committed to the repo.
- **Runtime configs** live in `config/` and are gitignored.
- Run `scripts/init_config.sh` to generate local config from examples for demo runs.
- If you have the private config repo, overlay with `scripts/sync_private_config.sh`.

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```
ANTHROPIC_API_KEY=     # Required for draft generation
NEWSROOM_MODEL=        # LLM model ID (default: claude-sonnet-4-20250514)
NEWSROOM_NOW=          # Optional: fixed ISO 8601 timestamp for deterministic runs
```

## Development

```bash
# Run linter, formatter check, and tests
bash scripts/verify.sh

# Run tests only
uv run pytest tests/ -v
```

## Project Structure

```
config.example/     Example configs (committed)
config/             Runtime configs (gitignored)
docs/               Architecture docs, ADRs, PRDs
fixtures/           Test fixtures (sanitized RSS, expected outputs)
scripts/            Verification and config scripts
src/newsroom/       Python package
tests/              Unit, integration, and e2e tests
```

## Stack

Python 3.12+, uv, Ruff, pytest, Pydantic, feedparser, httpx, rich, anthropic SDK, scikit-learn.
