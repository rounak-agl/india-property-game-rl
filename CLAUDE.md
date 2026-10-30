# CLAUDE.md: guide for AI assistants and teammates

## Start of every session
1. Read `docs/memory/PROJECT_CONTEXT.md`, then `docs/memory/PROGRESS.md` (current phase + "Next up").
2. Check `docs/memory/OPEN_QUESTIONS.md` before assuming anything. If a question blocks you, ask; don't guess.
3. For interfaces (event schema, API, env spaces), follow `docs/TECH_SPEC.md` exactly.

## End of every session
- Update `docs/memory/PROGRESS.md` (checklist + a dated log entry + "Next up").
- Record any design or parameter choice in `docs/memory/DECISIONS.md` (append-only, next D-number).

## Project in one line
Original Indian-themed 2-player property-trading game following Monopoly rules + RL agents (DQN/PPO/MaskablePPO) + FastAPI/React game UI with an explainability "X-Ray" panel. AI course project, team of 4.

## Rules that must not be broken
- **No Hasbro/Funskool branding, logos, artwork or official card wording.** Use the original game name (see Q1), original art, original card text.
- **Never put an unmeasured or unverified number in the README, slides or UI.** Paper facts → `docs/memory/RESEARCH_NOTES.md`. Our results → `results/summary/*.json`.
- `src/engine` is pure Python: no imports from gymnasium, stable_baselines3, fastapi or torch.
- Changing the event schema or API after Phase 1 needs a DECISIONS entry and must notify the API and UI owners.
- Commit only when asked; use feature branches `feat/<area>-<thing>`.

## Layout (planned; see TECH_SPEC §2)
`src/engine` · `src/bots` · `src/envs` · `src/rl` · `src/api` · `tests/` · `experiments/` · `models/` · `results/` · `frontend/` · `presentation/` · `docs/`

## Commands (fill in as they are created)
| Task | Command |
|---|---|
| Install (Python) | `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |
| Tests | `pytest -q` |
| Lint | `ruff check src tests` |
| Train | `python -m src.rl.train --config experiments/<name>.yaml` |
| Evaluate | `python -m src.rl.evaluate --model models/<id>.zip --games 1000` |
| Plots | `python -m src.rl.make_plots` |
| API | `uvicorn src.api.main:app --reload --port 8000` |
| Frontend | `cd frontend && npm install && npm run dev` |

## Style
- Python: type hints, dataclasses, ruff defaults, small pure functions in `rules.py`.
- TypeScript: strict mode, function components, shared types in `frontend/src/types/api.ts` mirroring TECH_SPEC §5–6.
- Money is always an `int` number of rupees; format with `en-IN` only in the UI.
