"""Reading the list of planes from the CSV file.

Format (docs/SRS.md, section 4): one plane per row, 9 or 12 numbers.
    ax,ay,az,bx,by,bz,cx,cy,cz                       (triangle a, b, c)
    a1x,a1y,a1z,a2x,a2y,a2z,bx,by,bz,cx,cy,cz        (trapezoid a1, a2, b, c)
Empty lines and lines starting with '#' are ignored. An optional first line
of column names (no numbers in it) is treated as a header.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .errors import InvalidPlaneError, PlaneCsvError
from .plane import Plane


@dataclass(frozen=True)
class PlaneRow:
    """One CSV row: either a valid plane or the reason it is invalid."""
    line: int
    plane: Plane | None
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.plane is not None


def _is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def read_plane_csv(path: str | Path) -> list[PlaneRow]:
    """Parse every row. A bad row never stops the others (Q&A 3)."""
    path = Path(path)
    if not path.is_file():
        raise PlaneCsvError(f"CSV file not found: {path}")
    rows: list[PlaneRow] = []
    first_data_row = True
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for line_no, cells in enumerate(csv.reader(handle), start=1):
            cells = [c.strip() for c in cells if c.strip()]
            if not cells or cells[0].startswith("#"):
                continue
            if first_data_row and not any(_is_number(c) for c in cells):
                first_data_row = False
                continue  # header row
            first_data_row = False
            try:
                values = [float(c) for c in cells]
                rows.append(PlaneRow(line_no, Plane.from_values(values)))
            except ValueError as exc:  # also covers InvalidPlaneError
                reason = str(exc) if isinstance(exc, InvalidPlaneError) else f"not a number: {exc}"
                rows.append(PlaneRow(line_no, None, reason))
    if not rows:
        raise PlaneCsvError(f"no plane rows found in {path}")
    return rows
