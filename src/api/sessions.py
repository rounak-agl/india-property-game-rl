"""In-memory game sessions. Each session wraps an engine Game plus one controller per seat."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

import numpy as np

from src.bots import jail_policy, make_bot
from src.engine import Decision, Game
from src.engine.board_data import GROUP_NAMES, TILES
from src.engine.rules import raw_net_worth, weighted_net_worth
from src.engine.state import BUY, JAIL_CARD, JAIL_PAY, JAIL_ROLL, PASS, action_group
from src.envs.observation import encode_a, encode_b
from src.envs.rewards import RewardConfig, net_worth_share
from src.rl.agent import RLAgent

from .agents import load_agent

SESSION_TTL_SECONDS = 3600
MODES = ("ai_vs_bot", "human_vs_ai", "bot_vs_bot")
AI_SEAT = 0


def action_label(decision: Decision, action: int) -> str:
    if decision.kind == "jail":
        return {JAIL_ROLL: "Roll for doubles", JAIL_PAY: "Pay ₹50 fine", JAIL_CARD: "Use bail card"}[action]
    if decision.kind == "turn":
        return ("Pass", "Buy", "Build")[action]
    if action == PASS:
        return "Pass"
    if action == BUY:
        return "Buy"
    return f"Build on {GROUP_NAMES[action_group(action)]}"


@dataclass
class Seat:
    kind: str  # "agent" | "bot" | "human"
    name: str
    token: str
    agent: RLAgent | None = None
    bot: object | None = None


@dataclass
class GameSession:
    id: str
    mode: str
    game: Game
    seats: list[Seat]
    reward_cfg: RewardConfig
    lock: threading.Lock = field(default_factory=threading.Lock)
    touched: float = field(default_factory=time.time)

    # ------------------------------------------------------------------ driving
    def advance(self) -> list[dict]:
        """Play until the end of the next turn, a human decision, or game over."""
        start = len(self.game.events)
        self._run(stop_at_next_turn=True)
        return [e.to_dict() for e in self.game.events[start:]]

    def human_action(self, action: int) -> list[dict]:
        decision = self.game.pending
        if decision is None or self.seats[decision.player].kind != "human":
            raise ValueError("no human decision is pending")
        if action not in decision.legal:
            raise ValueError(f"action {action} is not legal here")
        start = len(self.game.events)
        self.game.log_event("human_decision", decision.player, kind=decision.kind, tile=decision.tile,
                            chosen=action, label=action_label(decision, action))
        self.game.act(action)
        self._run(stop_at_next_turn=True)
        return [e.to_dict() for e in self.game.events[start:]]

    def _run(self, stop_at_next_turn: bool) -> None:
        game = self.game
        passed_turn_start = False
        decision = game.advance()
        while decision is not None:
            seat = self.seats[decision.player]
            if decision.kind == "next_turn":
                if passed_turn_start and stop_at_next_turn:
                    return
                passed_turn_start = True
                decision = game.act(0)
            elif seat.kind == "human":
                return
            elif seat.kind == "bot":
                decision = game.act(seat.bot.decide(game, decision))
            elif decision.kind == "jail":
                decision = game.act(jail_policy(game, decision))
            else:
                decision = game.act(self._agent_decide(seat.agent, decision))

    def _agent_decide(self, agent: RLAgent, decision: Decision) -> int:
        state = self.game.state
        share = net_worth_share(state, decision.player, self.reward_cfg)
        if agent.env_name == "A":
            obs = encode_a(state, decision.player)
            mask = np.ones(3, dtype=bool)
        else:
            obs = encode_b(state, decision.player, decision, share)
            mask = np.zeros(10, dtype=bool)
            mask[decision.legal] = True
        xray = agent.xray(obs, mask)
        action = xray.chosen if xray.chosen in decision.legal else PASS
        self.game.log_event(
            "decision", decision.player,
            decision_type=decision.kind, tile=decision.tile, algo=agent.algo, env=agent.env_name,
            actions=xray.actions, legal=xray.legal, probs=xray.probs, q_values=xray.q_values,
            value=xray.value, chosen=action, chosen_label=action_label(decision, action), share=share,
        )
        return action

    # ------------------------------------------------------------------ views
    def awaiting(self) -> dict | None:
        d = self.game.pending
        if d is None or d.kind == "next_turn" or self.seats[d.player].kind != "human":
            return None
        return {"player": d.player, "kind": d.kind, "tile": d.tile,
                "legal": [{"action": a, "label": action_label(d, a)} for a in d.legal]}

    def state(self) -> dict:
        s = self.game.state
        players = []
        for i, pl in enumerate(s.players):
            seat = self.seats[i]
            players.append({
                "idx": i, "name": seat.name, "kind": seat.kind, "token": seat.token,
                "cash": pl.cash, "position": pl.position, "in_jail": pl.in_jail, "jail_cards": pl.jail_cards,
                "bankrupt": pl.bankrupt, "net_worth": raw_net_worth(s, i),
                "weighted_net_worth": round(weighted_net_worth(s, i, self.reward_cfg.b_single,
                                                               self.reward_cfg.b_monopoly), 1),
            })
        return {
            "id": self.id, "mode": self.mode, "round": s.round, "max_rounds": self.game.max_rounds,
            "current_player": s.current, "last_dice": list(s.last_dice),
            "finished": s.finished, "winner": s.winner, "end_reason": s.end_reason,
            "players": players,
            "tiles": [{"idx": i, "owner": t.owner, "houses": t.houses, "mortgaged": t.mortgaged}
                      for i, t in enumerate(s.tiles)],
            "share": net_worth_share(s, AI_SEAT, self.reward_cfg),
            "awaiting": self.awaiting(),
        }


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, GameSession] = {}
        self._lock = threading.Lock()

    def create(self, mode: str, agent_id: str | None, opponent: str, seed: int | None) -> GameSession:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        agent = load_agent(agent_id) if mode != "bot_vs_bot" else None
        if mode == "ai_vs_bot":
            seats = [Seat("agent", "RL Agent", "rickshaw", agent=agent),
                     Seat("bot", f"{opponent.title()} Bot", "elephant", bot=make_bot(opponent, seed))]
        elif mode == "human_vs_ai":
            seats = [Seat("agent", "RL Agent", "rickshaw", agent=agent), Seat("human", "You", "tiger")]
        else:
            seats = [Seat("bot", "Fixed Bot", "rickshaw", bot=make_bot("fixed")),
                     Seat("bot", f"{opponent.title()} Bot", "elephant", bot=make_bot(opponent, seed))]
        blueprint = {AI_SEAT} if agent is not None and agent.env_name == "A" else set()
        reward = RewardConfig(**agent.meta["config"]["reward"]) if agent else RewardConfig()
        game = Game(seed=seed, names=[s.name for s in seats], blueprint_players=blueprint, pause_each_turn=True)
        session = GameSession(uuid.uuid4().hex[:12], mode, game, seats, reward)
        with self._lock:
            self._expire()
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> GameSession:
        with self._lock:
            session = self._sessions[session_id]
        session.touched = time.time()
        return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def _expire(self) -> None:
        cutoff = time.time() - SESSION_TTL_SECONDS
        for sid in [sid for sid, s in self._sessions.items() if s.touched < cutoff]:
            del self._sessions[sid]


BOARD = [
    {"idx": t.idx, "name": t.name, "kind": t.kind, "group": t.group,
     "group_name": GROUP_NAMES.get(t.group) if t.group else None, "price": t.price,
     "rents": list(t.rents), "house_cost": t.house_cost, "tax": t.tax}
    for t in TILES
]
