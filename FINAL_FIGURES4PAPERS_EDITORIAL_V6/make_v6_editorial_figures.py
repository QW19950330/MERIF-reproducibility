#!/usr/bin/env python3
"""Render the MERIF V6 editorial figure system from frozen results only.

The module contains no fitting, model selection, threshold selection, or
inferential recomputation.  All transformations are deterministic display
expressions of frozen result tables, predictions, or frozen bootstrap summaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd
from PIL import Image
import pubfig


OUT = Path(__file__).resolve().parent
PKG = OUT.parent
SRC = PKG / "02_figure_source_tables"
TAB = PKG / "09_authoritative_tables"


MARKETS = ["DE-LU", "DK1", "BE", "ES", "FR"]
MC = {"DE-LU": "#1F5A94", "DK1": "#3C8D94", "BE": "#C58B1A", "ES": "#B6534F", "FR": "#7E5A86"}
MM = {"DE-LU": "o", "DK1": "s", "BE": "^", "ES": "D", "FR": "P"}
BLACK = "#1F1F1F"
GREY = "#6E6E6E"
LIGHT = "#D2D2D2"
PALE_BLUE = "#DDEBF2"
RAW = "#FFFFFF"
RCQR = "#1F5A94"
GOOD = "#27856F"
BAD = "#B54B4A"
METHOD_COLORS = {
    "Persistence": "#9A9A9A", "Direct QR": "#6E93B4", "RQR": "#4B87A5",
    "SQR": "#2B718F", "TSQR": "#103E66",
}
IQR = (
    pd.read_csv(SRC / "Fig7_RCQR_Calibration_source.csv")
    .query("source_table == 'rcqr_main'")
    .set_index("market")
    .training_IQR
    .reindex(MARKETS)
)
COMMON_N = int(pd.read_csv(TAB / "Table_Main_2_Five_Market_Central.csv")["N"].min())
TIMES_SPEC = replace(pubfig.get_figure_spec("nature"), name="nature_times_merif_v6", font_family="Times New Roman")


def configure() -> None:
    font_manager.findfont("Times New Roman", fallback_to_default=False)
    theme = pubfig.get_theme("nature")
    pubfig.set_default_theme(replace(theme, name="nature_times_merif_v6", font_family=["Times New Roman", "Times", "serif"]))
    plt.rcParams.update({
        "font.family": "Times New Roman", "font.size": 7.5,
        "axes.titlesize": 8.2, "axes.labelsize": 7.5,
        "xtick.labelsize": 6.7, "ytick.labelsize": 6.7,
        "legend.fontsize": 6.4, "axes.linewidth": 0.78,
        "axes.edgecolor": BLACK, "axes.spines.top": True,
        "axes.spines.right": True, "xtick.top": False, "ytick.right": False,
        "xtick.direction": "out", "ytick.direction": "out",
        "legend.frameon": True, "legend.edgecolor": "black",
        "legend.facecolor": "white", "legend.framealpha": 1,
        "legend.fancybox": False, "figure.facecolor": "white",
        "axes.facecolor": "white", "savefig.facecolor": "white",
        "svg.fonttype": "none", "pdf.fonttype": 42,
        "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
    })


def finish(ax: plt.Axes, *, zero_x: bool = False, zero_y: bool = False, grid: str | None = None) -> None:
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.78)
        spine.set_color(BLACK)
    ax.tick_params(top=False, right=False, labeltop=False, labelright=False, length=2.5, width=0.7)
    if zero_x:
        ax.axvline(0, color="#8D8D8D", lw=0.65, ls="--", zorder=0)
    if zero_y:
        ax.axhline(0, color="#8D8D8D", lw=0.65, ls="--", zorder=0)
    if grid == "x":
        ax.grid(axis="x", color="#E5E5E5", lw=0.45, zorder=0)
    if grid == "y":
        ax.grid(axis="y", color="#E5E5E5", lw=0.45, zorder=0)


def panel_label(ax: plt.Axes, text: str, x: float = -0.12, y: float = 1.04) -> None:
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=8.8, fontweight="bold")


def boxed_legend(ax: plt.Axes, *args, **kwargs):
    leg = ax.legend(*args, **kwargs)
    if leg is not None:
        f = leg.get_frame()
        f.set_visible(True); f.set_facecolor("white"); f.set_edgecolor("black")
        f.set_linewidth(0.72); f.set_alpha(1.0); f.set_boxstyle("square", pad=0.22)
    return leg


def source_rel(path: Path) -> str:
    return path.resolve().relative_to(WORK.resolve()).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(panel: str, market: str, metric: str, value: float | int | str | None,
           source: Path, source_key: str, transformation: str,
           *, setting: str = "S1", mask: str = "COMMON_MASK",
           support: float | int | None = None, status: str = "descriptive", **extra) -> dict:
    row = {
        "panel": panel, "market": market, "metric": metric, "setting": setting,
        "mask": mask, "value": value, "source_file": source_rel(source),
        "source_row_key": source_key, "display_transformation": transformation,
        "support_N": support, "inferential_status": status,
    }
    row.update(extra)
    return row


def long_rows(frame: pd.DataFrame, source: Path, *, panel: str, metrics: Iterable[str],
              market_col: str = "market", setting: str = "S1", mask: str = "COMMON_MASK",
              transform: str = "identity", status: str = "descriptive") -> list[dict]:
    rows: list[dict] = []
    for idx, r in frame.iterrows():
        for metric in metrics:
            rows.append(record(panel, str(r[market_col]), metric, r[metric], source, str(idx), transform,
                               setting=setting, mask=mask, support=r.get("N", np.nan), status=status))
    return rows


def write_table(code: str, data: pd.DataFrame) -> None:
    folder = OUT / code
    folder.mkdir(parents=True, exist_ok=True)
    data.to_csv(folder / f"{code.upper()}_SOURCE_TABLE.csv", index=False, encoding="utf-8-sig")
    lineage_cols = ["panel", "market", "metric", "setting", "mask", "value", "source_file",
                    "source_row_key", "display_transformation", "support_N", "inferential_status"]
    data.reindex(columns=lineage_cols).to_csv(folder / f"{code.upper()}_VALUE_LINEAGE.csv", index=False, encoding="utf-8-sig")


def read_table(code: str) -> pd.DataFrame:
    return pd.read_csv(OUT / code / f"{code.upper()}_SOURCE_TABLE.csv")


def create_wrapper(code: str) -> None:
    wrapper = OUT / code / f"{code.upper()}_PLOTTING_SCRIPT.py"
    wrapper.write_text(
        "from pathlib import Path\nimport sys\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        "from make_v6_editorial_figures import render_one\n"
        f"render_one('{code}', stage='final')\n", encoding="utf-8")


def caption_path(code: str) -> Path:
    return OUT / code / f"{code.upper()}_CAPTION.md"


def qa_path(code: str) -> Path:
    return OUT / code / f"{code.upper()}_QA.md"


def combined_stem(code: str) -> str:
    return code.upper()


def export_panel(fig: plt.Figure, axes: list[plt.Axes], path: Path, fmt: str, dpi: int) -> None:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_tightbbox(renderer) for ax in axes]
    bbox = Bbox.union(boxes).expanded(1.04, 1.08).transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(path, format=fmt, dpi=dpi, bbox_inches=bbox, facecolor="white")


def export_figure(code: str, fig: plt.Figure, panel_groups: list[list[plt.Axes]], stage: str, height_mm: float) -> None:
    folder = OUT / code
    for ax in fig.axes:
        finish(ax)
    fig.align_labels()
    if stage == "layout":
        fig.savefig(folder / f"{code.upper()}_LAYOUT_v0.png", dpi=120, bbox_inches="tight", facecolor="white")
    else:
        pubfig.batch_export(fig, folder / combined_stem(code), formats=("svg", "pdf", "png"),
                            spec=TIMES_SPEC, width="double", height_mm=height_mm, dpi=600,
                            transparent=False, trim=True, svg_fonttype="none")
        pdir = folder / "panels"
        pdir.mkdir(exist_ok=True)
        for idx, axes in enumerate(panel_groups):
            letter = chr(ord("a") + idx)
            for fmt, dpi in (("png", 600), ("pdf", 600), ("svg", 600)):
                export_panel(fig, axes, pdir / f"{code.upper()}_panel_{letter}.{fmt}", fmt, dpi)
    plt.close(fig)


def _source_manifest(data: pd.DataFrame) -> list[dict]:
    rows = []
    for rel in sorted(data.source_file.dropna().astype(str).unique()):
        path = WORK / rel
        rows.append({"source_file": rel, "sha256": sha256(path), "exists": path.exists()})
    return rows


def write_caption_qa(code: str, caption: str, question: str, grammar: str, data: pd.DataFrame) -> None:
    caption_path(code).write_text(caption.strip() + "\n", encoding="utf-8")
    manifest = _source_manifest(data)
    pd.DataFrame(manifest).to_csv(OUT / code / f"{code.upper()}_SOURCE_MANIFEST.csv", index=False, encoding="utf-8-sig")
    qa_path(code).write_text(
        f"# {code.upper()} QA\n\n"
        f"- Scientific question: {question}\n"
        f"- Dominant grammar: {grammar}\n"
        f"- Frozen source files hashed: {len(manifest)}.\n"
        f"- Materialized plotted rows: {len(data):,}.\n"
        f"- Required lineage fields populated: {'PASS' if data[['panel','market','metric','source_file','source_row_key','display_transformation','inferential_status']].notna().all().all() else 'FAIL'}.\n"
        f"- COMMON_MASK/GLOBAL_COMMON contract: {'PASS' if set(data['mask'].dropna()).issubset({'COMMON_MASK','GLOBAL_COMMON','MARKET_VALID','FULL_SERIES','LOCKED_WINDOW'}) else 'FAIL'}.\n"
        "- Times New Roman, four spines, and suppressed top/right ticks: PASS by render configuration.\n"
        "- Scientific values manually embedded in plotting calls: NO; renderer reads the materialized table.\n",
        encoding="utf-8")


def central_reconstruction() -> tuple[pd.DataFrame, pd.DataFrame]:
    central = pd.read_csv(TAB / "Table_Main_2_Five_Market_Central.csv").set_index("market").reindex(MARKETS)
    attr = pd.read_csv(SRC / "Fig12_Attribution_Robustness_Cost_source.csv")
    attr = attr[attr.source_table.eq("module_attribution")]
    gain_mae = attr.pivot(index="market", columns="method", values="MAE").reindex(MARKETS)
    gain_pin = attr.pivot(index="market", columns="method", values="mean_pinball").reindex(MARKETS)

    mae = pd.DataFrame(index=MARKETS)
    mae["Persistence"] = central.Persistence_MAE
    mae["TSQR"] = central.TSQR_MAE
    mae["SQR"] = central.SQR_MAE
    mae["RQR"] = mae.SQR + gain_mae.RQR_to_SQR_gain
    mae["Direct QR"] = mae.RQR + gain_mae.Direct_to_RQR_gain
    mae = mae[["Persistence", "Direct QR", "RQR", "SQR", "TSQR"]]

    pin = pd.DataFrame(index=MARKETS)
    pin["TSQR"] = central.TSQR_mean_pinball
    inf = pd.read_csv(TAB / "Table_Main_5_Five_Market_Inference.csv")
    pfx = inf[inf.family.eq("TSQR_PINBALL")].set_index("market").reindex(MARKETS)
    pin["SQR"] = pin.TSQR - pfx.effect_method_minus_comparator
    pin["RQR"] = pin.SQR + gain_pin.RQR_to_SQR_gain
    pin["Direct QR"] = pin.RQR + gain_pin.Direct_to_RQR_gain
    pin = pin[["Direct QR", "RQR", "SQR", "TSQR"]]
    return mae.reindex(MARKETS), pin.reindex(MARKETS)


def build_fig05() -> pd.DataFrame:
    fp_path = SRC / "Fig5_Five_Market_Characteristics_source.csv"
    fp_all = pd.read_csv(fp_path)
    fp = fp_all[fp_all.source_table.eq("market_fingerprint")].set_index("market").reindex(MARKETS)
    rc_path = SRC / "Fig7_RCQR_Calibration_source.csv"
    iq = pd.read_csv(rc_path).query("source_table == 'rcqr_main'").set_index("market").training_IQR.reindex(MARKETS)
    rows: list[dict] = []
    for i, market in enumerate(MARKETS):
        path = SRC / f"Appendix_EDA_{market.replace('-', '_')}_source.csv"
        q = pd.read_csv(path)
        train = q[q.split.eq("train")].price_eur_mwh.astype(float)
        median = train.median(); tiqr = train.quantile(.75) - train.quantile(.25)
        z = (q.price_eur_mwh.astype(float) - median) / tiqr
        hist, edges = np.histogram(z.clip(-4, 10), bins=120, range=(-4, 10), density=True)
        for j, val in enumerate(hist):
            rows.append(record("a", market, "standardized_price_density", val, path, f"hist_bin:{j}",
                               "price centered by training median, divided by training IQR; fixed-bin density",
                               mask="FULL_SERIES", x=(edges[j] + edges[j + 1]) / 2, support=len(q)))
        r = fp.loc[market]
        metrics = {
            "negative_price_share_pct": r.negative_price_share * 100,
            "standard_deviation_over_full_IQR": r.standard_deviation / r.IQR,
            "rolling_7day_volatility_over_full_IQR": r.rolling_7day_volatility_mean / r.IQR,
        }
        for j, (metric, value) in enumerate(metrics.items()):
            rows.append(record("b", market, metric, value, fp_path, f"market_fingerprint:{market}",
                               "ratio or percentage from frozen exploratory fingerprint", mask="FULL_SERIES", facet=j))
        for metric, value in (("ACF_lag24h", r.daily_autocorrelation_lag24h),
                              ("ACF_lag168h", r.weekly_autocorrelation_lag168h)):
            rows.append(record("c", market, metric, value, fp_path, f"market_fingerprint:{market}", "identity", mask="FULL_SERIES"))
        rows.append(record("d", market, "P95_common_test_events", r.test_P95_event_count_common,
                           fp_path, f"market_fingerprint:{market}", "identity", support=r.test_P95_event_count_common,
                           status="descriptive-low-support" if r.test_P95_event_count_common < 10 else "descriptive",
                           threshold_over_training_IQR=r.training_P95_threshold / iq.loc[market]))
    return pd.DataFrame(rows)


def build_fig06() -> pd.DataFrame:
    central_path = TAB / "Table_Main_2_Five_Market_Central.csv"
    inf_path = TAB / "Table_Main_5_Five_Market_Inference.csv"
    attr_path = SRC / "Fig12_Attribution_Robustness_Cost_source.csv"
    mae, pin = central_reconstruction()
    central = pd.read_csv(central_path).set_index("market").reindex(MARKETS)
    inf = pd.read_csv(inf_path)
    rows: list[dict] = []
    for market in MARKETS:
        for method in ["Persistence", "Direct QR", "RQR", "SQR", "TSQR"]:
            rows.append(record("a", market, "MAE_over_training_IQR", mae.loc[market, method] / IQR.loc[market],
                               attr_path if method not in ["Persistence", "TSQR"] else central_path,
                               f"{market}:{method}", "algebraic reconstruction from frozen stage gains, then divide by training IQR",
                               support=central.loc[market, "N"], method=method))
    specs = [("b", "TSQR_MAE", "Persistence", "MAE", central.Persistence_MAE),
             ("c", "TSQR_MAE", "SQR", "MAE", central.SQR_MAE),
             ("d", "TSQR_PINBALL", "SQR", "pinball", pin["SQR"])]
    for panel, family, comp, metric_name, denom in specs:
        q = inf[inf.family.eq(family) & inf.comparator_or_metric.eq(comp)]
        for idx, r in q.iterrows():
            d = float(denom.loc[r.market])
            rows.append(record(panel, r.market, f"TSQR_improvement_vs_{comp}_{metric_name}_pct",
                               -r.effect_method_minus_comparator / d * 100, inf_path, str(idx),
                               "sign inversion and division by frozen comparator value; positive favors TSQR",
                               support=central.loc[r.market, "N"], status="168h moving-block bootstrap",
                               low=-r.ci95_high / d * 100, high=-r.ci95_low / d * 100, comparator=comp))
    return pd.DataFrame(rows)


def build_fig07() -> pd.DataFrame:
    path = SRC / "Fig12_Attribution_Robustness_Cost_source.csv"
    d = pd.read_csv(path).query("source_table == 'module_attribution'")
    labels = {"Direct_to_RQR_gain": "Direct QR→RQR", "RQR_to_SQR_gain": "RQR→SQR", "SQR_to_TSQR_gain": "SQR→TSQR"}
    rows: list[dict] = []
    for idx, r in d.iterrows():
        rows.append(record(chr(ord('a') + MARKETS.index(r.market)), r.market, "MAE_reduction_over_training_IQR",
                           r.MAE / IQR.loc[r.market], path, str(idx), "frozen stage MAE reduction divided by training IQR",
                           support=r.N, transition=labels[r.method]))
    for transition in labels.values():
        vals = [x["value"] for x in rows if x["transition"] == transition]
        for stat, value in (("median", np.median(vals)), ("q25", np.quantile(vals, .25)), ("q75", np.quantile(vals, .75))):
            rows.append(record("f", "cross-market", "MAE_reduction_over_training_IQR", value, path,
                               f"summary:{transition}:{stat}", f"cross-market {stat}", transition=transition, summary_stat=stat))
    return pd.DataFrame(rows)


def build_fig08() -> pd.DataFrame:
    path = SRC / "Fig7_RCQR_Calibration_source.csv"
    d = pd.read_csv(path).query("source_table == 'rcqr_main'").set_index("market").reindex(MARKETS)
    pairs = [("a", "PICP80", "Raw_PICP80", "RCQR_PICP80", "identity"),
             ("b", "absolute_coverage_gap", "Raw_absolute_coverage_gap", "RCQR_absolute_coverage_gap", "identity"),
             ("c", "interval_score_over_training_IQR", "Raw_IS_over_IQR", "RCQR_IS_over_IQR", "already normalized by frozen training IQR"),
             ("d", "width_over_training_IQR", "Raw_width_over_IQR", "RCQR_width_over_IQR", "already normalized by frozen training IQR")]
    rows: list[dict] = []
    for market, r in d.iterrows():
        for panel, metric, raw_col, rc_col, transform in pairs:
            for method, col in (("Raw TSQR", raw_col), ("W60 RCQR", rc_col)):
                rows.append(record(panel, market, metric, r[col], path, f"rcqr_main:{market}", transform,
                                   support=COMMON_N, method=method))
    return pd.DataFrame(rows)


def build_fig09() -> pd.DataFrame:
    path = SRC / "Fig12_Attribution_Robustness_Cost_source.csv"
    d = pd.read_csv(path).query("source_table == 'rcqr_window_sensitivity'")
    rows: list[dict] = []
    for market in MARKETS:
        q = d[d.market.eq(market)].sort_values("window_complete_days")
        first = q.iloc[0]
        rows.append(record(chr(ord('a') + MARKETS.index(market)), market, "reliability_sharpness", first.Raw_absolute_coverage_gap,
                           path, f"raw:{market}", "raw point; x=width/training IQR, y=absolute coverage gap",
                           support=first.N, method="Raw", x=first.Raw_width_over_IQR, y=first.Raw_absolute_coverage_gap,
                           interval_score_over_IQR=first.Raw_IS_over_IQR, order=0))
        for order, (_, r) in enumerate(q.iterrows(), start=1):
            rows.append(record(chr(ord('a') + MARKETS.index(market)), market, "reliability_sharpness", r.RCQR_absolute_coverage_gap,
                               path, str(r.name), "x=RCQR width/training IQR, y=absolute coverage gap",
                               support=r.N, method=f"W{int(r.window_complete_days)}", x=r.RCQR_width_over_IQR,
                               y=r.RCQR_absolute_coverage_gap, interval_score_over_IQR=r.RCQR_IS_over_IQR, order=order))
    base = pd.DataFrame(rows)
    for method in ["Raw", "W7", "W14", "W30", "W60"]:
        q = base[base.method.eq(method)]
        rows.append(record("f", "cross-market", "reliability_sharpness", q.y.median(), path, f"summary:{method}",
                           "cross-market medians with IQR", method=method, x=q.x.median(), y=q.y.median(),
                           x_q25=q.x.quantile(.25), x_q75=q.x.quantile(.75), y_q25=q.y.quantile(.25), y_q75=q.y.quantile(.75),
                           interval_score_over_IQR=q.interval_score_over_IQR.median(), order=int(q.order.iloc[0])))
    return pd.DataFrame(rows)


def build_fig10() -> pd.DataFrame:
    path = SRC / "Fig8_Information_Settings_source.csv"
    d = pd.read_csv(path).query("source_table == 'authoritative_setting_summary'")
    d = d[d.setting.isin(["S1", "S2_DA"])].copy()
    rows: list[dict] = []
    specs = [("a", "TSQR_MAE_over_S1_training_IQR", "TSQR_MAE", "divide by market S1 training IQR"),
             ("b", "raw_absolute_coverage_gap", "TSQR_absolute_coverage_gap", "identity"),
             ("c", "RCQR_interval_score_over_S1_training_IQR", "RCQR_interval_score", "divide by market S1 training IQR")]
    for market in MARKETS:
        q = d[d.market.eq(market)].set_index("setting")
        denom = IQR.loc[market]
        for panel, metric, col, transform in specs:
            for setting in ["S1", "S2_DA"]:
                value = q.loc[setting, col] / denom if "IQR" in metric else q.loc[setting, col]
                rows.append(record(panel, market, metric, value, path, f"authoritative_setting_summary:{market}:{setting}",
                                   transform, setting=setting, mask="GLOBAL_COMMON", support=q.loc[setting, "N"], method=setting))
    return pd.DataFrame(rows)


def build_fig11() -> pd.DataFrame:
    path = SRC / "Fig9_Temporal_Robustness_Trajectories_source.csv"
    d = pd.read_csv(path).query("source_table == 'temporal_slices'")
    rows: list[dict] = []
    for idx, r in d.iterrows():
        if r.slice_type == "year":
            value = (r.SQR_MAE - r.TSQR_MAE) / IQR.loc[r.market]
            metric, panel = "TSQR_improvement_over_SQR_over_training_IQR", "a"
        else:
            value = (r.Raw_IS - r.RCQR_IS) / IQR.loc[r.market]
            metric, panel = "RCQR_interval_score_reduction_over_training_IQR", "b"
        rows.append(record(panel, r.market, metric, value, path, str(idx), "sign chosen so positive favors proposed component; divide by training IQR",
                           support=r.N, slice_type=r.slice_type, slice=r.slice))
    return pd.DataFrame(rows)


def build_trajectory(window: str, code: str) -> pd.DataFrame:
    path = SRC / "Fig9_Temporal_Robustness_Trajectories_source.csv"
    d = pd.read_csv(path)
    d = d[(d.source_table.eq("locked_trajectory_predictions")) & d.trajectory_window.eq(window)].copy()
    series = [("Observed price", "price_eur_mwh"), ("TSQR median", "tsqr_q50"),
              ("Raw lower", "tsqr_q10"), ("Raw upper", "tsqr_q90"),
              ("RCQR lower", "rcqr_w60_q10"), ("RCQR upper", "rcqr_w60_q90")]
    rows: list[dict] = []
    for idx, r in d.iterrows():
        market = r.market
        panel = chr(ord('a') + MARKETS.index(market))
        for metric, col in series:
            rows.append(record(panel, market, metric, r[col], path, str(idx), "identity; exact hourly value, no smoothing",
                               mask="LOCKED_WINDOW", support=len(d[d.market.eq(market)]), timestamp_utc=r.timestamp_utc,
                               trajectory_window=window, series=metric))
    return pd.DataFrame(rows)


def build_fig13() -> pd.DataFrame:
    path = SRC / "Fig10_Conditional_Regimes_source.csv"
    d = pd.read_csv(path).query("source_table == 'negative_price_regimes'")
    rows: list[dict] = []
    for idx, r in d.iterrows():
        col = MARKETS.index(r.market)
        for method, value in (("Raw TSQR", r.Raw_PICP80), ("W60 RCQR", r.RCQR_PICP80)):
            rows.append(record(chr(ord('a') + col), r.market, "conditional_PICP80", value, path, str(idx), "identity",
                               support=r.N, status="descriptive nested regime", method=method, group=r.group, row="coverage"))
        improvement = (r.Raw_IS - r.RCQR_IS) / IQR.loc[r.market]
        rows.append(record(chr(ord('f') + col), r.market, "conditional_interval_score_reduction_over_training_IQR",
                           improvement, path, str(idx), "Raw minus RCQR interval score divided by training IQR; positive favors RCQR",
                           support=r.N, status="descriptive nested regime", method="W60 RCQR", group=r.group, row="score"))
    return pd.DataFrame(rows)


def build_fig14() -> pd.DataFrame:
    path = SRC / "Fig10_Conditional_Regimes_source.csv"
    d = pd.read_csv(path).query("source_table == 'upper_tail_escalation'")
    level = {0.90: "P90", 0.95: "P95", 0.975: "P97.5", 0.99: "P99"}
    order = {"P90": 0, "P92.5": 1, "P95": 2, "P97.5": 3, "P99": 4}
    rows: list[dict] = []
    for idx, r in d.iterrows():
        lev = level[float(r.gamma)]
        rows.append(record(chr(ord('a') + MARKETS.index(r.market)), r.market, "upper_tail_TSQR_MAE_over_training_IQR",
                           r.MAE / IQR.loc[r.market] if pd.notna(r.MAE) else np.nan, path, str(idx), "divide by training IQR",
                           support=r.test_N, status="descriptive-low-support" if r.test_N < 10 else "descriptive",
                           event_level=lev, order=order[lev]))
    base = pd.DataFrame(rows)
    for lev in ["P90", "P95", "P97.5", "P99"]:
        q = base[base.event_level.eq(lev) & base.value.notna()]
        rows.append(record("f", "cross-market", "upper_tail_TSQR_MAE_over_training_IQR", q.value.median(), path,
                           f"summary:{lev}", "cross-market median and IQR of available frozen estimates",
                           support=q.support_N.sum(), event_level=lev, order=order[lev], q25=q.value.quantile(.25), q75=q.value.quantile(.75)))
    return pd.DataFrame(rows)


def build_fig15() -> pd.DataFrame:
    path = SRC / "Fig11_XRM_Support_Monitoring_source.csv"
    inf_path = MASTER / "SUPPLEMENTARY_FIVE_MARKET" / "FIVE_MARKET_XRM_INFERENCE.csv"
    d = pd.read_csv(path).query("source_table == 'xrm_support_sensitivity' and event_level == 'P95'")
    rows: list[dict] = []
    specs = [("Prevalence", "prevalence"), ("TSQR q0.50", "q0_50_AUPRC"), ("TSQR q0.90", "q0_90_AUPRC"), ("XRM", "XRM_AUPRC")]
    for idx, r in d.iterrows():
        panel = chr(ord('a') + MARKETS.index(r.market))
        low = r.test_events < 10
        for method, col in specs:
            rows.append(record(panel, r.market, "P95_AUPRC", r[col], path, str(idx), "identity",
                               support=r.test_events, status="descriptive only" if low else "descriptive", method=method))
    inf = pd.read_csv(inf_path)
    q = inf[(inf.block_hours.eq(168)) & inf.comparator_or_metric.eq("q0.90_AUPRC")]
    for idx, r in q.iterrows():
        low = r.market in ["ES", "FR"]
        rows.append(record("f", r.market, "XRM_minus_q0.90_AUPRC", r.effect_method_minus_comparator, inf_path, str(idx), "identity; positive favors XRM",
                           support=float(d.set_index("market").loc[r.market, "test_events"]),
                           status="descriptive only" if low else "168h moving-block bootstrap",
                           low=r.ci95_low, high=r.ci95_high))
    return pd.DataFrame(rows)


def build_fig16() -> pd.DataFrame:
    path = SRC / "Fig12_Attribution_Robustness_Cost_source.csv"
    d = pd.read_csv(path)
    outage = d[d.source_table.eq("s1_feature_outages")]
    cost = d[d.source_table.eq("computational_cost")]
    rows: list[dict] = []
    for idx, r in outage.iterrows():
        rows.append(record(chr(ord('a') + MARKETS.index(r.market)), r.market, "outage_delta_MAE_over_training_IQR",
                           r.delta_MAE / IQR.loc[r.market], path, str(idx), "outage delta MAE divided by training IQR; positive is deterioration",
                           support=r.N, outage_group=r.outage_group))
    metrics = [("Forecast inference", "inference_24_products_ms_median", 1.0),
               ("XRM scoring", "XRM_24_products_ms_median", 1.0),
               ("RCQR update", "RCQR_daily_update_ms_median", 1.0),
               ("Model loading", "model_load_seconds", 1000.0)]
    for idx, r in cost.iterrows():
        for operation, col, factor in metrics:
            rows.append(record("f", r.market, "online_latency_ms", r[col] * factor, path, str(idx),
                               "identity in ms" if factor == 1 else "seconds converted to milliseconds",
                               support=r.formal_repeats_feature_inference_update, operation=operation))
    return pd.DataFrame(rows)


def build_fig17() -> pd.DataFrame:
    summary_path = SRC / "Fig13_Integrated_Portability_Synthesis_source.csv"
    xinf_path = MASTER / "SUPPLEMENTARY_FIVE_MARKET" / "FIVE_MARKET_XRM_INFERENCE.csv"
    s = pd.read_csv(summary_path).query("source_table == 'authoritative_s1_summary'").set_index("market").reindex(MARKETS)
    rows: list[dict] = []
    for market, r in s.iterrows():
        values = [
            ("a", "TSQR_vs_Persistence_relative_MAE_improvement_pct", r.TSQR_vs_Persistence_relative_MAE_improvement * 100),
            ("b", "TSQR_vs_SQR_relative_MAE_improvement_pct", r.TSQR_vs_SQR_relative_MAE_improvement * 100),
            ("c", "RCQR_absolute_coverage_gap_reduction", r.TSQR_absolute_coverage_gap - r.RCQR_absolute_coverage_gap),
            ("d", "RCQR_interval_score_reduction_over_training_IQR", (r.TSQR_interval_score - r.RCQR_interval_score) / IQR.loc[market]),
        ]
        for panel, metric, value in values:
            rows.append(record(panel, market, metric, value, summary_path, f"authoritative_s1_summary:{market}",
                               "positive sign convention; normalization recorded in metric", support=r.N))
    inf = pd.read_csv(xinf_path)
    q = inf[(inf.block_hours.eq(168)) & inf.comparator_or_metric.eq("q0.90_AUPRC")]
    p95 = s.P95_test_events
    for idx, r in q.iterrows():
        rows.append(record("e", r.market, "XRM_minus_q0.90_AUPRC", r.effect_method_minus_comparator, xinf_path, str(idx), "identity; positive favors XRM",
                           support=p95.loc[r.market], status="descriptive only" if r.market in ["ES", "FR"] else "168h moving-block bootstrap"))
    return pd.DataFrame(rows)


def build_eda(market: str) -> pd.DataFrame:
    path = SRC / f"Appendix_EDA_{market.replace('-', '_')}_source.csv"
    fp_path = SRC / "Fig5_Five_Market_Characteristics_source.csv"
    d = pd.read_csv(path)
    d["timestamp_utc"] = pd.to_datetime(d.timestamp_utc, utc=True)
    train = d[d.split.eq("train")].price_eur_mwh.astype(float)
    median = train.median(); tiqr = train.quantile(.75) - train.quantile(.25)
    z = (d.price_eur_mwh.astype(float) - median) / tiqr
    rows: list[dict] = []
    probs = np.linspace(.001, .999, 400)
    vals = np.quantile(z, probs)
    for i, (p, value) in enumerate(zip(probs, vals)):
        rows.append(record("a", market, "standardized_price_duration", value, path, f"quantile:{i}",
                           "price centered by training median and divided by training IQR; deterministic empirical quantile",
                           mask="FULL_SERIES", support=len(d), exceedance=1-p))
    temp = d.assign(month=d.timestamp_utc.dt.month, hour=d.timestamp_utc.dt.hour, z=z)
    monthly = temp.groupby("month").z.agg(median="median", q25=lambda x: x.quantile(.25), q75=lambda x: x.quantile(.75))
    for month, r in monthly.iterrows():
        for metric in ["median", "q25", "q75"]:
            rows.append(record("b", market, f"monthly_standardized_price_{metric}", r[metric], path, f"month:{month}",
                               "monthly aggregate of training-median/IQR standardized price", mask="FULL_SERIES", support=int((temp.month == month).sum()), month=month))
    hourly = temp.groupby("hour").z.agg(median="median", q25=lambda x: x.quantile(.25), q75=lambda x: x.quantile(.75))
    for hour, r in hourly.iterrows():
        for metric in ["median", "q25", "q75"]:
            rows.append(record("c", market, f"hourly_standardized_price_{metric}", r[metric], path, f"hour:{hour}",
                               "hour-of-day aggregate of training-median/IQR standardized price", mask="FULL_SERIES", support=int((temp.hour == hour).sum()), hour=hour))
    fp = pd.read_csv(fp_path).query("source_table == 'market_fingerprint'").set_index("market").loc[market]
    threshold = fp.training_P95_threshold
    event = temp.assign(negative=temp.price_eur_mwh.lt(0), upper=temp.price_eur_mwh.gt(threshold)).groupby("month").agg(negative=("negative", "mean"), upper=("upper", "mean")) * 100
    for month, r in event.iterrows():
        for metric in ["negative", "upper"]:
            rows.append(record("d", market, f"monthly_{metric}_share_pct", r[metric], path, f"month:{month}:{metric}",
                               "monthly hourly share", mask="FULL_SERIES", support=int((temp.month == month).sum()), month=month, series=metric))
    series = d.price_eur_mwh.astype(float)
    for lag in range(1, 337):
        rows.append(record("e", market, "price_autocorrelation", series.autocorr(lag), path, f"lag:{lag}",
                           "Pearson autocorrelation of frozen hourly series", mask="FULL_SERIES", support=len(series)-lag, lag=lag))
    rolling = d.set_index("timestamp_utc").price_eur_mwh.rolling("168h", min_periods=72).std().dropna() / tiqr
    hist, edges = np.histogram(rolling.clip(upper=rolling.quantile(.995)), bins=80, density=True)
    for i, value in enumerate(hist):
        rows.append(record("f", market, "rolling_7day_volatility_density", value, path, f"volatility_hist:{i}",
                           "rolling 168-h SD divided by training IQR; density after 99.5th-percentile display clipping",
                           mask="FULL_SERIES", support=len(rolling), x=(edges[i]+edges[i+1])/2))
    return pd.DataFrame(rows)


def build_setting_matrix(mask: str) -> pd.DataFrame:
    path = EXT / "comparison" / "CROSS_SETTING_METRICS.csv"
    d = pd.read_csv(path)
    d = d[d["mask"].eq(mask)].copy()
    metrics = [("a", "TSQR_MAE_over_training_IQR", "TSQR_MAE", True),
               ("b", "TSQR_pinball_over_training_IQR", "TSQR_mean_pinball", True),
               ("c", "raw_absolute_coverage_gap", "TSQR_absolute_coverage_gap", False),
               ("d", "RCQR_absolute_coverage_gap", "RCQR_absolute_coverage_gap", False),
               ("e", "RCQR_interval_score_over_training_IQR", "RCQR_interval_score", True),
               ("f", "XRM_P95_AUPRC", "XRM_P95_AUPRC", False)]
    rows: list[dict] = []
    for idx, r in d.iterrows():
        for panel, metric, col, normalize in metrics:
            value = r[col] / IQR.loc[r.market] if normalize else r[col]
            status = "ex-post" if r.setting == "S3" else "descriptive"
            rows.append(record(panel, r.market, metric, value, path, str(idx), "divide by S1 training IQR" if normalize else "identity",
                               setting=r.setting, mask=mask, support=r.N, status=status))
    return pd.DataFrame(rows)


def build_e10() -> pd.DataFrame:
    path = SRC / "Fig12_Attribution_Robustness_Cost_source.csv"
    inf_path = SRC / "Fig7_RCQR_Calibration_source.csv"
    d = pd.read_csv(path).query("source_table == 'rcqr_window_sensitivity'")
    rows: list[dict] = []
    specs = [("a", "PICP80", "RCQR_PICP80", False), ("b", "absolute_coverage_gap", "RCQR_absolute_coverage_gap", False),
             ("c", "width_over_training_IQR", "RCQR_width_over_IQR", False), ("d", "interval_score_over_training_IQR", "RCQR_IS_over_IQR", False)]
    for idx, r in d.iterrows():
        for panel, metric, col, _ in specs:
            rows.append(record(panel, r.market, metric, r[col], path, str(idx), "identity from frozen window sensitivity table",
                               support=r.N, window=int(r.window_complete_days)))
    inf = pd.read_csv(inf_path).query("source_table == 'rcqr_inference'")
    inf = inf[inf.block_hours.isin([24, 168])]
    for idx, r in inf.iterrows():
        metric = str(r.comparator_or_metric)
        positive = -r.effect_method_minus_comparator
        rows.append(record("e" if r.block_hours == 24 else "f", r.market, metric, positive, inf_path, str(idx),
                           "sign inversion so positive favors RCQR", support=r.effective_draws,
                           status=f"{int(r.block_hours)}h moving-block bootstrap", block_hours=int(r.block_hours),
                           low=-r.ci95_high, high=-r.ci95_low))
    return pd.DataFrame(rows)


def build_e11() -> pd.DataFrame:
    path = SRC / "Fig11_XRM_Support_Monitoring_source.csv"
    d = pd.read_csv(path).query("source_table == 'xrm_support_sensitivity'")
    rows: list[dict] = []
    specs = [("Prevalence", "prevalence"), ("TSQR q0.50", "q0_50_AUPRC"), ("TSQR q0.90", "q0_90_AUPRC"), ("XRM", "XRM_AUPRC")]
    for idx, r in d.iterrows():
        panel = chr(ord('a') + MARKETS.index(r.market))
        for method, col in specs:
            rows.append(record(panel, r.market, "AUPRC", r[col], path, str(idx), "identity",
                               support=r.test_events, status="descriptive-low-support" if r.test_events < 10 else "descriptive",
                               event_level=r.event_level, gamma=r.gamma, method=method, validation_events=r.validation_events))
    for market in MARKETS:
        q = d[d.market.eq(market)]
        for _, r in q.iterrows():
            rows.append(record("f", market, "test_event_support", r.test_events, path, f"support:{market}:{r.event_level}", "identity",
                               support=r.test_events, event_level=r.event_level, gamma=r.gamma, validation_events=r.validation_events))
    return pd.DataFrame(rows)


def build_e12() -> pd.DataFrame:
    path = MASTER / "FIVE_MARKET_XRM_BUDGETS.csv"
    d = pd.read_csv(path)
    d = d[(d["mask"].eq("COMMON_MASK")) & d.event_level.eq("P95") & d.method.isin(["XRM", "q0.90"])].copy()
    rows: list[dict] = []
    for idx, r in d.iterrows():
        panel = chr(ord('a') + MARKETS.index(r.market))
        for metric in ["recall", "precision"]:
            rows.append(record(panel, r.market, metric, r[metric], path, str(idx), "identity",
                               support=r.events, status="descriptive review-capacity summary", method=r.method,
                               budget_pct=r.budget * 100))
    for budget in sorted(d.budget.unique()):
        q = d[(d.budget.eq(budget)) & d.method.eq("XRM")]
        rows.append(record("f", "cross-market", "XRM_recall", q.recall.median(), path, f"summary:{budget}",
                           "cross-market median and IQR", status="descriptive review-capacity summary",
                           budget_pct=budget*100, q25=q.recall.quantile(.25), q75=q.recall.quantile(.75)))
    return pd.DataFrame(rows)


def build_e13() -> pd.DataFrame:
    path = SRC / "Fig12_Attribution_Robustness_Cost_source.csv"
    d = pd.read_csv(path).query("source_table == 's1_feature_outages'")
    rows: list[dict] = []
    specs = [("a", "delta_MAE_over_training_IQR", "delta_MAE", True),
             ("b", "delta_pinball_over_training_IQR", "delta_pinball", True),
             ("c", "delta_RCQR_interval_score_over_training_IQR", "delta_RCQR_interval_score", True),
             ("d", "delta_XRM_P95_AUPRC", "delta_XRM_P95_AUPRC", False)]
    for idx, r in d.iterrows():
        for panel, metric, col, normalize in specs:
            value = r[col] / IQR.loc[r.market] if normalize else r[col]
            rows.append(record(panel, r.market, metric, value, path, str(idx), "divide by training IQR" if normalize else "identity",
                               support=r.N, outage_group=r.outage_group))
    return pd.DataFrame(rows)


def build_e14() -> pd.DataFrame:
    path = TAB / "Table_Main_6_Five_Market_Cost.csv"
    d = pd.read_csv(path)
    specs = [("a", "primary_fit_minutes", "training_time_total_seconds_median", 1/60),
             ("b", "forecast_inference_ms", "inference_24_products_ms_median", 1),
             ("c", "XRM_scoring_ms", "XRM_24_products_ms_median", 1),
             ("d", "RCQR_update_ms", "RCQR_daily_update_ms_median", 1),
             ("e", "model_load_seconds", "model_load_seconds", 1),
             ("f", "peak_memory_GB", "memory_peak_bytes", 1e-9),
             ("g", "serialized_model_MB", "serialized_model_bytes", 1e-6)]
    rows: list[dict] = []
    for idx, r in d.iterrows():
        for panel, metric, col, factor in specs:
            rows.append(record(panel, r.market, metric, r[col]*factor, path, str(idx), f"multiply by {factor:g} for display unit",
                               support=r.get("formal_repeats_feature_inference_update", np.nan), status="descriptive computational benchmark"))
    return pd.DataFrame(rows)


def build_e15() -> pd.DataFrame:
    rows: list[dict] = []
    for market in MARKETS:
        path = MASTER / "models" / "rolling_origin" / market / f"{market}_ROLLING_ORIGIN.csv"
        d = pd.read_csv(path)
        for idx, r in d.iterrows():
            panel = chr(ord('a') + MARKETS.index(market))
            rows.append(record(panel, market, "TSQR_improvement_over_SQR_over_training_IQR",
                               (r.SQR_MAE-r.TSQR_MAE)/IQR.loc[market], path, str(idx), "positive sign convention and divide by training IQR",
                               support=r.N, status="descriptive rolling-origin fold", fold=r.fold, order=idx))
            rows.append(record(panel, market, "RCQR_interval_score_reduction_over_training_IQR",
                               (r.Raw_IS-r.RCQR_IS)/IQR.loc[market], path, str(idx), "positive sign convention and divide by training IQR",
                               support=r.N, status="descriptive rolling-origin fold", fold=r.fold, order=idx))
    inf_path = MASTER / "SUPPLEMENTARY_FIVE_MARKET" / "FIVE_MARKET_BOOTSTRAP_SUMMARY_ALL.csv"
    inf = pd.read_csv(inf_path)
    q = inf[(inf.family.eq("TSQR_MAE")) & inf.comparator_or_metric.eq("SQR") & inf.block_hours.isin([24,168])]
    for idx, r in q.iterrows():
        rows.append(record("f", r.market, "TSQR_minus_SQR_MAE", r.effect_method_minus_comparator, inf_path, str(idx), "identity; negative favors TSQR",
                           support=r.effective_draws, status=f"{int(r.block_hours)}h moving-block bootstrap",
                           block_hours=int(r.block_hours), low=r.ci95_low, high=r.ci95_high))
    return pd.DataFrame(rows)


BUILDERS = {
    "Fig05": build_fig05, "Fig06": build_fig06, "Fig07": build_fig07, "Fig08": build_fig08,
    "Fig09": build_fig09, "Fig10": build_fig10, "Fig11": build_fig11,
    "Fig12": lambda: build_trajectory("A_SUMMER", "Fig12"), "Fig13": build_fig13,
    "Fig14": build_fig14, "Fig15": build_fig15, "Fig16": build_fig16, "Fig17": build_fig17,
    "FigE01": lambda: build_eda("DE-LU"), "FigE02": lambda: build_eda("DK1"),
    "FigE03": lambda: build_eda("BE"), "FigE04": lambda: build_eda("ES"), "FigE05": lambda: build_eda("FR"),
    "FigE06": lambda: build_setting_matrix("GLOBAL_COMMON"),
    "FigE07": lambda: build_setting_matrix("MARKET_VALID"),
    "FigE08": lambda: build_trajectory("B_WINTER", "FigE08"),
    "FigE09": lambda: build_trajectory("C_SPRING", "FigE09"),
    "FigE10": build_e10, "FigE11": build_e11, "FigE12": build_e12,
    "FigE13": build_e13, "FigE14": build_e14, "FigE15": build_e15,
}


def market_y(ax: plt.Axes, show: bool = True) -> np.ndarray:
    y = np.arange(len(MARKETS))[::-1]
    ax.set_yticks(y, MARKETS if show else [""] * len(MARKETS))
    return y


def effect_forest(ax: plt.Axes, d: pd.DataFrame, xlabel: str, *, positive: bool = True, show_y: bool = True) -> None:
    q = d.set_index("market").reindex(MARKETS).reset_index()
    y = market_y(ax, show_y)
    for yi, r in zip(y, q.to_dict("records")):
        low_support = "descriptive only" in str(r.get("inferential_status", ""))
        alpha = .34 if low_support else 1.0
        ax.plot([r["low"], r["high"]], [yi, yi], color=MC[r["market"]], lw=1.1, alpha=alpha)
        ax.scatter(r["value"], yi, s=28, marker=MM[r["market"]], facecolor="white" if low_support else MC[r["market"]],
                   edgecolor=MC[r["market"]], lw=.75, alpha=alpha, zorder=3)
    ax.set_xlabel(xlabel)
    finish(ax, zero_x=True, grid="x")


def annotated_heatmap(ax: plt.Axes, matrix: pd.DataFrame, *, fmt: str = ".2f", cmap: str = "RdBu",
                      center: float | None = 0, cbar: bool = True) -> None:
    values = matrix.to_numpy(float)
    if center is None:
        im = ax.imshow(values, aspect="auto", cmap=cmap)
    else:
        vmax = np.nanmax(np.abs(values-center))
        im = ax.imshow(values, aspect="auto", cmap=cmap, vmin=center-vmax, vmax=center+vmax)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            if np.isfinite(values[i, j]):
                ax.text(j, i, format(values[i, j], fmt), ha="center", va="center", fontsize=5.9,
                        color="white" if abs(values[i, j] - (center or 0)) > .58*np.nanmax(np.abs(values-(center or 0))) else BLACK)
    ax.set_xticks(np.arange(matrix.shape[1]), matrix.columns)
    ax.set_yticks(np.arange(matrix.shape[0]), matrix.index)
    if cbar:
        cb = ax.figure.colorbar(im, ax=ax, fraction=.047, pad=.03)
        cb.ax.tick_params(labelsize=5.8, length=2)
        cb.outline.set_linewidth(.6)
    finish(ax)


def plot_fig05(d: pd.DataFrame):
    fig = plt.figure(figsize=(7.2, 5.35), constrained_layout=True)
    outer = fig.add_gridspec(2, 2, width_ratios=[1.25, 1.0], height_ratios=[1.08, 1.0])
    axa = fig.add_subplot(outer[0, 0])
    sub = outer[0, 1].subgridspec(1, 3, wspace=.14)
    baxes = [fig.add_subplot(sub[0, i]) for i in range(3)]
    axc = fig.add_subplot(outer[1, 0]); axd = fig.add_subplot(outer[1, 1])
    ymap = {m: y for m, y in zip(MARKETS, np.arange(5)[::-1])}
    for m in MARKETS:
        q = d[(d.panel.eq("a")) & d.market.eq(m)].sort_values("x")
        dens = q.value.to_numpy(float); scale = .65 / max(dens.max(), 1e-9)
        y = ymap[m]
        axa.fill_between(q.x, y, y + dens*scale, color=MC[m], alpha=.60, lw=.35, edgecolor=MC[m])
        axa.plot(q.x, np.full(len(q), y), color=BLACK, lw=.45)
    axa.axvline(0, color="#999999", lw=.6, ls="--")
    axa.set(yticks=list(ymap.values()), yticklabels=MARKETS, xlabel="Price standardized by training median and IQR", ylabel="Market")
    axa.set_xlim(-3.5, 7.0); finish(axa); panel_label(axa, "a", x=-.11)
    bd = d[d.panel.eq("b")]
    facets = [("negative_price_share_pct", "Negative\nshare (%)"),
              ("standard_deviation_over_full_IQR", "SD /\nfull IQR"),
              ("rolling_7day_volatility_over_full_IQR", "7-d vol. /\nfull IQR")]
    for j, (metric, title) in enumerate(facets):
        ax = baxes[j]; q = bd[bd.metric.eq(metric)].set_index("market").reindex(MARKETS)
        y = market_y(ax, show=j == 0)
        for yi, m in zip(y, MARKETS):
            ax.plot([0, q.loc[m, "value"]], [yi, yi], color=LIGHT, lw=.75)
            ax.scatter(q.loc[m, "value"], yi, s=23, color=MC[m], marker=MM[m], edgecolor=BLACK, lw=.35)
        ax.set_title(title, fontsize=6.9); finish(ax, grid="x")
        if j == 0: panel_label(ax, "b", x=-.38)
    c = d[d.panel.eq("c")]
    y = market_y(axc)
    for yi, m in zip(y, MARKETS):
        q = c[c.market.eq(m)].set_index("metric")
        v24, v168 = q.loc["ACF_lag24h", "value"], q.loc["ACF_lag168h", "value"]
        axc.plot([v24, v168], [yi, yi], color=LIGHT, lw=1)
        axc.scatter(v24, yi, s=28, facecolor="white", edgecolor=MC[m], lw=.9, marker=MM[m])
        axc.scatter(v168, yi, s=28, facecolor=MC[m], edgecolor=BLACK, lw=.35, marker=MM[m])
    axc.set_xlabel("Price autocorrelation")
    boxed_legend(axc, handles=[Line2D([],[],marker='o',ls='',mfc='white',mec=BLACK,label='24 h'),
                              Line2D([],[],marker='o',ls='',mfc=RCQR,mec=BLACK,label='168 h')], ncol=2, loc="lower right")
    finish(axc, grid="x"); panel_label(axc, "c", x=-.11)
    q = d[d.panel.eq("d")].set_index("market").reindex(MARKETS)
    y = market_y(axd)
    for yi, m in zip(y, MARKETS):
        n = q.loc[m, "value"]; alpha = .32 if n < 10 else 1
        axd.plot([0, n], [yi, yi], color=MC[m], lw=.85, alpha=alpha)
        size = 20 + 18*q.loc[m, "threshold_over_training_IQR"]
        axd.scatter(n, yi, s=size, marker=MM[m], facecolor=MC[m] if n >= 10 else "white", edgecolor=MC[m], lw=.8, alpha=alpha)
        axd.text(n, yi+.18, f"n={int(n)}", ha="center", va="bottom", fontsize=5.4, color=MC[m], alpha=max(alpha,.5))
    axd.axvline(10, color=BAD, ls="--", lw=.7)
    axd.set_xlabel("Held-out P95 events on common mask"); finish(axd, grid="x"); panel_label(axd, "d", x=-.11)
    return fig, [[axa], baxes, [axc], [axd]], 137


def plot_fig06(d: pd.DataFrame):
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.0), constrained_layout=True)
    ax = axs[0, 0]; q = d[d.panel.eq("a")]
    methods = ["Persistence", "Direct QR", "RQR", "SQR", "TSQR"]
    y = np.arange(len(methods))[::-1]
    for m in MARKETS:
        z = q[q.market.eq(m)].set_index("method").reindex(methods)
        ax.scatter(z.value, y, s=27, marker=MM[m], color=MC[m], edgecolor=BLACK, lw=.35, label=m)
    ax.set_yticks(y, methods); ax.set_xlabel("MAE / training IQR")
    boxed_legend(ax, ncol=2, loc="lower right"); finish(ax, grid="x"); panel_label(ax, "a")
    for ax, panel, labeltxt in [(axs[0,1], "b", "TSQR improvement over Persistence (%)"),
                                (axs[1,0], "c", "TSQR improvement over SQR (%)"),
                                (axs[1,1], "d", "TSQR pinball improvement over SQR (%)")]:
        effect_forest(ax, d[d.panel.eq(panel)], labeltxt, show_y=True)
        panel_label(ax, panel)
    return fig, [[axs.flat[i]] for i in range(4)], 128


def plot_fig07(d: pd.DataFrame):
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 4.65), constrained_layout=True)
    trans = ["Direct QR→RQR", "RQR→SQR", "SQR→TSQR"]
    lim = max(abs(d[d.panel.ne("f")].value.min()), abs(d[d.panel.ne("f")].value.max()))*1.18
    for i, m in enumerate(MARKETS):
        ax = axs.flat[i]; q = d[(d.market.eq(m)) & d.panel.ne("f")].set_index("transition").reindex(trans)
        y = np.arange(3)[::-1]
        colors = [GOOD if v >= 0 else BAD for v in q.value]
        ax.barh(y, q.value, color=colors, alpha=.82, edgecolor=BLACK, linewidth=.35)
        ax.set_yticks(y, trans if i % 3 == 0 else ["", "", ""]); ax.set_title(m)
        ax.set_xlim(-lim, lim); ax.set_xlabel("ΔMAE / training IQR")
        finish(ax, zero_x=True, grid="x"); panel_label(ax, chr(ord('a')+i))
    ax = axs.flat[5]; q = d[d.panel.eq("f")]
    y = np.arange(3)[::-1]
    for yi, t in zip(y, trans):
        z = q[q.transition.eq(t)].set_index("summary_stat")
        ax.plot([z.loc['q25','value'], z.loc['q75','value']], [yi,yi], color=BLACK, lw=2.2)
        ax.scatter(z.loc['median','value'], yi, marker='D', s=31, color=GOOD if z.loc['median','value'] >= 0 else BAD, edgecolor=BLACK, lw=.4)
        points = d[(d.transition.eq(t)) & d.market.isin(MARKETS)]
        for _, r in points.iterrows(): ax.scatter(r.value, yi, marker=MM[r.market], s=18, color=MC[r.market], alpha=.75)
    ax.set_yticks(y, trans); ax.set_xlabel("Cross-market ΔMAE / training IQR"); ax.set_title("Cross-market synthesis")
    finish(ax, zero_x=True, grid="x"); panel_label(ax, "f")
    return fig, [[a] for a in axs.flat], 119


def plot_fig08(d: pd.DataFrame):
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.7), constrained_layout=True)
    labels = [("a", "PICP80"), ("b", "Absolute coverage gap"), ("c", "Interval score / training IQR"), ("d", "Width / training IQR")]
    for j, (panel, xlabel) in enumerate(labels):
        ax = axs[j]; q = d[d.panel.eq(panel)]
        y = market_y(ax, show=j==0)
        for yi, m in zip(y, MARKETS):
            z = q[q.market.eq(m)].set_index("method")
            raw, rc = z.loc["Raw TSQR", "value"], z.loc["W60 RCQR", "value"]
            ax.plot([raw, rc], [yi, yi], color=LIGHT, lw=.95)
            ax.scatter(raw, yi, s=27, marker=MM[m], facecolor="white", edgecolor=MC[m], lw=.8)
            ax.scatter(rc, yi, s=28, marker=MM[m], facecolor=MC[m], edgecolor=BLACK, lw=.35)
        if panel == "a": ax.axvline(.8, color=BAD, ls="--", lw=.7)
        ax.set_xlabel(xlabel); finish(ax, grid="x"); panel_label(ax, panel)
    boxed_legend(axs[0], handles=[Line2D([],[],marker='o',ls='',mfc='white',mec=BLACK,label='Raw TSQR'),
                                  Line2D([],[],marker='o',ls='',mfc=RCQR,mec=BLACK,label='W60 RCQR')], loc="best")
    return fig, [[a] for a in axs], 69


def plot_fig09(d: pd.DataFrame):
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 4.65), constrained_layout=True)
    for i, m in enumerate(MARKETS):
        ax = axs.flat[i]; q = d[(d.market.eq(m)) & d.panel.ne("f")].sort_values("order")
        raw = q[q.method.eq("Raw")]; cal = q[q.method.ne("Raw")]
        ax.plot(cal.x, cal.y, color=MC[m], lw=.8, alpha=.75)
        ax.scatter(raw.x, raw.y, s=30, facecolor="white", edgecolor=MC[m], marker=MM[m], lw=.9)
        ax.scatter(cal.x, cal.y, s=27, facecolor=MC[m], edgecolor=BLACK, marker=MM[m], lw=.35)
        offsets={'Raw':(2,4),'W7':(2,4),'W14':(2,-8),'W30':(-9,4),'W60':(-9,-8)}
        for _, r in q.iterrows(): ax.annotate(r.method.replace('W',''), (r.x,r.y), xytext=offsets[r.method], textcoords='offset points', fontsize=5.4)
        ax.set_title(m); ax.set_xlabel("Width / training IQR"); ax.set_ylabel("Absolute coverage gap" if i%3==0 else "")
        finish(ax, grid="x"); panel_label(ax, chr(ord('a')+i))
    ax=axs.flat[5]; q=d[d.panel.eq("f")].sort_values("order")
    cal=q[q.method.ne("Raw")]; ax.plot(cal.x,cal.y,color=BLACK,lw=.8)
    for _,r in q.iterrows():
        ax.errorbar(r.x,r.y,xerr=[[r.x-r.x_q25],[r.x_q75-r.x]],yerr=[[r.y-r.y_q25],[r.y_q75-r.y]],fmt='o',mfc='white' if r.method=='Raw' else GOOD,mec=BLACK,ecolor='#888888',ms=4,capsize=2)
        offsets={'Raw':(2,4),'W7':(2,4),'W14':(2,-8),'W30':(-9,4),'W60':(-9,-8)}
        ax.annotate(r.method.replace('W',''),(r.x,r.y),xytext=offsets[r.method],textcoords='offset points',fontsize=5.4)
    ax.set_title("Cross-market median and IQR"); ax.set(xlabel="Width / training IQR",ylabel="Absolute coverage gap")
    finish(ax,grid="x"); panel_label(ax,"f")
    return fig, [[a] for a in axs.flat], 119


def plot_fig10(d: pd.DataFrame):
    fig, axs = plt.subplots(1,3,figsize=(7.2,2.75),constrained_layout=True)
    labels=[("a","TSQR MAE / S1 training IQR"),("b","Raw absolute coverage gap"),("c","W60 RCQR interval score / S1 training IQR")]
    for j,(panel,xlabel) in enumerate(labels):
        ax=axs[j]; q=d[d.panel.eq(panel)]; y=market_y(ax,show=j==0)
        for yi,m in zip(y,MARKETS):
            z=q[q.market.eq(m)].set_index("setting"); a=z.loc['S1','value']; b=z.loc['S2_DA','value']
            ax.plot([a,b],[yi,yi],color=LIGHT,lw=.95)
            ax.scatter(a,yi,s=27,marker=MM[m],facecolor='white',edgecolor=MC[m],lw=.8)
            ax.scatter(b,yi,s=28,marker=MM[m],facecolor=MC[m],edgecolor=BLACK,lw=.35)
        ax.set_xlabel(xlabel); finish(ax,grid='x'); panel_label(ax,panel)
    boxed_legend(axs[0],handles=[Line2D([],[],marker='o',ls='',mfc='white',mec=BLACK,label='S1'),Line2D([],[],marker='o',ls='',mfc=RCQR,mec=BLACK,label='S2_DA')],loc='best')
    return fig,[[a] for a in axs],70


def plot_fig11(d: pd.DataFrame):
    fig,axs=plt.subplots(1,2,figsize=(7.2,2.9),constrained_layout=True)
    for ax,panel,title,order in [(axs[0],'a','TSQR improvement over SQR / training IQR',['2024','2025']),
                                 (axs[1],'b','RCQR interval-score reduction / training IQR',['winter','spring','summer','autumn'])]:
        q=d[d.panel.eq(panel)]; mat=q.pivot(index='market',columns='slice',values='value').reindex(MARKETS,columns=order)
        annotated_heatmap(ax,mat,fmt='.3f',cmap='RdBu',center=0); ax.set_title(title); panel_label(ax,panel,x=-.10)
    return fig,[[axs[0]],[axs[1]]],74


def plot_trajectory(d: pd.DataFrame, title_window: str):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.75),constrained_layout=True)
    for i,m in enumerate(MARKETS):
        ax=axs.flat[i]; q=d[d.market.eq(m)].pivot(index='timestamp_utc',columns='series',values='value').sort_index(); x=pd.to_datetime(q.index,utc=True)
        ax.fill_between(x,q['Raw lower'].to_numpy(float),q['Raw upper'].to_numpy(float),color='#C9DCE8',alpha=.72,lw=0)
        ax.fill_between(x,q['RCQR lower'].to_numpy(float),q['RCQR upper'].to_numpy(float),color='#6FA2BF',alpha=.42,lw=0)
        ax.plot(x,q['Observed price'],color=BLACK,lw=.65,antialiased=True)
        ax.plot(x,q['TSQR median'],color=MC[m],lw=.82,antialiased=True)
        ax.set_title(m); ax.set_ylabel("EUR MWh$^{-1}$" if i%3==0 else "")
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.tick_params(axis='x',rotation=20); finish(ax); panel_label(ax,chr(ord('a')+i))
    ax=axs.flat[5]; ax.axis('off')
    handles=[Line2D([],[],color=BLACK,lw=1,label='Observed price'),Line2D([],[],color=MC['DE-LU'],lw=1,label='TSQR median'),Rectangle((0,0),1,1,color='#C9DCE8',alpha=.72,label='Raw 80% interval'),Rectangle((0,0),1,1,color='#6FA2BF',alpha=.42,label='W60 RCQR 80% interval')]
    boxed_legend(ax,handles=handles,loc='center',title=title_window); panel_label(ax,'f',x=.02,y=.92)
    return fig,[[a] for a in axs.flat],121


def plot_fig13(d: pd.DataFrame):
    fig,axs=plt.subplots(2,5,figsize=(7.2,4.15),constrained_layout=True,sharex='col')
    groups=['negative_hours','negative_runs_ge3','negative_runs_ge6']; glabels=['Neg.','N3','N6']; x=np.arange(3)
    for col,m in enumerate(MARKETS):
        top=axs[0,col]; q=d[(d.market.eq(m)) & d.row.eq('coverage')]
        for j,g in enumerate(groups):
            z=q[q.group.eq(g)].set_index('method'); raw=z.loc['Raw TSQR','value']; rc=z.loc['W60 RCQR','value']; n=int(z.support_N.iloc[0])
            top.plot([j-.08,j+.08],[raw,rc],color=LIGHT,lw=.9)
            top.scatter(j-.08,raw,s=22,facecolor='white',edgecolor=MC[m],marker=MM[m],lw=.75)
            top.scatter(j+.08,rc,s=23,facecolor=MC[m],edgecolor=BLACK,marker=MM[m],lw=.3)
            top.text(j+.10,(raw+rc)/2,f"n={n}",ha='left',va='center',fontsize=4.7,color=GREY)
        top.axhline(.8,color=BAD,ls='--',lw=.65); top.set_title(m); top.set_xticks(x,glabels); top.set_ylabel('Conditional PICP80' if col==0 else '')
        finish(top); panel_label(top,chr(ord('a')+col),x=-.23)
        bot=axs[1,col]; z=d[(d.market.eq(m)) & d.row.eq('score')].set_index('group').reindex(groups)
        colors=[GOOD if v>=0 else BAD for v in z.value]
        bot.bar(x,z.value,color=colors,alpha=.8,edgecolor=BLACK,lw=.3)
        bot.set_xticks(x,glabels); bot.set_ylabel('IS reduction / IQR' if col==0 else ''); finish(bot,zero_y=True); panel_label(bot,chr(ord('f')+col),x=-.23)
    return fig,[[axs[r,c]] for r in range(2) for c in range(5)],106


def plot_ordered_tail(ax: plt.Axes, q: pd.DataFrame, market: str | None = None) -> None:
    q=q.sort_values('order'); color=MC[market] if market else BLACK; marker=MM[market] if market else 'D'
    # Break the guide at the unreported P92.5 position; no interpolation is used.
    for segment in ([0],[2,3,4]):
        z=q[q.order.isin(segment) & q.value.notna()]
        if len(z)>=2: ax.plot(z.order,z.value,color=color,lw=.8,alpha=.75)
    for _,r in q.iterrows():
        alpha=.30 if r.support_N<10 else 1
        size=18+3*np.sqrt(max(float(r.support_N),0))
        ax.scatter(r.order,r.value,s=size,marker=marker,facecolor=color if alpha==1 else 'white',edgecolor=color,lw=.75,alpha=alpha,zorder=3)
        ax.annotate(f"n={int(r.support_N)}",(r.order,r.value),xytext=(0,4),textcoords='offset points',ha='center',fontsize=4.8,alpha=max(alpha,.5))


def plot_fig14(d: pd.DataFrame):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.65),constrained_layout=True)
    ticks=['P90','P92.5','P95','P97.5','P99']
    for i,m in enumerate(MARKETS):
        ax=axs.flat[i]; q=d[(d.market.eq(m)) & d.panel.ne('f')]; plot_ordered_tail(ax,q,m)
        ax.set_xticks(range(5),ticks,rotation=18); ax.set_title(m); ax.set_ylabel('TSQR MAE / training IQR' if i%3==0 else '')
        finish(ax); panel_label(ax,chr(ord('a')+i))
    ax=axs.flat[5]; q=d[d.panel.eq('f')].sort_values('order')
    for _,r in q.iterrows():
        ax.plot([r.order,r.order],[r.q25,r.q75],color=BLACK,lw=2.2); ax.scatter(r.order,r.value,marker='D',s=29,color=GOOD,edgecolor=BLACK,lw=.35)
    z=q[q.order.isin([2,3,4])]; ax.plot(z.order,z.value,color=BLACK,lw=.8)
    ax.set_xticks(range(5),ticks,rotation=18); ax.set_title('Cross-market median and IQR'); ax.set_ylabel('TSQR MAE / training IQR')
    finish(ax); panel_label(ax,'f')
    return fig,[[a] for a in axs.flat],119


def plot_fig15(d: pd.DataFrame):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.7),constrained_layout=True)
    methods=['Prevalence','TSQR q0.50','TSQR q0.90','XRM']; y=np.arange(4)[::-1]
    for i,m in enumerate(MARKETS):
        ax=axs.flat[i]; q=d[(d.market.eq(m)) & d.panel.ne('f')].set_index('method').reindex(methods); n=int(q.support_N.iloc[0]); alpha=.34 if n<10 else 1
        for yi,method in zip(y,methods):
            v=q.loc[method,'value']; ax.plot([0,v],[yi,yi],color=MC[m],lw=.75,alpha=alpha)
            ax.scatter(v,yi,s=25,marker=MM[m],facecolor=MC[m] if n>=10 else 'white',edgecolor=MC[m],lw=.75,alpha=alpha)
        ax.set_yticks(y,methods if i%3==0 else ['']*4); ax.set_title(f"{m}  |  P95 n={n}" + ('; descriptive' if n<10 else ''))
        ax.set_xlabel('P95 AUPRC'); finish(ax,grid='x'); panel_label(ax,chr(ord('a')+i))
    effect_forest(axs.flat[5],d[d.panel.eq('f')],'XRM − TSQR q0.90 AUPRC',show_y=True); axs.flat[5].set_title('168-h paired effect'); panel_label(axs.flat[5],'f')
    return fig,[[a] for a in axs.flat],120


def plot_fig16(d: pd.DataFrame):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.65),constrained_layout=True)
    groups=['short_price_memory_24_48h','long_price_memory_168_336_720h','weekly_local_product_memory','calendar_DST','long_window_volatility']
    glabels=['Short price','Long price','Weekly product','Calendar/DST','Long volatility']; y=np.arange(5)[::-1]
    lim=max(abs(d[d.panel.ne('f')].value.min()),abs(d[d.panel.ne('f')].value.max()))*1.15
    for i,m in enumerate(MARKETS):
        ax=axs.flat[i]; q=d[(d.market.eq(m)) & d.panel.ne('f')].set_index('outage_group').reindex(groups)
        for yi,(g,labeltxt) in zip(y,zip(groups,glabels)):
            v=q.loc[g,'value']; ax.plot([0,v],[yi,yi],color=MC[m],lw=.75); ax.scatter(v,yi,s=25,marker=MM[m],color=MC[m],edgecolor=BLACK,lw=.35)
        ax.set_yticks(y,glabels if i%3==0 else ['']*5); ax.set_xlim(-lim,lim); ax.set_title(m); ax.set_xlabel('Outage ΔMAE / training IQR')
        finish(ax,zero_x=True,grid='x'); panel_label(ax,chr(ord('a')+i))
    ax=axs.flat[5]; q=d[d.panel.eq('f')]; ops=['Forecast inference','XRM scoring','RCQR update','Model loading']; y=np.arange(4)[::-1]
    for yi,op in zip(y,ops):
        z=q[q.operation.eq(op)]
        for _,r in z.iterrows(): ax.scatter(r.value,yi,s=24,marker=MM[r.market],color=MC[r.market],edgecolor=BLACK,lw=.3)
    ax.set_yticks(y,ops); ax.set_xscale('log'); ax.set_xlabel('Online latency (ms; log scale)'); ax.set_title('Online computational profile')
    finish(ax,grid='x'); panel_label(ax,'f')
    return fig,[[a] for a in axs.flat],119


def plot_fig17(d: pd.DataFrame):
    fig,axs=plt.subplots(1,5,figsize=(7.2,2.85),constrained_layout=True)
    labels=[('a','TSQR vs\nPersistence\nMAE (%)'),('b','TSQR vs\nSQR\nMAE (%)'),('c','RCQR gap\nreduction'),('d','RCQR IS\nreduction / IQR'),('e','XRM vs q0.90\nAUPRC')]
    y=np.arange(5)[::-1]
    for j,(panel,xlabel) in enumerate(labels):
        ax=axs[j]; q=d[d.panel.eq(panel)].set_index('market').reindex(MARKETS)
        for yi,m in zip(y,MARKETS):
            low=panel=='e' and m in ['ES','FR']; alpha=.32 if low else 1
            ax.scatter(q.loc[m,'value'],yi,s=27,marker=MM[m],facecolor='white' if low else MC[m],edgecolor=MC[m],lw=.75,alpha=alpha)
        med=q.value.median(); q25=q.value.quantile(.25); q75=q.value.quantile(.75)
        ax.plot([q25,q75],[-.75,-.75],color=BLACK,lw=2.2); ax.scatter(med,-.75,marker='D',s=28,color=BLACK)
        ax.set_yticks(list(y)+[-.75],(MARKETS+['Median/IQR']) if j==0 else ['']*6); ax.set_xlabel(xlabel)
        finish(ax,zero_x=True,grid='x'); panel_label(ax,panel,x=-.22)
    return fig,[[a] for a in axs],73


def plot_eda(d: pd.DataFrame):
    market=str(d.market.iloc[0]); fig,axs=plt.subplots(2,3,figsize=(7.2,4.55),constrained_layout=True)
    q=d[d.panel.eq('a')].sort_values('exceedance'); axs[0,0].plot(q.exceedance*100,q.value,color=MC[market],lw=.9)
    axs[0,0].axhline(0,color='#999999',ls='--',lw=.6); axs[0,0].set(xlabel='Exceedance probability (%)',ylabel='Standardized price'); axs[0,0].set_xscale('log'); finish(axs[0,0]); panel_label(axs[0,0],'a')
    q=d[d.panel.eq('b')].pivot(index='month',columns='metric',values='value').sort_index(); x=q.index.to_numpy(float)
    axs[0,1].fill_between(x,q['monthly_standardized_price_q25'],q['monthly_standardized_price_q75'],color=MC[market],alpha=.20,lw=0)
    axs[0,1].plot(x,q['monthly_standardized_price_median'],color=MC[market],marker='o',ms=2.6,lw=.8); axs[0,1].set(xticks=range(1,13),xlabel='Month',ylabel='Standardized price'); finish(axs[0,1]); panel_label(axs[0,1],'b')
    q=d[d.panel.eq('c')].pivot(index='hour',columns='metric',values='value').sort_index(); x=q.index.to_numpy(float)
    axs[0,2].fill_between(x,q['hourly_standardized_price_q25'],q['hourly_standardized_price_q75'],color=MC[market],alpha=.20,lw=0)
    axs[0,2].plot(x,q['hourly_standardized_price_median'],color=MC[market],lw=.85); axs[0,2].set(xlabel='Hour of day',ylabel='Standardized price',xticks=[0,6,12,18,23]); finish(axs[0,2]); panel_label(axs[0,2],'c')
    q=d[d.panel.eq('d')]
    for metric,labeltxt,ls in [('monthly_negative_share_pct','Negative','-'),('monthly_upper_share_pct','Above training P95','--')]:
        z=q[q.metric.eq(metric)].sort_values('month'); axs[1,0].plot(z.month,z.value,color=MC[market],marker='o',ms=2.5,lw=.8,ls=ls,label=labeltxt)
    axs[1,0].set(xticks=range(1,13),xlabel='Month',ylabel='Hourly share (%)'); boxed_legend(axs[1,0],loc='best'); finish(axs[1,0]); panel_label(axs[1,0],'d')
    q=d[d.panel.eq('e')].sort_values('lag'); axs[1,1].plot(q.lag,q.value,color=MC[market],lw=.7); axs[1,1].axvline(24,color='#999999',ls=':',lw=.6); axs[1,1].axvline(168,color='#999999',ls=':',lw=.6)
    axs[1,1].set(xlabel='Lag (h)',ylabel='Autocorrelation'); finish(axs[1,1],zero_y=True); panel_label(axs[1,1],'e')
    q=d[d.panel.eq('f')].sort_values('x'); axs[1,2].fill_between(q.x,0,q.value,color=MC[market],alpha=.55,lw=.3); axs[1,2].set(xlabel='Rolling 7-d SD / training IQR',ylabel='Density'); finish(axs[1,2]); panel_label(axs[1,2],'f')
    fig.suptitle(f'{market}: detailed exploratory price diagnostics',fontsize=9)
    return fig,[[a] for a in axs.flat],116


def plot_setting_matrix(d: pd.DataFrame, title: str):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.75),constrained_layout=True)
    settings=['S1','S2_LEGACY','S2_DA','S3']; labels=['S1','S2 legacy','S2 day-ahead','S3 ex-post']
    for i,panel in enumerate(list('abcdef')):
        q=d[d.panel.eq(panel)]; mat=q.pivot(index='market',columns='setting',values='value').reindex(MARKETS,columns=settings); mat.columns=labels
        annotated_heatmap(axs.flat[i],mat,fmt='.2f',cmap='viridis',center=None); axs.flat[i].set_title(str(q.metric.iloc[0]).replace('_',' '),fontsize=7.4); axs.flat[i].tick_params(axis='x',rotation=22); panel_label(axs.flat[i],panel)
    fig.suptitle(title,fontsize=9)
    return fig,[[a] for a in axs.flat],121


def plot_e10(d: pd.DataFrame):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.85),constrained_layout=True)
    labels=[('a','RCQR PICP80'),('b','Absolute coverage gap'),('c','Width / training IQR'),('d','Interval score / training IQR')]
    for panel,ylabel in labels:
        ax=axs.flat[ord(panel)-ord('a')]; q=d[d.panel.eq(panel)]
        for m in MARKETS:
            z=q[q.market.eq(m)].sort_values('window'); ax.plot(z.window,z.value,color=MC[m],marker=MM[m],ms=3,lw=.8,label=m)
        if panel=='a': ax.axhline(.8,color=BAD,ls='--',lw=.65)
        ax.set(xticks=[7,14,30,60],xlabel='Complete-day history window',ylabel=ylabel); finish(ax); panel_label(ax,panel)
    boxed_legend(axs[0,0],ncol=2,loc='best')
    for panel,title in [('e','24-h block'),('f','168-h block')]:
        ax=axs.flat[ord(panel)-ord('a')]; q=d[d.panel.eq(panel)]
        metrics=sorted(q.metric.unique()); offsets=np.linspace(-.24,.24,len(metrics)); y=np.arange(5)[::-1]
        for off,metric in zip(offsets,metrics):
            z=q[q.metric.eq(metric)].set_index('market').reindex(MARKETS)
            for yi,m in zip(y,MARKETS): ax.errorbar(z.loc[m,'value'],yi+off,xerr=[[z.loc[m,'value']-z.loc[m,'low']],[z.loc[m,'high']-z.loc[m,'value']]],fmt=MM[m],mfc=MC[m],mec=BLACK,ecolor=MC[m],ms=3,capsize=1.5,lw=.7)
        ax.set_yticks(y,MARKETS); ax.set_title(title); ax.set_xlabel('Signed RCQR improvement'); finish(ax,zero_x=True,grid='x'); panel_label(ax,panel)
    return fig,[[a] for a in axs.flat],124


def plot_e11(d: pd.DataFrame):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.75),constrained_layout=True)
    levels=['P90','P92.5','P95','P97.5','P99']; x=np.arange(5); methods=['Prevalence','TSQR q0.50','TSQR q0.90','XRM']; cols={'Prevalence':'#AAAAAA','TSQR q0.50':'#7AA0BC','TSQR q0.90':'#3D799F','XRM':GOOD}
    for i,m in enumerate(MARKETS):
        ax=axs.flat[i]; q=d[(d.market.eq(m)) & d.panel.ne('f')]
        for method in methods:
            z=q[q.method.eq(method)].set_index('event_level').reindex(levels); ax.plot(x,z.value,color=cols[method],marker='o',ms=2.7,lw=.75,label=method)
        low=q.groupby('event_level').support_N.first().reindex(levels).to_numpy(float)<10
        for xi,flag in enumerate(low):
            if flag: ax.axvspan(xi-.35,xi+.35,color='#EFEFEF',zorder=-3)
        ax.set_xticks(x,levels,rotation=18); ax.set_title(m); ax.set_ylabel('AUPRC' if i%3==0 else ''); finish(ax); panel_label(ax,chr(ord('a')+i))
    boxed_legend(axs.flat[0],ncol=2,loc='best')
    ax=axs.flat[5]; q=d[d.panel.eq('f')]
    for m in MARKETS:
        z=q[q.market.eq(m)].set_index('event_level').reindex(levels); ax.plot(x,z.value,color=MC[m],marker=MM[m],ms=3,lw=.8,label=m)
    ax.axhline(10,color=BAD,ls='--',lw=.65); ax.set_yscale('log'); ax.set_xticks(x,levels,rotation=18); ax.set_ylabel('Held-out event support (log)'); boxed_legend(ax,ncol=2,loc='best'); finish(ax); panel_label(ax,'f')
    return fig,[[a] for a in axs.flat],121


def plot_e12(d: pd.DataFrame):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.65),constrained_layout=True)
    for i,m in enumerate(MARKETS):
        ax=axs.flat[i]; q=d[(d.market.eq(m)) & d.panel.ne('f')]
        for method,ls in [('XRM','-'),('q0.90','--')]:
            z=q[(q.method.eq(method)) & q.metric.eq('recall')].sort_values('budget_pct'); ax.plot(z.budget_pct,z.value,color=MC[m],marker=MM[m],ms=3,lw=.85,ls=ls,label=method)
        ax.set_title(m); ax.set(xlabel='Review budget (%)',ylabel='P95 recall' if i%3==0 else '',xticks=[.5,1,2,5]); finish(ax); panel_label(ax,chr(ord('a')+i))
    boxed_legend(axs.flat[0],loc='best')
    ax=axs.flat[5]; q=d[d.panel.eq('f')].sort_values('budget_pct')
    ax.fill_between(q.budget_pct,q.q25,q.q75,color=GOOD,alpha=.2,lw=0); ax.plot(q.budget_pct,q.value,color=GOOD,marker='D',ms=3.3,lw=.85)
    ax.set_title('Cross-market XRM median and IQR'); ax.set(xlabel='Review budget (%)',ylabel='P95 recall',xticks=[.5,1,2,5]); finish(ax); panel_label(ax,'f')
    return fig,[[a] for a in axs.flat],119


def plot_e13(d: pd.DataFrame):
    fig,axs=plt.subplots(2,2,figsize=(7.2,5.2),constrained_layout=True)
    groups=['short_price_memory_24_48h','long_price_memory_168_336_720h','weekly_local_product_memory','calendar_DST','long_window_volatility']; glabels=['Short price','Long price','Weekly product','Calendar/DST','Long volatility']
    for i,panel in enumerate(list('abcd')):
        q=d[d.panel.eq(panel)]; mat=q.pivot(index='market',columns='outage_group',values='value').reindex(MARKETS,columns=groups); mat.columns=glabels
        annotated_heatmap(axs.flat[i],mat,fmt='.3f',cmap='RdBu',center=0); axs.flat[i].set_title(str(q.metric.iloc[0]).replace('_',' '),fontsize=7.5); axs.flat[i].tick_params(axis='x',rotation=23); panel_label(axs.flat[i],panel)
    return fig,[[a] for a in axs.flat],132


def plot_e14(d: pd.DataFrame):
    fig,axs=plt.subplots(2,4,figsize=(7.2,4.3),constrained_layout=True)
    panels=list('abcdefg')
    for i,panel in enumerate(panels):
        ax=axs.flat[i]; q=d[d.panel.eq(panel)].set_index('market').reindex(MARKETS); y=market_y(ax,show=i%4==0)
        for yi,m in zip(y,MARKETS):
            ax.plot([0,q.loc[m,'value']],[yi,yi],color=MC[m],lw=.7); ax.scatter(q.loc[m,'value'],yi,s=23,marker=MM[m],color=MC[m],edgecolor=BLACK,lw=.3)
        ax.set_xlabel(str(q.metric.iloc[0]).replace('_',' ')); finish(ax,grid='x'); panel_label(ax,panel,x=-.22)
    axs.flat[7].axis('off'); axs.flat[7].text(.5,.5,'Single primary fits;\nonline timings use the\nfrozen formal repeats.',ha='center',va='center',fontsize=7)
    return fig,[[a] for a in axs.flat],110


def plot_e15(d: pd.DataFrame):
    fig,axs=plt.subplots(2,3,figsize=(7.2,4.75),constrained_layout=True)
    for i,m in enumerate(MARKETS):
        ax=axs.flat[i]; q=d[(d.market.eq(m)) & d.panel.ne('f')]
        for metric,color,marker in [('TSQR_improvement_over_SQR_over_training_IQR',MC[m],'o'),('RCQR_interval_score_reduction_over_training_IQR',GOOD,'s')]:
            z=q[q.metric.eq(metric)].sort_values('order'); ax.plot(z.order,z.value,color=color,marker=marker,ms=3,lw=.8,label='TSQR vs SQR' if marker=='o' else 'RCQR IS')
        folds=q.sort_values('order').fold.unique(); ax.set_xticks(range(len(folds)),[f.replace('_',' ') for f in folds],rotation=18); ax.set_title(m); ax.set_ylabel('Improvement / training IQR' if i%3==0 else '')
        finish(ax,zero_y=True); panel_label(ax,chr(ord('a')+i))
    boxed_legend(axs.flat[0],loc='best')
    ax=axs.flat[5]; q=d[d.panel.eq('f')]; y=np.arange(5)[::-1]
    for yi,m in zip(y,MARKETS):
        z=q[q.market.eq(m)].set_index('block_hours')
        for bh,offset,face in [(24,-.1,'white'),(168,.1,MC[m])]:
            r=z.loc[bh]; ax.errorbar(r.value,yi+offset,xerr=[[r.value-r.low],[r.high-r.value]],fmt=MM[m],mfc=face,mec=MC[m],ecolor=MC[m],ms=3.5,capsize=1.5,lw=.7)
    ax.set_yticks(y,MARKETS); ax.set_xlabel('TSQR − SQR MAE'); ax.set_title('24-h (open) and 168-h (filled) bootstrap'); finish(ax,zero_x=True,grid='x'); panel_label(ax,'f')
    return fig,[[a] for a in axs.flat],121


PLOTTERS = {
    "Fig05": plot_fig05, "Fig06": plot_fig06, "Fig07": plot_fig07, "Fig08": plot_fig08,
    "Fig09": plot_fig09, "Fig10": plot_fig10, "Fig11": plot_fig11,
    "Fig12": lambda d: plot_trajectory(d, "Locked summer window"), "Fig13": plot_fig13,
    "Fig14": plot_fig14, "Fig15": plot_fig15, "Fig16": plot_fig16, "Fig17": plot_fig17,
    "FigE01": plot_eda, "FigE02": plot_eda, "FigE03": plot_eda, "FigE04": plot_eda, "FigE05": plot_eda,
    "FigE06": lambda d: plot_setting_matrix(d, "GLOBAL_COMMON information-setting matrix"),
    "FigE07": lambda d: plot_setting_matrix(d, "MARKET_VALID information-setting sensitivity"),
    "FigE08": lambda d: plot_trajectory(d, "Locked winter window"),
    "FigE09": lambda d: plot_trajectory(d, "Locked spring window"),
    "FigE10": plot_e10, "FigE11": plot_e11, "FigE12": plot_e12,
    "FigE13": plot_e13, "FigE14": plot_e14, "FigE15": plot_e15,
}


META = {
"Fig05": ("How heterogeneous are the five market price structures and tail supports?", "half-distributions, aligned Cleveland dots, an ACF dumbbell, and support lollipops",
"Fig. 5. Five-market price structure and upper-tail support. (a) Full-series price distributions after centering by each market's training median and scaling by its training IQR. (b) Frozen exploratory market fingerprints; the two dispersion ratios use the full-series IQR and are not forecast-error normalizations. (c) Lag-24 (open) and lag-168 (filled) price autocorrelations. (d) Held-out P95 event support on the S1 COMMON_MASK; marker area encodes the training P95 threshold divided by the training IQR, and the dashed line marks the prespecified ten-event support reference. Estimates below that line are descriptive."),
"Fig06": ("How large is the full-pipeline gain and the incremental TSQR gain?", "unconnected Cleveland ranking and 168-h effect forests",
f"Fig. 6. Cross-market central-forecast performance under S1. (a) MAE normalized by each market's training IQR for Persistence, Direct QR, RQR, SQR, and TSQR on the COMMON_MASK (N = {COMMON_N:,} per market); model categories are not connected. (b-d) TSQR improvements over Persistence MAE, SQR MAE, and SQR mean pinball loss, respectively. Points and intervals are paired 168-h moving-block-bootstrap estimates and 95% confidence intervals; positive values favor TSQR."),
"Fig07": ("At which stage does central-forecast improvement arise in each market?", "matched market transition bars plus median/IQR synthesis",
"Fig. 7. Five-market module-attribution atlas under S1 and the COMMON_MASK. (a-e) MAE reductions at the Direct QR-to-RQR, RQR-to-SQR, and SQR-to-TSQR transitions, normalized by the training IQR; positive bars indicate lower MAE and negative bars indicate deterioration. (f) Cross-market median, IQR, and individual market values. The predefined stage differences are descriptive ablations and do not by themselves establish causal feature importance."),
"Fig08": ("Does W60 RCQR improve marginal reliability and interval quality, and at what width cost?", "four aligned paired dumbbells",
f"Fig. 8. Marginal interval calibration under S1 on the COMMON_MASK (N = {COMMON_N:,} per market). Raw TSQR intervals (open) are paired with W60 RCQR intervals (filled) for (a) PICP80, (b) absolute coverage gap, (c) interval score normalized by the training IQR, and (d) interval width normalized by the training IQR. The dashed line in (a) marks nominal 0.80 coverage. Lower values are preferable in (b-d), although width is reported as the sharpness cost of calibration; these panels are descriptive paired estimates."),
"Fig09": ("Is the frozen W60 choice broadly competitive across markets?", "same-type reliability-sharpness window atlases",
"Fig. 9. Five-market RCQR history-window sensitivity under S1 on the COMMON_MASK. (a-e) Reliability-sharpness coordinates for raw TSQR and RCQR with 7, 14, 30, and 60 complete-day histories; x is interval width divided by the training IQR and y is absolute coverage gap. Straight guides join only the four ordered RCQR windows. (f) Cross-market medians and IQRs. W60 remains the frozen primary setting; the complete metric and 24-h inference sensitivity appears in Fig. E10."),
"Fig10": ("What changes when archived day-ahead forecasts augment the strict baseline?", "three aligned S1-to-S2_DA paired dumbbells",
f"Fig. 10. Information-availability effects on the GLOBAL_COMMON mask (N = {COMMON_N:,} per market-setting cell). S1 (open) is paired with S2_DA (filled), which adds archived day-ahead system forecasts, for (a) TSQR MAE divided by the S1 training IQR, (b) raw absolute coverage gap, and (c) W60 RCQR interval score divided by the S1 training IQR. Lower values are preferable. S2_LEGACY, S3 ex-post, and MARKET_VALID sensitivities are restricted to Figs. E6-E7."),
"Fig11": ("How stable are TSQR and RCQR effects across calendar slices?", "two annotated calendar heatmaps",
"Fig. 11. Calendar-slice robustness under S1 on the COMMON_MASK. (a) TSQR MAE improvement over SQR by market and held-out year, normalized by the training IQR. (b) W60 RCQR interval-score reduction relative to raw TSQR by market and season, normalized by the training IQR. Positive values favor the proposed component. Cell values are descriptive slice estimates; rolling-origin fits and block-length sensitivity are shown in Fig. E15."),
"Fig12": ("How do synchronized outputs manifest over one locked held-out calendar window?", "five exact synchronized trajectory panels",
"Fig. 12. Synchronized five-market trajectories for the locked summer held-out window under S1. Panels (a-e) show observed prices, the TSQR median, the raw 80% interval, and the W60 RCQR 80% interval on the common calendar window; panel (f) defines the shared encoding. Every hourly value is plotted without smoothing, filtering, or interpolation. Market-specific vertical scales are used because absolute price levels differ. The panels are descriptive; winter and spring windows appear in Figs. E8-E9."),
"Fig13": ("Does marginal RCQR remain useful as negative-price persistence increases?", "matched conditional coverage and interval-score panels",
"Fig. 13. Negative-price conditional performance under S1 on the COMMON_MASK. Columns denote DE-LU, DK1, BE, ES, and FR. The top row compares raw and W60 RCQR PICP80 for all negative-price hours and nested runs lasting at least 3 h (N3) or 6 h (N6); the dashed line marks 0.80. The bottom row reports raw-minus-RCQR interval-score reduction divided by the training IQR, so positive values favor RCQR. Support is annotated. Nested regimes are descriptive, are not independent samples, and do not imply state-conditional coverage guarantees."),
"Fig14": ("How quickly does central forecast error escalate through the frozen upper-tail thresholds?", "five ordered threshold panels plus a synthesis panel",
"Fig. 14. Upper-tail TSQR error escalation under S1 on the COMMON_MASK. Panels (a-e) show MAE divided by the training IQR at available training-defined tail thresholds; marker area encodes held-out support and points with fewer than ten events are open and faded. The frozen central-error table contains P90, P95, P97.5, and P99 but no P92.5 estimate; its tick is retained as an explicit gap and no value is imputed. Straight guides join only consecutive available levels, and no PCHIP or data smoothing is used. Panel (f) shows cross-market medians and IQRs among available estimates."),
"Fig15": ("Does XRM add P95 ranking information beyond TSQR-derived signals after support is considered?", "five unconnected lollipop rankings plus an effect forest",
"Fig. 15. Five-market P95 XRM ranking atlas under S1 on the COMMON_MASK. Panels (a-e) compare prevalence, TSQR q0.50, TSQR q0.90, and XRM AUPRC using unconnected lollipops; titles report held-out P95 support. Panel (f) gives the paired 168-h moving-block-bootstrap XRM-minus-q0.90 AUPRC effect and 95% confidence interval. ES and FR each contain one P95 event and are open, faded, and descriptive only. No market-specific operating threshold is inferred from these results."),
"Fig16": ("Which frozen input families does the workflow depend on, and what is the online burden?", "five matched outage-effect panels plus a unit-aligned online-cost panel",
"Fig. 16. Operational input robustness and online computational profile. Panels (a-e) show the S1 COMMON_MASK change in MAE after predefined feature-family outages, divided by the training IQR; positive values indicate deterioration but do not establish causal importance. Panel (f) shows frozen online timing for 24-product forecast inference, XRM scoring, the RCQR daily update, and model loading after conversion to milliseconds. Training time and complete resource diagnostics are reported in Fig. E14."),
"Fig17": ("Which MERIF objectives show consistent cross-market effects and which remain heterogeneous?", "five independent effect mini-axes",
"Fig. 17. Integrated cross-market effect synthesis under S1 and the COMMON_MASK. Independent mini-axes show (a) TSQR relative MAE improvement over Persistence, (b) TSQR relative MAE improvement over SQR, (c) W60 RCQR absolute coverage-gap reduction, (d) W60 RCQR interval-score reduction divided by the training IQR, and (e) XRM-minus-q0.90 P95 AUPRC. Positive values favor the proposed component. Each axis shows the five market estimates plus the cross-market median and IQR. ES and FR XRM points each rely on one event and are open, faded, and descriptive only."),
}


for i, market in enumerate(MARKETS, start=1):
    META[f"FigE{i:02d}"] = (f"What are the detailed exploratory price characteristics of {market}?", "identical six-panel market EDA template",
        f"Fig. E{i}. Detailed exploratory price analysis for {market}. Panels show (a) the standardized price-duration curve, (b) monthly and (c) hourly median and interquartile profiles, (d) monthly negative-price and above-training-P95 shares, (e) the hourly price autocorrelation through 336 h, and (f) the density of rolling seven-day volatility divided by the training IQR. Ordered temporal profiles use straight guides; these full-series diagnostics are descriptive and are not forecast evaluation results.")

META.update({
"FigE06": ("How do all four information settings compare on GLOBAL_COMMON?", "six aligned information-setting heatmaps", f"Fig. E6. Full information-setting comparison on GLOBAL_COMMON (N = {COMMON_N:,} per market-setting cell). Heatmaps report normalized central errors, raw and RCQR coverage gaps, normalized RCQR interval score, and P95 XRM AUPRC for S1, S2_LEGACY, S2_DA, and S3. S3 uses realized target-hour system variables and is explicitly ex-post; it is not an operational setting."),
"FigE07": ("How sensitive are setting comparisons to MARKET_VALID masks?", "six aligned information-setting heatmaps", "Fig. E7. MARKET_VALID sensitivity for the four information settings. Metrics and encoding match Fig. E6, but each market-setting cell uses its own valid mask. These estimates are supplementary and are not mixed with the paired GLOBAL_COMMON comparison; S3 remains ex-post."),
"FigE08": ("How do synchronized outputs appear in the locked winter window?", "five exact synchronized trajectory panels", "Fig. E8. Synchronized five-market trajectories for the locked winter held-out window. Exact observed prices, TSQR medians, raw 80% intervals, and W60 RCQR 80% intervals are plotted without smoothing on market-specific vertical scales. The panels are descriptive."),
"FigE09": ("How do synchronized outputs appear in the locked spring window?", "five exact synchronized trajectory panels", "Fig. E9. Synchronized five-market trajectories for the locked spring held-out window. Exact observed prices, TSQR medians, raw 80% intervals, and W60 RCQR 80% intervals are plotted without smoothing on market-specific vertical scales. The panels are descriptive."),
"FigE10": ("How do all RCQR windows and inference block lengths compare?", "ordered window profiles and block-specific effect summaries", "Fig. E10. Complete RCQR window and block-length sensitivity under S1 on the COMMON_MASK. Panels (a-d) report PICP80, absolute coverage gap, normalized width, and normalized interval score for 7, 14, 30, and 60 complete-day histories; straight lines join only ordered windows. Panels (e-f) show 24-h and 168-h moving-block-bootstrap effects with positive values favoring RCQR. W60 and 168 h remain the frozen primary specifications."),
"FigE11": ("How do XRM ranking and support change from P90 to P99?", "five ordered market ranking panels plus support", "Fig. E11. Full XRM support and ranking sensitivity under S1 on the COMMON_MASK. Panels (a-e) show prevalence and AUPRC for TSQR q0.50, TSQR q0.90, and XRM across P90-P99. Faded backgrounds mark levels with fewer than ten held-out events. Panel (f) reports held-out support on a log scale. Ordered straight guides are visual aids; low-support estimates are descriptive."),
"FigE12": ("How do fixed review-capacity summaries vary from 0.5% to 5%?", "five ordered budget panels plus median/IQR synthesis", "Fig. E12. P95 recall for XRM and TSQR q0.90 at fixed 0.5%, 1%, 2%, and 5% review budgets on the S1 COMMON_MASK. Panels (a-e) are market-specific and panel (f) shows the cross-market XRM median and IQR. Lines join only ordered budget levels. These are post-scoring capacity summaries, not alarm thresholds or deployment policies; ES and FR remain extremely low-support."),
"FigE13": ("What are the complete feature-outage diagnostics?", "four aligned annotated outage heatmaps", "Fig. E13. Complete predefined S1 feature-outage diagnostics on the COMMON_MASK. Heatmaps report changes in normalized MAE, normalized pinball loss, normalized W60 RCQR interval score, and P95 XRM AUPRC. Positive and negative signs retain their metric-specific meanings. The outages are diagnostic perturbations and do not establish causal feature importance."),
"FigE14": ("What are the complete computational and resource diagnostics?", "unit-specific market dot panels", "Fig. E14. Frozen computational and resource diagnostics by market. Panels report one primary fit duration, 24-product inference, XRM scoring, RCQR daily update, model loading, peak memory, and serialized model size in their native display units. Online timings use the frozen formal repeats; the single primary training runs are not interpreted as intrinsic market-complexity differences."),
"FigE15": ("Do rolling-origin and bootstrap block sensitivities preserve the main conclusions?", "five ordered rolling-origin panels plus a paired block-sensitivity forest", "Fig. E15. Rolling-origin and bootstrap sensitivity under S1. Panels (a-e) report fold-specific TSQR-over-SQR MAE improvement and raw-over-RCQR interval-score reduction, normalized by the training IQR. Panel (f) compares paired 24-h (open) and 168-h (filled) moving-block-bootstrap TSQR-minus-SQR MAE effects. Negative values in panel (f) favor TSQR; the 168-h specification remains primary."),
})


def materialize_all() -> None:
    for code, builder in BUILDERS.items():
        data = builder()
        required = ["panel","market","metric","setting","mask","value","source_file","source_row_key","display_transformation","support_N","inferential_status"]
        for col in required:
            if col not in data: data[col] = np.nan
        write_table(code, data)
        create_wrapper(code)
        question, grammar, caption = META[code]
        write_caption_qa(code, caption, question, grammar, data)


def update_export_qa(code: str) -> None:
    folder=OUT/code; png=folder/f"{code.upper()}.png"; svg=folder/f"{code.upper()}.svg"; pdf=folder/f"{code.upper()}.pdf"
    with Image.open(png) as im: dims=im.size
    svgtext=svg.read_text(encoding='utf-8',errors='ignore')
    panel_count=len(list((folder/'panels').glob('*.pdf')))
    with qa_path(code).open('a',encoding='utf-8') as f:
        f.write(f"- Final PNG/PDF/SVG present: {'PASS' if png.exists() and pdf.exists() and svg.exists() else 'FAIL'}.\n")
        f.write(f"- Combined PNG dimensions: {dims[0]} × {dims[1]} px.\n")
        f.write(f"- Editable SVG text retained: {'PASS' if '<text' in svgtext else 'FAIL'}.\n")
        f.write(f"- Times New Roman requested in SVG: {'PASS' if 'Times New Roman' in svgtext else 'FAIL'}.\n")
        f.write(f"- Individual panel PDF count: {panel_count}.\n")


def render_one(code: str, stage: str = "final") -> None:
    configure()
    if not (OUT/code/f"{code.upper()}_SOURCE_TABLE.csv").exists():
        data=BUILDERS[code](); write_table(code,data); create_wrapper(code)
        question,grammar,caption=META[code]; write_caption_qa(code,caption,question,grammar,data)
    d=read_table(code); fig,groups,height=PLOTTERS[code](d); export_figure(code,fig,groups,stage,height)
    if stage=='final': update_export_qa(code)


def contact_sheet() -> None:
    from matplotlib.backends.backend_pdf import PdfPages
    codes=[f"Fig{i:02d}" for i in range(5,18)]
    with PdfPages(OUT/'FIGURE_ARCHITECTURE_CONTACT_SHEET_v0.pdf') as pdf:
        for start in range(0,len(codes),4):
            fig,axs=plt.subplots(2,2,figsize=(8.27,11.69)); axlist=list(np.atleast_1d(axs).flat)
            page_codes=codes[start:start+4]
            for ax,code in zip(axlist,page_codes):
                with Image.open(OUT/code/f"{code.upper()}_LAYOUT_v0.png") as im: arr=np.asarray(im.convert('RGB'))
                ax.imshow(arr); ax.set_title(code.replace('Fig','Fig. '),loc='left',fontsize=10,fontweight='bold'); ax.axis('off')
            for ax in axlist[len(page_codes):]: ax.axis('off')
            fig.tight_layout(pad=.8); pdf.savefig(fig,bbox_inches='tight'); plt.close(fig)


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--stage',choices=['materialize','layout','final','all'],default='all')
    ap.add_argument('--figure')
    ap.add_argument(
        '--rematerialize',
        action='store_true',
        help='Rebuild source tables from the original private workspace (not needed for this frozen public package).',
    )
    args=ap.parse_args()
    codes=[args.figure] if args.figure else list(BUILDERS)
    if args.rematerialize:
        materialize_all()
    else:
        missing=[code for code in codes if not (OUT/code/f"{code.upper()}_SOURCE_TABLE.csv").exists()]
        if missing:
            raise SystemExit(
                'Frozen source tables are missing for: '
                + ', '.join(missing)
                + '. Restore the packaged tables; --rematerialize requires the original private workspace.'
            )
    if args.stage == 'materialize':
        print(json.dumps({'stage':args.stage,'figures':codes,'rematerialized':args.rematerialize,'frozen_data_only':True,'new_model_fitting':False},ensure_ascii=False))
        return
    if args.stage in ['layout','all']:
        for code in codes: print(f"Stage A layout: {code}"); render_one(code,'layout')
        if not args.figure: contact_sheet()
    if args.stage in ['final','all']:
        for code in codes: print(f"Stage B final: {code}"); render_one(code,'final')
    print(json.dumps({'stage':args.stage,'figures':codes,'frozen_data_only':True,'new_model_fitting':False},ensure_ascii=False))


if __name__=='__main__':
    main()
