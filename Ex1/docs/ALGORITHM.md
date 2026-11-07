# The projection algorithm

## 1. The idea
The plane is a triangle (or trapezoid) inside the volume. We "scan" it row by row,
from the apex `a` down to the base `bc`, like a printer:

```
            a                 row y = 0      (one pixel)
           / \
          /   \               row y          (segment p1 -> p2)
       p1 *-----* p2
        /         \
       b-----------c          row y = floor(Dab)  (the base)
```

* `p1` walks from `a1` to `b`, `p2` walks from `a2` to `c`, both one voxel per row.
* In each row we walk from `p1` to `p2`, one voxel per step, and copy the value of the
  closest voxel of `M` into the image.
* Rows are centered: a short segment (near the apex) is drawn in the middle of the
  image, the base fills the full width `Dbc`.

## 2. The lecturer's pseudocode, with our two design decisions
```
Dab = dist(a1, b)          # = dist(a2, c) up to EPS
Dbc = dist(b, c)
v1 = (b - a1) / Dab        # unit vector a1 -> b
v2 = (c - a2) / Dab        # unit vector a2 -> c
E  = zeros(rows = floor(Dab) + 1, cols = floor(Dbc) + 1)

for y in 0 .. floor(Dab):                  # (decision 1: include apex and base)
    p1  = a1 + y * v1
    p2  = a2 + y * v2
    d12 = dist(p1, p2)
    dp  = (p2 - p1) / d12                  # (0 when d12 = 0, at the apex)
    for x1 in 0 .. floor(d12):
        p = p1 + x1 * dp
        v = M[round(p)]   if round(p) is inside M   else 0      # (decision 2: closest voxel)
        x = round(Dbc/2 - d12/2 + x1)
        E[y][x] = v
return E
```
For a triangle `a1 = a2 = a`; for a trapezoid the top row is the segment `a1 a2`.

## 3. Making it fast (vectorized version, `projection/projector.py`)
A Python double loop over ~230,000 pixels runs at about 1 frame per second. The
requirement is 30+ (target 100+). So the same computation is written for **all
pixels at once** with numpy arrays:

1. `y = [0, 1, …, rows-1]` → `p1`, `p2`, `d12`, `dp` for all rows at once (arrays of size `rows`).
2. **Invert the inner loop.** Instead of "step `x1` writes to column `x`", ask "which step
   does column `x` show?":  `x1 = round(x - (Dbc/2 - d12/2))`. The column is filled only
   if `0 <= x1 <= floor(d12)` and the forward loop really writes there
   (`round(offset + x1) == x`, this settles exact .5 ties).
3. `p = p1 + x1 * dp` for every pixel, one axis at a time (x, y, z arrays of shape
   `rows x cols`, float32).
4. Closest voxel: `i = int(coord + 0.5)` per axis, check `0 <= i < size`, combine into
   one flat index `ix*sy*sz + iy*sz + iz`, and read all values with one numpy gather.
   Outside → 0.

Every operation is a numpy operation on whole arrays, so the work happens in C.

### Complexity
* Time: **O(rows × cols) = O(Dab × Dbc)** per plane – each pixel is computed once,
  independent of the volume size. No preprocessing of the volume is needed.
* Memory: a few `rows × cols` temporary arrays (≈ 10 MB for a 500 × 700 image).

### Correctness of the fast version
`tests/test_projector.py::test_matches_reference_loop_on_random_planes` runs the
literal loop above and the fast version on random planes and requires the same image.
In our runs they match on 100% of the pixels for the small test volumes and on 99.996%
for a 500³ plane (9 of ~227,000 pixels: a coordinate within float error of a .5
boundary rounds to the neighbouring voxel – the "negligible difference" of Q&A 4).
The test allows 1%. Measured on the same plane, the literal loop takes 0.8 s per
frame (≈1 FPS), the vectorized version 3.3 ms (≈300 FPS).

## 4. Validation of the plane (before projecting)
See SRS FR-2: equal edges (`< EPS`), `dist(a1,a2) <= dist(b,c)`, coplanar
(`|(a2 - a1) · n| < EPS` with `n` the unit normal of `a1, b, c`), and non-degenerate
(not collinear, sides at least 1 voxel).
