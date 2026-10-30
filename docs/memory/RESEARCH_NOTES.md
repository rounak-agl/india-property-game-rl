# Research Notes (verified)

> Checked against the primary sources on 2026-10-30. When the blueprint PDF and this file disagree, **this file wins**.

## 1. Bailis, Fachantidis & Vlahavas (2014)
**Citation:** P. Bailis, A. Fachantidis, I. Vlahavas, "Learning to play Monopoly: A Reinforcement Learning approach," *Proc. 50th Anniversary Convention of the AISB*, 2014. PDF: https://www.doc.gold.ac.uk/aisb50/AISB50-S02/AISB50-S2-Bailis-paper.pdf
- **MDP:** 23-value state.
  - Area: 10 groups × 2, ownership/development fraction with thresholds at 12/17. 12 is the LCM of group sizes 2, 3 and 4; adding 5 for the maximum buildings gives the denominator 17.
  - Position relative to colour group (1 value).
  - Finance (2 values): property-count ratio and sigmoid cash `x/(1+|x|)`.
- **Actions:** per group, Spend / Sell / Do nothing. Spend = build or buy; Sell = sell hotel → house → mortgage.
- **Reward:** `r = (v/p·c) / (1 + |v/p·c|) + (1/p)·m`, where p = number of players, c = smoothing factor, v = own asset value − opponents', m = own share of all money.
- **Algorithm:** Q(λ)-learning with a 3-layer back-prop NN. Parameters: a = 0.2, γ = 0.95, NN α = 0.2, λ = 0.85. **Not DQN.**
- **They did implement auctions** (a bidding contest); they did not implement trading.
- **Fixed-policy agent:** sells if money < 150, buys if > 350, otherwise nothing. Fixed beat Random 97% to 3% over 1,000 games.
- **Results:**
  - RL agent vs Random: 100% after 1,000 training episodes (average of 25 trials).
  - **3-player table** of Random + Fixed + RL over 1,000 games: RL 69.4%, Fixed 28.6%, Random 2%.

## 2. Arun, Rajesh, Chakrabarti, Cherala & George (2019)
**Citation:** E. Arun, H. Rajesh, D. Chakrabarti, H. Cherala, K. George, "Monopoly using reinforcement learning," *TENCON 2019 – IEEE Region 10 Conference*, Kochi, India, pp. 858–862, 2019.
- Full text not accessed (IEEE paywall). The facts below come from Bonjour/Haliem et al.'s related-work section; **cite cautiously**:
  - actions limited to **buy / do nothing**;
  - feed-forward NN with **experience replay** (DQN-style);
  - found that a **higher-dimensional state representation improves performance**;
  - supports the idea that **no single strategy maintains high win rates against all others**.
- Bonjour/Haliem et al. compare their state representation and reward function against Arun's (their Fig. 6–7).

## 3. Bonjour, Haliem et al. (2022)
**Citation:** T. Bonjour, M. Haliem, A. Alsalem, S. Thomas, H. Li, V. Aggarwal, M. Kejriwal, B. Bhargava, "Decision Making in Monopoly using a Hybrid Deep Reinforcement Learning Approach," *IEEE Trans. Emerging Topics in Computational Intelligence*, 2022. arXiv:2103.00683 (v4, Apr 2022).
⚠ The first author is **Bonjour**, not Haliem. Write it as "Bonjour, Haliem et al."
- **Setting:** full **4-player** game with trading. State is 240 dims (16 player + 224 property); action space is 2,922 dims.
- **Reward:**
  - Eq. 1: ±c at win/loss, otherwise the in-game reward r_x.
  - Eq. 2: `nw_x = c_x + Σ p_a`.
  - Eq. 3: `p_a = (bp − mv)·b + n_h·p_h + n_H·p_H`, with **b = 1.5** for a non-monopoly asset and **b = 2** for a monopoly asset.
  - Eq. 4: `r_x = nw_x / Σ_{y ≠ x} nw_y` (others only).
- **c:** tested {0, 1, 10, 20, 50, 100}. **c = 10** was best for DDQN; **c = 0** was used for PPO.
- **Algorithms:** PPO and DDQN, each in a standard and a **hybrid** form (DRL for frequent decisions, fixed policy for rare ones). Masking of invalid actions.
- **Results vs fixed-policy agents** (4-player): hybrid PPO **91.65%**, standard PPO 69.95%. Hybrid agents won ~30% more games than standard ones.

## 4. Viva prep (answers grounded in the notes above)
1. **Why 2 players, no trading?** Following Bailis (no trading) and Arun (buy/pass only), a reduced action set makes the MDP learnable in our time budget. Bonjour/Haliem show that the full game needs 2,922 actions plus a hybrid architecture.
2. **Why the 1.5 / 2.0 weights?** Bonjour/Haliem Eq. 3: holding property is usually better than equal cash, and monopolies more so. We also ran b = 1.0 (E4) to measure the effect.
3. **Why reward the *change* in share?** The absolute share is always positive, so it rewards long games. The delta is potential-based shaping (Ng et al., 1999), which keeps the optimal policy unchanged.
4. **Why masking?** It removes invalid actions so learning focuses on real choices. Bonjour/Haliem mask too. We measured the effect in E2.
5. **Is the win rate comparable to the papers?** No: they used different player counts (3 or 4 vs our 2), different rules and different opponents. We compare *trends*, not absolute numbers.

## 5. Board source
World of Monopoly, "India" (Funskool India Ltd., Chennai, June 2008): https://www.worldofmonopoly.com/albert/india_uk.htm. It gives **names only**. "Chennai Central Railway Station" (index 5) and the city "Chennai" (index 32) are both genuinely on the board.

## 6. Additional references to cite
- A. Y. Ng, D. Harada, S. Russell, "Policy invariance under reward transformations," *ICML* 1999 (potential-based shaping).
- S. Huang, S. Ontañón, "A Closer Look at Invalid Action Masking in Policy Gradient Algorithms," *FLAIRS* 2022 (masking).
- A. Raffin et al., "Stable-Baselines3," *JMLR* 2021.
