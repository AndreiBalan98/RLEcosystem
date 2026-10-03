"""The PPO pieces that can be checked by hand: advantages, action mapping, one update."""

import numpy as np
import torch

from rlecosystem.ppo import PPO, Brain, PPOConfig, gae, to_wheels


def test_gae_matches_a_hand_computed_case():
    rewards = np.array([[1.0], [0.0], [2.0]])
    values = np.array([[0.5], [1.0], [0.0]])
    adv, ret = gae(rewards, values, last_value=np.array([1.0]), gamma=0.9, lam=0.5)
    # delta_2 = 2 + 0.9*1.0 - 0.0 = 2.9;  A_2 = 2.9
    # delta_1 = 0 + 0.9*0.0 - 1.0 = -1.0; A_1 = -1.0 + 0.45*2.9 = 0.305
    # delta_0 = 1 + 0.9*1.0 - 0.5 = 1.4;  A_0 = 1.4 + 0.45*0.305 = 1.53725
    np.testing.assert_allclose(adv[:, 0], [1.53725, 0.305, 2.9])
    np.testing.assert_allclose(ret[:, 0], [2.03725, 1.305, 2.9])


def test_any_network_output_maps_to_a_forward_wheel_speed():
    x = np.array([-5.0, -1.0, 0.0, 1.0, 5.0])
    np.testing.assert_allclose(to_wheels(x, vmax=150.0), [0.0, 0.0, 75.0, 150.0, 150.0])


def batch(n=64, obs_size=80, seed=0):
    rng = np.random.default_rng(seed)
    return (
        rng.random((n, obs_size), dtype=np.float32),
        rng.normal(size=(n, 2)).astype(np.float32),
        rng.normal(size=n).astype(np.float32),
    )


def test_act_returns_actions_log_probs_and_values_per_agent():
    torch.manual_seed(0)
    brain = Brain(obs_size=80)
    obs, _, _ = batch()
    actions, logp, values = brain.act(obs)
    assert actions.shape == (64, 2) and logp.shape == (64,) and values.shape == (64,)
    assert brain.mean_action(obs).shape == (64, 2)


def params(brain):
    return torch.cat([p.detach().flatten() for p in brain.parameters()]).clone()


def run_update(lr):
    torch.manual_seed(0)
    brain = Brain(obs_size=80)
    ppo = PPO(brain, PPOConfig(lr=lr), seed=0)
    obs, _, adv = batch()
    actions, logp, values = brain.act(obs)
    before = params(brain)
    ppo.update(obs, actions, logp, adv, values + adv)
    return before, params(brain)


def test_update_changes_the_brain():
    before, after = run_update(lr=3e-4)
    assert not torch.equal(before, after)


def test_update_with_zero_learning_rate_changes_nothing():
    before, after = run_update(lr=0.0)
    assert torch.equal(before, after)
