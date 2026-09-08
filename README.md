# MERIF reproducibility and publication figures

This repository contains the plot-ready reproducibility package for:

> MERIF: A Market-informed Electricity-price Risk and Interval Forecasting Framework for Renewable-rich Power Markets

It is aligned to the clean R1 manuscript returned to the editorial office on
7 September 2026. The repository preserves the authoritative five-market
result tables, frozen figure-source data, the latest complete executable
Matplotlib renderer, editable workflow diagrams, and the figures embedded in
the submitted manuscript as visual references.

## Scope

- Assembles all 16 main-text figures: Figures 1-4 use the submitted reference
  renders (with editable PPTX sources retained), while Figures 5-16 are rebuilt
  from frozen machine-readable plot data.
- Exports data-driven figures as 600-dpi PNG, PDF, and editable-text SVG.
- Preserves the final submitted PNGs for visual comparison.
- Does not refit forecasting models or recompute inferential quantities; the
  repository starts from the frozen, audited result tables used for plotting.
- Does not include the manuscript DOCX, reviewer correspondence, credentials,
  virtual environments, caches, or historical duplicate packages.

## Quick start

Python 3.11 or 3.12 is recommended. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts\build_submission_figures.py
.\.venv\Scripts\python scripts\verify_outputs.py
```

Generated files are written to `outputs/submission_figures` and intentionally
ignored by Git. To rebuild one figure:

```powershell
.\.venv\Scripts\python scripts\build_submission_figures.py --figure 9
```

## Repository layout

| Path | Purpose |
|---|---|
| `01_authoritative_results` | Frozen result summaries, lineage, and result locks |
| `02_figure_source_tables` | Audited source tables used by the figure system |
| `08_audit_and_manifest` | Packaging QA and source hashes |
| `09_authoritative_tables` | Main and supplementary paper tables |
| `10_authoritative_predictions_index` | Hash index of retained prediction artifacts |
| `FINAL_FIGURES4PAPERS_EDITORIAL_V6` | Latest complete renderer, materialized plot tables, reference exports, and QA |
| `reference/editable_diagrams` | Editable PowerPoint sources for Figures 1-4 |
| `reference/submitted_main_figures` | PNGs embedded in the submitted clean manuscript |
| `scripts` | Stable build and verification entry points |

See [FIGURE_MAP.md](FIGURE_MAP.md) for the final manuscript numbering.

## Reproducibility notes

- Scientific values are read from frozen CSV tables; the plotting entry point
  performs no model fitting or parameter selection.
- The original workflow used Times New Roman, a white background, explicit
  panel labels, and multi-format vector/raster export through `pubfig==0.3.0`.
- For the closest visual match, run on Windows with Times New Roman installed.
- Source-data and publisher/provider licensing terms remain applicable. No
  additional license grant is implied by this private research repository.

## 中文说明

本仓库对应 2026 年 9 月 7 日返还编辑部的 R1 清稿，包含五市场权威结果表、
最终绘图数据、可执行绘图脚本、图 1-4 的可编辑 PPTX，以及论文中实际嵌入的
16 张主文图作为校验基准。运行上面的两条脚本即可生成并检查全部主文图。
