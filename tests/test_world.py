"""The world without the browser: wheels, wrap-around, vision slices, food respawn."""

import math

import numpy as np
import pytest

from rlecosystem.world import BLUE, FOOD, NOTHING, World, WorldConfig

CFG = WorldConfig()
FAR = (1300.0, 800.0)  # parking spot for food a test doesn't use: out of everyone's sight


def make_world(blues, food=()):
    """One world with blues at the given (x, y, heading) and the listed food; the rest parked."""
    world = World(CFG, n_worlds=1, n_blues=len(blues), seed=0)
    world.pos[0] = [(x, y) for x, y, _ in blues]
    world.heading[0] = [h for _, _, h in blues]
    world.food[0] = FAR
    for i, xy in enumerate(food):
        world.food[0, i] = xy
    return world


def slices(world, blue=0):
    """(16, 5) view of one blue's observation: one-hot type (4) + distance / radius."""
    return world.observe()[0, blue].reshape(CFG.n_slices, 5)


def assert_slice(obs, k, kind, distance):
    expected = np.zeros(5)
    expected[kind] = 1.0
    expected[4] = distance / CFG.vision_radius
    np.testing.assert_allclose(obs[k], expected, atol=1e-5)


def wheels(left, right):
    return np.array([[[left, right]]], dtype=np.float64)


def test_equal_wheels_drive_straight():
    world = make_world([(800.0, 450.0, 0.0)])
    world.step(wheels(CFG.vmax, CFG.vmax))
    np.testing.assert_allclose(world.pos[0, 0], [800.0 + CFG.vmax * CFG.dt, 450.0])
    assert world.heading[0, 0] == pytest.approx(0.0)


def test_faster_left_wheel_turns_right_at_one_turn_per_second():
    world = make_world([(800.0, 450.0, 0.0)])
    world.step(wheels(CFG.vmax, 0.0))
    # Screen y points down, so a growing heading turns clockwise: to the agent's right.
    assert world.heading[0, 0] == pytest.approx(2 * math.pi * CFG.dt)
    world = make_world([(800.0, 450.0, 0.0)])
    world.step(wheels(0.0, CFG.vmax))
    assert world.heading[0, 0] == pytest.approx(-2 * math.pi * CFG.dt)


def test_wheel_speeds_are_clipped_to_forward_only():
    world = make_world([(800.0, 450.0, 0.0)])
    world.step(wheels(-50.0, 10 * CFG.vmax))
    clipped = make_world([(800.0, 450.0, 0.0)])
    clipped.step(wheels(0.0, CFG.vmax))
    np.testing.assert_allclose(world.pos, clipped.pos)
    np.testing.assert_allclose(world.heading, clipped.heading)


@pytest.mark.parametrize(
    "start, heading, end",
    [
        ((1599.0, 450.0), 0.0, (4.0, 450.0)),  # out the right, in on the left
        ((1.0, 450.0), math.pi, (1596.0, 450.0)),  # out the left, in on the right
        ((800.0, 899.0), math.pi / 2, (800.0, 4.0)),  # out the bottom, in at the top
        ((800.0, 1.0), -math.pi / 2, (800.0, 896.0)),  # out the top, in at the bottom
    ],
)
def test_edges_wrap_around(start, heading, end):
    world = make_world([(*start, heading)])
    world.step(wheels(CFG.vmax, CFG.vmax))
    np.testing.assert_allclose(world.pos[0, 0], end, atol=1e-6)


def test_food_straight_ahead_lands_in_slice_zero():
    obs = slices(make_world([(800.0, 450.0, 0.0)], food=[(900.0, 450.0)]))
    assert_slice(obs, 0, FOOD, 100.0)


def test_slice_index_follows_angle_relative_to_heading():
    # Food 90 degrees to the right (screen y down) is 4 slices of 22.5 degrees around.
    obs = slices(make_world([(800.0, 450.0, 0.0)], food=[(800.0, 550.0)]))
    assert_slice(obs, 4, FOOD, 100.0)
    # The same food, seen by a blue already facing down, is straight ahead.
    obs = slices(make_world([(800.0, 450.0, math.pi / 2)], food=[(800.0, 550.0)]))
    assert_slice(obs, 0, FOOD, 100.0)


def test_empty_slices_report_nothing_at_full_distance():
    obs = slices(make_world([(800.0, 450.0, 0.0)], food=[(900.0, 450.0)]))
    for k in range(1, CFG.n_slices):
        assert_slice(obs, k, NOTHING, CFG.vision_radius)


def test_nearest_thing_in_a_slice_wins():
    obs = slices(make_world([(800.0, 450.0, 0.0)], food=[(900.0, 450.0), (850.0, 452.0)]))
    assert_slice(obs, 0, FOOD, math.hypot(50.0, 2.0))


def test_other_blues_are_seen_as_blue_and_self_is_not_seen():
    world = make_world([(800.0, 450.0, 0.0), (870.0, 450.0, 0.0)])
    obs = slices(world, blue=0)
    assert_slice(obs, 0, BLUE, 70.0)
    assert_slice(obs, 8, NOTHING, CFG.vision_radius)  # behind blue 0: nothing, not itself


def test_food_beyond_the_vision_radius_is_not_seen():
    obs = slices(make_world([(800.0, 450.0, 0.0)], food=[(800.0 + 151.0, 450.0)]))
    assert_slice(obs, 0, NOTHING, CFG.vision_radius)


def test_vision_sees_across_the_wrapped_edge():
    # Facing left at x=10: food at x=1550 is 60 px ahead through the left edge.
    obs = slices(make_world([(10.0, 450.0, math.pi)], food=[(1550.0, 450.0)]))
    assert_slice(obs, 0, FOOD, 60.0)


def test_eating_gives_plus_one_and_food_respawns_elsewhere():
    world = make_world([(100.0, 100.0, 0.0)], food=[(105.0, 100.0)])
    rewards = world.step(wheels(0.0, 0.0))
    assert rewards.shape == (1, 1)
    assert rewards[0, 0] == 1.0
    assert world.food.shape == (1, CFG.n_food, 2)
    assert not np.allclose(world.food[0, 0], (105.0, 100.0))
    x, y = world.food[0, 0]
    assert 0 <= x < CFG.width and 0 <= y < CFG.height


def test_food_out_of_reach_is_not_eaten():
    world = make_world([(100.0, 100.0, 0.0)], food=[(100.0 + CFG.eat_distance + 1, 100.0)])
    rewards = world.step(wheels(0.0, 0.0))
    assert rewards[0, 0] == 0.0


def test_one_food_feeds_only_the_closest_blue():
    world = make_world([(100.0, 100.0, 0.0), (112.0, 100.0, 0.0)], food=[(110.0, 100.0)])
    rewards = world.step(wheels(0.0, 0.0).repeat(2, axis=1))
    np.testing.assert_array_equal(rewards[0], [0.0, 1.0])


def run(seed, steps=60):
    world = World(CFG, n_worlds=2, n_blues=3, seed=seed)
    rng = np.random.default_rng(99)
    for _ in range(steps):
        world.step(rng.uniform(0, CFG.vmax, size=(2, 3, 2)))
    return world.pos.copy(), world.food.copy(), world.observe()


def test_same_seed_gives_the_same_world_and_a_different_seed_does_not():
    a, b, c = run(1), run(1), run(2)
    for x, y in zip(a, b, strict=True):
        np.testing.assert_array_equal(x, y)
    assert not np.array_equal(a[0], c[0])
