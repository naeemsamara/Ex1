"""The projection algorithm (docs/ALGORITHM.md explains it step by step)."""

from __future__ import annotations

import numpy as np

from .errors import InvalidPlaneError
from .plane import Plane
from .volume import Volume

MAX_IMAGE_SIDE = 4096  # guards memory against absurd planes far outside M


class Projector:
    """Projects a Volume onto a Plane and returns the 2D image E.

    This is the lecturer's algorithm written in "array form":
    instead of walking point-by-point with p = p + dp, every output pixel
    computes its own 3D point directly. The result is the same, but numpy
    does all pixels at once (needed for the 30+ FPS requirement), and there
    are no holes or accumulated floating-point drift.
    """

    def __init__(self, volume: Volume):
        self._volume = volume

    @property
    def volume(self) -> Volume:
        return self._volume

    @staticmethod
    def image_shape(plane: Plane) -> tuple[int, int]:
        """(rows, cols) = (floor(Dab) + 1, floor(Dbc) + 1)."""
        return int(plane.edge_length) + 1, int(plane.base_length) + 1

    def project(self, plane: Plane) -> np.ndarray:
        """Return E as an array indexed image[y, x] (row y, column x)."""
        rows, cols = self.image_shape(plane)
        if rows > MAX_IMAGE_SIDE or cols > MAX_IMAGE_SIDE:
            raise InvalidPlaneError(
                f"plane is too large ({rows}x{cols} > {MAX_IMAGE_SIDE} pixels per side)")

        f32 = np.float32
        a1, a2, b, c = (p.astype(f32) for p in (plane.a1, plane.a2, plane.b, plane.c))
        # Step 2: unit vectors along the two equal edges.
        v1 = (b - a1) / f32(np.linalg.norm(b - a1))
        v2 = (c - a2) / f32(np.linalg.norm(c - a2))

        # Step 5a/5b: for every row y, a1 and a2 have moved y voxels down their edges.
        y = np.arange(rows, dtype=f32)[:, None]            # (rows, 1)
        p1 = a1 + y * v1                                     # (rows, 3)
        p2 = a2 + y * v2                                     # (rows, 3)

        # Step 5d/5e: length and direction of the segment p1 -> p2 in each row.
        seg = p2 - p1
        d12 = np.linalg.norm(seg, axis=1)                    # (rows,)
        safe = np.where(d12 > 0, d12, f32(1))
        dp = seg / safe[:, None]                             # unit vector (0 at an apex)

        # Step 5f-ii inverted: the loop writes step x1 (0, 1, ..., floor(d12))
        # to column x = round(Dbc/2 - d12/2 + x1). So column x shows step
        # x1 = round(x - (Dbc/2 - d12/2)), if that step exists.
        offset = f32(plane.base_length / 2) - d12 / 2        # (rows,)
        x = np.arange(cols, dtype=f32)[None, :]              # (1, cols)
        x1 = np.rint(x - offset[:, None])                    # (rows, cols)
        valid = (x1 >= 0) & (x1 <= np.floor(d12)[:, None])
        # On an exact .5 tie two columns would claim the same step; keep only
        # the column the forward loop actually writes to.
        valid &= np.rint(offset[:, None] + x1) == x

        # Step 5f-i: the 3D point p = p1 + x1 * dp of every pixel (one axis at
        # a time - faster than a (rows, cols, 3) array), then the closest voxel.
        px, py, pz = (p1[:, k, None] + x1 * dp[:, k, None] for k in range(3))
        return self._volume.sample_nearest(px, py, pz, valid)
