import { GROUP_COLORS, rupees } from '../lib/format'
import type { PlayerView, TileInfo, TileView } from '../types/api'

const RENT_LABELS = ['Base rent', '1 house', '2 houses', '3 houses', '4 houses', 'Hotel']

export function PropertyCard({ tile, state, players, onClose }: {
  tile: TileInfo; state: TileView | null; players: PlayerView[]; onClose: () => void
}) {
  const owner = state?.owner != null ? players[state.owner] : null
  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div className="modal deed-card" role="dialog" aria-label={tile.name} onClick={(e) => e.stopPropagation()}>
        <header style={{ background: tile.group && tile.kind === 'city' ? GROUP_COLORS[tile.group] : '#3c3530' }}>
          <small>{tile.kind === 'city' ? `${tile.group_name} group` : tile.kind.replace('_', ' ')}</small>
          <h3>{tile.name}</h3>
        </header>
        <div className="deed-body">
          {tile.kind === 'city' && (
            <table>
              <tbody>
                {tile.rents.map((r, i) => (
                  <tr key={i} className={state?.houses === i && state.owner != null ? 'current' : ''}>
                    <td>{RENT_LABELS[i]}{i === 0 ? ' (×2 with full set)' : ''}</td>
                    <td>{rupees(r)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tile.kind === 'station' && <p>Rent {rupees(25)} / {rupees(50)} / {rupees(100)} / {rupees(200)} for 1–4 stations owned.</p>}
          {tile.kind === 'utility' && <p>Rent is 4× the dice roll, or 10× if both utilities are owned.</p>}
          {tile.tax > 0 && <p>Pay {rupees(tile.tax)} to the bank.</p>}
          {tile.price > 0 && (
            <p className="deed-meta">
              Price {rupees(tile.price)} · Mortgage {rupees(tile.price / 2)}
              {tile.house_cost > 0 && <> · House {rupees(tile.house_cost)}</>}
            </p>
          )}
          {tile.price > 0 && <p><strong>Owner:</strong> {owner ? owner.name : 'Bank (unowned)'}{state?.mortgaged ? ' · mortgaged' : ''}</p>}
          <button type="button" className="btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
