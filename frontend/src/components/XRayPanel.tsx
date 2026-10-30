import { pct, rupees } from '../lib/format'
import type { DecisionData, TileInfo } from '../types/api'

const ALGO_NAMES: Record<string, string> = { maskppo: 'MaskablePPO', ppo: 'PPO', dqn: 'DQN' }

export function XRayPanel({ decision, board, count }: { decision: DecisionData | null; board: TileInfo[]; count: number }) {
  if (!decision) {
    return (
      <section className="card xray">
        <h3>AI Brain X-Ray</h3>
        <p className="muted">Waiting for the agent's first decision. Every time the RL agent decides, you'll see what its network thought here.</p>
      </section>
    )
  }
  const useProbs = decision.probs !== null
  const values = (useProbs ? decision.probs : decision.q_values) ?? []
  const legalValues = values.filter((_, i) => decision.legal[i])
  const max = Math.max(...legalValues.map(Math.abs), 1e-9)
  const tile = decision.tile !== null ? board[decision.tile] : null
  const rows = decision.actions.map((name, i) => ({ name, value: values[i], legal: decision.legal[i], chosen: i === decision.chosen }))
    .filter((r) => r.legal)
  return (
    <section className="card xray" aria-live="polite">
      <h3>AI Brain X-Ray <small className="muted">#{count}</small></h3>
      <p className="xray-context">
        <strong>{decision.decision_type === 'build' ? 'Build or save cash?' : tile ? `Buy ${tile.name}?` : 'Turn decision'}</strong>
        {tile && tile.price > 0 && decision.decision_type !== 'build' && <> · {rupees(tile.price)}</>}
      </p>
      <p className="muted small">{ALGO_NAMES[decision.algo]} on Env {decision.env} · {useProbs ? 'policy probability' : 'Q-value'} per legal action</p>
      <ul className="bars">
        {rows.map((r) => (
          <li key={r.name} className={r.chosen ? 'chosen' : ''}>
            <span className="bar-label">{r.name}{r.chosen ? ' ✓' : ''}</span>
            <span className="bar-track">
              <span className="bar-fill" style={{ width: `${Math.max(2, (Math.abs(r.value) / max) * 100)}%` }} />
            </span>
            <span className="bar-value">{useProbs ? pct(r.value) : r.value.toFixed(3)}</span>
          </li>
        ))}
      </ul>
      <div className="xray-foot">
        <div>
          <small>Net-worth share (reward signal)</small>
          <div className="gauge"><span style={{ width: pct(decision.share) }} /></div>
          <strong>{pct(decision.share)}</strong>
        </div>
        {decision.value !== null && (
          <div><small>{useProbs ? 'Critic value' : 'Best Q'}</small><strong>{decision.value.toFixed(2)}</strong></div>
        )}
      </div>
      <p className="explain">
        Chose <strong>{decision.chosen_label}</strong>
        {useProbs && decision.probs ? ` with ${pct(decision.probs[decision.chosen])} confidence.` : ' (highest Q-value).'}
      </p>
    </section>
  )
}
