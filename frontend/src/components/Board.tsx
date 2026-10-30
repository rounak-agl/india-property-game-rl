import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { GROUP_COLORS, PLAYER_COLORS, TOKENS, cellFor, rupees } from '../lib/format'
import type { PlayerView, TileInfo, TileView } from '../types/api'

const CORNER_ICON: Record<string, string> = { go: '➜', jail: '⛓', parking: '🅿', goto_jail: '👮' }
const KIND_ICON: Record<string, string> = { station: '🚆', chance: '?', chest: '🪔', tax: '₹', utility: '' }

interface Props {
  board: TileInfo[]
  tiles: TileView[] | null
  players: PlayerView[]
  positions: number[]
  highlight: number | null
  onTileClick?: (idx: number) => void
  children?: ReactNode
}

export function Board({ board, tiles, players, positions, highlight, onTileClick, children }: Props) {
  return (
    <div className="board" role="grid" aria-label="Game board">
      {board.map((t) => {
        const { row, col, side } = cellFor(t.idx)
        const state = tiles?.[t.idx]
        const owner = state?.owner ?? null
        const here = players.filter((p) => positions[p.idx] === t.idx && !p.bankrupt)
        return (
          <button
            key={t.idx}
            type="button"
            className={`tile tile-${side} kind-${t.kind}${highlight === t.idx ? ' highlight' : ''}${state?.mortgaged ? ' mortgaged' : ''}`}
            style={{ gridRow: row, gridColumn: col }}
            onClick={() => onTileClick?.(t.idx)}
            aria-label={`${t.name}${t.price ? `, ${rupees(t.price)}` : ''}${owner !== null ? `, owned by ${players[owner]?.name}` : ''}`}
          >
            {t.kind === 'city' && t.group && <span className="band" style={{ background: GROUP_COLORS[t.group] }} />}
            <span className="tile-body">
              {side === 'corner' ? (
                <>
                  <span className="corner-icon">{CORNER_ICON[t.kind]}</span>
                  <span className="tile-name">{t.name}</span>
                </>
              ) : (
                <>
                  {KIND_ICON[t.kind] && <span className="kind-icon">{KIND_ICON[t.kind]}</span>}
                  {t.kind === 'utility' && <span className="kind-icon">{t.name.startsWith('Electric') ? '💡' : '🚰'}</span>}
                  <span className="tile-name">{t.name.replace(' Railway Station', ' Rly').replace('Chhatrapati Shivaji Terminus', 'CST Mumbai')}</span>
                  {t.price > 0 && <span className="tile-price">{rupees(t.price)}</span>}
                  {t.tax > 0 && <span className="tile-price">Pay {rupees(t.tax)}</span>}
                </>
              )}
            </span>
            {state && state.houses > 0 && (
              <span className="houses" aria-label={`${state.houses === 5 ? 'hotel' : `${state.houses} houses`}`}>
                {state.houses === 5 ? <i className="hotel" /> : Array.from({ length: state.houses }, (_, i) => <i key={i} className="house" />)}
              </span>
            )}
            {owner !== null && <span className="owner-flag" style={{ background: PLAYER_COLORS[owner] }} />}
            <span className="tokens">
              {here.map((p) => (
                <motion.span
                  key={p.idx}
                  layoutId={`token-${p.idx}`}
                  className="token"
                  style={{ borderColor: PLAYER_COLORS[p.idx] }}
                  transition={{ type: 'spring', stiffness: 520, damping: 32 }}
                >
                  {TOKENS[p.token] ?? '●'}
                </motion.span>
              ))}
            </span>
          </button>
        )
      })}
      <div className="board-center">{children}</div>
    </div>
  )
}
