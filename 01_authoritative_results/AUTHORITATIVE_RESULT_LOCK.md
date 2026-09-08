
# MERIF five-market authoritative result lock

Lock date (UTC): 2026-08-22T18:53:24.754475+00:00

## Scientific scope

The authoritative scope comprises DE-LU, DK1, BE, ES, and FR under a common chronological protocol with local re-estimation in every bidding zone. No parameter, stacking weight, event threshold, or conformal correction is transferred between markets. No sixth market and no new model family are admitted.

## Information hierarchy

- **Primary:** S1 strict price-calendar information. Tier-1 portability statements and the central Figures 5–7, 9–13 use this setting unless a panel explicitly states otherwise.
- **Main extension:** S2_DA, which adds archived ENTSO-E day-ahead load, wind, and solar forecasts under the frozen extension contract. It is used in Figure 8 and Table S2 as an information-availability extension, not as a replacement for S1.
- **Secondary sensitivity:** S2_LEGACY, the deterministic 0.70×D-1 + 0.30×D-7 proxy construction.
- **Ex-post upper bound:** S3, which admits realized target-hour exogenous information and is never described as deployable.

## Mask hierarchy

- **Main-text five-market comparisons:** `COMMON_MASK` in setting-level tables and `GLOBAL_COMMON` in cross-setting tables. Both identify the strict five-market/cross-setting intersection of **N=15,311 observations per market**.
- **Market-valid masks:** used only in supplementary sensitivity reporting. They must not be mixed with common-mask values in one paired comparison.
- **P95 event support:** counted on the same common mask used by the corresponding ranking metric. ES and FR each contain one P95 test event, so their AUPRC values are descriptive only.

## Inferential hierarchy

Paired moving-block bootstrap results use 2,000 draws. The 168 h block is primary and the 24 h block is sensitivity. Benjamini-Hochberg adjustment is interpreted within the frozen objective-specific family. Direction counts are descriptive and are not substitutes for paired uncertainty.

## Main-text evidence

1. S1 TSQR versus Persistence and SQR under the strict common mask.
2. S1 raw versus RCQR PICP80, absolute coverage gap, interval score, and width.
3. S1 conditional behavior in negative-price and training-defined upper-tail regimes.
4. S2_DA versus S1 as a bounded information-availability extension.
5. XRM only as a support-qualified continuous ranking diagnostic.

## Supplementary evidence

S2_LEGACY, S3, market-valid masks, P90/P92.5 post-hoc XRM support diagnostics, P97.5/P99 stress levels, rolling-origin folds, detailed feature outages, RCQR window sweeps, full budget tables, and per-market EDA belong in the Supplementary/Appendix.

## Numerical-process qualification

S1 remains the frozen primary numerical baseline. The S2/S3 extension manifest records different numerical-effort profiles for previously completed and later completed stages, and rolling-origin fits use the locked minimal-budget sensitivity profile. These facts are retained in the internal audit and reproducibility manifest. They are not converted into a claim of exact same-iteration reruns, and reduced-budget rolling folds do not carry Tier-1 claims.

## Claim lock

- Supported: procedural portability after market-specific re-estimation across these five European day-ahead bidding zones.
- Strongest reproducible contribution: RCQR improves marginal coverage gap and interval score in all five S1 final-test markets, with wider intervals.
- Bounded contribution: TSQR strongly improves over Persistence, while the incremental TSQR-over-SQR gain is smaller and should be reported as such.
- Not supported: universal model superiority, universal XRM value, global generalization, deployable S3 performance, or state-conditional nominal-coverage guarantees.
