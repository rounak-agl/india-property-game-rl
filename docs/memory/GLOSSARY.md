# Glossary

| Term | Meaning in this project |
|---|---|
| **Agent** | The RL-controlled player (always one of the 2 seats). |
| **Bot** | A rule-based opponent: Random, Fixed-Policy (Bailis 350/150 thresholds) or Greedy. |
| **Controller** | Anything that answers engine decisions: RL agent, bot or human (via the API). |
| **Decision point** | A moment with a real choice: buy an affordable unowned tile, or build before rolling. |
| **Env A / Blueprint** | 32-dim obs, Discrete(3) every turn, invalid ⇒ Pass (faithful to the PDF). |
| **Env B / Masked** | 133-dim obs, Discrete(10) only at decision points, invalid actions masked. |
| **Action mask** | Boolean vector of which actions are legal; MaskablePPO gives illegal actions zero probability. |
| **Raw net worth** | cash + property price (half if mortgaged) + house costs. Decides the winner at round 200. |
| **Weighted net worth** | Bonjour/Haliem Eq. 3: property × b (1.5, or 2.0 in a completed group) + houses. Used only for the reward. |
| **Share** | nw_AI / (nw_AI + nw_opp) using weighted net worth, in [0, 1]. |
| **delta_share** | Default per-step reward: share_t − share_{t−1}. |
| **c** | Terminal reward magnitude (±c for win/loss); default 10. |
| **Round** | Both players have taken a turn. The game ends at 200 rounds. |
| **Group** | A colour set (8 groups), plus Stations (4) and Utilities (2). |
| **Monopoly (lowercase)** | Owning all properties of a colour group; enables building and doubles base rent. |
| **Liquidation** | Automatic selling of houses then mortgaging when cash < 0. |
| **X-Ray** | UI panel showing the agent's action probabilities / Q-values, mask, value and reward for each decision. |
| **Seat** | Who moves first (0) or second (1); randomised every episode. |
| **Wilson CI** | Confidence interval for a win rate (better than the normal approximation near 0% or 100%). |
| **DQN / PPO / MaskablePPO** | Value-based / policy-gradient / policy-gradient-with-masking algorithms (SB3, sb3-contrib). |
