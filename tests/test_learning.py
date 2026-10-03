"""The claim "blues learn to eat", as a fixed-seed test on a tiny world (about 20 s)."""

import torch

from rlecosystem.ppo import PPOConfig
from rlecosystem.trainer import Trainer, brain_policy, evaluate, random_policy
from rlecosystem.world import WorldConfig

TINY = WorldConfig(width=400.0, height=300.0, n_food=10)
N_WORLDS, N_BLUES, ROLLOUT, UPDATES = 8, 2, 64, 40
EVAL_SEED, EVAL_MINUTES = 123, 1.0
LR = PPOConfig().lr  # set to 0.0 to watch this test go red


def score(policy):
    return evaluate(policy, TINY, N_BLUES, EVAL_SEED, EVAL_MINUTES)


def test_trained_blues_eat_at_least_twice_as_much_as_random():
    torch.set_num_threads(4)
    trainer = Trainer(TINY, N_WORLDS, N_BLUES, seed=0, ppo_config=PPOConfig(lr=LR), rollout=ROLLOUT)
    baselines = {
        "uniform random": score(random_policy(TINY, seed=7)),
        "untrained (mean)": score(brain_policy(trainer.brain, TINY)),
        "untrained (sampled)": score(brain_policy(trainer.brain, TINY, sample=True)),
    }
    for _ in range(UPDATES * ROLLOUT):
        trainer.tick()
    trained = score(brain_policy(trainer.brain, TINY))
    best = max(baselines.values())
    print(f"baselines {baselines} → trained {trained:.1f} food/min/blue ({trained / best:.2f}×)")
    assert trained >= 2 * best
