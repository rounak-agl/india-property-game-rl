"""FastAPI app.

    uvicorn src.api.main:app --reload --port 8000
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agents import default_agent_id, list_agents
from .sessions import BOARD, SessionStore

RESULTS_SUMMARY = Path("results/summary/summary.json")

app = FastAPI(title="Indian Property Game RL API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
store = SessionStore()


class NewGame(BaseModel):
    mode: Literal["ai_vs_bot", "human_vs_ai", "bot_vs_bot"] = "ai_vs_bot"
    agent_id: str | None = None
    opponent: Literal["random", "fixed", "greedy"] = "fixed"
    seed: int | None = Field(default=None, ge=0)


class HumanAction(BaseModel):
    action: int = Field(ge=0, le=9)


def _session(game_id: str):
    try:
        return store.get(game_id)
    except KeyError:
        raise HTTPException(404, "game not found or expired") from None


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/board")
def board() -> list[dict]:
    return BOARD


@app.get("/api/agents")
def agents() -> list[dict]:
    return list_agents()


@app.post("/api/games")
def create_game(body: NewGame) -> dict:
    agent_id = body.agent_id
    if body.mode != "bot_vs_bot":
        agent_id = agent_id or default_agent_id()
        if agent_id is None:
            raise HTTPException(409, "no trained agents found in models/")
    try:
        session = store.create(body.mode, agent_id, body.opponent, body.seed)
    except KeyError:
        raise HTTPException(404, f"agent {agent_id!r} not found") from None
    with session.lock:
        return {"game_id": session.id, "agent_id": agent_id, "events": [], "state": session.state()}


@app.get("/api/games/{game_id}")
def get_game(game_id: str) -> dict:
    session = _session(game_id)
    with session.lock:
        return {"state": session.state()}


@app.post("/api/games/{game_id}/advance")
def advance(game_id: str) -> dict:
    session = _session(game_id)
    with session.lock:
        if session.awaiting() is not None:
            raise HTTPException(409, "waiting for a human decision")
        events = session.advance()
        return {"events": events, "state": session.state()}


@app.post("/api/games/{game_id}/action")
def action(game_id: str, body: HumanAction) -> dict:
    session = _session(game_id)
    with session.lock:
        try:
            events = session.human_action(body.action)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        return {"events": events, "state": session.state()}


@app.delete("/api/games/{game_id}")
def delete_game(game_id: str) -> dict:
    store.delete(game_id)
    return {"ok": True}


@app.get("/api/results")
def results() -> dict:
    if not RESULTS_SUMMARY.exists():
        raise HTTPException(404, "no results yet; run python -m src.rl.make_plots")
    return json.loads(RESULTS_SUMMARY.read_text())
