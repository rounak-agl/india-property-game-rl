// Mirrors docs/TECH_SPEC.md §5-6 and src/api/sessions.py.

export interface TileInfo {
  idx: number
  name: string
  kind: 'go' | 'city' | 'chest' | 'tax' | 'station' | 'chance' | 'jail' | 'utility' | 'parking' | 'goto_jail'
  group: number | null
  group_name: string | null
  price: number
  rents: number[]
  house_cost: number
  tax: number
}

export interface PlayerView {
  idx: number
  name: string
  kind: 'agent' | 'bot' | 'human'
  token: string
  cash: number
  position: number
  in_jail: boolean
  jail_cards: number
  bankrupt: boolean
  net_worth: number
  weighted_net_worth: number
}

export interface TileView {
  idx: number
  owner: number | null
  houses: number
  mortgaged: boolean
}

export interface Awaiting {
  player: number
  kind: 'buy' | 'build' | 'jail'
  tile: number | null
  legal: { action: number; label: string }[]
}

export interface GameState {
  id: string
  mode: 'ai_vs_bot' | 'human_vs_ai' | 'bot_vs_bot'
  round: number
  max_rounds: number
  current_player: number
  last_dice: [number, number]
  finished: boolean
  winner: number | null
  end_reason: 'bankruptcy' | 'max_rounds' | null
  players: PlayerView[]
  tiles: TileView[]
  share: number
  awaiting: Awaiting | null
}

export interface GameEvent {
  seq: number
  round: number
  player: number | null
  type: string
  data: Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
}

export interface DecisionData {
  decision_type: 'buy' | 'build' | 'turn'
  tile: number | null
  algo: 'dqn' | 'ppo' | 'maskppo'
  env: 'A' | 'B'
  actions: string[]
  legal: boolean[]
  probs: number[] | null
  q_values: number[] | null
  value: number | null
  chosen: number
  chosen_label: string
  share: number
}

export interface AgentInfo {
  id: string
  algo: string
  env: string
  trained_vs: string
  reward: string
  steps: number
  win_rates: Record<string, number>
  default?: boolean
}

export interface StepResponse {
  events: GameEvent[]
  state: GameState
}

export interface WinStat {
  win_rate: number
  ci_low: number
  ci_high: number
  games: number
  seed_std: number
  per_seed: number[]
  mean_rounds: number
  bankruptcy_rate: number
  invalid_action_rate: number
}

export interface ResultsSummary {
  final: Record<string, { label: string; seeds: number; algo: string; env: string; train_minutes: number; vs: Record<string, WinStat> }>
  curves: Record<string, Record<string, { timesteps: number[]; mean: number[]; std: number[] }>>
  experiments: Record<string, string[]>
  baselines: { agent: string; opponent: string; games: number; win_rate: number; ci_low: number; ci_high: number }[]
  best: { config: string; run_id: string }
  behaviour: {
    model: string
    games: number
    buy_rate_by_group: Record<string, number>
    offers_by_group: Record<string, number>
    mean_cash_when_buying: number | null
    mean_cash_when_passing: number | null
  }
  figures: string[]
}
