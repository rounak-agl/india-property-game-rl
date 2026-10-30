import { Fragment, useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ErrorBar, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../lib/api'
import { GROUP_COLORS, pct, rupees } from '../lib/format'
import type { ResultsSummary } from '../types/api'

const LINE_COLORS = ['#ea7317', '#14837b', '#4338ca', '#d6458f', '#8a5a32', '#e8b81d', '#1f9a55', '#27408b', '#d63a2f']
const GROUP_IDS: Record<string, number> = { Brown: 1, 'Light Blue': 2, Pink: 3, Orange: 4, Red: 5, Yellow: 6, Green: 7, 'Dark Blue': 8 }

export default function Results() {
  const [data, setData] = useState<ResultsSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [opp, setOpp] = useState<'fixed' | 'random' | 'greedy'>('fixed')

  useEffect(() => { api.results().then(setData).catch((e) => setError(e.message)) }, [])

  const curveData = useMemo(() => {
    if (!data) return []
    const rows: Record<number, Record<string, number>> = {}
    for (const [name, byOpp] of Object.entries(data.curves)) {
      const c = byOpp[opp === 'greedy' ? 'fixed' : opp]
      c?.timesteps.forEach((t, i) => { rows[t] = { ...(rows[t] ?? { t }), [name]: c.mean[i] } })
    }
    return Object.values(rows).sort((a, b) => a.t - b.t)
  }, [data, opp])

  if (error) return <div className="page"><div className="alert">No results yet: {error}</div></div>
  if (!data) return <div className="page"><p className="muted">Loading results…</p></div>

  const best = data.final[data.best.config]
  const bars = Object.entries(data.final).map(([name, r]) => ({
    name: r.label,
    key: name,
    win: r.vs[opp].win_rate,
    err: [r.vs[opp].win_rate - r.vs[opp].ci_low, r.vs[opp].ci_high - r.vs[opp].win_rate],
  }))
  const behaviour = Object.entries(data.behaviour.buy_rate_by_group).map(([g, rate]) => ({ group: g, rate, fill: GROUP_COLORS[GROUP_IDS[g]] ?? '#6b6257' }))

  return (
    <div className="page results">
      <header className="page-head">
        <h1>Experiment results</h1>
        <p className="muted">Every number on this page is read from <code>results/summary/summary.json</code>, produced by <code>python -m src.rl.make_plots</code>. Win rates are pooled over all seeds (1,000 evaluation games per seed) with 95% Wilson intervals.</p>
      </header>

      <div className="kpis">
        <div className="card kpi"><small>Best agent</small><strong>{best.label}</strong><span className="muted">{data.best.run_id}</span></div>
        {(['random', 'fixed', 'greedy'] as const).map((o) => (
          <div key={o} className="card kpi">
            <small>Best agent vs {o} bot</small>
            <strong>{pct(best.vs[o].win_rate)}</strong>
            <span className="muted">95% CI {pct(best.vs[o].ci_low)}–{pct(best.vs[o].ci_high)}</span>
          </div>
        ))}
      </div>

      <div className="segmented" role="radiogroup" aria-label="Opponent">
        {(['fixed', 'random', 'greedy'] as const).map((o) => (
          <button type="button" key={o} className={opp === o ? 'on' : ''} onClick={() => setOpp(o)}>vs {o}</button>
        ))}
      </div>

      <section className="card chart">
        <h3>Final win rate by configuration (vs {opp})</h3>
        <ResponsiveContainer width="100%" height={360}>
          <BarChart data={bars} margin={{ top: 10, right: 16, bottom: 90, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" angle={-30} textAnchor="end" interval={0} height={90} tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 1]} tickFormatter={(v) => pct(v, 0)} />
            <Tooltip formatter={(v: number) => pct(v)} />
            <ReferenceLine y={0.5} stroke="#999" strokeDasharray="4 4" />
            <Bar dataKey="win" name="win rate" fill="#ea7317" radius={[4, 4, 0, 0]}>
              <ErrorBar dataKey="err" width={4} stroke="#3c3530" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="card chart">
        <h3>Learning curves (periodic evaluation vs {opp === 'greedy' ? 'fixed' : opp}, mean over seeds)</h3>
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={curveData} margin={{ top: 10, right: 16, bottom: 10, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="t" tickFormatter={(v) => `${v / 1000}k`} />
            <YAxis domain={[0, 1]} tickFormatter={(v) => pct(v, 0)} />
            <Tooltip formatter={(v: number) => pct(v)} labelFormatter={(v) => `${v} steps`} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {Object.keys(data.curves).map((name, i) => (
              <Line key={name} dataKey={name} name={data.final[name]?.label ?? name} stroke={LINE_COLORS[i % LINE_COLORS.length]} dot={false} strokeWidth={2} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </section>

      <div className="two-col">
        <section className="card">
          <h3>Experiments</h3>
          <table className="table">
            <thead><tr><th>Configuration</th><th>vs Random</th><th>vs Fixed</th><th>vs Greedy</th><th>Invalid actions</th></tr></thead>
            <tbody>
              {Object.entries(data.experiments).map(([exp, names]) => (
                <Fragment key={exp}>
                  <tr className="group-row"><td colSpan={5}>{exp}</td></tr>
                  {names.map((n) => (
                    <tr key={`${exp}-${n}`}>
                      <td>{data.final[n].label}</td>
                      {(['random', 'fixed', 'greedy'] as const).map((o) => <td key={o}>{pct(data.final[n].vs[o].win_rate)}</td>)}
                      <td>{pct(data.final[n].vs.fixed.invalid_action_rate)}</td>
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
          <h3>Rule-bot baselines</h3>
          <table className="table">
            <thead><tr><th>Bot</th><th>Opponent</th><th>Win rate</th></tr></thead>
            <tbody>
              {data.baselines.map((b) => (
                <tr key={`${b.agent}-${b.opponent}`}><td>{b.agent}</td><td>{b.opponent}</td><td>{pct(b.win_rate)}</td></tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card chart">
          <h3>What the best agent learned: buy rate by colour group</h3>
          <p className="muted small">{data.behaviour.games} games vs Fixed bot. How often it buys when it lands on an unowned, affordable property.</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={behaviour} margin={{ top: 10, right: 10, bottom: 30, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="group" angle={-25} textAnchor="end" interval={0} tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 1]} tickFormatter={(v) => pct(v, 0)} />
              <Tooltip formatter={(v: number) => pct(v)} />
              <Bar dataKey="rate" name="buy rate" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="small">
            Average cash when buying: <strong>{data.behaviour.mean_cash_when_buying ? rupees(Math.round(data.behaviour.mean_cash_when_buying)) : '–'}</strong> ·
            when passing: <strong>{data.behaviour.mean_cash_when_passing ? rupees(Math.round(data.behaviour.mean_cash_when_passing)) : '–'}</strong>
          </p>
        </section>
      </div>
    </div>
  )
}
