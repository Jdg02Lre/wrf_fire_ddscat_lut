# WRF-Fire + DDSCAT-LUT Execution Checklist

Language versions:
- English: `EXEC_CHECKLIST_EN.md`
- 中文: `EXEC_CHECKLIST.md`
- README (EN): `README.md`
- README (中文): `README_zh-CN.md`

## 0. Purpose

This checklist is for running the minimal postprocess coupling workflow to generate `LR/LDR`.
Execution scope is fixed to:

1. 1-hour minimal case first.
2. Then extend to the full 2-day window.

## 1. Environment Checks

1. Load environment:

```bash
source /home/jyx/wrf-chem/env/setup_wrf_wps_env_ifort.sh
ulimit -s unlimited
```

2. Check machine resources:

```bash
nproc
free -h
```

3. Check core tools:

```bash
command -v ncdump
command -v ncatted
command -v ncks
```

## 2. Input File Checks

1. WRF output file exists:

```bash
ls -lh /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00
```

2. Required `wrfout` variables exist:

```bash
ncdump -h /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 | \
rg 'T\(|P\(|PB\(|QVAPOR\(|so4_a01|bc_a04|num_a01|num_a04|XLAT|XLONG'
```

3. DDSCAT LUT exists and is readable:

```bash
ls -lh /home/jyx/wrf-chem/data/ddscat_lut/
ncdump -h /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc | \
rg 'wavelength_nm|rh_percent|reff_um|m_real|m_imag|shape_class|Cext_m2|Cback_par_m2|Cback_perp_m2'
```

## 3. 1-Hour Minimal Run Steps

Fixed time window:

1. Start: `2020-07-01 00:00:00`
2. End: `2020-07-01 01:00:00`

Execution steps:

1. Read `wrfout` and select the target hour.
2. Compute `Tk` and `rho_dry`, and perform unit conversion.
3. Build bin-wise `reff`, `m_real`, `m_imag`, `shape_class`.
4. Interpolate LUT to obtain `Cext/Cback_par/Cback_perp`.
5. Compute `alpha_ext/beta_par/beta_perp/LR/LDR`.
6. Write output to:
   - `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc`

## 4. Numerical and Physical Checks

1. Output structure check:

```bash
ncdump -h /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc
```

2. Non-empty value checks:

```bash
ncdump -v LR /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc | sed -n '1,80p'
ncdump -v LDR /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc | sed -n '1,80p'
```

3. Suggested physical ranges:

1. `alpha_ext >= 0`
2. `beta_par >= 0`
3. `beta_perp >= 0`
4. `LR > 0` and no widespread extreme outliers
5. `0 <= LDR <= 1.5` (empirical upper guard for anomaly detection)

## 5. Two-Day Extension

Time window:

1. `2020-07-01 00:00:00` to `2020-07-02 23:00:00`

Execution rules:

1. Process hourly and write one output file per hour.
2. Record clipping counters (`clip_*_count`) and guards (`lr_guard_count`, `ldr_guard_count`) each hour.
3. Emit progress logs at least every 6 hours.

## 6. Troubleshooting Table

1. Error `missing variable ...`
   - Action: verify `wrfout` variable naming for `chem_opt=7`.

2. Error `LUT dimension missing ...`
   - Action: verify LUT dimensions and variable names.

3. Large amount of NaN values
   - Action: inspect guard triggers for `beta_total` and `beta_par`.
   - Action: inspect LUT coverage and clipping rates.

4. Memory pressure or slow runtime
   - Action: reduce parallelism and process by time/level.
   - Action: chunk spatial dimensions.

## 7. Acceptance Criteria

1. 1-hour case:
   - Target output file generated, variables complete, `LR/LDR` valid ratio acceptable.

2. 2-day case:
   - Full period completes without fatal interruption.
   - Interpolation out-of-range ratios are explainable.

3. Traceability:
   - Output contains attributes: `method`, `wavelength_nm`, `lut_version`, `generated_utc`.

## 8. Run Record Template

Append one record per run:

1. Run time:
2. Input `wrfout`:
3. Input LUT:
4. Output file:
5. Clip counters:
6. Guard counters:
7. Notes on anomalies:

