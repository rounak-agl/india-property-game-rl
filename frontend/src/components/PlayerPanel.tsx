import { GROUP_COLORS, PLAYER_COLORS, TOKENS, rupees } from '../lib/format'
import type { PlayerView, TileInfo, TileView } from '../types/api'

export function PlayerPanel({ player, board, tiles, active }: {
  player: PlayerView; board: TileInfo[]; tiles: TileView[]; active: boolean
}) {
  const owned = tiles.filter((t) => t.owner === player.idx).map((t) => board[t.idx])
  const label = { agent: 'RL agent', bot: 'Rule bot', human: 'Human' }[player.kind]
  return (
    <section className={`card player${active ? ' active' : ''}`} style={{ borderTopColor: PLAYER_COLORS[player.idx] }}>
      <header>
        <span className="player-token">{TOKENS[player.token]}</span>
        <div>
          <h3>{player.name}</h3>
          <small>{label}{player.in_jail ? ' · in Jail' : ''}{player.jail_cards ? ' · bail card' : ''}{player.bankrupt ? ' · bankrupt' : ''}</small>
        </div>
      </header>
      <div className="stats">
        <div><small>Cash</small><strong>{rupees(player.cash)}</strong></div>
        <div><small>Net worth</small><strong>{rupees(player.net_worth)}</strong></div>
      </div>
      <div className="deeds" aria-label="Properties owned">
        {owned.length === 0 && <small className="muted">No properties yet</small>}
        {owned.map((t) => (
          <span
            key={t.idx}
            className={`deed${tiles[t.idx].mortgaged ? ' mortgaged' : ''}`}
            title={`${t.name}${tiles[t.idx].houses ? ` · ${tiles[t.idx].houses === 5 ? 'hotel' : `${tiles[t.idx].houses} houses`}` : ''}`}
            style={{ background: t.group && t.kind === 'city' ? GROUP_COLORS[t.group] : '#6b6257' }}
          >
            {t.name.split(' ')[0].slice(0, 3)}
          </span>
        ))}
      </div>
    </section>
  )
}
