"""Many worlds feeding one shared blue brain. World 0 is the one shown in the browser."""

from collections import deque
from collections.abc import Callable

import numpy as np
import torch

from rlecosystem.ppo import DEFAULT_PPO, PPO, Brain, PPOConfig, gae, to_wheels
from rlecosystem.world import DEFAULT_WORLD, N_TYPES, World, WorldConfig

Policy = Callable[[np.ndarray], np.ndarray]  # observations (N, obs) → wheel speeds (N, 2)


def steps_per_minute(config: WorldConfig) -> int:
    return round(60 / config.dt)


class Trainer:
    def __init__(
        self,
        world_config: WorldConfig = DEFAULT_WORLD,
        n_worlds: int = 16,
        n_blues: int = 5,
        seed: int = 0,
        ppo_config: PPOConfig = DEFAULT_PPO,
        rollout: int = 128,
    ):
        torch.manual_seed(seed)
        self.config = world_config
        self.world = World(world_config, n_worlds, n_blues, seed)
        self.brain = Brain(world_config.obs_size, config=ppo_config)
        self.ppo = PPO(self.brain, ppo_config, seed)
        self.ppo_config = ppo_config
        self.rollout = rollout
        self.n_agents = n_worlds * n_blues
        self.obs = self.world.observe()
        self.buffer: list[tuple[np.ndarray, ...]] = []
        self.steps = 0
        self.updates = 0
        self.recent_food = deque(maxlen=steps_per_minute(world_config))  # world 0, per step

    def tick(self) -> None:
        """One step in every world; a PPO update every `rollout` steps."""
        flat = self.obs.reshape(self.n_agents, -1)
        actions, logp, values = self.brain.act(flat)
        wheels = to_wheels(actions, self.config.vmax).reshape(*self.obs.shape[:2], 2)
        rewards = self.world.step(wheels)
        self.buffer.append((flat, actions, logp, values, rewards.reshape(-1)))
        self.recent_food.append(rewards[0].sum())
        self.obs = self.world.observe()
        self.steps += 1
        if len(self.buffer) == self.rollout:
            self._update()

    def _update(self) -> None:
        obs, actions, logp, values, rewards = (np.stack(x) for x in zip(*self.buffer, strict=True))
        with torch.no_grad():
            last_value = self.brain.value(torch.as_tensor(self.obs.reshape(self.n_agents, -1)))
        c = self.ppo_config
        adv, ret = gae(rewards, values, last_value.numpy(), c.gamma, c.lam)
        samples = self.rollout * self.n_agents
        self.ppo.update(
            obs.reshape(samples, -1),
            actions.reshape(samples, -1),
            logp.reshape(samples),
            adv.reshape(samples),
            ret.reshape(samples),
        )
        self.buffer.clear()
        self.updates += 1

    def food_per_minute(self) -> float:
        """Food eaten per blue in world 0 over the last simulated minute (or less, scaled)."""
        if not self.recent_food:
            return 0.0
        minutes = len(self.recent_food) / steps_per_minute(self.config)
        return float(sum(self.recent_food)) / self.obs.shape[1] / minutes

    def snapshot(self) -> dict:
        """World 0 as plain data for the browser."""
        c = self.config
        seen = self.obs[0].reshape(-1, c.n_slices, N_TYPES + 1)
        kinds = seen[..., :N_TYPES].argmax(-1)
        dists = seen[..., N_TYPES] * c.vision_radius
        return {
            "world": {
                "width": c.width,
                "height": c.height,
                "food_radius": c.food_radius,
                "blue_radius": c.blue_radius,
                "vision_radius": c.vision_radius,
                "slices": c.n_slices,
            },
            "food": np.round(self.world.food[0], 1).tolist(),
            "blues": [
                [round(float(x), 1), round(float(y), 1), round(float(h), 3)]
                for (x, y), h in zip(self.world.pos[0], self.world.heading[0], strict=True)
            ],
            "slices": [
                [[int(k), round(float(d), 1)] for k, d in zip(ks, ds, strict=True)]
                for ks, ds in zip(kinds, dists, strict=True)
            ],
            "stats": {
                "sim_seconds": round(self.steps * c.dt, 1),
                "food_per_min": round(self.food_per_minute(), 1),
                "updates": self.updates,
            },
        }


def evaluate(policy: Policy, config: WorldConfig, n_blues: int, seed: int, minutes: float) -> float:
    """Food eaten per blue per simulated minute, in one fresh world with a fixed seed."""
    world = World(config, n_worlds=1, n_blues=n_blues, seed=seed)
    steps = round(minutes * steps_per_minute(config))
    total = 0.0
    for _ in range(steps):
        total += float(world.step(policy(world.observe()[0])[None]).sum())
    return total / n_blues / minutes


def random_policy(config: WorldConfig, seed: int) -> Policy:
    rng = np.random.default_rng(seed)
    return lambda obs: rng.uniform(0, config.vmax, size=(len(obs), 2))


def brain_policy(brain: Brain, config: WorldConfig, sample: bool = False) -> Policy:
    if sample:
        return lambda obs: to_wheels(brain.act(obs)[0], config.vmax)
    return lambda obs: to_wheels(brain.mean_action(obs), config.vmax)
