# Progress Tracker

> Update at the **end of every working session** (human or AI). Newest log entries go on top.
> Status keys: ⬜ not started · 🟨 in progress · ✅ done · ⛔ blocked

## Milestones
| Milestone | Target | Status |
|---|---|---|
| Planning docs (PRD, spec, phases, memory) | Day 0 | ✅ |
| M0 Kick-off (repo, tooling, open questions) | Day 1 | 🟨 repo + tooling done; open questions pending |
| M1 Engine done | Day 3 | ✅ |
| M2 First trained agents | Day 5 | 🟨 pipeline works; full experiment run in progress |
| **M3 MVP: AI vs Bot in the UI** | **Day 7** | ⬜ |
| M4 Feature complete | Day 10 | ⬜ |
| M5 README + slides + rehearsal | Day 12 | ⬜ |

## Phase checklist
### Phase 0: Setup
- ✅ Git repo + GitHub remote (private, rounak-agl/india-property-game-rl)
- ✅ Python venv, requirements, pytest/ruff (pyproject.toml)
- ⬜ Vite React-TS scaffold
- ⬜ Open questions Q1–Q6 resolved
- ✅ `board_data.py`

### Phase 1: Engine
- ✅ state/events · ✅ rules · ✅ cards · ✅ engine loop · ✅ bots · ✅ tests + soak + benchmark (~24k games/min; Fixed beats Random 72% over 500 games)

### Phase 2: RL core
- ✅ Env A · ✅ Env B + masks · ✅ rewards · ✅ check_env · ✅ train.py · ✅ evaluate.py · 🟨 first models (training)

### Phase 3: API + board UI
- ✅ real API (mock skipped) · ✅ real sessions · ✅ X-Ray payload · ⬜ board · ⬜ animations · ⬜ Watch mode · ⬜ X-Ray panel

### Phase 4: Experiments
- ⬜ E1 · ⬜ E2 · ⬜ E3 · ⬜ E4 · ⬜ E5 (stretch) · ⬜ plots + summary JSON · ⬜ behaviour analysis

### Phase 5: Features & polish
- ⬜ Human vs AI · ⬜ Results page · ⬜ How it works · ⬜ a11y/responsive · ⬜ smoke test · ⬜ dev script

### Phase 6: Docs & presentation
- ⬜ README · ⬜ web slide deck · ⬜ demo GIF · ⬜ rehearsals · ⬜ release v1.0

## Session log
### 2026-10-30: Build session 1 (with Claude)
- Created the private GitHub repo; all commits use the user's identity (D-017).
- Phase 1 done: engine (`src/engine`), bots (`src/bots`) and 41 tests passing (`pytest -q`).
- Phase 2 core done: Env A/B (`src/envs`), rewards, `src/rl/{train,evaluate,agent,config,stats}.py`, configs `experiments/e1..e5*.yaml`, `scripts/run_experiments.sh`.
- Phase 3 backend done: FastAPI `src/api` (board, agents, games, advance, action, results) + tests.
- Measured: Env A ~17k steps/s (~127 steps/episode); Env B ~8k steps/s (~36 steps/episode); 20k MaskablePPO steps ≈ 12 s.
- Gotcha: running 4 training jobs plus pytest got OOM-killed (exit 137). Use ≤3 parallel jobs, and don't run tests alongside training.
- Experiments relaunched: `scripts/run_experiments.sh 3` → logs in `results/logs/`, models in `models/`, final evals in `results/eval/`.
- **Next up:** `src/rl/make_plots.py` (summary JSON + figures) → React frontend (board, animations, X-Ray, Human vs AI, Results) → README + web slide deck.

### 2026-10-30: Planning (with Claude)
- Reviewed the blueprint PDF; verified the three papers and the board source on the web.
- Decisions D-001…D-006 accepted by the user; D-007…D-011 proposed.
- Created `docs/PRD.md`, `TECH_SPEC.md`, `PHASES.md`, `REFLECTIONS.md`, `docs/memory/*`, `CLAUDE.md`.
- **Next up:** resolve OPEN_QUESTIONS, set up the git repo, start Phase 0/1.
