"""End-to-end test of the demo: python Ex0.py file.nrrd file.csv file.mp4 (SRS FR-6, FR-7)."""

import subprocess
import sys

import imageio.v2 as imageio
import numpy as np

from conftest import ROOT
from projection import write_nrrd

import Ex0


def make_inputs(tmp_path):
    x, y, z = np.indices((40, 40, 40))
    data = np.where((x - 20) ** 2 + (y - 20) ** 2 + (z - 20) ** 2 < 15 ** 2, 200, 0).astype(np.uint8)
    nrrd = tmp_path / "ball.nrrd"
    write_nrrd(nrrd, data)
    csv = tmp_path / "planes.csv"
    csv.write_text(
        "0,0,20,39,0,20,0,39,20,39,39,20\n"   # 1: middle slice -> a disc
        "0,0,0,10,0,0,0,11,0\n"               # 2: invalid (edges not equal)
        "19.5,0,20,0,39,20,39,39,20\n"        # 3: triangle through the ball
    )
    return nrrd, csv, tmp_path / "out.mp4"


def read_frames(path):
    reader = imageio.get_reader(path)
    frames = [f for f in reader]
    reader.close()
    return frames


def test_run_creates_one_frame_per_row(tmp_path):
    nrrd, csv, mp4 = make_inputs(tmp_path)
    summary = Ex0.run(str(nrrd), str(csv), str(mp4), fps=5)
    assert summary["frames"] == 3 and summary["valid"] == 2
    assert [line for line, _ in summary["errors"]] == [2]

    frames = read_frames(mp4)
    assert len(frames) == 3
    first, error, third = frames
    # frame 1: bright disc in the middle, black corners
    h, w, _ = first.shape
    assert first[h // 2, w // 2].mean() > 150 and first[2, 2].mean() < 30
    # frame 2: the error frame has red in it (the X), the normal frames do not
    red = lambda f: np.mean((f[..., 0] > 150) & (f[..., 1] < 100))  # noqa: E731
    assert red(error) > 0.005 and red(first) == 0 and red(third) == 0


def test_command_line(tmp_path):
    nrrd, csv, mp4 = make_inputs(tmp_path)
    result = subprocess.run([sys.executable, "Ex0.py", str(nrrd), str(csv), str(mp4)],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "1 error frames" in result.stdout and mp4.exists()


def test_command_line_bad_input_gives_message_not_traceback(tmp_path):
    result = subprocess.run([sys.executable, "Ex0.py", str(tmp_path / "missing.nrrd"),
                             "x.csv", str(tmp_path / "o.mp4")],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1
    assert result.stderr.startswith("Error:") and "Traceback" not in result.stderr
