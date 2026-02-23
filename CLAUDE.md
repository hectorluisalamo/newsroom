STATUS: PUBLIC REPOSITORY — portfolio-safe, auditable, publishable code only.

## Authority Hierarchy (In Case of Conflict)

1. CI / verification output (`scripts/verify.sh`, QA gates)
2. `CLAUDE.md` (repo-local operational rules and conventions)
3. `docs/architecture.md` (system design authority)
4. `docs/decisions.md` (ADR-style design decisions)
5. `docs/prd/*.md` (feature specifications)

---

## Project Conventions

- **Package**: `newsroom` under `src/newsroom/` (src layout)
- **Package manager**: `uv`
- **Linter/formatter**: Ruff (py312, E/F/I/W rules)
- **Tests**: pytest with NO NETWORK policy (enforced by conftest.py)

## File Header Rule

Every new Python file must begin with a two-line comment, each line prefixed with `ABOUTME: `, describing what the file does. Example:

```python
# ABOUTME: Argument parsing for the Newsroom CLI using argparse.
# ABOUTME: Defines pitch, draft, and qa subcommands with their flags.
```

## Comment Rules

- No `TODO`, `FIXME`, or `HACK` comments.
- No temporal or aspirational comments (e.g., "recently added", "will be implemented later").
- Comments must be evergreen and describe the code as it is.

## Config Boundary (Open-Core)

- **Never commit `config/` or `.env`.** The entire `config/` directory is gitignored.
- **Only commit `config.example/`.** Example configs are the public repo's reference configs.
- Runtime config is generated locally via `scripts/init_config.sh`.

## Verification

```bash
bash scripts/verify.sh          # lint + format check + tests
bash scripts/verify_content.sh  # content verification (Phase 7+)
```
