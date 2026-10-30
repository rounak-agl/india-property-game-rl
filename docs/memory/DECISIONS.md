# Decision Log

> Append-only. Format: ID · date · status · decision · why · alternatives considered.
> Status: **Accepted** (team/user confirmed) · **Proposed** (needs confirmation) · **Superseded by D-xxx**.

### D-001 · 2026-10-30 · Accepted · Original Indian theme, no official branding
**Decision:** Our own game name, logo, tokens, artwork and card text. The board uses the Funskool India space names (real place names) and the classic square layout and rules. The report states that the environment models Monopoly rules for research.
**Why:** Monopoly's name, trade dress and artwork are protected IP; an original theme avoids copying them and looks more distinctive.
**Alternatives:** minimal neutral research look (rejected: less engaging demo).

### D-002 · 2026-10-30 · Accepted · FastAPI backend + React/TypeScript frontend
**Why:** A real animated board game is impractical in Streamlit (it reruns the whole script on every click). Python keeps the engine and models in one language.
**Alternatives:** Streamlit (blueprint; rejected), static web + ONNX in the browser (rejected: rules would need implementing twice).

### D-003 · 2026-10-30 · Accepted · Medium rule depth
Real rent tables, station/utility rent, jail (3 turns, doubles, ₹50, card), two original 16-card decks, forced liquidation only. **No** trading, auctions, voluntary mortgages or even-building rule.
**Alternatives:** blueprint-simple (20% rent, cash-only cards), near-full.

### D-004 · 2026-10-30 · Accepted · Build both env designs as an experiment
Env A "Blueprint" (32-dim, Discrete(3), every turn, invalid ⇒ Pass) and Env B "Masked" (decision points, 133-dim, Discrete(10), MaskablePPO). Comparing them is experiment E2.

### D-005 · 2026-10-30 · Accepted · Memory docs = repo docs for team + AI
`CLAUDE.md` + `docs/memory/*`, updated every working session.

### D-006 · 2026-10-30 · Accepted · Web slide deck for the presentation
Built at the end (Phase 6), with embedded result figures and a demo GIF.

### D-007 · 2026-10-30 · **Proposed** · Classic standard-edition prices/rents in ₹
**Why:** The only source for the Funskool India board (World of Monopoly) lists names but no prices. Rather than invent numbers, we use the classic price/rent structure and say so.
**Needs:** team confirmation, or values from someone who owns the physical board (OPEN_QUESTIONS Q2).

### D-008 · 2026-10-30 · Proposed · Default reward = delta of net-worth share + terminal ±c
`share = nw_AI/(nw_AI+nw_opp)` with Bonjour/Haliem weighted net worth (b = 1.5 / 2.0). Per-step reward = Δshare; terminal ±10.
**Why:** The blueprint's absolute share is always positive and rewards prolonging games. The delta version is potential-based shaping, so it doesn't change the optimal policy. The absolute version is kept as ablation E3.

### D-009 · 2026-10-30 · Proposed · Game ends at 200 rounds → higher raw net worth wins
From the blueprint. A round = both players take a turn. Ending at round 200 is a game rule, so the env returns `terminated=True` (not `truncated`).

### D-010 · 2026-10-30 · Proposed · Random seat assignment each episode
**Why:** Avoids learning a first-mover bias; makes evaluation fair.

### D-011 · 2026-10-30 · Proposed · Jail decisions handled by a fixed rule for all players
**Why:** Rare decision, which matches the hybrid idea in Bonjour/Haliem et al. (DRL for frequent decisions, rules for infrequent ones). Rule: pay ₹50 if cash > ₹500 and round < 100, otherwise try for doubles.
