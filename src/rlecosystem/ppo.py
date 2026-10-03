"""A small PPO: one shared brain (policy + value net) for every agent of a species.

Wheel speeds are continuous, so the policy is a Gaussian over 2 numbers that `to_wheels` maps to
[0, vmax]. There are no episodes: the world runs forever, and GAE bootstraps from the last value.
"""

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class PPOConfig:
    hidden: int = 64
    log_std_init: float = -0.5
    gamma: float = 0.99
    lam: float = 0.95
    clip: float = 0.2
    lr: float = 3e-4
    epochs: int = 4
    minibatches: int = 4
    entropy_coef: float = 0.001
    value_coef: float = 0.5
    max_grad_norm: float = 0.5


DEFAULT_PPO = PPOConfig()


def mlp(n_in: int, hidden: int, n_out: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(n_in, hidden),
        nn.Tanh(),
        nn.Linear(hidden, hidden),
        nn.Tanh(),
        nn.Linear(hidden, n_out),
    )


def to_wheels(x: np.ndarray, vmax: float) -> np.ndarray:
    """Network output (any real number) → wheel speed in [0, vmax]."""
    return np.clip((x + 1) / 2, 0.0, 1.0) * vmax


def gae(
    rewards: np.ndarray, values: np.ndarray, last_value: np.ndarray, gamma: float, lam: float
) -> tuple[np.ndarray, np.ndarray]:
    """Generalised advantage estimation over (T, B) arrays. Returns (advantages, returns)."""
    adv = np.zeros_like(rewards, dtype=np.float32)
    running = np.zeros_like(last_value, dtype=np.float32)
    next_value = last_value
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * next_value - values[t]
        running = delta + gamma * lam * running
        adv[t] = running
        next_value = values[t]
    return adv, adv + values


class Brain(nn.Module):
    def __init__(self, obs_size: int, n_actions: int = 2, config: PPOConfig = DEFAULT_PPO):
        super().__init__()
        self.policy = mlp(obs_size, config.hidden, n_actions)
        self.value_net = mlp(obs_size, config.hidden, 1)
        self.log_std = nn.Parameter(torch.full((n_actions,), config.log_std_init))

    def dist(self, obs: torch.Tensor) -> torch.distributions.Normal:
        return torch.distributions.Normal(self.policy(obs), self.log_std.exp())

    def value(self, obs: torch.Tensor) -> torch.Tensor:
        return self.value_net(obs).squeeze(-1)

    @torch.no_grad()
    def act(self, obs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Sample actions for a batch of agents: (actions, log-probs, values)."""
        o = torch.as_tensor(obs)
        d = self.dist(o)
        actions = d.sample()
        return actions.numpy(), d.log_prob(actions).sum(-1).numpy(), self.value(o).numpy()

    @torch.no_grad()
    def mean_action(self, obs: np.ndarray) -> np.ndarray:
        return self.policy(torch.as_tensor(obs)).numpy()


class PPO:
    def __init__(self, brain: Brain, config: PPOConfig = DEFAULT_PPO, seed: int = 0):
        self.brain = brain
        self.config = config
        self.optimizer = torch.optim.Adam(brain.parameters(), lr=config.lr)
        self.generator = torch.Generator().manual_seed(seed)

    def update(
        self,
        obs: np.ndarray,
        actions: np.ndarray,
        logp: np.ndarray,
        advantages: np.ndarray,
        returns: np.ndarray,
    ) -> None:
        """PPO-clip on one rollout, flattened to (samples, ...)."""
        c = self.config
        obs_t, act_t, old_logp, adv_t, ret_t = (
            torch.as_tensor(x, dtype=torch.float32)
            for x in (obs, actions, logp, advantages, returns)
        )
        adv_t = (adv_t - adv_t.mean()) / (adv_t.std() + 1e-8)
        n = len(obs_t)
        size = n // c.minibatches
        for _ in range(c.epochs):
            order = torch.randperm(n, generator=self.generator)
            for start in range(0, size * c.minibatches, size):
                idx = order[start : start + size]
                d = self.brain.dist(obs_t[idx])
                ratio = (d.log_prob(act_t[idx]).sum(-1) - old_logp[idx]).exp()
                clipped = ratio.clamp(1 - c.clip, 1 + c.clip)
                policy_loss = -torch.min(ratio * adv_t[idx], clipped * adv_t[idx]).mean()
                value_loss = (self.brain.value(obs_t[idx]) - ret_t[idx]).pow(2).mean()
                entropy = d.entropy().sum(-1).mean()
                loss = policy_loss + c.value_coef * value_loss - c.entropy_coef * entropy
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.brain.parameters(), c.max_grad_norm)
                self.optimizer.step()
