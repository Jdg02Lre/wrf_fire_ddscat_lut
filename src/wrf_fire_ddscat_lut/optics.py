"""Optics computation skeleton."""

from __future__ import annotations

import numpy as np
import xarray as xr

from .constants import (
    CP,
    DEFAULT_M_IMAG,
    DEFAULT_M_REAL,
    MOSAIC_BINS,
    P0,
    RD,
    REFF_UM,
)
from .lut import DdsCatLut


def compute_rho_dry(ds_t: xr.Dataset) -> np.ndarray:
    """Compute dry air density from WRF thermodynamic fields."""
    t_pert = ds_t["T"].values
    p_pert = ds_t["P"].values
    p_base = ds_t["PB"].values
    qv = ds_t["QVAPOR"].values

    p_full = p_pert + p_base
    theta = t_pert + 300.0
    tk = theta * np.power(p_full / P0, RD / CP)
    tv = tk * (1.0 + 0.61 * qv)
    rho_moist = p_full / (RD * tv)
    rho_dry = rho_moist / (1.0 + qv)
    return rho_dry


def _decide_shape_class(ds_t: xr.Dataset) -> str:
    dry_oin = 0.0
    dry_total = 0.0
    for bin_name in MOSAIC_BINS:
        dry_oin += float(np.nanmean(ds_t[f"oin_{bin_name}"].values))
        dry_total += float(np.nanmean(ds_t[f"num_{bin_name}"].values))
    if dry_total <= 0.0:
        return "smoke"
    ratio = dry_oin / max(dry_total, 1e-20)
    return "smoke_ash_mix" if ratio >= 0.20 else "smoke"


def compute_optics_for_time(
    ds_t: xr.Dataset,
    lut: DdsCatLut,
    wavelength_nm: float,
) -> xr.Dataset:
    """
    Compute optics for one time step.

    This is a skeleton:
    - Uses fixed placeholder RH and refractive index.
    - Uses bin-wise scalar lookup in LUT.
    """
    rho_dry = compute_rho_dry(ds_t)
    shape_class = _decide_shape_class(ds_t)

    rh_percent = 50.0
    m_real = DEFAULT_M_REAL
    m_imag = DEFAULT_M_IMAG

    alpha_ext = np.zeros_like(rho_dry, dtype=np.float64)
    beta_par = np.zeros_like(rho_dry, dtype=np.float64)
    beta_perp = np.zeros_like(rho_dry, dtype=np.float64)

    for bin_name in MOSAIC_BINS:
        num_per_kg_dry = ds_t[f"num_{bin_name}"].values
        n_m3 = num_per_kg_dry * rho_dry

        cext, cpar, cperp = lut.lookup_scalar(
            wavelength_nm=wavelength_nm,
            rh_percent=rh_percent,
            reff_um=REFF_UM[bin_name],
            m_real=m_real,
            m_imag=m_imag,
            shape_class=shape_class,
        )

        alpha_ext += n_m3 * cext
        beta_par += n_m3 * cpar
        beta_perp += n_m3 * cperp

    beta_total = beta_par + beta_perp
    lr = np.where(beta_total > 1e-20, alpha_ext / beta_total, np.nan)
    ldr = np.where(beta_par > 1e-20, beta_perp / beta_par, np.nan)

    out = xr.Dataset(
        data_vars={
            "alpha_ext": (("bottom_top", "south_north", "west_east"), alpha_ext),
            "beta_par": (("bottom_top", "south_north", "west_east"), beta_par),
            "beta_perp": (("bottom_top", "south_north", "west_east"), beta_perp),
            "beta_total": (("bottom_top", "south_north", "west_east"), beta_total),
            "LR": (("bottom_top", "south_north", "west_east"), lr),
            "LDR": (("bottom_top", "south_north", "west_east"), ldr),
        },
        coords={
            "bottom_top": ds_t["bottom_top"],
            "south_north": ds_t["south_north"],
            "west_east": ds_t["west_east"],
            "XLAT": ds_t["XLAT"],
            "XLONG": ds_t["XLONG"],
        },
    )
    out["alpha_ext"].attrs["units"] = "m-1"
    out["beta_par"].attrs["units"] = "m-1 sr-1"
    out["beta_perp"].attrs["units"] = "m-1 sr-1"
    out["beta_total"].attrs["units"] = "m-1 sr-1"
    out["LR"].attrs["units"] = "sr"
    out["LDR"].attrs["units"] = "1"
    return out

