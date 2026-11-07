"""NRRD reading and CSV parsing (SRS FR-1, FR-5)."""

import gzip

import numpy as np
import pytest

from projection import (NrrdFormatError, PlaneCsvError, read_nrrd, read_plane_csv,
                        write_nrrd)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32, np.int16])
@pytest.mark.parametrize("encoding", ["raw", "gzip"])
def test_nrrd_round_trip(tmp_path, dtype, encoding):
    x, y, z = np.indices((7, 5, 3))
    data = (x + 10 * y + 100 * z).astype(dtype)
    path = tmp_path / "v.nrrd"
    write_nrrd(path, data, encoding)
    volume = read_nrrd(path)
    assert volume.shape == (7, 5, 3)
    assert volume.dtype == dtype
    np.testing.assert_array_equal(volume.data, data)
    assert volume.data[6, 4, 2] == 6 + 40 + 200   # M[x][y][z]


def test_nrrd_big_endian(tmp_path):
    data = np.arange(24, dtype=">u2").reshape((4, 3, 2), order="F")
    header = b"NRRD0004\ntype: ushort\ndimension: 3\nsizes: 4 3 2\nendian: big\nencoding: gzip\n\n"
    (tmp_path / "b.nrrd").write_bytes(header + gzip.compress(data.tobytes(order="F")))
    np.testing.assert_array_equal(read_nrrd(tmp_path / "b.nrrd").data, data.astype(np.uint16))


@pytest.mark.parametrize("content, message", [
    (b"hello", "magic"),
    (b"NRRD0004\ntype: uchar\ndimension: 2\nsizes: 2 2\n\n" + bytes(4), "dimension"),
    (b"NRRD0004\ntype: complex\ndimension: 3\nsizes: 1 1 1\n\n" + bytes(1), "type"),
    (b"NRRD0004\ntype: uchar\ndimension: 3\nsizes: 2 2 2\nencoding: raw\n\n" + bytes(3), "shorter"),
    (b"NRRD0004\ntype: uchar\ndimension: 3\nsizes: 2 2 2\nencoding: bzip2\n\n" + bytes(8), "encoding"),
])
def test_nrrd_bad_files(tmp_path, content, message):
    path = tmp_path / "bad.nrrd"
    path.write_bytes(content)
    with pytest.raises(NrrdFormatError, match=message):
        read_nrrd(path)


def test_csv_mixed_valid_and_invalid_rows(tmp_path):
    path = tmp_path / "p.csv"
    path.write_text(
        "ax,ay,az,bx,by,bz,cx,cy,cz\n"              # header
        "# a comment\n"
        "0,0,0,10,-5,0,10,5,0\n"                    # valid triangle
        "\n"
        "0,0,0,10,0,0,0,11,0\n"                     # edges not equal
        "1,2,3\n"                                   # too few values
        "0,0,0,5,0,0,0,5,0,5,5,0\n"                 # valid trapezoid
        "x,0,0,10,-5,0,10,5,0\n"                    # not a number
    )
    rows = read_plane_csv(path)
    assert [r.is_valid for r in rows] == [True, False, False, True, False]
    assert [r.line for r in rows] == [3, 5, 6, 7, 8]
    assert "not equal" in rows[1].error


def test_csv_missing_or_empty(tmp_path):
    with pytest.raises(PlaneCsvError):
        read_plane_csv(tmp_path / "nope.csv")
    (tmp_path / "empty.csv").write_text("# only a comment\n")
    with pytest.raises(PlaneCsvError):
        read_plane_csv(tmp_path / "empty.csv")
