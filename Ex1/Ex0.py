"""Demo: project a NRRD volume onto every plane in a CSV file and save an MP4.

Usage:
    python Ex0.py file.nrrd file.csv file.mp4 [--fps 5]

One frame per CSV row, in the CSV order. A row with an invalid plane becomes
an "error frame" (black with a red X and the reason); the other rows still
produce their normal frames.
"""

from __future__ import annotations

import argparse
import sys
import time

from projection import NrrdFormatError, PlaneCsvError, Projector, read_nrrd, read_plane_csv
from projection.errors import InvalidPlaneError
from projection.video_writer import canvas_size, error_frame, place_on_canvas, to_uint8, write_mp4


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plane projection of a 3D NRRD volume to MP4.")
    parser.add_argument("nrrd", help="input 3D volume (.nrrd)")
    parser.add_argument("csv", help="planes: one row of 9 or 12 numbers per plane")
    parser.add_argument("mp4", help="output video file")
    parser.add_argument("--fps", type=float, default=5.0,
                        help="frames per second of the output video (default 5)")
    return parser.parse_args(argv)


def run(nrrd_path: str, csv_path: str, mp4_path: str, fps: float = 5.0) -> dict:
    """Do the work and return a short summary (used by the tests too)."""
    volume = read_nrrd(nrrd_path)
    rows = read_plane_csv(csv_path)
    projector = Projector(volume)

    # 1) project every valid plane; a plane that fails becomes an error row.
    results: list[tuple[int, object]] = []      # (csv line, image or error text)
    projection_time = 0.0
    for row in rows:
        if not row.is_valid:
            results.append((row.line, row.error))
            continue
        try:
            start = time.perf_counter()
            image = projector.project(row.plane)
            projection_time += time.perf_counter() - start
            results.append((row.line, image))
        except InvalidPlaneError as exc:
            results.append((row.line, str(exc)))

    # 2) one canvas size for the whole video, gray levels from the whole volume.
    images = [r for _, r in results if not isinstance(r, str)]
    size = canvas_size([im.shape for im in images])
    low, high = volume.value_range()
    frames = []
    for line, result in results:
        if isinstance(result, str):
            frames.append(error_frame(size, line, result))
        else:
            frames.append(place_on_canvas(to_uint8(result, low, high), size))

    write_mp4(mp4_path, frames, fps)
    n_ok = len(images)
    return {
        "volume_shape": volume.shape,
        "frames": len(frames),
        "valid": n_ok,
        "errors": [(line, r) for line, r in results if isinstance(r, str)],
        "avg_projection_ms": 1000 * projection_time / n_ok if n_ok else 0.0,
        "canvas": size,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run(args.nrrd, args.csv, args.mp4, args.fps)
    except (OSError, NrrdFormatError, PlaneCsvError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Volume {summary['volume_shape']}, {summary['frames']} frames "
          f"({summary['valid']} valid, {len(summary['errors'])} error frames), "
          f"canvas {summary['canvas'][1]}x{summary['canvas'][0]}")
    for line, reason in summary["errors"]:
        print(f"  CSV line {line}: {reason}")
    print(f"Average projection time: {summary['avg_projection_ms']:.2f} ms per plane")
    print(f"Saved {args.mp4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
