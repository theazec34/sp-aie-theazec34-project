# Evaluation report — Brasaland revenue regressor

> **Depends on training milestone** `feature/sales-forecast-model`: artifact from `scripts/train_sales_forecast.py` (`models/brasaland_sales_forecast.joblib`). This evaluation adds TimeSeriesSplit CV, learning curves, and staging diagnosis.

## Business context (Brasaland)

- **Mariana (CEO):** needs to separate good vs bad months (Gini) and an error she can read as a percentage (MAPE) before funding a full executive dashboard.
- **Felipe (Operations):** anticipates ingredient purchases; **underestimating** sales causes stockouts and emergency buys (asymmetric high cost).
- **Lucía (Procurement):** projects volume to negotiate beef prices; large misses in peak season (December) distort coverage.

### Primary metric: RMSE (not MAE)

For Brasaland the cost is non-linear: missing December or an event month hurts more than many small misses. **RMSE** penalizes those large misses and better matches Felipe/Lucía operational risk. **MAE** is reported for communication (average USD deviation) but **staging decisions use RMSE**.

## Model under evaluation: `xgboost`

CONTEXT temporal split: **8 years train / 2 years test** (no shuffle).

## Hold-out test (last 2 years)

| Metric | Value |
|---|---|
| MAE | $38,439.68 |
| RMSE | $56,077.53 |
| MSE | 3,144,689,018.39 USD² |
| MAPE | 4.67% |
| Gini | 0.651 |
| K2 (R²) | 0.422 |
| PSI (train→test target) | 5.809 |

## Temporal cross-validation (`TimeSeriesSplit`, 5 folds)

Verified: no fold mixes future into the past (guards: `[{'fold': 1, 'n_train': 14, 'n_test': 14, 'train_idx_max': 13, 'test_idx_min': 14}, {'fold': 2, 'n_train': 28, 'n_test': 14, 'train_idx_max': 27, 'test_idx_min': 28}, {'fold': 3, 'n_train': 42, 'n_test': 14, 'train_idx_max': 41, 'test_idx_min': 42}, {'fold': 4, 'n_train': 56, 'n_test': 14, 'train_idx_max': 55, 'test_idx_min': 56}, {'fold': 5, 'n_train': 70, 'n_test': 14, 'train_idx_max': 69, 'test_idx_min': 70}]`).

- **MAE:** 41,382.18 ± 19,889.37 USD
- **RMSE:** 52,473.98 ± 19,872.62 USD

## Learning curve

File: `data/eval/learning_curve.png`

- Final train RMSE: $14,171.19
- Final validation RMSE: $121,328.63
- Gap (val − train): $107,157.44

## Diagnosis

**Classification: `overfitting`**

Persistent train≪validation gap: model memorizes monthly noise. Concrete action: raise XGBoost regularization (reg_lambda=2–5, min_child_weight=3, max_depth≤3) and use early stopping on the last temporal fold; do not grow n_estimators without that control.

## Staging recommendation

Promote to staging **only if** CV RMSE mean±std stays bounded and train→test PSI remains < 0.25. Current PSI = 5.809.
