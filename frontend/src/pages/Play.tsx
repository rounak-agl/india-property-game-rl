import { useCallback, useEffect, useRef, useState } from 'react'
import { Board } from '../components/Board'
import { Dice } from '../components/Dice'
import { PlayerPanel } from '../components/PlayerPanel'
import { PropertyCard } from '../components/PropertyCard'
import { XRayPanel } from '../components/XRayPanel'
import { api } from '../lib/api'
import { GAME_NAME, PLAYER_COLORS, describeEvent, pct, rupees } from '../lib/format'
import type { AgentInfo, DecisionData, GameEvent, GameState, TileInfo } from '../types/api'

type Mode = 'ai_vs_bot' | 'human_vs_ai'
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))
const reducedMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

interface LogLine { seq: number; text: string; player: number | null }

export default function Play() {
  const [board, setBoard] = useState<TileInfo[]>([])
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('ai_vs_bot')
  const [agentId, setAgentId] = useState<string>('')
  const [opponent, setOpponent] = useState('fixed')

  const [gameId, setGameId] = useState<string | null>(null)
  const [game, setGame] = useState<GameState | null>(null)
  const [positions, setPositions] = useState<number[]>([0, 0])
  const [dice, setDice] = useState<[number, number]>([0, 0])
  const [rollKey, setRollKey] = useState(0)
  const [log, setLog] = useState<LogLine[]>([])
  const [card, setCard] = useState<string | null>(null)
  const [banner, setBanner] = useState<string>('')
  const [decision, setDecision] = useState<DecisionData | null>(null)
  const [decisionCount, setDecisionCount] = useState(0)
  const [busy, setBusy] = useState(false)
  const [auto, setAuto] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [inspect, setInspect] = useState<number | null>(null)
  const runToken = useRef(0)
  const speedRef = useRef(speed)
  speedRef.current = speed

  useEffect(() => {
    api.board().then(setBoard).catch((e) => setError(e.message))
    api.agents().then((a) => {
      setAgents(a)
      setAgentId(a.find((x) => x.default)?.id ?? a[0]?.id ?? '')
    }).catch((e) => setError(e.message))
  }, [])

  const names = game?.players.map((p) => p.name) ?? ['Player 1', 'Player 2']

  const playEvents = useCallback(async (events: GameEvent[], final: GameState, token: number) => {
    const delay = (ms: number) => wait(reducedMotion ? 0 : ms / speedRef.current)
    const playerNames = final.players.map((p) => p.name)
    for (const e of events) {
      if (runToken.current !== token) return
      const text = describeEvent(e, board, playerNames)
      if (text) {
        setLog((l) => [{ seq: e.seq, text, player: e.player }, ...l].slice(0, 80))
        setBanner(text)
      }
      switch (e.type) {
        case 'dice_rolled':
          setDice([e.data.dice[0], e.data.dice[1]])
          setRollKey((k) => k + 1)
          await delay(550)
          break
        case 'moved':
          for (const step of e.data.path as number[]) {
            if (runToken.current !== token) return
            setPositions((pos) => pos.map((p, i) => (i === e.player ? step : p)))
            await delay(110)
          }
          await delay(120)
          break
        case 'jailed':
          setPositions((pos) => pos.map((p, i) => (i === e.player ? 10 : p)))
          await delay(400)
          break
        case 'card_drawn':
          setCard(e.data.text)
          await delay(900)
          break
        case 'decision':
          setDecision(e.data as DecisionData)
          setDecisionCount((c) => c + 1)
          await delay(700)
          break
        case 'bought': case 'rent_paid': case 'built': case 'tax_paid': case 'bankrupt':
          await delay(350)
          break
        default:
          break
      }
    }
    if (runToken.current !== token) return
    setGame(final)
    setPositions(final.players.map((p) => p.position))
  }, [board])

  const start = async () => {
    setError(null)
    runToken.current += 1
    setAuto(false)
    try {
      const res = await api.newGame({ mode, agent_id: agentId || undefined, opponent })
      setGameId(res.game_id)
      setGame(res.state)
      setPositions([0, 0])
      setDice([0, 0])
      setLog([])
      setCard(null)
      setDecision(null)
      setDecisionCount(0)
      setBanner(mode === 'human_vs_ai' ? 'You are the 🐯 tiger. Good luck against the AI!' : 'Press Step or Auto-play to start.')
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const step = useCallback(async (action?: number) => {
    if (!gameId || busy) return
    setBusy(true)
    const token = runToken.current
    try {
      const res = action === undefined ? await api.advance(gameId) : await api.act(gameId, action)
      await playEvents(res.events, res.state, token)
    } catch (e) {
      setError((e as Error).message)
      setAuto(false)
    } finally {
      setBusy(false)
    }
  }, [gameId, busy, playEvents])

  // Auto-play: watch mode when toggled; in human mode the AI's turns always run automatically.
  useEffect(() => {
    if (!game || game.finished || busy || game.awaiting) return
    const aiTurn = game.mode === 'human_vs_ai' && game.players[game.current_player].kind !== 'human'
    if (!(auto || aiTurn)) return
    const t = setTimeout(() => step(), reducedMotion ? 0 : 250 / speed)
    return () => clearTimeout(t)
  }, [game, busy, auto, step, speed])

  const humanTurn = game?.mode === 'human_vs_ai' && !game.finished && !game.awaiting
    && game.players[game.current_player].kind === 'human'
  const highlight = game?.awaiting?.tile ?? decision?.tile ?? null
  const winner = game?.finished ? (game.winner === null ? 'Draw' : `${names[game.winner]} wins!`) : null

  return (
    <div className="play">
      {error && <div className="alert" role="alert">⚠ {error}{error.includes('agents') && ' — train a model first (see README).'}</div>}

      <aside className="sidebar left">
        <section className="card setup">
          <h3>New game</h3>
          <div className="segmented" role="radiogroup" aria-label="Mode">
            <button type="button" className={mode === 'ai_vs_bot' ? 'on' : ''} onClick={() => setMode('ai_vs_bot')}>Watch AI vs Bot</button>
            <button type="button" className={mode === 'human_vs_ai' ? 'on' : ''} onClick={() => setMode('human_vs_ai')}>Play vs AI</button>
          </div>
          <label>RL agent
            <select value={agentId} onChange={(e) => setAgentId(e.target.value)}>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.id}{a.win_rates.fixed !== undefined ? ` · ${pct(a.win_rates.fixed, 0)} vs Fixed` : ''}{a.default ? ' ★' : ''}
                </option>
              ))}
            </select>
          </label>
          {mode === 'ai_vs_bot' && (
            <label>Opponent bot
              <select value={opponent} onChange={(e) => setOpponent(e.target.value)}>
                <option value="fixed">Fixed-Policy (Bailis 2014)</option>
                <option value="random">Random</option>
                <option value="greedy">Greedy</option>
              </select>
            </label>
          )}
          <button type="button" className="btn primary" onClick={start} disabled={!agentId}>Start new game</button>
        </section>

        {game && game.players.map((p) => (
          <PlayerPanel key={p.idx} player={p} board={board} tiles={game.tiles} active={!game.finished && game.current_player === p.idx} />
        ))}
      </aside>

      <main className="board-wrap">
        {board.length > 0 && (
          <Board
            board={board}
            tiles={game?.tiles ?? null}
            players={game?.players ?? []}
            positions={positions}
            highlight={highlight}
            onTileClick={setInspect}
          >
            <div className="logo">
              <span className="logo-mark">₹</span>
              <h1>{GAME_NAME}</h1>
              <p>A reinforcement-learning board game</p>
            </div>
            {game && (
              <>
                <div className="round">Round {game.round} / {game.max_rounds}</div>
                <Dice dice={dice} rollKey={rollKey} />
                <p className="banner" aria-live="polite">{winner ? `🏆 ${winner}` : banner}</p>
                {card && <div className="drawn-card">{card}</div>}

                {game.awaiting && (
                  <div className="decision-box">
                    <strong>
                      {game.awaiting.kind === 'buy' && game.awaiting.tile !== null
                        ? `Buy ${board[game.awaiting.tile].name} for ${rupees(board[game.awaiting.tile].price)}?`
                        : game.awaiting.kind === 'build' ? 'Build a house before rolling?' : 'You are in Jail'}
                    </strong>
                    <div className="decision-buttons">
                      {game.awaiting.legal.map((a) => (
                        <button key={a.action} type="button" className={`btn ${a.action === 1 ? 'primary' : ''}`} disabled={busy} onClick={() => step(a.action)}>
                          {a.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {humanTurn && (
                  <button type="button" className="btn roll" disabled={busy} onClick={() => step()}>🎲 Roll dice</button>
                )}
                {game.mode === 'ai_vs_bot' && !game.finished && (
                  <div className="controls">
                    <button type="button" className="btn" disabled={busy || auto} onClick={() => step()}>Step turn</button>
                    <button type="button" className={`btn ${auto ? 'on' : 'primary'}`} onClick={() => setAuto((a) => !a)}>{auto ? '⏸ Pause' : '⏩ Auto-play'}</button>
                  </div>
                )}
                <label className="speed">Speed
                  <input type="range" min={0.5} max={4} step={0.5} value={speed} onChange={(e) => setSpeed(Number(e.target.value))} />
                  <span>×{speed}</span>
                </label>
              </>
            )}
            {!game && <p className="banner">Choose a mode and press <strong>Start new game</strong>.</p>}
          </Board>
        )}
      </main>

      <aside className="sidebar right">
        <XRayPanel decision={decision} board={board} count={decisionCount} />
        {game && (
          <section className="card share">
            <h3>Net-worth share</h3>
            <div className="share-bar" aria-label={`RL agent share ${pct(game.share)}`}>
              <span style={{ width: pct(game.share), background: PLAYER_COLORS[0] }} />
              <span style={{ width: pct(1 - game.share), background: PLAYER_COLORS[1] }} />
            </div>
            <small className="muted">{names[0]} {pct(game.share)} · {names[1]} {pct(1 - game.share)} (weighted net worth, the agent's reward signal)</small>
          </section>
        )}
        <section className="card log">
          <h3>Game log</h3>
          <ol>
            {log.map((l) => (
              <li key={l.seq} style={{ borderLeftColor: l.player !== null ? PLAYER_COLORS[l.player] : '#999' }}>{l.text}</li>
            ))}
          </ol>
        </section>
      </aside>

      {inspect !== null && board[inspect] && (
        <PropertyCard tile={board[inspect]} state={game?.tiles[inspect] ?? null} players={game?.players ?? []} onClose={() => setInspect(null)} />
      )}
    </div>
  )
}
