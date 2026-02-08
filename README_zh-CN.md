# WRF-Fire + DDSCAT LUT Python 骨架

[English](README.md) | [**中文**](README_zh-CN.md)

关联文档:
- [Implementation Plan (EN)](IMPLEMENTATION_PLAN_EN.md) | [实施方案 (中文)](IMPLEMENTATION_PLAN.md)
- [Execution Checklist (EN)](EXEC_CHECKLIST_EN.md) | [执行清单 (中文)](EXEC_CHECKLIST.md)

本目录包含一套可运行的 Python 骨架，用于以下流程:

1. 读取 WRF/WRF-Chem 输出 `wrfout`。
2. 读取 DDSCAT 查找表 (LUT)。
3. 计算占位版光学产品 (`alpha_ext`, `beta_*`, `LR`, `LDR`)，并预留扩展接口。
4. 输出 NetCDF 文件。

这是工程骨架，不是最终科研生产版本。

## 目录结构

- `src/wrf_fire_ddscat_lut/cli.py`: 命令行入口。
- `src/wrf_fire_ddscat_lut/pipeline.py`: 主流程编排。
- `src/wrf_fire_ddscat_lut/io_wrf.py`: WRF 文件读取与检查。
- `src/wrf_fire_ddscat_lut/lut.py`: DDSCAT LUT 读取与查表。
- `src/wrf_fire_ddscat_lut/optics.py`: 光学计算骨架。
- `requirements.txt`: 最小 Python 依赖。

## 快速开始

```bash
cd /home/jyx/wrf-chem/wrf_fire_ddscat_lut
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

检查输入:

```bash
wrf-fire-ddscat-lut check-inputs \
  --wrfout /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 \
  --lut /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc
```

干跑 (不写输出文件):

```bash
wrf-fire-ddscat-lut run \
  --wrfout /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 \
  --lut /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc \
  --output-dir /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output \
  --dry-run \
  --max-times 1
```

正式运行:

```bash
wrf-fire-ddscat-lut run \
  --wrfout /home/jyx/wrf-chem/WRF/run/wrfout_d01_2020-07-01_00:00:00 \
  --lut /home/jyx/wrf-chem/data/ddscat_lut/<your_lut_file>.nc \
  --output-dir /home/jyx/wrf-chem/wrf_fire_ddscat_lut/output \
  --max-times 1
```

## 说明

- 当前 `RH`、`m_real`、`m_imag` 和形状映射使用默认占位逻辑。
- 请把 `optics.py` 中占位实现替换为你们组 DDSCAT 数据处理规则。
- 输出命名规则为 `optics_lut_product_d01_<time>.nc`。
