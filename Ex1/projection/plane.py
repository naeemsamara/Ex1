"""The plane p, given as an isosceles triangle (3 points) or trapezoid (4 points)."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .errors import InvalidPlaneError

EPS = 0.001  # tolerance given by the lecturer (Q&A 1, 3)


class Plane:
    """A validated plane section: two equal-length edges a1->b and a2->c.

    * 3 points (a, b, c):      a1 = a2 = a  (isosceles triangle)
    * 4 points (a1, a2, b, c): isosceles trapezoid

    Points are in voxel coordinates (x, y, z) of the volume. They may lie
    outside the volume; those parts of the image are simply 0.
    """

    def __init__(self, a1: Sequence[float], a2: Sequence[float],
                 b: Sequence[float], c: Sequence[float]):
        self.a1, self.a2, self.b, self.c = (self._as_point(p) for p in (a1, a2, b, c))
        self._validate()

    # ---- factories -------------------------------------------------------
    @classmethod
    def from_points(cls, points: Sequence[Sequence[float]]) -> "Plane":
        """Build from 3 points (a, b, c) or 4 points (a1, a2, b, c)."""
        if len(points) == 3:
            a, b, c = points
            return cls(a, a, b, c)
        if len(points) == 4:
            return cls(*points)
        raise InvalidPlaneError(f"expected 3 or 4 points, got {len(points)}")

    @classmethod
    def from_values(cls, values: Sequence[float]) -> "Plane":
        """Build from a flat list of 9 or 12 numbers (one CSV row)."""
        if len(values) not in (9, 12):
            raise InvalidPlaneError(f"expected 9 or 12 numbers, got {len(values)}")
        pts = [values[i:i + 3] for i in range(0, len(values), 3)]
        return cls.from_points(pts)

    # ---- derived quantities ----------------------------------------------
    @property
    def edge_length(self) -> float:
        """Dab = dist(a1, b) (= dist(a2, c) up to EPS)."""
        return float(np.linalg.norm(self.b - self.a1))

    @property
    def base_length(self) -> float:
        """Dbc = dist(b, c)."""
        return float(np.linalg.norm(self.c - self.b))

    @property
    def is_triangle(self) -> bool:
        return bool(np.array_equal(self.a1, self.a2))

    # ---- validation (docs/SRS.md, FR-2) ----------------------------------
    @staticmethod
    def _as_point(p: Sequence[float]) -> np.ndarray:
        arr = np.asarray(p, dtype=np.float64)
        if arr.shape != (3,):
            raise InvalidPlaneError(f"a point needs 3 coordinates, got {p!r}")
        if not np.all(np.isfinite(arr)):
            raise InvalidPlaneError(f"point has a non-finite coordinate: {p!r}")
        return arr

    def _validate(self) -> None:
        d1 = np.linalg.norm(self.b - self.a1)
        d2 = np.linalg.norm(self.c - self.a2)
        if abs(d1 - d2) >= EPS:
            raise InvalidPlaneError(
                f"edges are not equal: |{d1:.4f} - {d2:.4f}| >= {EPS}")
        if d1 < 1.0:
            raise InvalidPlaneError("edges are shorter than one voxel")
        if self.base_length < 1.0:
            raise InvalidPlaneError("b and c are less than one voxel apart")
        if np.linalg.norm(self.a2 - self.a1) > self.base_length:
            raise InvalidPlaneError("dist(a1, a2) must be <= dist(b, c)")
        # All points on one plane, and not all on one line.
        normal = np.cross(self.b - self.a1, self.c - self.a1)
        n = np.linalg.norm(normal)
        if n < EPS:
            raise InvalidPlaneError("points are collinear - they do not define a plane")
        if not self.is_triangle:
            distance = abs(np.dot(self.a2 - self.a1, normal / n))
            if distance >= EPS:
                raise InvalidPlaneError(
                    f"a2 is {distance:.4f} voxels off the plane of a1, b, c")

    def __repr__(self) -> str:
        pts = ", ".join(str(p.tolist()) for p in (self.a1, self.a2, self.b, self.c))
        return f"Plane({pts})"
