# Technical Specification

> The single source of truth for interfaces between Engine (A), RL (B), API (C) and UI (D).
> **Freeze §5 (event schema) and §6 (API) at the end of Phase 1.** After that, change them only via an entry in `memory/DECISIONS.md`.

---

## 1. Architecture

```
┌──────────────────────────── frontend/ (React + TS + Vite) ─────────────────────────────┐
│  Pages: Play (Watch / Human vs AI) · Results · How it works                             │
│  Components: Board · Tile · Token · Dice · CardDeck · PlayerPanel · XRayPanel · Charts  │
│  State: zustand store ← REST (fetch) ← event queue → animation timeline                 │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ JSON over HTTP (/api/*)
┌──────────────────────────── src/api (FastAPI) ───────────────────────────────────────────┐
│  sessions.py: in-memory GameSession {engine, controllers, event log}                     │
│  agents.py:   loads models/*.zip, computes X-Ray (probs / Q-values / value)              │
└───────────────┬──────────────────────────────────────────────┬───────────────────────────┘
                │                                              │
┌───────────────▼──────── src/engine (pure Python) ──┐  ┌──────▼──────── src/envs + src/rl ────────────┐
│ board_data · cards · state · rules · engine        │◄─┤ EnvA (Blueprint) · EnvB (Masked) · rewards   │
│ deterministic(seed) · emits Event objects          │  │ train.py · evaluate.py · make_plots.py       │
└────────────────────────────────────────────────────┘  └──────────────────────────────────────────────┘
                ▲
        src/bots: RandomBot · FixedPolicyBot (Bailis) · GreedyBot · jail_policy
```

**Key principle:** the engine is driven by **controllers**. A controller answers `decide(state, decision) -> action`. RL agents, bots and the human (via the API) are all controllers, so the same engine runs training, evaluation and the UI.

## 2. Repository layout

```
.
├── CLAUDE.md                     # guide for AI assistants + team
├── README.md                     # (final phase)
├── pyproject.toml / requirements.txt
├── src/
│   ├── engine/  board_data.py cards.py state.py rules.py engine.py events.py
│   ├── bots/    base.py random_bot.py fixed_policy_bot.py greedy_bot.py jail_policy.py
│   ├── envs/    env_a_blueprint.py env_b_masked.py rewards.py observation.py
│   ├── rl/      train.py evaluate.py callbacks.py make_plots.py xray.py
│   └── api/     main.py sessions.py agents.py schemas.py
├── tests/       test_rules.py test_engine_invariants.py test_envs.py test_api.py
├── experiments/ *.yaml           # one file per experiment config
├── models/      *.zip + *.json   # trained agents + metadata (git-LFS or release asset)
├── results/     raw/*.csv  summary/*.json  figures/*.png
├── frontend/    (Vite app)
├── presentation/                 # web slide deck (final phase)
└── docs/        PRD · TECH_SPEC · PHASES · REFLECTIONS · memory/
```

## 3. Game rules (Medium depth, D-003)

### 3.1 Board data (`board_data.py`)
Names are verified against the Funskool India 2008 board (World of Monopoly). **Prices and rents use the classic standard-edition structure in ₹ (D-007, pending confirmation).**
Rent columns: base / 1 house / 2 / 3 / 4 / hotel. "×2" means base rent doubles when the full group is owned and unimproved.

| # | Space | Type | Group | Price | Rent (0/1/2/3/4/H) | House |
|---|---|---|---|---|---|---|
| 0 | GO | corner | – | – | collect ₹200 | – |
| 1 | Guwahati | city | 1 Brown | 60 | 2/10/30/90/160/250 | 50 |
| 2 | Community Chest | card | – | – | – | – |
| 3 | Bhubaneshwar | city | 1 Brown | 60 | 4/20/60/180/320/450 | 50 |
| 4 | Income Tax | tax | – | – | pay ₹200 | – |
| 5 | Chennai Central Railway Station | station | Stations | 200 | 25/50/100/200 by count | – |
| 6 | Panaji (Goa) | city | 2 Light Blue | 100 | 6/30/90/270/400/550 | 50 |
| 7 | Chance | card | – | – | – | – |
| 8 | Agra | city | 2 Light Blue | 100 | 6/30/90/270/400/550 | 50 |
| 9 | Vadodara | city | 2 Light Blue | 120 | 8/40/100/300/450/600 | 50 |
| 10 | Jail / Just Visiting | corner | – | – | – | – |
| 11 | Ludhiana | city | 3 Pink | 140 | 10/50/150/450/625/750 | 100 |
| 12 | Electric Company | utility | Utilities | 150 | 4× / 10× dice | – |
| 13 | Patna | city | 3 Pink | 140 | 10/50/150/450/625/750 | 100 |
| 14 | Bhopal | city | 3 Pink | 160 | 12/60/180/500/700/900 | 100 |
| 15 | Howrah Railway Station | station | Stations | 200 | 25/50/100/200 | – |
| 16 | Indore | city | 4 Orange | 180 | 14/70/200/550/750/950 | 100 |
| 17 | Community Chest | card | – | – | – | – |
| 18 | Nagpur | city | 4 Orange | 180 | 14/70/200/550/750/950 | 100 |
| 19 | Kochi | city | 4 Orange | 200 | 16/80/220/600/800/1000 | 100 |
| 20 | Free Parking | corner | – | – | nothing | – |
| 21 | Lucknow | city | 5 Red | 220 | 18/90/250/700/875/1050 | 150 |
| 22 | Chance | card | – | – | – | – |
| 23 | Chandigarh | city | 5 Red | 220 | 18/90/250/700/875/1050 | 150 |
| 24 | Jaipur | city | 5 Red | 240 | 20/100/300/750/925/1100 | 150 |
| 25 | New Delhi Railway Station | station | Stations | 200 | 25/50/100/200 | – |
| 26 | Pune | city | 6 Yellow | 260 | 22/110/330/800/975/1150 | 150 |
| 27 | Hyderabad | city | 6 Yellow | 260 | 22/110/330/800/975/1150 | 150 |
| 28 | Water Works | utility | Utilities | 150 | 4× / 10× dice | – |
| 29 | Ahmedabad | city | 6 Yellow | 280 | 24/120/360/850/1025/1200 | 150 |
| 30 | Go To Jail | corner | – | – | move to 10, jailed | – |
| 31 | Kolkata | city | 7 Green | 300 | 26/130/390/900/1100/1275 | 200 |
| 32 | Chennai | city | 7 Green | 300 | 26/130/390/900/1100/1275 | 200 |
| 33 | Community Chest | card | – | – | – | – |
| 34 | Bengaluru | city | 7 Green | 320 | 28/150/450/1000/1200/1400 | 200 |
| 35 | Chhatrapati Shivaji Terminus | station | Stations | 200 | 25/50/100/200 | – |
| 36 | Chance | card | – | – | – | – |
| 37 | Delhi | city | 8 Dark Blue | 350 | 35/175/500/1100/1300/1500 | 200 |
| 38 | Super Tax | tax | – | – | pay ₹100 | – |
| 39 | Mumbai | city | 8 Dark Blue | 400 | 50/200/600/1400/1700/2000 | 200 |

Mortgage value = price / 2. Hotel = level 5 (cost = 1 more house).

### 3.2 Turn sequence
1. **Pre-roll:** if the player is in jail → jail policy (pay ₹50 / use card / try doubles). Otherwise → **build decisions** (repeat until Pass or nothing is buildable).
2. **Roll 2d6, move.** Passing GO pays ₹200. Third consecutive double → jail, turn ends.
3. **Resolve landing:** unowned buyable → **buy decision** (only if affordable; no auction, so it stays unowned) · owned by opponent → pay rent (none if mortgaged) · tax · card · Go To Jail.
4. **Cash < 0** → forced liquidation (sell houses at half cost, most expensive group first; then mortgage cheapest unimproved property). Still < 0 → bankrupt → game over.
5. Doubles (and not jailed) → back to step 1 (same player).
6. One **round** = both players took a turn. Round 200 ends the game; the higher **raw** net worth wins (ties → player 2 wins, logged; expected to be very rare).

### 3.3 Cards (`cards.py`)
Two original 16-card decks with themed text (e.g. *"Monsoon flooding repairs: pay ₹40 per house, ₹115 per hotel"*, *"Advance to the nearest railway station"*, *"Diwali bonus: collect ₹100"*). Mechanics mirror the standard deck types: move-to (GO, specific city, nearest station/utility), move back 3, collect/pay fixed amounts, collect from/pay to opponent, repairs, go to jail, get-out-of-jail card. **Do not copy official card wording.**

### 3.4 Invariants (asserted in tests and in debug mode)
- Total money is conserved apart from bank inflows/outflows (logged per event).
- Each property has ≤ 1 owner; houses only exist on full groups; 0 ≤ houses ≤ 5; mortgaged ⇒ houses = 0.
- Player position ∈ [0, 39]; the jailed flag is consistent with the position.

## 4. RL environments

### 4.1 Shared
- `gymnasium.Env`; the agent controls one player and the opponent is a bot inside `step()`.
- Seat (first/second) is chosen at random on each `reset()`.
- `info` carries `{events, winner, rounds, raw_nw, legal_mask}`.

### 4.2 Env A: "Blueprint" (faithful to the doc)
- **Observation** `Box(-1, 5, (32,))`: `[ai_pos/39, opp_pos/39, ai_cash/2000, opp_cash/2000]` + 28 properties ∈ {0 unowned, 1 AI, 2 AI with ≥1 house, −1 opponent}.
- **Action** `Discrete(3)`: 0 Pass · 1 Buy current tile · 2 Build (on the owned monopoly group with the fewest houses; ties go to the higher rent; requires cash ≥ house cost).
- **Step** = one agent turn: apply action at the current tile → opponent turn → agent rolls & moves → resolve landing. Invalid action ⇒ Pass.

### 4.3 Env B: "Masked" (our design)
- **Decision points only:** (a) buy decision on an affordable unowned tile, (b) pre-roll build decision when ≥1 build is legal. Everything else is simulated inside `step()`.
- **Action** `Discrete(10)`: 0 Pass · 1 Buy · 2–9 Build on colour group 1–8.
- **`action_masks()`** → bool[10] (used by `sb3_contrib.MaskablePPO`). Running B **without** masks (invalid ⇒ Pass) is a separate ablation.
- **Observation** `Box(133,)`, all values in [−1, 1]:
  - self (5): pos/39, clip(cash/3000), in_jail, has_jail_card, nw_share
  - opponent (5): same
  - 28 properties × 4 = 112: owned_by_self, owned_by_opp, houses/5, mortgaged
  - context (11): decision_type one-hot [buy, build] (2), current tile price/400 (1), buildable-group mask (8)

### 4.4 Rewards (`rewards.py`)
Weighted net worth (Bonjour/Haliem et al. Eq. 2–3):
```
nw_x = cash_x + Σ_{a ∈ assets_x} [ (price_a − mortgage_owed_a) · b_a + houses_a · house_cost_a ]
b_a = 2.0 if a is in a completed group else 1.5       (configurable; ablation b = 1.0)
share_t = nw_AI / (nw_AI + nw_opp)                      (our bounded 2-player adaptation of Eq. 4)
```
| Mode | Per-step reward | Terminal |
|---|---|---|
| `delta_share` (**default**) | `share_t − share_{t−1}` | ±c |
| `absolute_share` (blueprint) | `share_t` | ±c |
| `sparse` | 0 | ±c |

Default c = 10 (paper: best for DDQN). Also try c = 1 for PPO, since the paper used c = 0 for PPO.

### 4.5 Algorithms (stable-baselines3 2.x, sb3-contrib)
| Algo | Env | Notes |
|---|---|---|
| DQN | A, B-unmasked | Arun et al. lineage; `exploration_fraction=0.3`, buffer 100k |
| PPO | A, B-unmasked | Bonjour/Haliem lineage; `n_steps=2048, batch=256, ent_coef=0.01` |
| MaskablePPO | B | main agent |

Policy net: MLP [128, 128]. Start from SB3 defaults; tune only if time allows (log every change in DECISIONS).

### 4.6 Experiment matrix (3 seeds each, 300k steps unless noted)
| Exp | Question | Configs |
|---|---|---|
| E1 | DQN vs PPO (blueprint setting) | {DQN, PPO} × Env A × vs Fixed |
| E2 | Does env design + masking help? | PPO-A · PPO-B-unmasked · MaskablePPO-B (vs Fixed) |
| E3 | Reward design | MaskablePPO-B × {delta, absolute, sparse} |
| E4 | Property bonus | MaskablePPO-B × b ∈ {1.0, 1.5/2.0} |
| E5 *(stretch)* | Training-opponent generalisation | MaskablePPO-B trained vs {Random, Fixed, Mixed}; evaluated vs all |

Evaluation: 1,000 games per (model, opponent), random seat, Wilson 95% CI, plus mean rounds, mean final cash, % of games ending in bankruptcy.

## 5. Event schema (engine → API → UI)
```json
{ "seq": 57, "round": 12, "player": 0,
  "type": "dice_rolled | moved | passed_go | bought | declined | rent_paid | tax_paid |
           card_drawn | built | sold_house | mortgaged | jailed | left_jail | bankrupt | game_over | decision",
  "data": { "...type-specific..." },
  "state_hash": "a1b2c3" }
```
Examples: `moved {from: 7, to: 15, path: [8..15]}` · `rent_paid {to: 1, amount: 50, tile: 15}` · `card_drawn {deck: "chance", card_id: "c07", text: "..."}`.

**`decision` event (AI only), the X-Ray payload:**
```json
{ "type": "decision", "player": 0,
  "data": { "decision_type": "buy", "tile": 39,
            "actions": ["Pass","Buy","Build:Brown", "..."],
            "legal":   [true, true, false, "..."],
            "probs":   [0.08, 0.92, 0, "..."],     // PPO / MaskablePPO
            "q_values": null,                       // DQN
            "value": 0.63, "chosen": 1,
            "reward": {"share_before": 0.48, "share_after": 0.52, "delta": 0.04},
            "explanation": "Buys Mumbai: completes nothing yet, but 92% policy confidence" } }
```

## 6. REST API (FastAPI, prefix `/api`)
| Method | Path | Body → Response |
|---|---|---|
| GET | `/health` | → `{ok}` |
| GET | `/agents` | → `[{id, algo, env, trained_vs, steps, win_rate_vs_fixed}]` |
| POST | `/games` | `{mode, agent_id, opponent, seed?}` → `{game_id, state}` |
| GET | `/games/{id}` | → `{state}` |
| POST | `/games/{id}/advance` | `{max_events?}` → `{events[], state, awaiting: null \| {player, decision_type, legal_actions}}` |
| POST | `/games/{id}/action` | `{action}` → same as advance |
| DELETE | `/games/{id}` | → `{ok}` |
| GET | `/results` | → summary JSON for the Results page |

`state`: `{round, current_player, players:[{name, token, cash, position, in_jail, jail_cards, nw, nw_weighted}], tiles:[{idx, owner, houses, mortgaged}], last_dice, finished, winner}`.

## 7. Frontend
- **Stack:** Vite + React 18 + TypeScript, Tailwind CSS, Framer Motion (tokens/dice), Recharts (charts), Zustand (state), React Router.
- **Board:** CSS grid 11×11; tiles 0–10 bottom row (right→left), 11–19 left column, 20–30 top row, 31–39 right column; centre spans 9×9.
- **Animation loop:** the API returns a batch of events; the UI plays them in order (dice 600 ms → hop 150 ms/tile → transaction toast), then requests more. Speed slider ×0.5–×4; "instant" mode for auto-play.
- **Theme tokens:** saffron `#FF9933`, deep teal `#0F766E`, indigo `#312E81`, cream board `#FFF8E7`; group colours with text labels for colour-blind users; ₹ formatting via `Intl.NumberFormat('en-IN')`.
- **Pages:** `/play` (mode picker → game), `/results`, `/how-it-works`.

## 8. Testing
| Layer | Tooling | Must cover |
|---|---|---|
| Engine | pytest (+ hypothesis optional) | each rent case, GO, doubles/jail, cards, liquidation, bankruptcy, 200-round end, invariants over 10k random games |
| Envs | pytest, `check_env` | obs bounds, mask correctness, reward modes, determinism with seed |
| API | pytest + httpx TestClient | create/advance/action flow, human illegal action → 422 |
| UI | Vitest + React Testing Library; one Playwright smoke test | board renders 40 tiles, a full auto-played game finishes |

## 9. Tooling
- Python 3.12 venv; `pip install -r requirements.txt` (gymnasium, stable-baselines3, sb3-contrib, torch (CPU is fine), fastapi, uvicorn, pydantic, numpy, pandas, matplotlib, pyyaml, pytest, ruff).
- Node 20+ (local: Node 24, npm 11).
- Formatting: ruff (Python), prettier + eslint (TS).
- Git: `main` is protected by convention; feature branches `feat/<area>-<thing>`; PR review by one teammate.
