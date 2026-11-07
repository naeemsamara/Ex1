"""Runtime benchmark: projections per second on a 500^3 volume (requirement: >= 30, target 100).

Usage:
    python benchmark.py [--size 500] [--frames 200]
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from projection import Plane, Projector, Volume


def random_planes(n: int, size: int, rng: np.random.Generator) -> list[Plane]:
    """Random isosceles triangles roughly the size of the volume, in random orientations."""
    planes = []
    center = np.full(3, (size - 1) / 2)
    while len(planes) < n:
        # orthonormal frame (u, w) of a random plane through the center
        u = rng.normal(size=3); u /= np.linalg.norm(u)
        w = np.cross(u, rng.normal(size=3)); w /= np.linalg.norm(w)
        h, half = size * 0.9, size * 0.45
        a = center - u * h / 2
        b = a + u * h - w * half
        c = a + u * h + w * half
        planes.append(Plane.from_points([a, b, c]))
    return planes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=500)
    parser.add_argument("--frames", type=int, default=200)
    args = parser.parse_args()

    rng = np.random.default_rng(0)
    data = rng.integers(0, 256, size=(args.size,) * 3, dtype=np.uint8)
    projector = Projector(Volume(data))
    planes = random_planes(args.frames, args.size, rng)

    projector.project(planes[0])  # warm-up
    start = time.perf_counter()
    for plane in planes:
        image = projector.project(plane)
    elapsed = time.perf_counter() - start

    fps = args.frames / elapsed
    print(f"volume {args.size}^3 uint8, image {image.shape[1]}x{image.shape[0]} pixels")
    print(f"{args.frames} projections in {elapsed:.3f} s -> {fps:.1f} FPS "
          f"({1000 / fps:.2f} ms per projection)")
    print("requirement >= 30 FPS:", "PASS" if fps >= 30 else "FAIL")


if __name__ == "__main__":
    main()
