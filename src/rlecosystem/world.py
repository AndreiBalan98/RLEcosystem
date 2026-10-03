"""The 2D world: wrap-around plane, food, and blues that drive on two wheels and see in slices.

Many independent worlds are simulated at once (vectorised with numpy), so one shared brain can
learn from all of them. Screen coordinates: x to the right, y down, so a growing heading turns
clockwise, i.e. to the agent's right.
"""

import math
from dataclasses import dataclass

import numpy as np

FOOD, BLUE, RED, NOTHING = 0, 1, 2, 3
N_TYPES = 4


@dataclass(frozen=True)
class WorldConfig:
    width: float = 1600.0
    height: float = 900.0
    n_food: int = 50
    food_radius: float = 5.0
    blue_radius: float = 10.0
    eat_distance: float = 15.0
    vmax: float = 150.0  # px/s, top speed of each wheel
    max_turns_per_s: float = 1.0  # spin rate with one wheel at vmax and the other stopped
    dt: float = 1 / 30
    vision_radius: float = 150.0
    n_slices: int = 16

    @property
    def wheelbase(self) -> float:
        return self.vmax / (2 * math.pi * self.max_turns_per_s)

    @property
    def obs_size(self) -> int:
        return self.n_slices * (N_TYPES + 1)


DEFAULT_WORLD = WorldConfig()


class World:
    def __init__(self, config: WorldConfig, n_worlds: int, n_blues: int, seed: int):
        self.config = config
        self.rng = np.random.default_rng(seed)
        self.size = np.array([config.width, config.height])
        self.food = self.rng.uniform(0, 1, size=(n_worlds, config.n_food, 2)) * self.size
        self.pos = self.rng.uniform(0, 1, size=(n_worlds, n_blues, 2)) * self.size
        self.heading = self.rng.uniform(-math.pi, math.pi, size=(n_worlds, n_blues))

    def _delta(self, src: np.ndarray, dst: np.ndarray) -> np.ndarray:
        """Shortest wrapped vector from every src point to every dst point: (W, S, D, 2)."""
        d = dst[:, None, :, :] - src[:, :, None, :]
        return d - self.size * np.round(d / self.size)

    def step(self, wheels: np.ndarray) -> np.ndarray:
        """Advance one dt. wheels: (W, N, 2) left/right speeds in px/s → food eaten (W, N)."""
        c = self.config
        left, right = np.moveaxis(np.clip(wheels, 0.0, c.vmax), -1, 0)
        self.heading = self.heading + (left - right) / c.wheelbase * c.dt
        self.heading = (self.heading + math.pi) % (2 * math.pi) - math.pi
        speed = (left + right) / 2
        direction = np.stack([np.cos(self.heading), np.sin(self.heading)], axis=-1)
        self.pos = (self.pos + direction * speed[..., None] * c.dt) % self.size
        return self._eat()

    def _eat(self) -> np.ndarray:
        dist = np.linalg.norm(self._delta(self.pos, self.food), axis=-1)  # (W, N, F)
        eaten = (dist < self.config.eat_distance).any(axis=1)  # (W, F)
        eater = dist.argmin(axis=1)  # closest blue gets the food
        rewards = np.zeros(self.pos.shape[:2], dtype=np.float32)
        w_idx, f_idx = np.nonzero(eaten)
        np.add.at(rewards, (w_idx, eater[w_idx, f_idx]), 1.0)
        self.food[w_idx, f_idx] = self.rng.uniform(0, 1, size=(len(w_idx), 2)) * self.size
        return rewards

    def observe(self) -> np.ndarray:
        """Per blue, per slice: one-hot type of the nearest thing + distance / radius. (W, N, 80)"""
        c = self.config
        n_worlds, n_blues = self.heading.shape
        targets = np.concatenate([self.food, self.pos], axis=1)  # (W, F + N, 2)
        kinds = np.array([FOOD] * c.n_food + [BLUE] * n_blues)
        delta = self._delta(self.pos, targets)  # (W, N, M, 2)
        dist = np.linalg.norm(delta, axis=-1)
        self_mask = np.zeros((n_blues, len(kinds)), dtype=bool)
        self_mask[:, c.n_food :] = np.eye(n_blues, dtype=bool)
        dist = np.where((dist < c.vision_radius) & ~self_mask, dist, np.inf)

        width = 2 * math.pi / c.n_slices
        angle = np.arctan2(delta[..., 1], delta[..., 0]) - self.heading[..., None]
        slice_of = np.floor((angle + width / 2) / width).astype(int) % c.n_slices  # 0 = ahead

        obs = np.zeros((n_worlds, n_blues, c.n_slices, N_TYPES + 1), dtype=np.float32)
        for k in range(c.n_slices):
            d_k = np.where(slice_of == k, dist, np.inf)
            nearest = d_k.argmin(axis=-1)
            d_min = np.take_along_axis(d_k, nearest[..., None], axis=-1)[..., 0]
            seen = np.isfinite(d_min)
            kind = np.where(seen, kinds[nearest], NOTHING)
            obs[:, :, k, :N_TYPES] = np.eye(N_TYPES, dtype=np.float32)[kind]
            obs[:, :, k, N_TYPES] = np.where(seen, d_min / c.vision_radius, 1.0)
        return obs.reshape(n_worlds, n_blues, c.obs_size)
