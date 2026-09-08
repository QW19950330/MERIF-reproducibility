# Main-text table design

All CSVs in this directory are direct frozen exports. Tables should be typeset without color-dependent meaning and should retain market-level rows.

## Table 1 — Five-market data and market summary

Source: `Table_Main_1_Five_Market_Data.csv`. Report bidding zone, time zone, usable observations, common-test observations, training IQR, negative-price share, P95 test events, and memory/variability descriptors. Use compact units in headers and move full QA statistics to Supplementary Information.

## Table 2 — Five-market central forecasting summary

Source: `Table_Main_2_Five_Market_Central.csv`. Report Persistence, SQR, and TSQR MAE (and normalized MAE if space permits), plus TSQR relative improvement against both comparators. Direct QR and RQR belong in the attribution table/figure rather than the main benchmark block.

## Table 3 — Five-market interval calibration summary

Source: `Table_Main_3_Five_Market_RCQR.csv`. Pair raw and W60 RCQR PICP80, absolute coverage gap, interval score, and width. Preserve the width increase; never report calibration gain without sharpness cost.

## Table 4 — Five-market XRM summary

Source: `Table_Main_4_Five_Market_XRM.csv`. Report P95 event count, prevalence, q0.50/q0.90/XRM AUPRC, and fixed-budget monitoring where available. Mark ES/FR as descriptive and state that automatic validation-based operating points were unavailable.

## Table 5 — Five-market inference summary

Source: `Table_Main_5_Five_Market_Inference.csv`. Report paired 168-h moving-block effects and 95% intervals for TSQR central comparisons and RCQR calibration/score/width families. Preserve the effect sign convention in a footnote and include multiplicity status.

## Optional Table 6 — Computational cost and robustness

Source: `Table_Main_6_Five_Market_Cost.csv`. Report total fitting time and median latency for 24 products. The full raw timing distribution, feature outages, and Huber-weight diagnostics remain supplementary.
