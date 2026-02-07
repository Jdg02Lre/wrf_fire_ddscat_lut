"""Pipeline orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .io_wrf import check_wrf_variables, open_wrf, parse_wrf_time_string, select_time_indices
from .lut import DdsCatLut
from .optics import compute_optics_for_time

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunConfig:
    wrfout: Path
    lut_file: Path
    output_dir: Path
    wavelength_nm: float
    start_time: datetime | None
    end_time: datetime | None
    max_times: int
    dry_run: bool


def _safe_time_for_filename(time_str: str) -> str:
    return time_str.replace(":", "-")


def check_inputs(cfg: RunConfig) -> None:
    ds = open_wrf(cfg.wrfout)
    wrf_result = check_wrf_variables(ds)
    if wrf_result.missing:
        raise RuntimeError(f"WRF missing required variables: {wrf_result.missing}")
    LOG.info("WRF input check passed, Time dimension=%s", wrf_result.n_times)

    lut = DdsCatLut.from_file(cfg.lut_file)
    lut_result = lut.check()
    if lut_result.missing_dims:
        raise RuntimeError(f"LUT missing required dims: {lut_result.missing_dims}")
    if lut_result.missing_vars:
        raise RuntimeError(f"LUT missing required vars: {lut_result.missing_vars}")
    LOG.info("LUT check passed")


def run(cfg: RunConfig) -> list[Path]:
    ds = open_wrf(cfg.wrfout)
    lut = DdsCatLut.from_file(cfg.lut_file)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    time_indices = select_time_indices(
        ds=ds,
        start=cfg.start_time,
        end=cfg.end_time,
        max_times=cfg.max_times,
    )
    if not time_indices:
        raise RuntimeError("No time steps selected from WRF dataset.")

    written: list[Path] = []
    for idx in time_indices:
        time_str = parse_wrf_time_string(ds, idx)
        out_name = f"optics_lut_product_d01_{_safe_time_for_filename(time_str)}.nc"
        out_path = cfg.output_dir / out_name

        LOG.info("Processing Time index=%s (%s)", idx, time_str)
        if cfg.dry_run:
            LOG.info("[dry-run] would write: %s", out_path)
            continue

        ds_t = ds.isel(Time=idx)
        out_ds = compute_optics_for_time(ds_t=ds_t, lut=lut, wavelength_nm=cfg.wavelength_nm)
        out_ds = out_ds.expand_dims(Time=[idx])
        out_ds.attrs["source_case"] = "wrfchem_20200701_20200702_d01"
        out_ds.attrs["method"] = "wrfout_to_ddscat_lut_postprocess_v1_skeleton"
        out_ds.attrs["wavelength_nm"] = cfg.wavelength_nm
        out_ds.attrs["lut_version"] = "set-in-real-run"
        out_ds.attrs["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        out_ds.to_netcdf(out_path)
        written.append(out_path)
        LOG.info("Wrote %s", out_path)

    return written

