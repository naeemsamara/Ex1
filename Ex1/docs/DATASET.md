# Data set of NRRD files

| File | Size (x,y,z) | Type | Encoding | Where it comes from | Used for |
|---|---|---|---|---|---|
| `MRHead.nrrd` | 256 × 256 × 130 | int16 | gzip | 3D Slicer sample data (the file recommended in the assignment) | demo, experiment |
| `gradient_u8_raw.nrrd` | 10 × 9 × 2 | uint8 | raw | `scripts/make_dataset.py` | reader test, 8-bit |
| `gradient_u16_gzip.nrrd` | 20 × 15 × 12 | uint16 | gzip | `scripts/make_dataset.py` | reader test, 16-bit |
| `gradient_u32_gzip.nrrd` | 30 × 20 × 10 | uint32 | gzip | `scripts/make_dataset.py` | reader test, 32-bit |
| `sphere_128_u8.nrrd` | 128³ | uint8 | gzip | `scripts/make_dataset.py` | visual check (any cut through the center is a disc) |
| (in memory) | 500³ | uint8 | – | `benchmark.py` | performance (125 MB, not stored) |

**Why synthetic volumes?** Their content is known, so the right answer is known.
In a gradient volume each voxel's value is `x + 10*y + 100*z`, so the value of a pixel
tells exactly which voxel it came from.

## Getting the files
```bash
python scripts/make_dataset.py           # creates the synthetic files in data/
```
MRHead (6.6 MB) is in `data/`. If it is missing, download it from the 3D Slicer test data:
<https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/cc211f0dfd9a05ca3841ce1141b292898b2dd2d3f08286affadf823a7e58df93>
and save it as `data/MRHead.nrrd`.
