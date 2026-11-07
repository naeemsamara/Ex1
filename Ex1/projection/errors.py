"""Exceptions raised by the projection package."""


class InvalidPlaneError(ValueError):
    """The 3 or 4 points do not describe a valid plane (see docs/SRS.md, FR-2)."""


class NrrdFormatError(ValueError):
    """The input file is not a NRRD file this reader supports."""


class PlaneCsvError(ValueError):
    """The CSV file itself cannot be read (missing file, empty file)."""
