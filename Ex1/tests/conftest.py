import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projection import Volume  # noqa: E402


@pytest.fixture
def gradient_volume() -> Volume:
    """value = x + 10*y + 100*z, so the value of a voxel reveals its coordinates."""
    x, y, z = np.indices((10, 10, 10))
    return Volume((x + 10 * y + 100 * z).astype(np.uint16))
