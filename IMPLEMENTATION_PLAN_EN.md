# WRF-Fire + DDSCAT-LUT Postprocess Coupling Implementation Plan

[**English**](IMPLEMENTATION_PLAN_EN.md) | [中文](IMPLEMENTATION_PLAN.md)

Related docs:
- [README (EN)](README.md) | [README (中文)](README_zh-CN.md)
- [Execution Checklist (EN)](EXEC_CHECKLIST_EN.md) | [执行清单 (中文)](EXEC_CHECKLIST.md)

## 1. Goal and Success Criteria

The goal is to build a stable postprocessing pipeline:

1. Input `wrfout` from `WRF-Fire/WRF-Chem`.
2. Interpolate from precomputed `DDSCAT` LUT.
3. Output `extinction`, `backscatter`, `polarized backscatter`, `LR`, and `LDR`.

Success criteria:

1. A 1-hour minimal case runs end-to-end with finite outputs.
2. A 2-day window runs continuously without interruption.
3. Outputs are directly usable by your lab optical analysis workflow.

## 2. Scope and Boundaries

In scope:

1. Postprocess coupling only, no WRF core Fortran changes.
2. LUT lookup instead of per-grid online DDSCAT execution.
3. First target is your current case: `chem_opt=7 (CBMZ_MOSAIC_4BIN)`.

Out of scope:

1. Online radiative feedback coupling in this phase.
2. GPU acceleration in this phase.
3. Changing current chemistry mechanism settings in `WRF/run/namelist.input`.

## 3. Directory and Artifacts

Project directory:

1. `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/`

Artifact conventions:

1. Input: `/home/jyx/wrf-chem/WRF/run/wrfout_d01_*`
2. LUT: `/home/jyx/wrf-chem/data/ddscat_lut/`
3. Output: `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/`
4. Logs: `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/logs/`

Output naming:

1. `optics_lut_product_d01_YYYY-MM-DD_HH:MM:SS.nc`

## 4. Interface Definition

### 4.1 WRF Input Interface

Confirmed core variables in current `wrfout`:

1. Coordinates/time: `Times`, `XLAT`, `XLONG`
2. Thermodynamics: `T`, `P`, `PB`, `QVAPOR`
3. Near-surface helpers: `T2`, `PSFC`, `U10`, `V10`, `PBLH`
4. MOSAIC 4-bin mass variables:
   - `so4_a01..a04`, `no3_a01..a04`, `cl_a01..a04`, `nh4_a01..a04`
   - `na_a01..a04`, `oin_a01..a04`, `oc_a01..a04`, `bc_a01..a04`
   - `water_a01..a04`, `hysw_a01..a04`
5. MOSAIC 4-bin number variables:
   - `num_a01..a04` (units: `/kg-dryair`)

### 4.2 DDSCAT LUT Interface

Recommended LUT dimensions:

1. `wavelength_nm`
2. `rh_percent`
3. `reff_um`
4. `m_real`
5. `m_imag`
6. `shape_class`

Minimum variables per LUT point:

1. `Cext_m2`
2. `Cback_par_m2`
3. `Cback_perp_m2`

Preferred LUT format:

1. `NetCDF4`

## 5. Computation Rules

### 5.1 Thermodynamics and Density

Constants:

1. `Rd = 287.05 J/(kg*K)`
2. `Cp = 1004.0 J/(kg*K)`
3. `P0 = 100000.0 Pa`

Formulas:

1. `P_full = P + PB`
2. `theta = T + 300.0`
3. `Tk = theta * (P_full / P0)^(Rd/Cp)`
4. `Tv = Tk * (1.0 + 0.61*QVAPOR)`
5. `rho_moist = P_full / (Rd*Tv)`
6. `rho_dry = rho_moist / (1.0 + QVAPOR)`

Unit conversions:

1. `ug/kg-dryair -> ug/m3`: `conc_ugm3 = mixing_ugkg * rho_dry`
2. `/kg-dryair -> /m3`: `N_m3 = num_kg * rho_dry`

### 5.2 Default Representative Bin Radius

For MOSAIC 4-bin minimal implementation:

1. `a01 = 0.039 um`
2. `a02 = 0.156 um`
3. `a03 = 0.625 um`
4. `a04 = 2.500 um`

Notes:

1. Fixed radius is only for initial runnable version.
2. Can be replaced with dynamic `reff` parameterization later.

### 5.3 Default Complex Refractive Index Mixing

Rules:

1. Use volume-fraction linear mixing for complex refractive index.
2. Volume fraction from normalized `(mass / density)` by component.

Default component densities (kg/m3):

1. `so4=1770`
2. `no3=1720`
3. `nh4=1750`
4. `cl=2000`
5. `na=2160`
6. `oin=2600`
7. `oc=1500`
8. `bc=1800`
9. `water=1000`

Default shape classification:

1. If `oin / total_dry_mass >= 0.20` -> `shape_class = smoke_ash_mix`
2. Else -> `shape_class = smoke`

### 5.4 LUT Interpolation Rules

1. Linear interpolation for continuous dimensions (`rh_percent`, `reff_um`, `m_real`, `m_imag`).
2. `wavelength_nm` default fixed at `532 nm`; nearest selection if multiple wavelengths exist.
3. `shape_class` is discrete selection, no interpolation.
4. Out-of-range values are clipped with counters:
   - `clip_rh_count`
   - `clip_reff_count`
   - `clip_mreal_count`
   - `clip_mimag_count`

### 5.5 Optical Product Equations

For each grid point and vertical level:

1. `alpha_ext = sum_b( N_b * Cext_b )`
2. `beta_par = sum_b( N_b * Cback_par_b )`
3. `beta_perp = sum_b( N_b * Cback_perp_b )`
4. `beta_total = beta_par + beta_perp`
5. `LR = alpha_ext / beta_total`
6. `LDR = beta_perp / beta_par`

Numerical guards:

1. If `beta_total <= 1e-20`, set `LR = NaN` and count `lr_guard_count`.
2. If `beta_par <= 1e-20`, set `LDR = NaN` and count `ldr_guard_count`.

## 6. Output Data Specification

NetCDF dimensions:

1. `Time`
2. `bottom_top`
3. `south_north`
4. `west_east`

Output variables:

1. `alpha_ext` (m-1)
2. `beta_par` (m-1 sr-1)
3. `beta_perp` (m-1 sr-1)
4. `beta_total` (m-1 sr-1)
5. `LR` (sr)
6. `LDR` (1)
7. QC counters (scalar or by `Time`)

Global attributes:

1. `source_case = wrfchem_20200701_20200702_d01`
2. `method = wrfout_to_ddscat_lut_postprocess_v1`
3. `wavelength_nm = 532`
4. `lut_version = <required>`
5. `generated_utc = <required>`

## 7. Execution Phases

Phase 1: Input checks

1. `wrfout` exists and has continuous time axis.
2. All core variables are available.
3. LUT is readable and has required dimensions.

Phase 2: State derivation

1. Compute `Tk` and `rho_dry`.
2. Convert `ug/kg-dryair` to `ug/m3`.
3. Compute volume fractions, mixed refractive index, and shape class.

Phase 3: LUT interpolation and optics

1. Process by time and level to keep memory controlled.
2. Log interpolation clipping counters.
3. Produce `alpha_ext`, `beta_*`, `LR`, `LDR`.

Phase 4: QC

1. Unit and range checks.
2. NaN ratio checks.
3. Random point formula closure checks.

## 8. Failure Modes and Handling

1. Missing variables: fail fast and print missing list.
2. Missing LUT dimensions: fail fast and print expected vs actual.
3. LUT out-of-range: continue with clipping and log stats.
4. Output write failure: keep logs and return non-zero exit code.

## 9. Resource and Performance Constraints

1. Start with per-time-step loop, avoid loading full 4D period at once.
2. Single-process default to reduce memory pressure on current machine.
3. If parallelism is needed, split by `Time` chunks first.

## 10. Versions and Milestones

Milestone M1 (current priority):

1. Complete 1-hour case (`2020-07-01 00:00:00 -> 01:00:00`).
2. Output readable by `ncdump -h`.
3. `LR/LDR` numerically and physically reasonable.

Milestone M2:

1. Extend to full 2-day period.
2. Add observation comparison interface.
3. Finalize report template.

## 11. Key Defaults and Assumptions

1. Default wavelength: `532 nm`.
2. Default shape classes: `smoke`, `smoke_ash_mix`.
3. Default variable naming follows current `chem_opt=7` MOSAIC 4-bin outputs.
4. This phase remains postprocess-only without modifying WRF core.
