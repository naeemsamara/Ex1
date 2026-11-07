"""The 3D matrix M from the assignment."""

from __future__ import annotations

import numpy as np

_MAX_SIDE = 2 ** 10  # assignment: 1 <= sx, sy, sz < 2^10


class Volume:
    """A 3D raster M of size sx*sy*sz, indexed M[x][y][z] (voxel coordinates).

    The class owns the data and answers one question quickly:
    "what is the value of the voxel closest to each of these points?"
    """

    def __init__(self, data: np.ndarray):
        if data.ndim != 3:
            raise ValueError("a volume must be 3D")
        if any(s < 1 or s >= _MAX_SIDE for s in data.shape):
            raise ValueError(f"each side must be in [1, {_MAX_SIDE}), got {data.shape}")
        self._data = np.ascontiguousarray(data)
        self._flat = self._data.reshape(-1)  # a view, no copy
        sx, sy, sz = self._data.shape
        self._strides = np.array([sy * sz, sz, 1], dtype=np.int64)
        self._upper = np.array([sx - 1, sy - 1, sz - 1], dtype=np.float32)

    @property
    def data(self) -> np.ndarray:
        return self._data

    @property
    def shape(self) -> tuple[int, int, int]:
        return self._data.shape  # type: ignore[return-value]

    @property
    def dtype(self) -> np.dtype:
        return self._data.dtype

    def value_range(self) -> tuple[float, float]:
        return float(self._data.min()), float(self._data.max())

    def sample_nearest(self, x: np.ndarray, y: np.ndarray, z: np.ndarray,
                       valid: np.ndarray | None = None) -> np.ndarray:
        """Nearest-voxel values at the points (x, y, z) (arrays of equal shape).

        Points outside the volume (and points where `valid` is False) get 0,
        exactly as in the assignment ("if p is NOT in M, v=0").
        Nearest voxel = round each coordinate (lecturer, Q&A 4).
        """
        inside = np.ones(x.shape, dtype=bool) if valid is None else valid.copy()
        flat_index = np.zeros(x.shape, dtype=np.int32)
        for coord, upper, stride in zip((x, y, z), self._upper, self._strides):
            # +0.5 then truncate == round-half-up for values >= -0.5
            idx = coord + np.float32(0.5)
            inside &= (idx >= 0) & (idx < upper + 1)
            idx_int = idx.astype(np.int32)
            if stride != 1:
                idx_int *= np.int32(stride)
            flat_index += idx_int
        flat_index[~inside] = 0  # any legal index; the value is zeroed below
        values = self._flat[flat_index]
        values[~inside] = 0
        return values
