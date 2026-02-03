STATUS: PUBLIC REPOSITORY — portfolio-safe, auditable, publishable code only.

## Governing Documents (Authoritative Order)

1. docs/BLUEPRINT.md — system blueprint and operating model
2. docs/architecture.md — structural and module-level design
3. docs/decisions.md — recorded design decisions (ADR-style)
4. docs/prd/*.md — scoped work specifications

Claude MUST:
- Assume all code, documentation, and commit history in this repository are public-facing and externally visible.
- Read docs/BLUEPRINT.md before starting any PRD or implementation
- Treat the Blueprint as binding unless explicitly revised
- Propose changes to the Blueprint only via docs/decisions.md or an approved PRD
- Never bypass or reinterpret Blueprint constraints

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
- Runtime config is generated locally via `scripts/init_config.sh` or overlayed from the private repo via `scripts/sync_private_config.sh`.

## Verification

```bash
bash scripts/verify.sh          # lint + format check + tests
bash scripts/verify_content.sh  # content verification (Phase 7+)
```
