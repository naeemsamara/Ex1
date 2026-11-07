# Software Requirements Specification (SRS)

**Project:** Ex1 – Plane projection of a 3D volume
**Course:** Introduction to Software Engineering (OOP/OOD), Ariel University

## 1. Purpose
Given a 3D raster volume **M** and a plane **p**, compute the 2D image (matrix **E**) of
the cut of **M** along **p**, quickly enough to show many planes per second, and
produce a demo video with one frame per plane.

## 2. Scope
In scope: reading NRRD volumes, validating planes, computing projections, the
command-line demo `python Ex0.py file.nrrd file.csv file.mp4`, tests and a benchmark.
Out of scope: a GUI, interpolation / "super-resolution" (the lecturer asked for the
closest voxel, Q&A 4), physical (mm) coordinates, detached-header NRRD files.

## 3. Definitions
| Term | Meaning |
|---|---|
| Voxel | One cell `M[x][y][z]` of the volume. |
| Voxel coordinates | Points are given as `(x, y, z)` in voxel units: `(0,0,0)` is the first voxel, `(sx-1, sy-1, sz-1)` the last. |
| Triangle plane | 3 points `a, b, c` with `dist(a,b) = dist(a,c)` (isosceles). |
| Trapezoid plane | 4 points `a1, a2, b, c` with `dist(a1,b) = dist(a2,c)`. A triangle is a trapezoid with `a1 = a2 = a`. |
| `Dab`, `Dbc` | `dist(a1,b)` and `dist(b,c)`. |
| EPS | 0.001, the tolerance for "equal" (given by the lecturer). |

## 4. Inputs and outputs
* **Volume** – NRRD file, attached header, `dimension: 3`, encoding `raw` or `gzip`,
  value type unsigned/signed 8, 16 or 32-bit integer (float/double also accepted).
  Sizes `1 <= sx, sy, sz < 2^10`.
* **Planes** – CSV file, one plane per row:
  * 9 numbers: `ax,ay,az,bx,by,bz,cx,cy,cz` (triangle)
  * 12 numbers: `a1x,a1y,a1z,a2x,a2y,a2z,bx,by,bz,cx,cy,cz` (trapezoid)
  * Empty lines and lines starting with `#` are ignored; an optional first header row
    (no numbers) is skipped.
* **Video** – MP4 (H.264), one frame per CSV row in CSV order.

## 5. Functional requirements
| ID | Requirement |
|---|---|
| FR-1 | Read a 3D NRRD file into `M` with `M[x][y][z]` indexing, keeping the value type. Unsupported or broken files raise `NrrdFormatError` with a clear message. |
| FR-2 | A plane is **valid** only if: (a) 3 or 4 points with 3 finite coordinates each; (b) `|dist(a1,b) - dist(a2,c)| < EPS`; (c) `dist(a1,a2) <= dist(b,c)`; (d) all 4 points on one plane (distance of `a2` from plane `a1,b,c` `< EPS`); (e) not degenerate: edges and `bc` at least 1 voxel long, points not collinear. Otherwise `InvalidPlaneError` is raised. |
| FR-3 | For a valid plane, return `E` of size `(floor(Dab)+1) x (floor(Dbc)+1)` computed by the lecturer's algorithm (docs/ALGORITHM.md), using the **closest voxel**. |
| FR-4 | Points of the plane outside `M` produce value 0. A plane may be partly or fully outside `M`. Images larger than 4096 pixels per side are refused (`InvalidPlaneError`) to protect memory. |
| FR-5 | Read the CSV; each row becomes either a valid plane or an error with its line number and reason. A bad row never stops the other rows. A missing or empty CSV raises `PlaneCsvError`. |
| FR-6 | The demo writes one frame per CSV row, in order. Valid rows: the image (gray levels scaled by the min/max of the whole volume, centered on a black canvas, 1 voxel = 1 pixel). Invalid rows: an **error frame** – black, red X, "INVALID PLANE", the CSV line and the reason. |
| FR-7 | The demo prints a summary (frames, errors with reasons, average projection time). Bad inputs (missing file, bad NRRD) print `Error: ...` and exit with code 1 – no traceback. |

## 6. Non-functional requirements
| ID | Requirement |
|---|---|
| NFR-1 | **Performance:** on a 500³ volume, at least **30** projections per second (must), target **100+**. Measured by `benchmark.py`. |
| NFR-2 | **Correctness:** the fast implementation must give the same image as a literal implementation of the lecturer's loop (tested). |
| NFR-3 | **Robustness:** no crash on any CSV content; all errors are reported, not hidden. |
| NFR-4 | **Portability:** Python 3.10+, depends only on numpy, Pillow, imageio, imageio-ffmpeg. |
| NFR-5 | **Maintainability:** one class per responsibility (see README, design), docstrings, automated tests (`pytest`). |

## 7. Assumptions and design decisions
1. **Coordinates are voxel indices**, not millimetres. The NRRD `space directions`
   (voxel spacing) are ignored, so a non-cubic voxel (MRHead: 1 x 1 x 1.3 mm) looks
   slightly squashed. This keeps M[x][y][z] = what the assignment defines.
2. **Rows start at the apex.** The pseudocode moves `a1, a2` *before* the first row, so
   the apex row is never drawn and the base is not reached. Here row `y` is at distance
   `y` from `a` (y = 0 … floor(Dab)), so both apex and base are included.
3. **Closest voxel** = round each coordinate (Q&A 4).
4. **Error frames** in the demo; the library raises exceptions (Q&A 3).
5. **Brightness** is scaled once per volume (not per frame) so frames are comparable.
