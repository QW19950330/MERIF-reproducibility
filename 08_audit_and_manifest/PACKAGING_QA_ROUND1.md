# Packaging QA — Round 1: lineage, numerical tie-out, and structural completeness

Round 1 checks authoritative values, masks, support vectors, export triplets, plot-ready sources, tables, and subsection completeness.

| Check | Status | Evidence |
|---|---:|---|
| 20 market-setting authoritative rows | PASS | rows=20 |
| Common N is 15,311 throughout summary | PASS | unique=[15311] |
| All four information settings and five markets present | PASS | settings=['S1', 'S2_DA', 'S2_LEGACY', 'S3']; markets=['BE', 'DE-LU', 'DK1', 'ES', 'FR'] |
| S1 TSQR point estimate improves over Persistence in all five markets | PASS | range=3.086% to 12.823% |
| S1 TSQR point estimate improves over SQR in all five markets | PASS | range=0.911% to 2.481% |
| RCQR reduces absolute marginal coverage gap in all five markets | PASS | max final gap=0.004520 |
| RCQR reduces interval score in all five markets | PASS | all delta_interval_score < 0 |
| RCQR width cost is explicit in all five markets | PASS | width increase=15.819 to 25.148 |
| P95 support vector locked | PASS | events=[45, 42, 15, 1, 1] |
| No validation P95 events | PASS | events=[0, 0, 0, 0, 0] |
| Fig. 5 P95 counts tie to frozen fingerprint | PASS | P95=[45, 42, 15, 1, 1] |
| Fig. 5 P99 counts re-derived from frozen predictions | PASS | P99=[13, 11, 3, 0, 0] |
| Table 2 TSQR MAE ties to authoritative S1 summary | PASS | exact within floating tolerance |
| TSQR-vs-SQR 168-h intervals exclude zero in all five markets | PASS | supported=5/5 |
| Ten required package directories exist | PASS | present=10/10 |
| Fig. 5 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 5 editable SVG uses Times New Roman | PASS | Fig5_Five_Market_Characteristics.svg |
| Fig. 5 plot-ready source and QA exist | PASS | source+QA |
| Fig. 6 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 6 editable SVG uses Times New Roman | PASS | Fig6_Central_Forecasting.svg |
| Fig. 6 plot-ready source and QA exist | PASS | source+QA |
| Fig. 7 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 7 editable SVG uses Times New Roman | PASS | Fig7_RCQR_Calibration.svg |
| Fig. 7 plot-ready source and QA exist | PASS | source+QA |
| Fig. 8 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 8 editable SVG uses Times New Roman | PASS | Fig8_Information_Settings.svg |
| Fig. 8 plot-ready source and QA exist | PASS | source+QA |
| Fig. 9 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 9 editable SVG uses Times New Roman | PASS | Fig9_Temporal_Robustness_Trajectories.svg |
| Fig. 9 plot-ready source and QA exist | PASS | source+QA |
| Fig. 10 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 10 editable SVG uses Times New Roman | PASS | Fig10_Conditional_Regimes.svg |
| Fig. 10 plot-ready source and QA exist | PASS | source+QA |
| Fig. 11 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 11 editable SVG uses Times New Roman | PASS | Fig11_XRM_Support_Monitoring.svg |
| Fig. 11 plot-ready source and QA exist | PASS | source+QA |
| Fig. 12 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 12 editable SVG uses Times New Roman | PASS | Fig12_Attribution_Robustness_Cost.svg |
| Fig. 12 plot-ready source and QA exist | PASS | source+QA |
| Fig. 13 PNG/PDF/SVG triplet | PASS | png=1, pdf=1, svg=1 |
| Fig. 13 editable SVG uses Times New Roman | PASS | Fig13_Integrated_Portability_Synthesis.svg |
| Fig. 13 plot-ready source and QA exist | PASS | source+QA |
| Appendix EDA DE-LU complete | PASS | PNG/PDF/SVG/source/QA |
| Appendix EDA DK1 complete | PASS | PNG/PDF/SVG/source/QA |
| Appendix EDA BE complete | PASS | PNG/PDF/SVG/source/QA |
| Appendix EDA ES complete | PASS | PNG/PDF/SVG/source/QA |
| Appendix EDA FR complete | PASS | PNG/PDF/SVG/source/QA |
| Nine separate Section 3 subsection files | PASS | files=9 |
| Six main and eight supplementary CSV tables | PASS | main=6, supp=8 |

**Result: 49/49 checks passed.**
