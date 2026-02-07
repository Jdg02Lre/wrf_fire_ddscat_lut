"""CLI entrypoint for WRF-Fire DDSCAT LUT skeleton."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wrf_fire_ddscat_lut",
        description="WRF-Fire + DDSCAT LUT postprocess skeleton.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--wrfout", required=True, type=Path, help="Path to wrfout file.")
        p.add_argument("--lut", required=True, type=Path, help="Path to DDSCAT LUT NetCDF.")
        p.add_argument("--output-dir", type=Path, default=Path("./output"), help="Output directory.")
        p.add_argument("--wavelength-nm", type=float, default=532.0, help="Laser wavelength.")
        p.add_argument("--time-start", type=str, default=None, help="Start time YYYY-MM-DD_HH:MM:SS")
        p.add_argument("--time-end", type=str, default=None, help="End time YYYY-MM-DD_HH:MM:SS")
        p.add_argument("--max-times", type=int, default=0, help="Limit selected time steps; 0 means all.")
        p.add_argument("--log-level", type=str, default="INFO", help="DEBUG/INFO/WARN/ERROR")

    p_check = sub.add_parser("check-inputs", help="Validate WRF and LUT structure.")
    add_common(p_check)

    p_run = sub.add_parser("run", help="Run optics postprocess.")
    add_common(p_run)
    p_run.add_argument("--dry-run", action="store_true", help="List outputs without writing files.")
    return parser


def _parse_cli_time_arg(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d_%H:%M:%S")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        from .pipeline import RunConfig, check_inputs, run
    except ModuleNotFoundError as exc:
        if exc.name in {"xarray", "numpy", "netCDF4"}:
            print(
                "Missing Python dependency. Install requirements first:\n"
                "  pip install -r /home/jyx/wrf-chem/wrf_fire_ddscat_lut/requirements.txt"
            )
            return 1
        raise
    cfg = RunConfig(
        wrfout=args.wrfout,
        lut_file=args.lut,
        output_dir=args.output_dir,
        wavelength_nm=args.wavelength_nm,
        start_time=_parse_cli_time_arg(args.time_start),
        end_time=_parse_cli_time_arg(args.time_end),
        max_times=args.max_times,
        dry_run=getattr(args, "dry_run", False),
    )

    if args.command == "check-inputs":
        check_inputs(cfg)
        print("Input checks passed.")
        return 0

    if args.command == "run":
        written = run(cfg)
        if cfg.dry_run:
            print("Dry run completed.")
        else:
            print(f"Run completed. Files written: {len(written)}")
            for path in written:
                print(path)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
