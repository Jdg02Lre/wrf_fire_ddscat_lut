# WRF-Fire + DDSCAT-LUT 执行清单

语言版本:
- 中文: `EXEC_CHECKLIST.md`
- English: `EXEC_CHECKLIST_EN.md`
- README (EN): `README.md`
- README (中文): `README_zh-CN.md`

## 0. 说明

本清单用于执行 `后处理耦合` 最小可运行流程，目标是生成 `LR/LDR` 产品。  
执行范围固定为先跑 1 小时样例，再扩展到 2 天。

## 1. 前置环境检查

1. 加载环境:

```bash
source /home/jyx/wrf-chem/env/setup_wrf_wps_env_ifort.sh
ulimit -s unlimited
```

2. 机器资源确认:

```bash
nproc
free -h
```

3. 核心工具确认:

```bash
command -v ncdump
command -v ncatted
command -v ncks
```

## 2. 输入文件检查

1. WRF 输出文件存在:

```bash
ls -lh /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00
```

2. `wrfout` 核心变量存在:

```bash
ncdump -h /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 | \
rg 'T\(|P\(|PB\(|QVAPOR\(|so4_a01|bc_a04|num_a01|num_a04|XLAT|XLONG'
```

3. DDSCAT LUT 文件存在并可读:

```bash
ls -lh /home/jyx/wrf-chem/data/ddscat_lut/
ncdump -h /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc | \
rg 'wavelength_nm|rh_percent|reff_um|m_real|m_imag|shape_class|Cext_m2|Cback_par_m2|Cback_perp_m2'
```

## 3. 1 小时样例执行步骤

时间窗固定:

1. 开始: `2020-07-01 00:00:00`
2. 结束: `2020-07-01 01:00:00`

执行步骤:

1. 读取 `wrfout` 并提取该时间窗数据。
2. 计算 `Tk`, `rho_dry`，完成质量与数浓度单位转换。
3. 构建每个 bin 的 `reff`, `m_real`, `m_imag`, `shape_class`。
4. 查表插值获取 `Cext/Cback_par/Cback_perp`。
5. 计算 `alpha_ext/beta_par/beta_perp/LR/LDR`。
6. 输出 NetCDF 到:
   - `/home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc`

## 4. 数值与物理检查

1. 输出文件结构检查:

```bash
ncdump -h /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc
```

2. 非空检查:

```bash
ncdump -v LR /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc | sed -n '1,80p'
ncdump -v LDR /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output/optics_lut_product_d01_2020-07-01_00:00:00.nc | sed -n '1,80p'
```

3. 物理范围建议检查:

1. `alpha_ext >= 0`
2. `beta_par >= 0`
3. `beta_perp >= 0`
4. `LR > 0` 且无大面积异常极值
5. `0 <= LDR <= 1.5` (经验上限，用于异常筛查)

## 5. 两天扩展执行

时间窗:

1. `2020-07-01 00:00:00` 到 `2020-07-02 23:00:00`

扩展规则:

1. 按小时循环处理，单时次写一个输出文件。
2. 每小时记录裁剪计数 (`clip_*_count`) 和保护计数 (`lr_guard_count`, `ldr_guard_count`)。
3. 每 6 小时输出一次进度日志。

## 6. 故障排查表

1. 报错 `missing variable ...`
   - 处理: 核对 `wrfout` 变量名是否与 `chem_opt=7` 对应。

2. 报错 `LUT dimension missing ...`
   - 处理: 核对 LUT 维度和变量命名是否符合实施方案。

3. 出现大量 NaN
   - 处理: 检查 `beta_total` 和 `beta_par` 保护阈值触发率。
   - 处理: 检查 LUT 覆盖范围是否过窄导致大量截断。

4. 内存不足或速度过慢
   - 处理: 降低并行度，改为逐时次逐层处理。
   - 处理: 对空间维做分块计算。

## 7. 验收标准

1. 1 小时样例:
   - 生成目标文件，变量齐全，`LR/LDR` 有效值占比可接受。

2. 两天样例:
   - 全时段完成，无致命中断。
   - 日志中插值越界比例在可解释范围内。

3. 文档可追溯:
   - 输出文件含 `method`, `wavelength_nm`, `lut_version`, `generated_utc` 属性。

## 8. 执行记录模板

记录建议每次追加一条:

1. 执行时间:
2. 输入 `wrfout`:
3. 输入 LUT:
4. 输出文件:
5. clip 计数:
6. guard 计数:
7. 异常说明:
