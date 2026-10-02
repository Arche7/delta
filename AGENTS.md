# AGENTS.md — kvant

Instructions for coding agents. Humans: read PROJECT.md first.

## Read before you write anything
1. `PROJECT.md` — what we build and why, and who to ask.
2. `ARCHITECTURE.md` — the boxes and their names.
3. `CONSTITUTION.md` — non-negotiable rules.
4. `DECISIONS/` — RFCs (proposals, approved or not) and the ADRs they left behind.

## Tooling defaults
- Python uses `uv` (`uv add`, `uv sync`, `uv run`) — never `pip`. Commit `uv.lock` (create it with `uv lock` where PyPI is reachable).
- Tests: `uv run python -m unittest discover -s tests -v` (unittest, no pytest — see ADR-0001).
- Local server with demo data: `uv run python scripts/seed_demo.py data/demo.db`, then `DB_PATH=data/demo.db RATES_REFRESH=0 uv run uvicorn app.web:app --port 8000`, login link: `DB_PATH=data/demo.db uv run python scripts/dev_login.py`.
- After editing `docs/ios-shortcut.md` run `uv run python scripts/build_ios_page.py` (regenerates `webapp/ios.html`).
- Business logic lives in `app/services.py`; `app/web.py` and `app/bot.py` stay thin.

## Working with the owner
- Владелец — новичок в разработке: объяснять пошагово и подробно, по-русски.
- Код отдавать полными файлами для замены в VS Code (macOS), архивом и готовой командой: распаковать, закоммитить, запушить.

## Process (enforced by the groundwork plugin)
Interview → RFC → human approval → spec → plan → tasks → evals → implement → handover.
You cannot approve documents; only the user can, with `/groundwork-specflow:approve`.

## Repositories
kvant — . — бот, сервер, Mini App и команда iOS
