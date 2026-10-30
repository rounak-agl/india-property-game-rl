# Progress Tracker

> Update at the **end of every working session** (human or AI). Newest log entries go on top.
> Status keys: ⬜ not started · 🟨 in progress · ✅ done · ⛔ blocked

## Milestones
| Milestone | Target | Status |
|---|---|---|
| Planning docs (PRD, spec, phases, memory) | Day 0 | ✅ |
| M0 Kick-off (repo, tooling, open questions) | Day 1 | ⬜ |
| M1 Engine done | Day 3 | ⬜ |
| M2 First trained agents | Day 5 | ⬜ |
| **M3 MVP: AI vs Bot in the UI** | **Day 7** | ⬜ |
| M4 Feature complete | Day 10 | ⬜ |
| M5 README + slides + rehearsal | Day 12 | ⬜ |

## Phase checklist
### Phase 0: Setup
- ⬜ Git repo + GitHub remote
- ⬜ Python venv, requirements, pytest/ruff
- ⬜ Vite React-TS scaffold
- ⬜ Open questions Q1–Q6 resolved
- ⬜ `board_data.py`

### Phase 1: Engine
- ⬜ state/events · ⬜ rules · ⬜ cards · ⬜ engine loop · ⬜ bots · ⬜ tests + soak + benchmark

### Phase 2: RL core
- ⬜ Env A · ⬜ Env B + masks · ⬜ rewards · ⬜ check_env · ⬜ train.py · ⬜ evaluate.py · ⬜ first models

### Phase 3: API + board UI
- ⬜ mock API · ⬜ real sessions · ⬜ X-Ray · ⬜ board · ⬜ animations · ⬜ Watch mode · ⬜ X-Ray panel

### Phase 4: Experiments
- ⬜ E1 · ⬜ E2 · ⬜ E3 · ⬜ E4 · ⬜ E5 (stretch) · ⬜ plots + summary JSON · ⬜ behaviour analysis

### Phase 5: Features & polish
- ⬜ Human vs AI · ⬜ Results page · ⬜ How it works · ⬜ a11y/responsive · ⬜ smoke test · ⬜ dev script

### Phase 6: Docs & presentation
- ⬜ README · ⬜ web slide deck · ⬜ demo GIF · ⬜ rehearsals · ⬜ release v1.0

## Session log
### 2026-10-30: Planning (with Claude)
- Reviewed the blueprint PDF; verified the three papers and the board source on the web.
- Decisions D-001…D-006 accepted by the user; D-007…D-011 proposed.
- Created `docs/PRD.md`, `TECH_SPEC.md`, `PHASES.md`, `REFLECTIONS.md`, `docs/memory/*`, `CLAUDE.md`.
- **Next up:** resolve OPEN_QUESTIONS, set up the git repo, start Phase 0/1.
