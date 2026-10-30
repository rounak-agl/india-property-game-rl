import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env as gym_check_env
from stable_baselines3.common.env_checker import check_env as sb3_check_env

from src.envs import EnvA, EnvB, make_env
from src.envs.rewards import RewardConfig


@pytest.mark.parametrize("name", ["A", "B"])
def test_env_checkers(name):
    gym_check_env(make_env(name), skip_render_check=True)
    sb3_check_env(make_env(name), warn=True)


def play_random(env, seed, masked=True):
    rng = np.random.default_rng(seed)
    obs, info = env.reset(seed=seed)
    total, steps = 0.0, 0
    while True:
        assert env.observation_space.contains(obs), obs
        if masked:
            legal = np.flatnonzero(env.action_masks())
            action = int(rng.choice(legal))
        else:
            action = int(env.action_space.sample())
        obs, reward, terminated, truncated, info = env.step(action)
        total += reward
        steps += 1
        if terminated or truncated:
            return total, steps, info


@pytest.mark.parametrize("opponent", ["random", "fixed", "greedy", "mixed"])
def test_env_b_full_episodes(opponent):
    env = EnvB(opponent=opponent)
    for seed in range(20):
        _, steps, info = play_random(env, seed)
        assert info["finished"] and steps > 0
        assert info["invalid_actions"] == 0
        assert not env.game.check_invariants()


def test_env_a_full_episodes_invalid_actions_counted():
    env = EnvA(opponent="fixed")
    invalid = 0
    for seed in range(20):
        _, _, info = play_random(env, seed, masked=False)
        invalid += info["invalid_actions"]
    assert invalid > 0


def test_masks_match_engine_legal_actions():
    env = EnvB()
    env.reset(seed=0)
    for _ in range(200):
        mask = env.action_masks()
        assert sorted(np.flatnonzero(mask).tolist()) == sorted(env.decision.legal)
        _, _, term, _, _ = env.step(int(np.flatnonzero(mask)[-1]))
        if term:
            env.reset()


def test_same_seed_is_deterministic():
    def run():
        return play_random(EnvB(), seed=11)

    assert run() == run()


def test_delta_share_rewards_sum_to_share_change_plus_terminal():
    env = EnvB(reward=RewardConfig(mode="delta_share", terminal=10.0))
    _, info0 = env.reset(seed=5)
    start_share = info0["share"]
    total, _, info = play_random(env, seed=5)
    terminal = 0.0 if info["winner"] is None else (10.0 if info["winner"] == 0 else -10.0)
    assert total == pytest.approx(info["share"] - start_share + terminal, abs=1e-6)


def test_sparse_reward_only_at_end():
    env = EnvB(reward={"mode": "sparse"})
    env.reset(seed=2)
    rewards = []
    while True:
        _, r, term, _, _ = env.step(int(np.flatnonzero(env.action_masks())[0]))
        rewards.append(r)
        if term:
            break
    assert all(r == 0 for r in rewards[:-1])


def test_unknown_reward_mode_rejected():
    with pytest.raises(ValueError):
        RewardConfig(mode="nope")
