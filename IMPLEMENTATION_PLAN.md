# WRF-Fire + DDSCAT-LUT 后处理耦合实施方案

语言版本:
- 中文: `IMPLEMENTATION_PLAN.md`
- English: `IMPLEMENTATION_PLAN_EN.md`
- README (EN): `README.md`
- README (中文): `README_zh-CN.md`

## 1. 目标与成功标准

目标是建立一条稳定的后处理链路:

1. 输入 `WRF-Fire/WRF-Chem` 的 `wrfout`。
2. 基于 `DDSCAT` 预计算 `LUT` 做插值。
3. 输出 `extinction`、`backscatter`、`polarized backscatter`、`LR`、`LDR`。

成功标准:

1. 1 小时最小样例可产出结果文件，变量齐全且数值有限。
2. 两天时段可连续处理完成，不中断。
3. 输出可直接用于你们组的后续光学分析流程。

## 2. 范围与边界

在范围内:

1. 后处理耦合，不修改 WRF 核心 Fortran。
2. 使用 LUT 替代逐格点实时 DDSCAT 计算。
3. 优先支持当前 case: `chem_opt=7 (CBMZ_MOSAIC_4BIN)`。

不在范围内:

1. 本阶段不做在线辐射反馈耦合。
2. 本阶段不做 GPU 并行加速。
3. 本阶段不改动 `WRF/run/namelist.input` 化学机制设置。

## 3. 目录与产物约定

项目目录:

1. `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/` (本专题目录)

后续运行产物约定:

1. 输入: `/home/jyx/wrf-chem/WRF/run/wrfout_d01_*`
2. LUT: 建议放在 `/home/jyx/wrf-chem/data/ddscat_lut/`
3. 输出: 建议放在 `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/`
4. 日志: 建议放在 `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/logs/`

输出文件命名:

1. `optics_lut_product_d01_YYYY-MM-DD_HH:MM:SS.nc`

## 4. 接口定义

### 4.1 WRF 输入接口

已在当前 `wrfout` 中确认的核心变量:

1. 坐标时间: `Times`, `XLAT`, `XLONG`
2. 热力状态: `T`, `P`, `PB`, `QVAPOR`
3. 近地面辅助: `T2`, `PSFC`, `U10`, `V10`, `PBLH`
4. MOSAIC 4-bin 质量变量:
   - `so4_a01..a04`, `no3_a01..a04`, `cl_a01..a04`, `nh4_a01..a04`
   - `na_a01..a04`, `oin_a01..a04`, `oc_a01..a04`, `bc_a01..a04`
   - `water_a01..a04`, `hysw_a01..a04`
5. MOSAIC 4-bin 数浓度变量:
   - `num_a01..a04` (units: `/kg-dryair`)

### 4.2 DDSCAT LUT 接口

推荐 LUT 维度:

1. `wavelength_nm`
2. `rh_percent`
3. `reff_um`
4. `m_real`
5. `m_imag`
6. `shape_class`

每个 LUT 单元的最小输出:

1. `Cext_m2`
2. `Cback_par_m2`
3. `Cback_perp_m2`

LUT 文件格式默认:

1. `NetCDF4` (首选，便于与 wrfout 一致处理)

## 5. 计算规范

### 5.1 热力量和密度

固定常数:

1. `Rd = 287.05 J/(kg*K)`
2. `Cp = 1004.0 J/(kg*K)`
3. `P0 = 100000.0 Pa`

公式:

1. `P_full = P + PB`
2. `theta = T + 300.0`
3. `Tk = theta * (P_full / P0)^(Rd/Cp)`
4. `Tv = Tk * (1.0 + 0.61*QVAPOR)`
5. `rho_moist = P_full / (Rd*Tv)`
6. `rho_dry = rho_moist / (1.0 + QVAPOR)`

单位换算:

1. `ug/kg-dryair -> ug/m3` 使用 `conc_ugm3 = mixing_ugkg * rho_dry`
2. `/kg-dryair -> /m3` 使用 `N_m3 = num_kg * rho_dry`

### 5.2 分箱代表粒径默认值

默认使用 MOSAIC 4-bin 代表有效半径 `reff_um`:

1. `a01 = 0.039`
2. `a02 = 0.156`
3. `a03 = 0.625`
4. `a04 = 2.500`

说明:

1. 本阶段固定半径用于最小可运行版本。
2. 后续可替换为动态 `reff` 参数化。

### 5.3 复折射率混合默认规则

规则:

1. 采用体积分数线性混合复折射率。
2. 各组分体积分数由 `mass / density` 归一化得到。

默认组分密度 (kg/m3):

1. `so4=1770`
2. `no3=1720`
3. `nh4=1750`
4. `cl=2000`
5. `na=2160`
6. `oin=2600`
7. `oc=1500`
8. `bc=1800`
9. `water=1000`

默认形状分类:

1. 若 `oin / total_dry_mass >= 0.20` -> `shape_class = smoke_ash_mix`
2. 否则 -> `shape_class = smoke`

### 5.4 LUT 插值规则

1. 连续维 (`rh_percent`, `reff_um`, `m_real`, `m_imag`) 用线性插值。
2. 波长维默认固定 `532 nm`，若多波长则按最近邻选择。
3. `shape_class` 为离散选择，不插值。
4. 超出 LUT 范围时采用截断策略并记录计数器:
   - `clip_rh_count`
   - `clip_reff_count`
   - `clip_mreal_count`
   - `clip_mimag_count`

### 5.5 光学产品计算

对每个网格点和垂直层:

1. `alpha_ext = sum_b( N_b * Cext_b )`
2. `beta_par = sum_b( N_b * Cback_par_b )`
3. `beta_perp = sum_b( N_b * Cback_perp_b )`
4. `beta_total = beta_par + beta_perp`
5. `LR = alpha_ext / beta_total`
6. `LDR = beta_perp / beta_par`

数值保护:

1. 当 `beta_total <= 1e-20` 时 `LR = NaN`，并计数 `lr_guard_count`。
2. 当 `beta_par <= 1e-20` 时 `LDR = NaN`，并计数 `ldr_guard_count`。

## 6. 输出数据规范

输出 NetCDF 维度:

1. `Time`
2. `bottom_top`
3. `south_north`
4. `west_east`

输出变量:

1. `alpha_ext` (m-1)
2. `beta_par` (m-1 sr-1)
3. `beta_perp` (m-1 sr-1)
4. `beta_total` (m-1 sr-1)
5. `LR` (sr)
6. `LDR` (1)
7. 质量控制计数器 (标量或按 Time)

全局属性:

1. `source_case = wrfchem_20200701_20200702_d01`
2. `method = wrfout_to_ddscat_lut_postprocess_v1`
3. `wavelength_nm = 532`
4. `lut_version = <required>`
5. `generated_utc = <required>`

## 7. 执行阶段定义

阶段 1: 输入检查

1. `wrfout` 文件存在且时间轴连续。
2. 核心变量全部存在。
3. LUT 文件可读且包含必需维度。

阶段 2: 状态量派生

1. 计算 `Tk`, `rho_dry`。
2. 转换 `ug/kg-dryair` 到 `ug/m3`。
3. 计算体积分数、混合折射率、形状类别。

阶段 3: LUT 插值与光学量计算

1. 分时次、分层处理，避免一次性占满内存。
2. 写入中间日志与裁剪计数。
3. 产出 `alpha_ext/beta/LR/LDR`。

阶段 4: 质量控制

1. 变量单位和范围检查。
2. NaN 占比检查。
3. 随机网格点抽样核验公式闭合。

## 8. 失败模式与处理策略

1. 缺变量: 立即失败，输出缺失字段列表。
2. LUT 维度不全: 立即失败，输出期望维度与实际维度差异。
3. 插值越界: 不失败，执行截断并输出统计。
4. 输出写盘失败: 保留临时日志并返回非 0 退出码。

## 9. 资源与性能约束

1. 先按单时次循环处理，不将全时段全层一次性载入。
2. 默认单进程实现，避免对现有机器造成额外内存冲击。
3. 需要并行时优先按 Time 维分块并行。

## 10. 版本与里程碑

里程碑 M1 (当前优先):

1. 完成 1 小时样例 (`2020-07-01 00:00:00 -> 01:00:00`)。
2. 输出文件可被 `ncdump -h` 正常读取。
3. `LR/LDR` 数值与物理范围基本合理。

里程碑 M2:

1. 扩展到两天全时段。
2. 加入观测对比接口。
3. 固化报告模板。

## 11. 关键默认值与假设

1. 默认波长为 `532 nm`。
2. 默认 shape 仅两类: `smoke`, `smoke_ash_mix`。
3. 默认以当前 `chem_opt=7` 的 MOSAIC 4-bin 变量命名为准。
4. 默认先实现后处理，不改变 WRF 主程序。
