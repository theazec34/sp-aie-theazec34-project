# Brasaland sales forecast — training report

## Algorithm choice

Compared Random Forest (explainability for Mariana/Finance) vs XGBoost (precision for Felipe/Lucía purchasing). Selected by lowest test RMSE with fixed random_state=42. Winner: **xgboost**.

**Selected model:** `xgboost` (random_state=42)

## Train / test split (CONTEXT)

- Train months: 2017-01-01 → 2023-12-01
- Test months: 2024-01-01 → 2025-12-01
- Rule: first **8 years** train, last **2 years** test; no shuffle / no leakage.

## Test-set metrics (required)

| Metric | Value | Meaning |
|---|---|---|
| MSE | 3,144,689,018.39 USD² | Mean squared error in USD² — penalizes large misses; translate via RMSE/MAPE for Felipe/Mariana. |
| RMSE | $56,077.53 | Square-root of MSE (same units as sales). |
| MAE | $38,439.68 | Finance-friendly average dollar error. |
| MAPE | 4.67% | Percent error Felipe/Mariana can read. |
| PSI | 5.809 | Population Stability Index train→test — high PSI ⇒ structural shift (growth/new sites); retrain. |
| Gini | 0.651 | Ranking quality of good vs bad months — low Gini ⇒ Mariana cannot spot weak months early. |
| K2 Score | 0.422 | K2 Score ≡ R² — share of revenue variance explained on the test window. |

### Why low MSE is not enough

A low MSE can hide ranking failures (Gini) or a train/test distribution shift (PSI). Brasaland needs both accurate dollars **and** early warning on weak months; CONTEXT asks for all four metrics on the **test** set.

## Visualization

See `data/forecast/prediction_band.png` — actual vs prediction with variability band for the 2 test years.
