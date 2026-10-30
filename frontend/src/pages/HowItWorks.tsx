export default function HowItWorks() {
  return (
    <div className="page prose">
      <h1>How it works</h1>
      <p>
        We model a 2-player property-trading game on a 40-space board of Indian cities and railway stations as a
        <strong> Markov Decision Process</strong>. The opponent bot, dice and cards are part of the environment, and the
        RL agent only chooses at real decision points.
      </p>

      <h2>1 · The game</h2>
      <ul>
        <li>₹1,500 starting cash, ₹200 for passing GO, standard rent tables, stations and utilities.</li>
        <li>Jail (3 attempts at doubles or a ₹50 fine), two original 16-card decks, forced liquidation, bankruptcy.</li>
        <li>No trading or auctions, following Bailis et al. (2014) and Arun et al. (2019). The game ends at bankruptcy or after 200 rounds (higher net worth wins).</li>
      </ul>

      <h2>2 · Two environment designs</h2>
      <div className="two-col">
        <div className="card">
          <h3>Env A · Blueprint</h3>
          <p>32 numbers: both positions, both cash amounts, and one code per property (unowned / mine / mine with houses / opponent's).</p>
          <p>3 actions asked after <em>every</em> move: Pass, Buy, Build. Impossible actions silently do nothing.</p>
        </div>
        <div className="card">
          <h3>Env B · Masked (ours)</h3>
          <p>133 numbers: player features plus 4 features per property (mine, theirs, houses, mortgaged) and the decision context.</p>
          <p>10 actions (Pass, Buy, Build on one of 8 groups), asked only when a real choice exists, with illegal actions <strong>masked</strong> (MaskablePPO).</p>
        </div>
      </div>

      <h2>3 · Reward</h2>
      <p>Weighted net worth from Bonjour, Haliem et al. (2022): property counts as 1.5× its price, or 2× in a completed colour set, plus houses.</p>
      <pre className="formula">{`nw   = cash + Σ (price − mortgage) · b + houses · house_cost
share = nw_agent / (nw_agent + nw_opponent)
reward_t = share_t − share_{t−1}      (+10 win / −10 loss at the end)`}</pre>
      <p>Paying the <em>change</em> in share avoids rewarding the agent for simply making games longer. We compare it against the absolute-share and win/loss-only rewards on the Results page.</p>

      <h2>4 · Agents and baselines</h2>
      <ul>
        <li><strong>DQN</strong> (value-based, like Arun et al. 2019), <strong>PPO</strong> and <strong>MaskablePPO</strong> (policy-gradient, like Bonjour, Haliem et al. 2022), via Stable-Baselines3.</li>
        <li><strong>Random bot</strong> (buys with 50% probability), <strong>Fixed-Policy bot</strong> (spends only above ₹350, Bailis et al. 2014) and <strong>Greedy bot</strong> (always buys and builds).</li>
      </ul>

      <h2>5 · The AI Brain X-Ray</h2>
      <p>For every agent decision the backend records the network's output: action probabilities (PPO family) or Q-values (DQN), which actions were legal, the critic's value estimate, and the current net-worth share.</p>

      <h2>References</h2>
      <ol className="refs">
        <li>P. Bailis, A. Fachantidis, I. Vlahavas. Learning to play Monopoly: A Reinforcement Learning approach. AISB 50, 2014.</li>
        <li>E. Arun, H. Rajesh, D. Chakrabarti, H. Cherala, K. George. Monopoly using reinforcement learning. TENCON 2019, pp. 858–862.</li>
        <li>T. Bonjour, M. Haliem, et al. Decision Making in Monopoly using a Hybrid Deep Reinforcement Learning Approach. IEEE TETCI, 2022 (arXiv:2103.00683).</li>
        <li>A. Raffin et al. Stable-Baselines3: Reliable Reinforcement Learning Implementations. JMLR, 2021.</li>
      </ol>
      <p className="muted small">This is an original game for research and teaching. It follows Monopoly's rules but uses no Hasbro or Funskool branding, artwork or card text.</p>
    </div>
  )
}
