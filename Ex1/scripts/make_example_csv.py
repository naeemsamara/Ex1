"""Generate examples/mrhead_planes.csv - the planes used in the experiment.

The volume is MRHead.nrrd, 256 x 256 x 130 voxels. The CSV contains:
  1. the three classic sections (rectangles = trapezoids with a1a2 = bc),
  2. a triangle rotating 360 degrees around the volume center (a "fly-through"),
  3. a few deliberately broken rows, to show the error frames.

Usage:  python scripts/make_example_csv.py [output.csv]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SX, SY, SZ = 256, 256, 130
CENTER = np.array([(SX - 1) / 2, (SY - 1) / 2, (SZ - 1) / 2])


def fmt(points) -> str:
    return ",".join(f"{v:.4f}" for p in points for v in p)


def rotating_triangles(steps: int) -> list[str]:
    """Isosceles triangles whose plane turns around the z axis."""
    rows = []
    for k in range(steps):
        t = 2 * np.pi * k / steps
        u = np.array([0.0, 0.0, 1.0])                 # apex -> base direction (z)
        w = np.array([np.cos(t), np.sin(t), 0.0])     # along the base
        height, half = 125.0, 120.0
        a = CENTER - u * height / 2
        b = a + u * height - w * half
        c = a + u * height + w * half
        rows.append(fmt([a, b, c]))
    return rows


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "examples/mrhead_planes.csv")
    z, y, x = (SZ - 1) / 2, (SY - 1) / 2, (SX - 1) / 2
    lines = [
        "# Planes for data/MRHead.nrrd (256x256x130). One plane per row.",
        "# 9 numbers = triangle a,b,c ; 12 numbers = trapezoid a1,a2,b,c",
        "# --- classic sections (rectangles) ---",
        fmt([[0, 0, z], [255, 0, z], [0, 255, z], [255, 255, z]]),        # z = const
        fmt([[0, y, 0], [255, y, 0], [0, y, 129], [255, y, 129]]),        # y = const
        fmt([[x, 0, 0], [x, 255, 0], [x, 0, 129], [x, 255, 129]]),        # x = const
        "# --- invalid on purpose: edges not equal (|dab - dac| >= 0.001) ---",
        fmt([[128, 0, z], [0, 255, z], [255, 255, z]]),
        "# --- rotating triangle ---",
        *rotating_triangles(12)[:6],
        "# --- invalid on purpose: a2 is not on the plane of a1, b, c ---",
        # equal edges (both sqrt(255^2 + 20^2)) but the quadrilateral is twisted
        fmt([[0, 0, z], [255, 0, z + 10], [0, 255, z + 20], [255, 255, z - 10]]),
        *rotating_triangles(12)[6:],
        "# --- invalid on purpose: wrong number of values / not numbers ---",
        "1,2,3,4,5",
        "a,b,c,1,2,3,4,5,6",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
