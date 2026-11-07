# Testing strategy

## Levels
| Level | What | Where |
|---|---|---|
| Unit | Plane validation rules (every rule in SRS FR-2, valid and invalid cases, EPS boundary) | `tests/test_plane.py` |
| Unit | NRRD reader: 8/16/32-bit, signed, raw/gzip, big-endian, broken files | `tests/test_io.py` |
| Unit | CSV parser: header, comments, empty lines, mixed valid/invalid rows, line numbers | `tests/test_io.py` |
| Unit | Projection: axis-aligned plane = native slice; exact voxel values (gradient volume); triangle shape; outside = 0; partly outside; output type kept; too-large plane refused | `tests/test_projector.py` |
| Oracle | Fast projection vs. a literal (slow) implementation of the lecturer's loop on random planes | `tests/test_projector.py` |
| End-to-end (demo) | `Ex0.py` on a ball volume and a CSV with 2 valid rows + 1 invalid row: 3 frames, frame 1 shows a bright disc, frame 2 is a red error frame, frames 1 and 3 have no red; command line works; bad input → `Error:` + exit code 1 | `tests/test_demo.py` |
| Performance | 500³ volume, random planes, FPS ≥ 30 | `benchmark.py` |
| Visual | Look at the output video of the experiment | `results/`, docs/EXPERIMENT.md |

## Key ideas
* **Known answers:** gradient volumes (`value = x + 10y + 100z`) let a test check that each
  pixel came from the right voxel, not just "the image looks fine".
* **Oracle test:** the vectorized code is fast but hard to read; the slow loop is easy to
  read. If both agree on random planes, the fast code does what the algorithm says.
* **The demo's error handling** (Q&A 3) is tested end-to-end: the invalid row must produce
  an error frame *and* the valid rows around it must still produce normal frames.

## Running
```bash
pip install -r requirements.txt
python -m pytest -q          # 49 tests, < 2 seconds
python benchmark.py          # FPS on 500^3
```
