# Section 3 terminology ledger

| Canonical term | First-use definition | Locked later form |
|---|---|---|
| multi-energy risk-informed forecasting | multi-energy risk-informed forecasting (MERIF) | MERIF |
| direct quantile regression | direct quantile regression (Direct QR) | Direct QR |
| residual quantile regression | residual quantile regression (RQR) | RQR |
| stacked quantile regression | stacked quantile regression (SQR) | SQR |
| tail-sensitive quantile regression | tail-sensitive quantile regression (TSQR) | TSQR |
| rolling conformalized quantile regression | rolling conformalized quantile regression (RCQR) | RCQR |
| extreme-risk monitor | extreme-risk monitor (XRM) | XRM |
| mean absolute error | mean absolute error (MAE) | MAE |
| root mean squared error | root mean squared error (RMSE) | RMSE |
| prediction-interval coverage probability | prediction-interval coverage probability (PICP) | PICP |
| interval score | interval score (IS) | IS |
| interquartile range | interquartile range (IQR) | IQR |
| area under the precision-recall curve | area under the precision-recall curve (AUPRC) | AUPRC |
| common test mask | common five-market test mask (`COMMON_MASK`) | common mask / `COMMON_MASK` |
| global common cross-setting mask | global common mask (`GLOBAL_COMMON`) | global common mask / `GLOBAL_COMMON` |
| day-ahead information setting | archived day-ahead information setting (S2_DA) | S2_DA |

Metric directions are fixed: lower MAE, RMSE, pinball loss, absolute coverage gap, IS, and width are preferable except where width is explicitly reported as the calibration cost; higher PICP toward 0.80 and higher AUPRC are preferable. Positive effect displays always mean that the proposed component performed better.
