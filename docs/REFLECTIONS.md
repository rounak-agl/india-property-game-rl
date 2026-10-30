# Reflections on the Original Blueprint

> Review of `Indian Monopoly RL Agent Blueprint.pdf` (17 pages), written 2026-10-30.
> Every claim about the papers below was checked against the papers themselves (see [`memory/RESEARCH_NOTES.md`](memory/RESEARCH_NOTES.md)).

## 1. What the blueprint gets right

| Strength | Why it matters |
|---|---|
| **Aggressive but defensible scoping** (2 players, no trading, no auctions) | Both Bailis et al. (2014) and Arun et al. (2019) used reduced action sets, so we can cite a precedent for the simplification. |
| **Three-paper literature arc** (Bailis 2014 → Arun 2019 → Bonjour/Haliem 2022) | Gives a clear story from tabular-ish Q(λ) → DQN → hybrid PPO/DDQN on the full game. |
| **Two baselines** (Random bot + Bailis fixed-policy bot) | Lets us show learning progress against a weak and a reasonable opponent. |
| **DQN vs PPO comparison** | A value-based vs a policy-gradient method is a natural experiment for an AI course. |
| **"AI Brain X-Ray"** (live action probabilities / Q-values) | Explainability is what makes the demo memorable; we keep it. |
| **Net-worth based dense reward** | Correctly identified as the key trick from Bonjour/Haliem et al. |

## 2. Problems found, and how the plan fixes them

### 2.1 Reward design (high impact)
- **Problem:** The blueprint pays `r_t = nw_AI / (nw_AI + nw_Bot)` **every step**. That is always positive (≈0.5 at the start), so the return grows with episode length: the agent is paid for *prolonging* games, not for winning them.
- **Also:** Bonjour/Haliem et al.'s Eq. 4 divides by the net worth of the *other* players, not by the sum including yourself. The blueprint silently changed this. Its version is actually nicer (bounded in [0,1]), but we must say it is our adaptation.
- **Fix:** Use the **change in share**, `r_t = share_t − share_{t−1}` (potential-based shaping, which leaves the optimal policy unchanged), plus a terminal ±c. Keep the blueprint's absolute version as an **ablation** so we can show *why* we changed it.
- **Note:** In the paper, c = 10 worked best for DDQN while PPO used c = 0. We test both.

### 2.2 The 1.5× / 2.0× property bonus
- Counting a ₹P property as 1.5·P makes **every purchase an instant reward of +0.5·P**, so "always buy" is baked in. The fixed-policy bot already does roughly that.
- **Fix:** Keep b = 1.5 / 2.0 as in the paper (Eq. 3) but make `b` configurable and run one ablation with b = 1.0.

### 2.3 Action design (high impact)
- **Problem:** The agent picks Pass / Buy / Build on *every* turn, including tax squares, Chance and opponent-owned tiles. Invalid actions silently become Pass, so most transitions carry no learning signal and the agent cannot tell "my Buy failed" from "I passed".
- **Problem:** "Build" doesn't say **which** colour group to build on.
- **Fix (team decision D-004: build both):**
  - **Env A, "Blueprint":** exactly as written (Discrete(3), every turn, 32-dim state) to stay faithful to the doc and act as a baseline.
  - **Env B, "Masked":** the agent is only asked at real decision points, uses Discrete(10) = {Pass, Buy, Build on group 1…8}, and invalid actions are masked using `MaskablePPO` from `sb3-contrib`. Bonjour/Haliem et al. also mask invalid actions.
  - Comparing A and B becomes a headline experiment.

### 2.4 State representation
- The 32-dim vector encodes "house built" as a single value 2.0, so it **cannot tell 1 house from a hotel**. It also has no opponent houses, no jail status and no mortgage flags.
- Arun et al. (2019) found that a **higher-dimensional state improves performance** (as summarised by Bonjour/Haliem et al.).
- **Fix:** Env A keeps 32 dims for faithfulness. Env B uses ~123 dims (per property: owner-self, owner-opp, houses/5, mortgaged; plus player and decision-context features). See `TECH_SPEC.md`.

### 2.5 Rules that were missing or undefined
Station rent, utility rent, the jail turn-skip and doubles were all left undefined, and Chance/Community Chest was reduced to random cash. The team chose **Medium rule depth** (D-003):
- real rent tables (base, monopoly ×2, 1–4 houses, hotel)
- station and utility rent
- jail with the 3-turn / doubles rule
- small fixed card decks (original card text)
- forced selling/mortgaging only to avoid bankruptcy
- still no trading or auctions

### 2.6 Board data
- The source the blueprint cites (World of Monopoly, Funskool India 2008) gives the **40 space names only, with no prices or rents**. The rupee values in the blueprint are the **classic London-edition numbers** with Indian names on top; they are not verified Funskool values.
- The duplicate "Chennai" (Chennai Central Railway Station at index 5 and the city Chennai at index 32) **is correct**. It matches the Funskool board, so it isn't a typo.
- **Fix:** Use the verified 40 names, but keep the classic price/rent structure denominated in ₹ and **say so explicitly** (D-007, pending team confirmation in `OPEN_QUESTIONS.md`).

### 2.7 Unverified or misquoted research claims
| Blueprint says | What the paper actually says |
|---|---|
| Bailis: "69.4% win rate against a Fixed-Policy Rule Bot" | 69.4% in **1000 three-player games** (RL agent + fixed-policy + random at the same table). It isn't a head-to-head figure. |
| Bailis: "no auctions" | Bailis **did** implement a bidding contest (auctions). It had no *trading*. |
| Bailis used "Basic DQN" | **Q(λ)-learning** with a 3-layer NN (α=0.2, γ=0.95, λ=0.85). There was no replay buffer, so it isn't DQN. |
| "Haliem et al." as first author | First author is **Trevor Bonjour**; Marina Haliem is second (IEEE TETCI 2022, arXiv:2103.00683). Cite it as *Bonjour, Haliem et al.* |
| Haliem: "91% win rate" | Correct: hybrid PPO **91.65%** vs fixed-policy agents in **4-player** games. Standard PPO got 69.95%. |
| Training curve "rising from ~35% to 75–90%+" | A prediction with no source. **We only report what we measure.** |
| Arun et al. (TENCON 2019) | Confirmed: *Monopoly using reinforcement learning*, TENCON 2019, pp. 858–862. Buy / do-nothing actions, FFNN + experience replay. We couldn't access the full text, so cite it carefully. |

### 2.8 UI stack
- Streamlit reruns the whole script on every click, so smooth token movement, dice animation and a real square board are impractical.
- **Fix (D-002):** a **FastAPI** backend (engine + trained models) with a **React + TypeScript** frontend that renders a real 40-tile board with animated tokens, dice, cards, an X-Ray panel and a results page.

### 2.9 Branding / IP
- "Monopoly", the board's trade dress and the Funskool artwork are Hasbro/Funskool property. **We don't reproduce them.**
- **Fix (D-001):** an **original Indian-themed** board game (own name, own artwork, original card text) that follows Monopoly's *rules*. The report states plainly that the environment models Monopoly rules for research.

### 2.10 Evaluation rigour
- The blueprint used one training run and one evaluation number.
- **Fix:**
  - 3–5 random seeds per configuration
  - 1,000 evaluation games each, with the starting player randomised (first-move advantage is real)
  - report mean ± 95% CI and average game length

## 3. Net effect on scope
The plan grows from "4 files in 1 week" to a 4-person, ~12-working-day project. A **Day-7 MVP cut line** (AI vs Bot playable in the real UI with a trained model) keeps it safe if time runs short. See [`PHASES.md`](PHASES.md).
