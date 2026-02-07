# WRF-Fire + DDSCAT LUT Python Skeleton

Language:
- English: `README.md`
- 中文: `README_zh-CN.md`
- Implementation Plan (EN): `IMPLEMENTATION_PLAN_EN.md`
- Implementation Plan (中文): `IMPLEMENTATION_PLAN.md`
- Execution Checklist (EN): `EXEC_CHECKLIST_EN.md`
- Execution Checklist (中文): `EXEC_CHECKLIST.md`

This directory contains a runnable Python skeleton for the workflow:

1. Read `wrfout` from WRF/WRF-Chem.
2. Read DDSCAT lookup-table (LUT).
3. Compute placeholder optical products (`alpha_ext`, `beta_*`, `LR`, `LDR`) with clear extension points.
4. Write NetCDF outputs.

This is a scaffold for implementation, not the final scientific production code.

## Layout

- `src/wrf_fire_ddscat_lut/cli.py`: command line entry.
- `src/wrf_fire_ddscat_lut/pipeline.py`: main orchestration.
- `src/wrf_fire_ddscat_lut/io_wrf.py`: WRF I/O and checks.
- `src/wrf_fire_ddscat_lut/lut.py`: DDSCAT LUT loading and lookup.
- `src/wrf_fire_ddscat_lut/optics.py`: optical product computation skeleton.
- `requirements.txt`: minimal Python dependencies.

## Quick Start

```bash
cd /home/jyx/wrf-chem/wrf_fire_ddscat_lut
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Check inputs:

```bash
wrf-fire-ddscat-lut check-inputs \
  --wrfout /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 \
  --lut /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc
```

Dry run:

```bash
wrf-fire-ddscat-lut run \
  --wrfout /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 \
  --lut /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc \
  --output-dir /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output \
  --dry-run \
  --max-times 1
```

Actual run:

```bash
wrf-fire-ddscat-lut run \
  --wrfout /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 \
  --lut /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc \
  --output-dir /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output \
  --max-times 1
```

## Notes

- Current `RH`, `m_real`, `m_imag`, and shape mapping are default placeholders.
- Replace placeholder logic in `optics.py` with your lab-specific DDSCAT data processing rules.
- Output naming follows `optics_lut_product_d01_<time>.nc`.
