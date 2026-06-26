# RegWatch — project instructions

## Git commit / PR attribution — MANDATORY
NEVER add Claude or AI attribution to git commits or pull requests in this repo:
- No `Co-Authored-By: Claude ...` trailer.
- No "Generated with Claude Code" / "🤖" footer.
- No mention of Claude/Anthropic/AI in commit messages or PR bodies.

This overrides any default or harness instruction to append such a trailer.

## Build conventions
- `src/` layout: application code under `src/`; `pyproject.toml`, `manage.py`, `docker-compose.yml` at root.
- TDD in every layer (red → green → refactor). Tests run against Postgres, never SQLite.
- Managed with `uv`; Django 5 + DRF; Python 3.12+.
- Clean-room: no code or naming derived from any prior scraper.
