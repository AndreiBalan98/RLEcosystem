"""Toolchain smoke test: the libraries later milestones rely on are present and deterministic."""

import numpy as np
import torch

import rlecosystem


def test_package_imports():
    assert rlecosystem.__version__ == "0.1.0"


def test_torch_is_cpu_build():
    assert not torch.cuda.is_available()
    assert torch.version.cuda is None


def test_fixed_seed_is_repeatable():
    def draw(seed):
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        return torch.rand(5).tolist(), rng.random(5).tolist()

    assert draw(7) == draw(7)
    assert draw(7) != draw(8)
