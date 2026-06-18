# Implementation Plan: Regression-Based Business Location Recommendation

## Summary
Implement the final regression-based recommendation system across training, artifacts, FastAPI, and frontend. The system will remove weak/leaky features, generate the new feature schema, train five regressors, select the best model, and serve ranked location recommendations.

## Phase 1: Training Notebook
Update `geomarketia_train.ipynb`:

- Remove classifier training.
- Remove unused/leaky features:
  - `hotspot_score`
  - `female_ratio`
  - `has_phone`
  - `has_url`
  - `has_open_hours`
  - `price_level`
  - `nearby_price_level_median_500m`
  - direct `cluster_id` as model feature
- Add final feature groups:
  - Market Demand
  - Competition
  - Commercial Activity
  - Accessibility
  - Land Suitability
  - Market Structure
- Rename features to clear English.
- Generate `suitability_score` as continuous target.
- Derive `suitability_band` from score thresholds.
- Train:
  - Linear Regression
  - Random Forest Regressor
  - Extra Trees Regressor
  - LightGBM Regressor
  - XGBoost Regressor
- Save:
  - `feature_store.csv`
  - `base_candidate_grid.parquet`
  - `model_comparison.csv`
  - best model `.joblib`
  - `rf_metadata.json` or renamed regression metadata
  - SHAP report for best model

## Phase 2: Artifact Contract
Update artifact metadata:

- Add `feature_schema_version`.
- Store final feature list.
- Store removed-feature list.
- Store model comparison results.
- Store selected model name.
- Store regression metrics:
  - `MAE`
  - `RMSE`
  - `R2`
  - `Spearman rank correlation`
  - `Precision@K`
  - `Top-K overlap`
- Store suitability band thresholds.

## Phase 3: FastAPI
Update recommendation service:

- Replace classifier probability scoring with regression prediction.
- Return:
  - `score`
  - `suitability_band`
  - `features`
  - `shap_explanation`
- Replace `kecamatan` with `subdistrict`.
- Temporarily support `kecamatan` as deprecated alias.
- Remove from API output:
  - `hotspot_score`
  - `female_ratio`
  - `price_level`
- Normalize old artifact columns through aliases if older artifacts are loaded.

## Phase 4: Frontend
Update recommendation UI:

- Rename filter from `kecamatan` to `subdistrict`.
- Remove display chips:
  - hotspot
  - female ratio
  - price level
- Show new explanation chips:
  - population density
  - road distance
  - business density
  - same-category density
  - nearest same-category distance
  - land suitability
  - cluster distance
  - suitability band
- Update TypeScript API types to match new response schema.

## Phase 5: Verification
Run checks:

- Confirm all final feature stores contain only approved feature names.
- Confirm removed features do not appear in:
  - model feature list
  - SHAP report
  - API response
  - frontend display
- Run model comparison for all datasets.
- Confirm recommendation endpoint returns valid ranked locations.
- Confirm top recommendations are:
  - on valid land
  - near roads
  - not over-saturated by same-category competitors
- Confirm frontend renders recommendations correctly.

## Assumptions
- LightGBM and XGBoost dependencies may be installed if missing.
- New artifacts use English feature names.
- Old names are supported only as migration aliases.
- The final model is selected by ranking quality, not only regression error.
