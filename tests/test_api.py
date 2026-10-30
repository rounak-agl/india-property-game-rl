import json

import pytest
from fastapi.testclient import TestClient

from src.api import agents as agents_mod
from src.api.main import app
from src.rl.agent import RLAgent
from src.rl.config import TrainConfig


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """A tiny MaskablePPO model in a temporary models/ directory."""
    from sb3_contrib import MaskablePPO

    from src.envs import make_env

    models = tmp_path_factory.mktemp("models")
    cfg = TrainConfig(name="tiny", steps=256)
    model = MaskablePPO("MlpPolicy", make_env("B"), n_steps=128, batch_size=64, seed=0, device="cpu")
    model.learn(256)
    model.save(models / "tiny_s0.zip")
    meta = {"run_id": "tiny_s0", "algo": "maskppo", "env": "B", "seed": 0, "steps": 256, "config": cfg.to_dict()}
    (models / "tiny_s0.json").write_text(json.dumps(meta))
    old = agents_mod.MODELS_DIR
    agents_mod.MODELS_DIR = models
    agents_mod.load_agent.cache_clear()
    assert isinstance(agents_mod.load_agent("tiny_s0"), RLAgent)
    yield TestClient(app)
    agents_mod.MODELS_DIR = old
    agents_mod.load_agent.cache_clear()


def test_board_and_agents(client):
    assert len(client.get("/api/board").json()) == 40
    agents = client.get("/api/agents").json()
    assert agents[0]["id"] == "tiny_s0" and agents[0]["default"]


def test_ai_vs_bot_plays_to_the_end_with_xray(client):
    game = client.post("/api/games", json={"mode": "ai_vs_bot", "seed": 3}).json()
    gid, decisions = game["game_id"], []
    for _ in range(2000):
        res = client.post(f"/api/games/{gid}/advance").json()
        decisions += [e for e in res["events"] if e["type"] == "decision"]
        if res["state"]["finished"]:
            break
    assert res["state"]["finished"]
    assert decisions and decisions[0]["data"]["probs"] is not None
    assert all(d["data"]["legal"][d["data"]["chosen"]] for d in decisions)


def test_human_vs_ai_flow_and_illegal_action(client):
    gid = client.post("/api/games", json={"mode": "human_vs_ai", "seed": 1}).json()["game_id"]
    for _ in range(500):
        state = client.get(f"/api/games/{gid}").json()["state"]
        if state["finished"]:
            break
        awaiting = state["awaiting"]
        if awaiting:
            assert client.post(f"/api/games/{gid}/advance").status_code == 409
            assert client.post(f"/api/games/{gid}/action", json={"action": 9}).status_code in (200, 422)
            state = client.get(f"/api/games/{gid}").json()["state"]
            if state["awaiting"]:
                legal = state["awaiting"]["legal"][0]["action"]
                assert client.post(f"/api/games/{gid}/action", json={"action": legal}).status_code == 200
        else:
            assert client.post(f"/api/games/{gid}/advance").status_code == 200
    events_seen = client.get(f"/api/games/{gid}").json()["state"]
    assert events_seen["round"] >= 1


def test_unknown_game_404(client):
    assert client.post("/api/games/nope/advance").status_code == 404
