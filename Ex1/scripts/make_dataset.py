"""Create the synthetic NRRD files of the data set (docs/DATASET.md).

Synthetic volumes have a known content, so the expected projection can be
computed by hand - that is what makes them useful for testing.

Usage:  python scripts/make_dataset.py [output_dir]   (default: data/)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from projection import write_nrrd  # noqa: E402


def gradient(shape, dtype) -> np.ndarray:
    """value = x + 10*y + 100*z  -> every voxel tells you its own coordinates."""
    x, y, z = np.indices(shape)
    return (x + 10 * y + 100 * z).astype(dtype)


def sphere(size: int, dtype=np.uint8) -> np.ndarray:
    """A bright ball (255) in a dark cube (0)."""
    c = (size - 1) / 2
    x, y, z = np.indices((size, size, size))
    inside = (x - c) ** 2 + (y - c) ** 2 + (z - c) ** 2 <= (size / 3) ** 2
    return np.where(inside, 255, 0).astype(dtype)


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "gradient_u8_raw.nrrd": (gradient((10, 9, 2), np.uint8), "raw"),
        "gradient_u16_gzip.nrrd": (gradient((20, 15, 12), np.uint16), "gzip"),
        "gradient_u32_gzip.nrrd": (gradient((30, 20, 10), np.uint32) * 1000, "gzip"),
        "sphere_128_u8.nrrd": (sphere(128), "gzip"),
    }
    for name, (data, encoding) in files.items():
        write_nrrd(out / name, data, encoding)
        print(f"wrote {out / name}  shape={data.shape} dtype={data.dtype} ({encoding})")


if __name__ == "__main__":
    main()
