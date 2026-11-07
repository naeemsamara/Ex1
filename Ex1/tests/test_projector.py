"""Correctness of the projection itself (SRS FR-3, FR-4)."""

import numpy as np
import pytest

from projection import InvalidPlaneError, Plane, Projector, Volume
from projection.projector import MAX_IMAGE_SIDE


def reference_projection(volume: Volume, plane: Plane) -> np.ndarray:
    """The lecturer's loop, written literally (slow but obviously correct).

    Differences from the pseudocode are the documented design decisions:
    row y is at distance y from a (so the apex and the base are included),
    and the pixel column is rounded.
    """
    rows, cols = Projector.image_shape(plane)
    E = np.zeros((rows, cols), dtype=volume.dtype)
    v1 = (plane.b - plane.a1) / np.linalg.norm(plane.b - plane.a1)
    v2 = (plane.c - plane.a2) / np.linalg.norm(plane.c - plane.a2)
    a1, a2 = plane.a1.copy(), plane.a2.copy()
    for y in range(rows):
        d12 = np.linalg.norm(a2 - a1)
        dp = (a2 - a1) / d12 if d12 > 0 else np.zeros(3)
        p = a1.copy()
        for x1 in range(int(d12) + 1):
            q = np.rint(p).astype(int)
            inside = all(0 <= q[k] < volume.shape[k] for k in range(3))
            x = int(round(plane.base_length / 2 - d12 / 2 + x1))
            if 0 <= x < cols:
                E[y, x] = volume.data[tuple(q)] if inside else 0
            p = p + dp
        a1, a2 = a1 + v1, a2 + v2
    return E


def test_axis_aligned_rectangle_equals_slice(gradient_volume):
    # a1=(0,0,4) -> b=(0,9,4), a2=(9,0,4) -> c=(9,9,4): the slice z=4
    plane = Plane.from_points([[0, 0, 4], [9, 0, 4], [0, 9, 4], [9, 9, 4]])
    image = Projector(gradient_volume).project(plane)
    assert image.shape == (10, 10)
    np.testing.assert_array_equal(image, gradient_volume.data[:, :, 4].T)


def test_values_come_from_the_right_voxels(gradient_volume):
    # the value of the gradient volume is x + 10y + 100z: check a few pixels
    plane = Plane.from_points([[0, 0, 7], [9, 0, 7], [0, 9, 7], [9, 9, 7]])
    image = Projector(gradient_volume).project(plane)
    assert image[0, 0] == 700          # row y=0, col x=0 -> voxel (0,0,7)
    assert image[3, 5] == 5 + 30 + 700  # row 3, col 5 -> voxel (5,3,7)


def test_triangle_shape_and_outside_is_zero(gradient_volume):
    plane = Plane.from_points([[4.5, 0, 2], [0, 9, 2], [9, 9, 2]])
    image = Projector(gradient_volume).project(plane)
    rows, cols = image.shape
    assert (rows, cols) == (int(plane.edge_length) + 1, 10)
    # the first row is the apex: exactly one pixel, even though it falls on a
    # .5 tie between two columns (x = 4.5)
    assert np.count_nonzero(image[0]) == 1
    # the last row (distance floor(Dab) from a, i.e. at the base b..c) is
    # (almost) full width; rows get wider from the apex down
    assert np.count_nonzero(image[-1]) >= cols - 1
    widths = np.count_nonzero(image, axis=1)
    assert np.all(np.diff(widths) >= 0)


def test_plane_outside_the_volume_is_black(gradient_volume):
    plane = Plane.from_points([[100, 100, 100], [100, 120, 100], [120, 100, 100], [120, 120, 100]])
    image = Projector(gradient_volume).project(plane)
    assert image.size > 0 and not image.any()


def test_partly_outside_plane(gradient_volume):
    plane = Plane.from_points([[-5, 0, 3], [4, 0, 3], [-5, 9, 3], [4, 9, 3]])
    image = Projector(gradient_volume).project(plane)
    assert not image[:, :5].any()                     # x < 0 part
    np.testing.assert_array_equal(image[:, 5:], gradient_volume.data[0:5, :, 3].T)


@pytest.mark.parametrize("seed", range(5))
def test_matches_reference_loop_on_random_planes(seed):
    rng = np.random.default_rng(seed)
    data = rng.integers(1, 1000, size=(30, 25, 20), dtype=np.uint16)
    volume = Volume(data)
    center = np.array([15.0, 12.0, 10.0])
    u = rng.normal(size=3); u /= np.linalg.norm(u)
    w = np.cross(u, rng.normal(size=3)); w /= np.linalg.norm(w)
    a = center - 10 * u
    plane = Plane.from_points([a, a + 20 * u - 8 * w, a + 20 * u + 8 * w])
    fast = Projector(volume).project(plane)
    slow = reference_projection(volume, plane)
    # They may differ only where a coordinate is (almost) exactly k + 0.5:
    # float32 (fast) vs float64 (loop with p = p + dp drift) can then round
    # to the neighbouring voxel - the "negligible difference" of Q&A 4.
    assert fast.shape == slow.shape
    assert np.mean(fast == slow) > 0.99


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
def test_output_keeps_the_volume_type(dtype):
    volume = Volume(np.full((5, 5, 5), 7, dtype=dtype))
    image = Projector(volume).project(Plane.from_points([[2, 0, 2], [0, 4, 2], [4, 4, 2]]))
    assert image.dtype == dtype


def test_huge_plane_is_rejected(gradient_volume):
    n = MAX_IMAGE_SIDE + 10
    plane = Plane.from_points([[0, 0, 0], [n, 0, 0], [0, n, 0], [n, n, 0]])
    with pytest.raises(InvalidPlaneError, match="too large"):
        Projector(gradient_volume).project(plane)
