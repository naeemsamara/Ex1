"""Minimal NRRD reader/writer (3D volumes only).

Only the subset of the NRRD format needed for this project is supported:
an attached header, `dimension: 3`, `raw` or `gzip` encoding, and the
8/16/32-bit integer types (plus float/double, which some files use).
Format reference: http://teem.sourceforge.net/nrrd/format.html

Why not the `pynrrd` package?  It works fine too, but this reader keeps the
project dependency-light and makes the file format part of the tested code.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np

from .errors import NrrdFormatError
from .volume import Volume

# NRRD type names -> numpy dtype (without byte order).
_TYPES = {
    "uchar": "u1", "unsigned char": "u1", "uint8": "u1", "uint8_t": "u1",
    "signed char": "i1", "int8": "i1", "int8_t": "i1",
    "short": "i2", "short int": "i2", "signed short": "i2", "signed short int": "i2",
    "int16": "i2", "int16_t": "i2",
    "ushort": "u2", "unsigned short": "u2", "unsigned short int": "u2",
    "uint16": "u2", "uint16_t": "u2",
    "int": "i4", "signed int": "i4", "int32": "i4", "int32_t": "i4",
    "uint": "u4", "unsigned int": "u4", "uint32": "u4", "uint32_t": "u4",
    "float": "f4", "double": "f8",
}

_DTYPE_TO_NRRD = {"u1": "uint8", "u2": "uint16", "u4": "uint32",
                  "i1": "int8", "i2": "int16", "i4": "int32",
                  "f4": "float", "f8": "double"}


def _parse_header(raw: bytes) -> tuple[dict[str, str], int]:
    """Return (fields, offset of the data block)."""
    if not raw.startswith(b"NRRD000"):
        raise NrrdFormatError("missing NRRD magic line")
    end = raw.find(b"\n\n")
    if end < 0:
        raise NrrdFormatError("header is not terminated by an empty line")
    fields: dict[str, str] = {}
    for line in raw[:end].decode("ascii", errors="replace").splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("#") or ":=" in line:
            continue  # comments and key/value pairs are ignored
        key, sep, value = line.partition(":")
        if not sep:
            raise NrrdFormatError(f"bad header line: {line!r}")
        fields[key.strip().lower()] = value.strip()
    return fields, end + 2


def read_nrrd(path: str | Path) -> Volume:
    """Read a 3D NRRD file. The result is indexed as volume.data[x, y, z]."""
    raw = Path(path).read_bytes()
    fields, offset = _parse_header(raw)

    if "data file" in fields or "datafile" in fields:
        raise NrrdFormatError("detached data files are not supported")
    if fields.get("dimension") != "3":
        raise NrrdFormatError(f"expected dimension 3, got {fields.get('dimension')}")
    type_name = fields.get("type", "").lower()
    if type_name not in _TYPES:
        raise NrrdFormatError(f"unsupported type {type_name!r}")
    try:
        sizes = [int(s) for s in fields["sizes"].split()]
    except (KeyError, ValueError) as exc:
        raise NrrdFormatError("missing or bad 'sizes' field") from exc
    if len(sizes) != 3 or min(sizes) < 1:
        raise NrrdFormatError(f"bad sizes {sizes}")

    endian = "<" if fields.get("endian", "little") == "little" else ">"
    dtype = np.dtype(endian + _TYPES[type_name])

    encoding = fields.get("encoding", "raw").lower()
    payload = raw[offset:]
    if encoding in ("gzip", "gz"):
        payload = gzip.decompress(payload)
    elif encoding != "raw":
        raise NrrdFormatError(f"unsupported encoding {encoding!r}")

    count = sizes[0] * sizes[1] * sizes[2]
    if len(payload) < count * dtype.itemsize:
        raise NrrdFormatError("data block is shorter than sizes * type")
    flat = np.frombuffer(payload, dtype=dtype, count=count)
    # NRRD stores the first axis fastest -> Fortran order gives data[x, y, z].
    data = flat.reshape(sizes, order="F").astype(dtype.newbyteorder("="))
    return Volume(np.ascontiguousarray(data))


def write_nrrd(path: str | Path, data: np.ndarray, encoding: str = "gzip") -> None:
    """Write a 3D array indexed [x, y, z] as an attached-header NRRD file."""
    if data.ndim != 3:
        raise ValueError("only 3D arrays are supported")
    kind = data.dtype.str[1:]
    if kind not in _DTYPE_TO_NRRD:
        raise ValueError(f"unsupported dtype {data.dtype}")
    body = np.asarray(data, dtype="<" + kind).tobytes(order="F")
    if encoding == "gzip":
        body = gzip.compress(body, compresslevel=1)
    elif encoding != "raw":
        raise ValueError("encoding must be 'gzip' or 'raw'")
    header = (
        "NRRD0004\n"
        f"type: {_DTYPE_TO_NRRD[kind]}\n"
        "dimension: 3\n"
        f"sizes: {data.shape[0]} {data.shape[1]} {data.shape[2]}\n"
        "endian: little\n"
        f"encoding: {encoding}\n\n"
    )
    Path(path).write_bytes(header.encode("ascii") + body)
