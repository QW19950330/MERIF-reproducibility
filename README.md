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

## Figure gallery / 图片预览

All 16 images below are the exact PNG files embedded in
`Manuscript_R1_Clean.docx`, in manuscript order. Editable PPTX sources are also
retained for Figures 1-4. Rebuilt outputs from the frozen V6 plotting package
can differ in final layout and are kept separately for reproducibility.

<table>
  <tr>
    <td align="center"><strong>Figure 1 — MERIF architecture</strong><br><img src="reference/submitted_main_figures/Figure_01.png" alt="Figure 1, MERIF architecture" width="100%"></td>
    <td align="center"><strong>Figure 2 — TSQR workflow</strong><br><img src="reference/submitted_main_figures/Figure_02.png" alt="Figure 2, TSQR workflow" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>Figure 3 — RCQR workflow</strong><br><img src="reference/submitted_main_figures/Figure_03.png" alt="Figure 3, RCQR workflow" width="100%"></td>
    <td align="center"><strong>Figure 4 — XRM workflow</strong><br><img src="reference/submitted_main_figures/Figure_04.png" alt="Figure 4, XRM workflow" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>Figure 5 — Market structure</strong><br><img src="reference/submitted_main_figures/Figure_05.png" alt="Figure 5, market structure" width="100%"></td>
    <td align="center"><strong>Figure 6 — Central forecasting</strong><br><img src="reference/submitted_main_figures/Figure_06.png" alt="Figure 6, central forecasting" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>Figure 7 — Stage-wise attribution</strong><br><img src="reference/submitted_main_figures/Figure_07.png" alt="Figure 7, stage-wise attribution" width="100%"></td>
    <td align="center"><strong>Figure 8 — RCQR calibration</strong><br><img src="reference/submitted_main_figures/Figure_08.png" alt="Figure 8, RCQR calibration" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>Figure 9 — S2-DA information</strong><br><img src="reference/submitted_main_figures/Figure_09.png" alt="Figure 9, S2-DA information" width="100%"></td>
    <td align="center"><strong>Figure 10 — Calendar slices</strong><br><img src="reference/submitted_main_figures/Figure_10.png" alt="Figure 10, calendar slices" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>Figure 11 — Summer trajectories</strong><br><img src="reference/submitted_main_figures/Figure_11.png" alt="Figure 11, summer trajectories" width="100%"></td>
    <td align="center"><strong>Figure 12 — Negative-price regimes</strong><br><img src="reference/submitted_main_figures/Figure_12.png" alt="Figure 12, negative-price regimes" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>Figure 13 — Upper-tail error</strong><br><img src="reference/submitted_main_figures/Figure_13.png" alt="Figure 13, upper-tail error" width="100%"></td>
    <td align="center"><strong>Figure 14 — XRM ranking</strong><br><img src="reference/submitted_main_figures/Figure_14.png" alt="Figure 14, XRM ranking" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>Figure 15 — Robustness and computation</strong><br><img src="reference/submitted_main_figures/Figure_15.png" alt="Figure 15, robustness and computation" width="100%"></td>
    <td align="center"><strong>Figure 16 — Integrated synthesis</strong><br><img src="reference/submitted_main_figures/Figure_16.png" alt="Figure 16, integrated synthesis" width="100%"></td>
  </tr>
</table>

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
