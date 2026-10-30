import type { AgentInfo, GameState, ResultsSummary, StepResponse, TileInfo } from '../types/api'

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  board: () => call<TileInfo[]>('/board'),
  agents: () => call<AgentInfo[]>('/agents'),
  results: () => call<ResultsSummary>('/results'),
  newGame: (body: { mode: string; agent_id?: string; opponent: string; seed?: number }) =>
    call<{ game_id: string; agent_id: string | null; state: GameState }>('/games', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  advance: (id: string) => call<StepResponse>(`/games/${id}/advance`, { method: 'POST' }),
  act: (id: string, action: number) =>
    call<StepResponse>(`/games/${id}/action`, { method: 'POST', body: JSON.stringify({ action }) }),
}
