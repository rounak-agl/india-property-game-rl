import type { GameEvent, TileInfo } from '../types/api'

export const GAME_NAME = 'India Property Game' // working title; final name pending (OPEN_QUESTIONS Q1)

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
export const rupees = (n: number) => inr.format(n)
export const pct = (x: number, digits = 1) => `${(x * 100).toFixed(digits)}%`

export const GROUP_COLORS: Record<number, string> = {
  1: '#8a5a32',
  2: '#5fb8e6',
  3: '#d6458f',
  4: '#ef7d1a',
  5: '#d63a2f',
  6: '#e8b81d',
  7: '#1f9a55',
  8: '#27408b',
}

export const TOKENS: Record<string, string> = { rickshaw: '🛺', elephant: '🐘', tiger: '🐯' }
export const PLAYER_COLORS = ['#ea7317', '#14837b']

/** Grid cell (row, col), 1-based, for board index 0..39 on an 11x11 grid. */
export function cellFor(idx: number): { row: number; col: number; side: 'bottom' | 'left' | 'top' | 'right' | 'corner' } {
  if (idx === 0) return { row: 11, col: 11, side: 'corner' }
  if (idx < 10) return { row: 11, col: 11 - idx, side: 'bottom' }
  if (idx === 10) return { row: 11, col: 1, side: 'corner' }
  if (idx < 20) return { row: 21 - idx, col: 1, side: 'left' }
  if (idx === 20) return { row: 1, col: 1, side: 'corner' }
  if (idx < 30) return { row: 1, col: idx - 19, side: 'top' }
  if (idx === 30) return { row: 1, col: 11, side: 'corner' }
  return { row: idx - 29, col: 11, side: 'right' }
}

export function describeEvent(e: GameEvent, board: TileInfo[], names: string[]): string | null {
  const who = e.player !== null ? names[e.player] : ''
  const tile = (i: number) => board[i]?.name ?? `#${i}`
  const d = e.data
  switch (e.type) {
    case 'dice_rolled':
      return `${who} rolled ${d.dice[0]} + ${d.dice[1]}${d.doubles ? ' (doubles!)' : ''}`
    case 'moved':
      return `${who} → ${tile(d.to)}`
    case 'collected':
      return `${who} collected ${rupees(d.amount)}${d.reason === 'passed_go' ? ' for passing GO' : ''}`
    case 'bought':
      return `${who} bought ${tile(d.tile)} for ${rupees(d.price)}${d.completes_group ? ' — colour set complete!' : ''}`
    case 'declined':
      return d.reason === 'cash' ? `${who} can't afford ${tile(d.tile)}` : `${who} passed on ${tile(d.tile)}`
    case 'rent_paid':
      return `${who} paid ${rupees(d.amount)} rent to ${names[d.to]}`
    case 'tax_paid':
      return `${who} paid ${rupees(d.amount)} tax`
    case 'paid':
      return `${who} paid ${rupees(d.amount)}${d.to !== null ? ` to ${names[d.to]}` : ''}`
    case 'card_drawn':
      return `${who} drew: “${d.text}”`
    case 'built':
      return `${who} built on ${tile(d.tile)} (${d.houses === 5 ? 'hotel' : `${d.houses} house${d.houses > 1 ? 's' : ''}`})`
    case 'sold_house':
      return `${who} sold a house on ${tile(d.tile)}`
    case 'mortgaged':
      return `${who} mortgaged ${tile(d.tile)}`
    case 'jailed':
      return `${who} went to Jail`
    case 'left_jail':
      return `${who} left Jail (${d.method.replace('_', ' ')})`
    case 'stayed_in_jail':
      return `${who} stays in Jail`
    case 'bankrupt':
      return `${who} is BANKRUPT`
    case 'game_over':
      return d.winner === null ? 'Game over — draw' : `Game over — ${names[d.winner]} wins (${d.reason === 'bankruptcy' ? 'bankruptcy' : 'net worth at round limit'})`
    case 'decision':
      return null
    case 'human_decision':
      return `${who} chose: ${d.label}`
    default:
      return null
  }
}
