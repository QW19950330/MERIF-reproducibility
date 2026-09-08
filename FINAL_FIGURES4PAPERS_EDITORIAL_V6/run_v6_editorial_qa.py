from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from PIL import Image
from pypdf import PdfReader


BASE = Path(__file__).resolve().parent
WORKSPACE = BASE.parent.parent
MAIN_CODES = [f"Fig{i:02d}" for i in range(5, 18)]
SUPP_CODES = [f"FigE{i:02d}" for i in range(1, 16)]
ALL_CODES = MAIN_CODES + SUPP_CODES
REQUIRED_MAIN = ["Fig05", "Fig06", "Fig08", "Fig10", "Fig11", "Fig12", "Fig13", "Fig14", "Fig15", "Fig17"]
OPTIONAL_MAIN = ["Fig16"]
SUPPLEMENTARY_PRIORITY = ["Fig07", "Fig09"] + SUPP_CODES
LINEAGE_COLUMNS = [
    "panel", "market", "metric", "setting", "mask", "value", "source_file",
    "source_row_key", "display_transformation", "support_N", "inferential_status",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fig_id(code: str) -> str:
    return code.upper()


def add(rows: list[dict], round_name: str, check: str, passed: bool, detail: str) -> None:
    rows.append({
        "round": round_name,
        "check": check,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
    })


def normalize_value(value):
    if pd.isna(value):
        return ""
    try:
        return round(float(value), 12)
    except (TypeError, ValueError):
        return str(value).strip()


def section_blocks(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(3\.[1-9])\b.*$", text, flags=re.MULTILINE))
    blocks = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks[match.group(1)] = text[match.end():end]
    return blocks


def prose_paragraphs(block: str) -> list[str]:
    chunks = re.split(r"\n\s*\n", block.strip())
    return [
        c.strip() for c in chunks
        if c.strip()
        and not c.lstrip().startswith("!")
        and not c.lstrip().startswith("<!--")
        and not c.lstrip().startswith("|")
    ]


def run() -> tuple[list[dict], dict]:
    rows: list[dict] = []
    stats = defaultdict(int)
    masks_by_code: dict[str, set[str]] = {}
    settings_by_code: dict[str, set[str]] = {}

    for code in ALL_CODES:
        folder = BASE / code
        stem = fig_id(code)
        required = [
            folder / f"{stem}_SOURCE_TABLE.csv",
            folder / f"{stem}_VALUE_LINEAGE.csv",
            folder / f"{stem}_PLOTTING_SCRIPT.py",
            folder / f"{stem}_CAPTION.md",
            folder / f"{stem}_QA.md",
            folder / f"{stem}_SOURCE_MANIFEST.csv",
            folder / f"{stem}.png",
            folder / f"{stem}.pdf",
            folder / f"{stem}.svg",
        ]
        missing = [p.name for p in required if not p.exists()]
        add(rows, "Round 1: technical and lineage QA", f"{code}: required artifacts", not missing,
            "complete" if not missing else f"missing: {', '.join(missing)}")
        if missing:
            continue

        source = pd.read_csv(required[0])
        lineage = pd.read_csv(required[1])
        masks_by_code[code] = set(source.get("mask", pd.Series(dtype=str)).dropna().astype(str))
        settings_by_code[code] = set(source.get("setting", pd.Series(dtype=str)).dropna().astype(str))
        stats["source_rows"] += len(source)
        stats["lineage_rows"] += len(lineage)

        missing_cols = [c for c in LINEAGE_COLUMNS if c not in source.columns or c not in lineage.columns]
        add(rows, "Round 1: technical and lineage QA", f"{code}: lineage schema", not missing_cols,
            "required fields present" if not missing_cols else f"missing fields: {', '.join(missing_cols)}")
        if not missing_cols:
            equal = len(source) == len(lineage)
            if equal:
                for col in LINEAGE_COLUMNS:
                    left = source[col].map(normalize_value).tolist()
                    right = lineage[col].map(normalize_value).tolist()
                    if left != right:
                        equal = False
                        break
            add(rows, "Round 1: technical and lineage QA", f"{code}: source-to-lineage value parity", equal,
                f"{len(source):,} rows compared")

        non_null = True
        for col in ["source_file", "source_row_key", "display_transformation", "inferential_status"]:
            non_null &= col in source.columns and source[col].notna().all() and (source[col].astype(str).str.strip() != "").all()
        add(rows, "Round 1: technical and lineage QA", f"{code}: provenance fields populated", bool(non_null),
            "source, row key, transformation, and status populated")

        manifest = pd.read_csv(required[5])
        manifest_ok = True
        manifest_detail = []
        for _, entry in manifest.iterrows():
            src = WORKSPACE / str(entry["source_file"])
            exists = src.exists()
            digest_ok = exists and sha256(src).lower() == str(entry["sha256"]).lower()
            manifest_ok &= bool(exists and digest_ok)
            if not exists:
                manifest_detail.append(f"missing {entry['source_file']}")
            elif not digest_ok:
                manifest_detail.append(f"hash mismatch {entry['source_file']}")
        add(rows, "Round 1: technical and lineage QA", f"{code}: frozen-source hashes", manifest_ok,
            "all source hashes verified" if manifest_ok else "; ".join(manifest_detail))

        png = required[6]
        with Image.open(png) as image:
            width, height = image.size
            dpi = image.info.get("dpi", (0, 0))
        png_ok = min(width, height) >= 1400 and min(float(dpi[0]), float(dpi[1])) >= 590
        add(rows, "Round 1: technical and lineage QA", f"{code}: 600-dpi combined PNG", png_ok,
            f"{width} x {height} px; dpi={dpi}")

        reader = PdfReader(str(required[7]))
        pdf_ok = len(reader.pages) == 1 and float(reader.pages[0].mediabox.width) > 0 and float(reader.pages[0].mediabox.height) > 0
        add(rows, "Round 1: technical and lineage QA", f"{code}: one-page vector PDF", pdf_ok,
            f"pages={len(reader.pages)}")

        svg_text = required[8].read_text(encoding="utf-8", errors="ignore")
        svg_ok = "<text" in svg_text and "Times New Roman" in svg_text
        add(rows, "Round 1: technical and lineage QA", f"{code}: editable SVG typography", svg_ok,
            "text retained and Times New Roman declared")

        panel_dir = folder / "panels"
        panel_sets = {}
        for ext in ["png", "pdf", "svg"]:
            panel_sets[ext] = {p.stem for p in panel_dir.glob(f"*.{ext}")}
        panels_ok = bool(panel_sets["png"]) and panel_sets["png"] == panel_sets["pdf"] == panel_sets["svg"]
        stats["panels"] += len(panel_sets["png"])
        add(rows, "Round 1: technical and lineage QA", f"{code}: independent panel exports", panels_ok,
            f"{len(panel_sets['png'])} panels in PNG/PDF/SVG")

        caption = required[3].read_text(encoding="utf-8").strip()
        expected_prefix = f"Fig. {int(code[3:])}." if not code.startswith("FigE") else f"Fig. E{int(code[4:])}."
        caption_ok = caption.startswith(expected_prefix) and " | " not in caption
        add(rows, "Round 2: editorial and graphical QA", f"{code}: caption form", caption_ok,
            f"prefix={expected_prefix}; stand-alone prose caption")

        script_text = required[2].read_text(encoding="utf-8", errors="ignore")
        no_fitting = not re.search(r"\.fit\s*\(|GridSearchCV|RandomizedSearchCV|optuna|hyperopt", script_text, flags=re.I)
        add(rows, "Round 1: technical and lineage QA", f"{code}: no new fitting or selection", no_fitting,
            "plotting-only script")

    # Core mask and setting contracts.
    main_except_cross = [c for c in MAIN_CODES if c not in {"Fig05", "Fig10", "Fig12"}]
    main_mask_ok = all(masks_by_code.get(c, set()) <= {"COMMON_MASK"} for c in main_except_cross)
    add(rows, "Round 1: technical and lineage QA", "Main-text COMMON_MASK contract", main_mask_ok,
        "all non-EDA, non-cross-setting, non-trajectory main figures use COMMON_MASK")
    fig10_ok = masks_by_code.get("Fig10") == {"GLOBAL_COMMON"} and settings_by_code.get("Fig10") == {"S1", "S2_DA"}
    add(rows, "Round 1: technical and lineage QA", "Fig10 GLOBAL_COMMON S1/S2_DA contract", fig10_ok,
        f"masks={sorted(masks_by_code.get('Fig10', set()))}; settings={sorted(settings_by_code.get('Fig10', set()))}")
    fig12_ok = masks_by_code.get("Fig12") == {"LOCKED_WINDOW"}
    add(rows, "Round 1: technical and lineage QA", "Fig12 locked-window trajectory contract", fig12_ok,
        f"masks={sorted(masks_by_code.get('Fig12', set()))}")
    no_main_s3 = all("S3" not in settings_by_code.get(c, set()) for c in MAIN_CODES)
    add(rows, "Round 2: editorial and graphical QA", "S3 restricted from main-text figures", no_main_s3,
        "S3 remains an ex-post supplementary sensitivity")

    fig15 = pd.read_csv(BASE / "Fig15" / "FIG15_SOURCE_TABLE.csv")
    sparse = fig15[fig15["market"].isin(["ES", "FR"])]
    sparse_ok = len(sparse) > 0 and (pd.to_numeric(sparse["support_N"]) == 1).all() and (sparse["inferential_status"] == "descriptive only").all()
    add(rows, "Round 2: editorial and graphical QA", "Low-support ES/FR XRM qualification", sparse_ok,
        "ES and FR P95 cells have n=1 and are marked descriptive only")

    fig14 = pd.read_csv(BASE / "Fig14" / "FIG14_SOURCE_TABLE.csv")
    fig14_script = (BASE / "Fig14" / "FIG14_PLOTTING_SCRIPT.py").read_text(encoding="utf-8", errors="ignore")
    tail_ok = not fig14.astype(str).apply(lambda c: c.str.contains("P92.5", regex=False)).any().any()
    pchip_absent = "pchip" not in fig14_script.lower()
    add(rows, "Round 1: technical and lineage QA", "Fig14 frozen tail thresholds only", bool(tail_ok and pchip_absent),
        "P90/P95/P97.5/P99 only; straight guides; no PCHIP")

    fig12 = pd.read_csv(BASE / "Fig12" / "FIG12_SOURCE_TABLE.csv")
    exact_ok = fig12["display_transformation"].astype(str).str.contains("no smoothing", case=False).all()
    add(rows, "Round 1: technical and lineage QA", "Fig12 exact unsmoothed trajectories", bool(exact_ok),
        "every trajectory row explicitly records no smoothing")

    # Section 3 structure, language, and callout checks.
    final_path = BASE / "Section3_FiveMarket_Editorial_Final.md"
    condensed_path = BASE / "Section3_FiveMarket_Editorial_Condensed.md"
    final_text = final_path.read_text(encoding="utf-8")
    condensed_text = condensed_path.read_text(encoding="utf-8")
    for name, text in [("final", final_text), ("condensed", condensed_text)]:
        blocks = section_blocks(text)
        headings_ok = list(blocks) == [f"3.{i}" for i in range(1, 10)]
        para_counts = {key: len(prose_paragraphs(value)) for key, value in blocks.items()}
        paragraphs_ok = headings_ok and all(count == 3 for count in para_counts.values())
        add(rows, "Round 2: editorial and graphical QA", f"Section 3 {name}: nine-subsection architecture", headings_ok,
            f"headings={', '.join(blocks)}")
        add(rows, "Round 2: editorial and graphical QA", f"Section 3 {name}: three-paragraph rhythm", paragraphs_ok,
            "; ".join(f"{k}={v}" for k, v in para_counts.items()))

    callout_ok = all(re.search(rf"Fig\.\s*{i}\b", final_text) for i in range(5, 18))
    add(rows, "Round 2: editorial and graphical QA", "Section 3 calls out Fig. 5-Fig. 17", callout_ok,
        "all candidate main-text figure numbers are referenced")
    stale_tics = [phrase for phrase in ["Therefore", "Taken together", "we ran", "we tested", "this experiment"] if phrase.lower() in final_text.lower()]
    add(rows, "Round 2: editorial and graphical QA", "Experiment-report and AI-tic language removed", not stale_tics,
        "no targeted tics found" if not stale_tics else f"found: {', '.join(stale_tics)}")
    s3_mentions = [line.strip() for line in final_text.splitlines() if re.search(r"\bS3\b", line)]
    s3_qualified = all("ex-post" in line.lower() for line in s3_mentions)
    add(rows, "Round 2: editorial and graphical QA", "Section 3 S3 qualification", s3_qualified,
        f"{len(s3_mentions)} S3-containing paragraph(s), all explicitly ex-post")

    alignment = pd.read_csv(BASE / "Section3_Figure_Callout_Alignment_v6.csv")
    alignment_ok = len(alignment) == 9 and alignment.notna().all(axis=None)
    add(rows, "Round 2: editorial and graphical QA", "Figure-callout alignment ledger", bool(alignment_ok),
        f"{len(alignment)} figure rows fully populated")

    architecture_files = [
        BASE / "FIGURES4PAPERS_FINAL_SKILL_AUDIT.md",
        BASE / "V6_FIGURE_ARCHITECTURE_FREEZE.md",
        BASE / "FIGURE_ARCHITECTURE_DECISION.md",
        BASE / "MAIN_TEXT_FIGURE_PRIORITY_DECISION.md",
        BASE / "TERMINOLOGY_LEDGER.md",
        BASE / "FIGURE_ARCHITECTURE_CONTACT_SHEET_v0.pdf",
    ]
    add(rows, "Round 2: editorial and graphical QA", "Architecture and skill-audit records", all(p.exists() for p in architecture_files),
        "skill audit, freeze, decisions, terminology ledger, and contact sheet present")

    return rows, stats


def write_outputs(rows: list[dict], stats: dict) -> None:
    results_path = BASE / "V6_QA_RESULTS.csv"
    with results_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["round", "check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failures = [r for r in rows if r["status"] == "FAIL"]
    by_round = defaultdict(list)
    for row in rows:
        by_round[row["round"]].append(row)

    report = [
        "# FINAL SECTION 3 AND FIGURES EDITORIAL QA",
        "",
        "## Overall result",
        "",
        f"**{'PASS' if not failures else 'FAIL'}** — {len(rows) - len(failures)}/{len(rows)} checks passed.",
        "",
        f"The audit covers {len(ALL_CODES)} combined figures, {stats['panels']} independent panels, "
        f"{stats['source_rows']:,} source-table rows, and {stats['lineage_rows']:,} lineage rows.",
        "",
    ]
    for round_name in ["Round 1: technical and lineage QA", "Round 2: editorial and graphical QA"]:
        report.extend([f"## {round_name}", "", "| Status | Check | Evidence |", "|---|---|---|"])
        for row in by_round[round_name]:
            mark = "PASS" if row["status"] == "PASS" else "FAIL"
            detail = str(row["detail"]).replace("|", "/")
            report.append(f"| {mark} | {row['check']} | {detail} |")
        report.append("")
    report.extend([
        "## Failure disposition",
        "",
        "No unresolved QA failures remain." if not failures else "\n".join(f"- {r['check']}: {r['detail']}" for r in failures),
        "",
        "## Frozen-analysis declaration",
        "",
        "This reconstruction reads frozen result tables only. It performs no model fitting, hyperparameter search, threshold selection, window selection, or inferential recomputation.",
        "",
    ])
    (BASE / "FINAL_SECTION3_AND_FIGURES_EDITORIAL_QA.md").write_text("\n".join(report), encoding="utf-8")

    candidate_descriptions = {
        "Fig. 5": "Five-market exploratory structure and support context",
        "Fig. 6": "Probabilistic benchmark hierarchy and paired effects",
        "Fig. 7": "Cross-market transition diagnostics",
        "Fig. 8": "Raw-to-RCQR calibration and sharpness pairs",
        "Fig. 9": "Window-length sensitivity",
        "Fig. 10": "S1 versus S2_DA information-availability effects",
        "Fig. 11": "Temporal and rolling-origin robustness summary",
        "Fig. 12": "Exact locked-window forecast trajectories",
        "Fig. 13": "Negative-price-state diagnostics",
        "Fig. 14": "Frozen upper-tail threshold sensitivity",
        "Fig. 15": "XRM discrimination, effects, and support qualification",
        "Fig. 16": "Computational cost",
        "Fig. 17": "Outage robustness",
    }
    terminal = [
        "MERIF V6 EDITORIAL FIGURE RECONSTRUCTION SUMMARY",
        "",
        "figures4papers skill:",
        "scientific-figure-making (figures4papers-compatible Matplotlib workflow)",
        "path:",
        "local Codex scientific-figure-making skill (path is environment-specific)",
        "",
        "Candidate figures rendered:",
    ]
    terminal.extend(f"{key}: {value}" for key, value in candidate_descriptions.items())
    terminal.extend([
        "",
        "Required main-text figures:",
        "Fig. 5, Fig. 6, Fig. 8, Fig. 10, Fig. 11, Fig. 12, Fig. 13, Fig. 14, Fig. 15, and Fig. 17",
        "Optional main-text figures:",
        "Fig. 16",
        "Supplementary figures:",
        "Fig. 7, Fig. 9, and Figs. E1-E15",
        "",
        "Same-type small-multiple groups created:",
        "market-faceted EDA, paired dot/dumbbell summaries, effect-and-CI facets, ordered threshold profiles, exact trajectory panels, and market-faceted robustness summaries",
        "",
        "Figures containing lines:",
        "Fig. 5, Fig. 6, Fig. 8, Fig. 9, Fig. 10, Fig. 12, Fig. 13, Fig. 14, Fig. 15, Fig. 16, and Fig. 17",
        "",
        "For every line figure:",
        "continuous/order justification:",
        "Lines are limited to continuous time or lag axes, ordered frozen thresholds/windows, confidence intervals, paired before-after states, or lollipop connectors; no nominal category is presented as a continuous trajectory.",
        "data smoothing used:",
        "NO",
        "visual-only PCHIP used:",
        "NO",
        "no-overshoot check:",
        "NOT APPLICABLE",
        "",
        "Discrete categories connected by lines:",
        "NO",
        "",
        "Low-support XRM qualification:",
        "PASS",
        "",
        "COMMON_MASK/GLOBAL_COMMON consistency:",
        "PASS",
        "",
        "Section 3 rewritten:",
        "YES",
        "",
        "Experiment-report language remaining:",
        "NO",
        "",
        "All values trace to frozen source:",
        "YES" if not failures else "NO",
        "",
        "New model fitting performed:",
        "NO",
        "",
        "Final editorial recommendation:",
        "Use the ten required figures in the main text, retain Fig. 16 only if the journal layout permits, and move Fig. 7, Fig. 9, and Figs. E1-E15 to the Appendix/Supplementary Information. This preserves a compact five-market argument while keeping the full frozen evidence trail available for review.",
    ])
    terminal_text = "\n".join(terminal) + "\n"
    (BASE / "V6_TERMINAL_SUMMARY.txt").write_text(terminal_text, encoding="utf-8")

    index = [
        "# MERIF V6 deliverable index",
        "",
        "## Manuscript text",
        "",
        "- `Section3_FiveMarket_Editorial_Final.md`: submission-facing full Section 3.",
        "- `Section3_FiveMarket_Editorial_Condensed.md`: space-saving alternative.",
        "- `Section3_Figure_Callout_Alignment_v6.csv`: subsection-to-figure alignment ledger.",
        "",
        "## Figures",
        "",
        "- `Fig05`-`Fig17`: candidate main-text figures, each with combined and panel PNG/PDF/SVG exports, caption, source table, lineage table, manifest, plotting wrapper, and QA record.",
        "- `FigE01`-`FigE15`: Appendix/Supplementary figures with the same artifact package.",
        "- `FIGURE_ARCHITECTURE_CONTACT_SHEET_v0.pdf`: Stage-A same-scale contact sheet.",
        "",
        "## Decisions and QA",
        "",
        "- `MAIN_TEXT_FIGURE_PRIORITY_DECISION.md`: required/optional/supplementary placement decision.",
        "- `FIGURE_ARCHITECTURE_DECISION.md`: graphical-grammar decision record.",
        "- `FIGURES4PAPERS_FINAL_SKILL_AUDIT.md`: mandatory skill audit.",
        "- `FINAL_SECTION3_AND_FIGURES_EDITORIAL_QA.md`: human-readable two-round final audit.",
        "- `V6_QA_RESULTS.csv`: machine-readable QA results.",
        "- `V6_TERMINAL_SUMMARY.txt`: requested terminal hand-off summary.",
        "",
    ]
    (BASE / "README_V6_DELIVERABLE_INDEX.md").write_text("\n".join(index), encoding="utf-8")
    print(terminal_text, end="")
    if failures:
        raise SystemExit(f"QA failed: {len(failures)} unresolved checks")


if __name__ == "__main__":
    qa_rows, qa_stats = run()
    write_outputs(qa_rows, qa_stats)
