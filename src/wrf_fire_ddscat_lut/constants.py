"""Constants and defaults for the optics skeleton."""

from __future__ import annotations

RD = 287.05
CP = 1004.0
P0 = 100000.0

MOSAIC_BINS = ("a01", "a02", "a03", "a04")

# Representative effective radius (um), default placeholders for 4-bin setup.
REFF_UM = {
    "a01": 0.039,
    "a02": 0.156,
    "a03": 0.625,
    "a04": 2.500,
}

# Default refractive index placeholders.
DEFAULT_M_REAL = 1.53
DEFAULT_M_IMAG = 0.01

# Minimal fields we expect from wrfout for this workflow.
REQUIRED_WRF_VARS = (
    "Times",
    "XLAT",
    "XLONG",
    "T",
    "P",
    "PB",
    "QVAPOR",
)

