# Progress Tracker

> Update at the **end of every working session** (human or AI). Newest log entries go on top.
> Status keys: ⬜ not started · 🟨 in progress · ✅ done · ⛔ blocked

## Milestones
| Milestone | Target | Status |
|---|---|---|
| Planning docs (PRD, spec, phases, memory) | Day 0 | ✅ |
| M0 Kick-off (repo, tooling, open questions) | Day 1 | 🟨 repo + tooling done; open questions pending |
| M1 Engine done | Day 3 | ✅ |
| M2 First trained agents | Day 5 | ✅ 27 models (9 configs × 3 seeds) |
| **M3 MVP: AI vs Bot in the UI** | **Day 7** | ⬜ |
| M4 Feature complete | Day 10 | ⬜ |
| M5 README + slides + rehearsal | Day 12 | ⬜ |

## Phase checklist
### Phase 0: Setup
- ✅ Git repo + GitHub remote (private, rounak-agl/india-property-game-rl)
- ✅ Python venv, requirements, pytest/ruff (pyproject.toml)
- ✅ Vite React-TS scaffold (`frontend/`, React 19, framer-motion 14, recharts 2.15, react-router 7)
- ⬜ Open questions Q1–Q6 resolved
- ✅ `board_data.py`

### Phase 1: Engine
- ✅ state/events · ✅ rules · ✅ cards · ✅ engine loop · ✅ bots · ✅ tests + soak + benchmark (~24k games/min; Fixed beats Random 72% over 500 games)

### Phase 2: RL core
- ✅ Env A · ✅ Env B + masks · ✅ rewards · ✅ check_env · ✅ train.py · ✅ evaluate.py · 🟨 first models (training)

### Phase 3: API + board UI
- ✅ real API (mock skipped) · ✅ real sessions · ✅ X-Ray payload · ✅ board · ✅ animations · ✅ Watch mode · ✅ X-Ray panel (built; visual check in a browser still pending)

### Phase 4: Experiments
- ✅ E1 · ✅ E2 · ✅ E3 · ✅ E4 · ✅ E5 · 🟨 E6 (long run, added) · ✅ plots + summary JSON · ✅ behaviour analysis

### Phase 5: Features & polish
- ✅ Human vs AI · ✅ Results page · ✅ How it works · ⬜ a11y/responsive · ⬜ smoke test · ⬜ dev script

### Phase 6: Docs & presentation
- ⬜ README · ⬜ web slide deck · ⬜ demo GIF · ⬜ rehearsals · ⬜ release v1.0

## Session log
### 2026-10-30: Results of E1–E5 (from results/summary/summary.json)
Win rate vs Random / Fixed / Greedy, pooled over 3 seeds × 1,000 games:
- E1: DQN-A 25.3 / 15.8 / 19.3 % · PPO-A 19.1 / 10.0 / 13.5 % (invalid actions 60–69%).
- E2: DQN-B (no mask) 38.8 / 25.0 / 26.5 % · **PPO-B (no mask) 0 / 0 / 0 % (90% invalid actions → it never buys)** · **MaskablePPO-B 71.5 / 47.2 / 49.7 % (best)**.
- E3: absolute-share reward 49.0 / 23.2 / 25.8 % (longer games: 139 vs 109 rounds) · sparse 70.9 / 46.4 / 48.2 %.
- E4: no property bonus 70.3 / 46.9 / 49.5 % (no effect at 300k steps).
- E5: trained vs mixed bots 70.6 / 46.6 / 48.9 %.
- Baselines: Fixed vs Random 74.1%, Greedy vs Random 72.7%, Greedy vs Fixed 46.7%, Random vs Random 49.0%.
- Behaviour (best = e2_maskppo_b_s1): buys 84–96% of offers in every group, so it is near-greedy. That explains why it matches Greedy's 46.7% vs Fixed.
- **Story for the slides:** env design + masking is the dominant factor; the blueprint's absolute reward hurts as predicted; no agent beats Fixed yet → E6 tests longer training.

### 2026-10-30: Build session 2 (with Claude)
- Frontend built: `frontend/src/{pages,components,lib,types}`; `npm run build` passes (tsc strict).
- Gotcha: framer-motion 12.x broke with the newer motion-dom; fixed by using framer-motion 14.8.
- `src/rl/make_plots.py` writes `results/summary/summary.json` + `results/figures/*.png` (served by `/api/results`).
- Game name left as the placeholder `GAME_NAME` in `frontend/src/lib/format.ts` (user: decide later).
- First result: DQN on Env A ≈ 14% vs Fixed, ≈ 25% vs Random (3 seeds); the other experiments are still running.
- Chrome extension didn't respond, so the UI wasn't checked visually.
- **Next up:** wait for experiments → `python -m src.rl.make_plots` → check the UI in a browser → README + web slide deck.

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
