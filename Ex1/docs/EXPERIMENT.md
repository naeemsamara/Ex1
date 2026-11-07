# Experiment

## Setup
* **Machine:** cloud Linux VM, Intel Xeon @ 2.10 GHz (2 cores), Python 3.13, numpy 2.5.
  (Numbers on a laptop such as an M2 Mac are expected to be similar or better.)
* **Volume:** `data/MRHead.nrrd`, 256 × 256 × 130, int16 (3D Slicer sample).
* **Planes:** `examples/mrhead_planes.csv` (made by `scripts/make_example_csv.py`), 19 rows:
  * 3 classic sections as rectangles (trapezoids): `z = 64.5`, `y = 127.5`, `x = 127.5`
  * a triangle rotating 360° around the volume center in 12 steps
  * 4 invalid rows on purpose: unequal edges, a twisted (non-planar) trapezoid,
    a row with 5 numbers, a row with text
* **Command:**
  ```bash
  python Ex0.py data/MRHead.nrrd examples/mrhead_planes.csv results/mrhead_planes.mp4
  ```

## Results
Output: [`results/mrhead_planes.mp4`](../results/mrhead_planes.mp4) (19 frames, 256×256, 5 FPS),
all frames side by side: [`results/mrhead_planes_contact_sheet.png`](../results/mrhead_planes_contact_sheet.png).

```
Volume (256, 256, 130), 19 frames (15 valid, 4 error frames), canvas 256x256
  CSV line 8: edges are not equal: |285.3226 - 284.8754| >= 0.001
  CSV line 17: a2 is 39.6061 voxels off the plane of a1, b, c
  CSV line 25: expected 9 or 12 numbers, got 5
  CSV line 26: not a number: could not convert string to float: 'a'
Average projection time: 0.65 ms per plane
```

Observations:
1. The three rectangle planes show the familiar sagittal, axial and coronal views of the
   head; the `z = 64.5` section is identical, voxel for voxel, to the native slice
   `M[:, :, 65]` (64.5 is a tie and our rounding rounds .5 up).
2. The rotating triangle shows a smooth sweep through the head; brightness is consistent
   between frames because the gray scale comes from the whole volume.
3. Every invalid row produced an error frame **in its place in the sequence**, with the
   reason written on it, and did not affect the frames before or after it.
4. Line 8 is a nice example of why EPS matters: apex at x = 128 instead of the true
   middle 127.5 makes the edges differ by 0.45 voxels, which is rejected.

## Performance (500³ volume, `benchmark.py`)
| Run | Projections | Time | FPS | ms / projection |
|---|---|---|---|---|
| 1 | 300 | 0.976 s | 307 | 3.25 |
| 2 | 300 | 1.018 s | 295 | 3.39 |
| 3 | 300 | 0.997 s | 301 | 3.32 |

Images were about 450 × 504 pixels. **≈300 FPS**: well above the 30 FPS requirement and
the 100 FPS target. For comparison, the literal Python loop (the reference used in the
tests) takes 0.8 s per frame (≈1 FPS) – the vectorized design is ~240× faster and gives
the same image.

## Limitations
* Coordinates are voxel indices; MRHead's voxels are 1.3 mm along one axis, so the
  `y` and `x` sections look slightly flattened (SRS §7.1).
* Closest-voxel sampling gives "blocky" edges on oblique planes; this is what the
  lecturer asked for (Q&A 4).
