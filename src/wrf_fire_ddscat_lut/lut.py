"""DDSCAT LUT loading and lookup skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import xarray as xr


@dataclass(frozen=True)
class LutCheckResult:
    missing_dims: list[str]
    missing_vars: list[str]


class DdsCatLut:
    REQUIRED_DIMS = ("wavelength_nm", "rh_percent", "reff_um", "m_real", "m_imag")
    REQUIRED_VARS = ("Cext_m2", "Cback_par_m2", "Cback_perp_m2")

    def __init__(self, ds: xr.Dataset):
        self.ds = ds

    @classmethod
    def from_file(cls, path: str | Path) -> "DdsCatLut":
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"LUT file not found: {file_path}")
        ds = xr.open_dataset(file_path, decode_times=False)
        return cls(ds=ds)

    def check(self) -> LutCheckResult:
        missing_dims = [d for d in self.REQUIRED_DIMS if d not in self.ds.dims]
        missing_vars = [v for v in self.REQUIRED_VARS if v not in self.ds.variables]
        return LutCheckResult(missing_dims=missing_dims, missing_vars=missing_vars)

    def _select_shape_dataset(self, shape_class: str) -> xr.Dataset:
        if "shape_class" not in self.ds.dims and "shape_class" not in self.ds.coords:
            return self.ds

        if "shape_class" in self.ds.coords:
            coord = self.ds["shape_class"]
        else:
            coord = self.ds.coords["shape_class"]

        if np.issubdtype(coord.dtype, np.number):
            target = 0 if shape_class == "smoke" else 1
            return self.ds.sel(shape_class=target, method="nearest")

        values = [str(v.item() if hasattr(v, "item") else v) for v in coord.values]
        target = shape_class if shape_class in values else values[0]
        return self.ds.sel(shape_class=target)

    def lookup_scalar(
        self,
        wavelength_nm: float,
        rh_percent: float,
        reff_um: float,
        m_real: float,
        m_imag: float,
        shape_class: str,
    ) -> tuple[float, float, float]:
        ds_shape = self._select_shape_dataset(shape_class)
        point = ds_shape.sel(
            wavelength_nm=wavelength_nm,
            rh_percent=rh_percent,
            reff_um=reff_um,
            m_real=m_real,
            m_imag=m_imag,
            method="nearest",
        )
        cext = float(point["Cext_m2"].values)
        cpar = float(point["Cback_par_m2"].values)
        cperp = float(point["Cback_perp_m2"].values)
        return cext, cpar, cperp

