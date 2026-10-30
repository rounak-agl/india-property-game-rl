# Project Context (read this first)

**Last updated:** 2026-10-30 · **Current phase:** Phase 0 (Setup), see `PROGRESS.md`

## One-paragraph summary
An AI course project by a team of 4, over 1–2 weeks. We build an **original, Indian-themed, 2-player property-trading board game that follows Monopoly's rules** (40 spaces: Indian cities and railway stations). We train **RL agents** (DQN, PPO, MaskablePPO via stable-baselines3) to beat rule-based bots, run controlled experiments (env design, masking, reward shaping), and show everything in a **FastAPI + React web game** with animated play, Human-vs-AI mode, an "AI Brain X-Ray" explainability panel and a Results page. Final deliverables: code, README and a web slide deck.

## Where things are
| Need | File |
|---|---|
| What & why (requirements) | `docs/PRD.md` |
| How (interfaces, rules, envs, API) | `docs/TECH_SPEC.md` |
| When & who | `docs/PHASES.md` |
| Review of the original blueprint PDF | `docs/REFLECTIONS.md` |
| Decisions made so far | `docs/memory/DECISIONS.md` |
| Status / next steps | `docs/memory/PROGRESS.md` |
| Verified paper facts | `docs/memory/RESEARCH_NOTES.md` |
| Unresolved questions | `docs/memory/OPEN_QUESTIONS.md` |
| Terms | `docs/memory/GLOSSARY.md` |
| Original input | `Indian Monopoly RL Agent Blueprint.pdf` (some claims in it are wrong; see REFLECTIONS §2.7) |

## Hard constraints
- 2 players · no trading · no auctions · Medium rule depth (D-003).
- **No Hasbro/Funskool branding, artwork or card wording.** Original name, art and card text (D-001).
- Only **verified** numbers go into the report and slides. Measured results come from `results/summary/*.json`.
- The engine stays pure Python, with no RL or web imports (FR-E11).

## Environment facts (dev machine of the person who started the project)
Linux, Python 3.12.3, Node 24.7, npm 11.12, 16 CPU threads, RTX 4050 laptop GPU (not required), only ~1–2 GB RAM free at the time, so keep training runs light or close other apps.
