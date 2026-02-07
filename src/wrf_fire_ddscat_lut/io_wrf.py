"""I/O helpers for WRF files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import xarray as xr

from .constants import MOSAIC_BINS, REQUIRED_WRF_VARS


@dataclass(frozen=True)
class WrfCheckResult:
    missing: list[str]
    available: list[str]
    n_times: int


def open_wrf(path: str | Path) -> xr.Dataset:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"WRF file not found: {file_path}")
    return xr.open_dataset(file_path, decode_times=False)


def get_required_vars() -> list[str]:
    req = list(REQUIRED_WRF_VARS)
    for bin_name in MOSAIC_BINS:
        req.append(f"num_{bin_name}")
        req.append(f"oin_{bin_name}")
    return req


def check_wrf_variables(ds: xr.Dataset) -> WrfCheckResult:
    required = get_required_vars()
    available = sorted(list(ds.variables))
    missing = [name for name in required if name not in ds.variables]
    n_times = int(ds.sizes.get("Time", 0))
    return WrfCheckResult(missing=missing, available=available, n_times=n_times)


def parse_wrf_time_string(ds: xr.Dataset, time_index: int) -> str:
    raw = ds["Times"].isel(Time=time_index).values
    chars = []
    for item in raw.tolist():
        if isinstance(item, (bytes, bytearray)):
            chars.append(item.decode("utf-8"))
        else:
            chars.append(str(item))
    return "".join(chars).strip()


def parse_cli_time_arg(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d_%H:%M:%S")


def select_time_indices(
    ds: xr.Dataset,
    start: datetime | None,
    end: datetime | None,
    max_times: int,
) -> list[int]:
    indices = list(range(int(ds.sizes.get("Time", 0))))
    if not indices:
        return []

    if start is None and end is None and max_times <= 0:
        return indices

    selected: list[int] = []
    for idx in indices:
        ts = parse_wrf_time_string(ds, idx)
        cur = datetime.strptime(ts, "%Y-%m-%d_%H:%M:%S")
        if start and cur < start:
            continue
        if end and cur > end:
            continue
        selected.append(idx)

    if max_times > 0:
        selected = selected[:max_times]
    return selected

