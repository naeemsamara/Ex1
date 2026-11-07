"""Plane validation rules (SRS FR-2)."""

import math

import pytest

from projection import EPS, InvalidPlaneError, Plane


def test_valid_triangle():
    p = Plane.from_points([[0, 0, 0], [10, -5, 0], [10, 5, 0]])
    assert p.is_triangle
    assert p.base_length == pytest.approx(10)
    assert p.edge_length == pytest.approx(math.sqrt(125))


def test_valid_trapezoid():
    p = Plane.from_points([[2, 0, 0], [8, 0, 0], [0, 0, 10], [10, 0, 10]])
    assert not p.is_triangle


def test_from_values_9_and_12():
    assert Plane.from_values([0, 0, 0, 10, -5, 0, 10, 5, 0]).is_triangle
    assert not Plane.from_values([0, 0, 0, 5, 0, 0, 0, 5, 0, 5, 5, 0]).is_triangle


def test_edges_equal_within_eps_is_accepted():
    # |dab - dac| just below EPS
    Plane.from_points([[0, 0, 0], [10, 0, 0], [0, 10 + EPS / 2, 0]])


def test_edges_differ_by_eps_is_rejected():
    with pytest.raises(InvalidPlaneError, match="not equal"):
        Plane.from_points([[0, 0, 0], [10, 0, 0], [0, 10 + 2 * EPS, 0]])


@pytest.mark.parametrize("points", [
    [[0, 0, 0], [5, 0, 0], [10, 0, 0], [15, 0, 0]],      # collinear trapezoid
    [[0, 0, 0], [10, 0, 0], [-10, 0, 0]],                 # collinear triangle
])
def test_collinear_rejected(points):
    with pytest.raises(InvalidPlaneError):
        Plane.from_points(points)


def test_b_equals_c_rejected():
    with pytest.raises(InvalidPlaneError):
        Plane.from_points([[0, 0, 0], [10, 0, 0], [10, 0, 0]])


def test_a1a2_longer_than_bc_rejected():
    with pytest.raises(InvalidPlaneError, match="<= dist"):
        Plane.from_points([[0, 0, 0], [20, 0, 0], [5, 10, 0], [15, 10, 0]])


def test_not_coplanar_rejected():
    # equal edges but twisted (a2 and c pulled to opposite sides)
    with pytest.raises(InvalidPlaneError, match="off the plane"):
        Plane.from_points([[0, 0, 0], [10, 0, 5], [0, 10, 10], [10, 10, -5]])


@pytest.mark.parametrize("n", [0, 1, 2, 5])
def test_wrong_point_count(n):
    with pytest.raises(InvalidPlaneError):
        Plane.from_points([[0, 0, 0]] * n)


def test_wrong_value_count():
    with pytest.raises(InvalidPlaneError):
        Plane.from_values([1, 2, 3, 4, 5])


def test_nan_rejected():
    with pytest.raises(InvalidPlaneError):
        Plane.from_points([[0, 0, float("nan")], [10, 0, 0], [0, 10, 0]])
