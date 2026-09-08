# figures4papers final skill audit

- Resolved skill: `scientific-figure-making` (the installed exact scientific-publication Matplotlib figure skill and closest available implementation to figures4papers).
- Skill path: local Codex `scientific-figure-making` skill (environment-specific).
- SHA-256: `952300B4D0BD8FBD0C55AAA732A47A0ABB8E9707BC80965C8E70221EF13F0292`.
- Backend: Python with Matplotlib and the locally installed `pubfig` export layer.
- Scientific contract: frozen tables and predictions only; no model fitting, selection, threshold change, imputation, or value recovery from images.

## Figure grammar adopted

Each figure is organized around one scientific question and one dominant visual grammar. Repeated market analyses use aligned, equally sized small multiples. Discrete models, markets, settings, outages, and cost categories are not joined by lines. Lines are reserved for exact hourly trajectories and ordered parameter or tail levels. Original observations remain marked wherever an ordered guide is drawn.

## Typography and export rules adopted

- Times New Roman throughout.
- Pure white background; all four spines visible.
- No ticks or tick labels on the top and right spines.
- Shared market palette, marker vocabulary, line weights, and legend grammar.
- Black, square legend frames where legends are required.
- Final double-column dimensions, 600-dpi PNG, editable PDF, and editable SVG.
- Individual panel PNG/PDF/SVG exports in addition to each combined figure.
- SVG text retained as text (`svg.fonttype = none`) and PDF TrueType embedding requested (`pdf.fonttype = 42`).
- Exact trajectories use antialiasing and rounded caps/joins without smoothing.

## Source-data and QA rules adopted

- A materialized source table and element-level value-lineage table accompany every figure.
- Every lineage row identifies panel, market, metric, setting, mask, value, source file and key, display transformation, support, and inferential status.
- Plotting scripts contain no manually typed scientific results.
- Stage A uses low-resolution layouts and a same-scale contact sheet; Stage B is released only after visual architecture review.
- Technical QA covers source hashes, row counts, masks, settings, font, vector text, dimensions, and clipping.
- Scientific/editorial QA covers claim direction, low-support qualifications, grammar, smoothing, duplicated functions, and Section 3 callout alignment.
