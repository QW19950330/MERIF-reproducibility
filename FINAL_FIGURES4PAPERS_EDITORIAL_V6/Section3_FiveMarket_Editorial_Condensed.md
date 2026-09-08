# 3. Results

## 3.1. Five-market price characteristics and experimental context

DE-LU, DK1, BE, ES, and FR were evaluated under one chronological protocol with local re-estimation and 15,311 common-mask products per market. The experiment addresses procedural portability, not parameter transfer.

Daily and weekly autocorrelation remained high, but standardized distributions, volatility, and negative-price incidence differed (Fig. 5a-c). Negative-price shares ranged from 1.28% to 3.30%.

P95 support was 45, 42, 15, 1, and 1 events (Fig. 5d). The ES and FR P95 results are descriptive; full EDA appears in Figs. E1-E5.

## 3.2. Central forecasting and module attribution

S1 TSQR reduced MAE relative to Persistence in all five markets by 3.09-12.82% (Fig. 6). The 168-h confidence interval crossed zero only in DK1.

TSQR gains over SQR were smaller, at 0.91-2.48%, but all five intervals excluded zero. Pinball loss declined in the same direction.

Most central improvement arose before tail weighting (Fig. 7). Direct QR-to-RQR gains were 1.14-2.68 EUR MWh^-1, while SQR-to-TSQR gains were 0.168-0.720 EUR MWh^-1.

## 3.3. Marginal interval calibration and history sensitivity

Raw PICP80 was 0.578-0.717. W60 RCQR moved coverage to 0.796-0.805 and reduced the largest absolute gap to 0.0045 (Fig. 8).

Interval score fell by 2.80-11.87 EUR MWh^-1, while width increased by 15.82-25.15 EUR MWh^-1. Calibration improved proper-score performance at a visible sharpness cost.

The direction persisted for W7, W14, W30, and W60 (Fig. 9). W60 remained frozen; the sweep was not used for post-test selection.

## 3.4. Information availability across markets

On GLOBAL_COMMON, S2_DA reduced TSQR MAE by 7.5-26.9% relative to S1 (Fig. 10a). The magnitude remained market dependent.

Raw coverage gap worsened in DE-LU and DK1 but improved in BE, ES, and FR. After RCQR, the largest S2_DA gap was 0.0105.

S2_LEGACY remains a proxy sensitivity and S3 is ex-post. Full GLOBAL_COMMON and MARKET_VALID matrices are separated in Figs. E6-E7.

## 3.5. Temporal robustness and synchronized trajectories

TSQR improved on SQR in 10 of 10 market-year and 17 of 20 market-season comparisons (Fig. 11a). Three small seasonal reversals remained.

RCQR reduced interval score in every displayed year and season (Fig. 11b). Its calendar direction was more stable than the terminal TSQR refinement.

The locked summer trajectories show the same scored forecasts without smoothing or episode selection (Fig. 12). Winter, spring, and rolling-origin sensitivities remain supplementary.

## 3.6. Conditional negative-price and upper-tail behavior

During negative runs of at least 3 h, RCQR raised PICP80 from 0.279-0.594 to 0.440-0.927 (Fig. 13). Coverage still remained below 0.80 in three markets.

Interval score improved in four markets but worsened slightly in ES. Marginal calibration did not guarantee conditional proper-score improvement.

Upper-tail MAE increased as support contracted (Fig. 14). At P99, event counts were 13, 11, 3, 0, and 0; no P92.5 central-error value was imputed.

## 3.7. Upper-tail risk ranking and monitoring limits

In DE-LU, DK1, and BE, XRM P95 AUPRC was 0.064-0.156 versus 0.173-0.184 for q0.90 (Fig. 15). XRM showed no supported ranking advantage.

Only the DE-LU 168-h interval excluded zero, favoring q0.90. ES and FR each contained one P95 event and remain descriptive.

No market passed the 10-event validation gate. Review budgets are retrospective capacity summaries, not operating thresholds (Figs. E11-E12).

## 3.8. Operational robustness and computational profile

Removing short price memory caused the largest normalized MAE deterioration in every market, at 0.108-0.285 training IQR (Fig. 16).

Other outage effects were smaller and occasionally favorable. They diagnose dependence of the frozen workflow, not causal importance (Fig. E13).

Twenty-four-product inference required 189.1-197.9 ms; XRM and RCQR each added less than 0.2 ms. Complete resource results appear in Fig. E14.

## 3.9. Integrated procedural portability

After local estimation, central improvement over Persistence was positive in all five markets, while the incremental TSQR gain was smaller (Fig. 17a,b).

RCQR provided the most consistent component-level result (Fig. 17c,d). Conditional calibration and XRM ranking remained heterogeneous or support limited (Fig. 17e).

The evidence supports procedural portability across the five studied markets. It does not establish parameter transfer, universal conditional coverage, deployable S3 performance, or an automatic extreme-price alarm.
