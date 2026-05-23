# GeoMarket AI (Training Pipeline)

This repository contains the end-to-end training pipeline for GeoMarket AI. It turns raw POI data in SQLite files into spatial clusters with DBSCAN, builds a feature store, and trains a Random Forest model to produce location suitability recommendations.

## Project Goals

- Clean and validate geospatial POI data from multiple SQLite sources.
- Cluster business locations using DBSCAN in meter-based coordinates.
- Generate a feature store for repeatable ML training and inference.
- Train a Random Forest model with spatial split to reduce leakage.
- Save model artifacts and metadata for downstream API serving.

## Repository Structure

```
content/
  data/
    raw/            # Input SQLite files (.db)
  runs/             # Per-db training runs (data, reports, models)
geomarketia_train.ipynb  # Main training notebook
prd.md                   # Product requirements or design notes
README.md                # This document
```

## Main Notebook

The notebook `geomarketia_train.ipynb` is the single source of truth for training. It contains these main stages:

1) Ingestion and validation
- Loads one selected SQLite file from `content/data/raw` per run.
- Normalizes column names and verifies required fields.
- Applies a validation gate and writes `rejected_rows.csv` for invalid data.

2) Preprocessing and coordinate conversion
- Converts WGS84 lat/lon into UTM (meter) coordinates.
- Creates basic numeric features such as `review_log` and cleans missing values.

3) DBSCAN clustering
- Runs DBSCAN on UTM coordinates.
- Evaluates clustering quality with Silhouette Score and Davies-Bouldin Index.
- Produces cluster visualizations and tuning helpers.

4) Feature engineering
- Computes centroid distance and density features.
- Saves the feature store to `content/runs/<db_key>/data/feature_store.csv`.

5) Random Forest training
- Builds a proxy suitability label (High/Medium/Low).
- Performs spatial split using grid-based grouping.
- Trains a Random Forest model and saves artifacts to `content/runs/<db_key>/models/`.

## Key Outputs

- `content/runs/<db_key>/data/feature_store.csv`
- `content/runs/<db_key>/data/rejected_rows.csv`
- `content/runs/<db_key>/data/category_distribution.json`
- `content/runs/<db_key>/data/category_distribution_valid.json`
- `content/runs/<db_key>/reports/clustering_result.png`
- `content/runs/<db_key>/reports/cluster_vs_noise.png`
- `content/runs/<db_key>/reports/category_distribution_top10.png`
- `content/runs/<db_key>/reports/rf_confusion_matrix.png`
- `content/runs/<db_key>/reports/rf_shap_summary.png`
- `content/runs/<db_key>/reports/rf_shap_waterfall.png`
- `content/runs/<db_key>/reports/rf_shap_importance.csv`
- `content/runs/<db_key>/models/clustering_metadata.json`
- `content/runs/<db_key>/models/rf_location_reco_v*.joblib`
- `content/runs/<db_key>/models/rf_metadata.json`

## Run Metadata

Per-run metrics and configuration are stored under `content/runs/<db_key>/models/`.

## How to Run

1) Place SQLite files under `content/data/raw/`.
2) Set `TARGET_DB_FILE` in the notebook (Tahap 2.1) to choose a single DB.
3) Open `geomarketia_train.ipynb` in VS Code.
4) Run cells in order from top to bottom.
5) Verify outputs in `content/runs/<db_key>/`.

## Notes

- DBSCAN parameters (`EPS_METER`, `MIN_SAMPLES`) are defined in the notebook and can be tuned with visualizations and grid search.
- The Random Forest uses a spatial split to reduce geographic leakage.
- Model labels are proxy labels built from PRD scoring rules, not direct ground truth.
- Each run is saved under `content/runs/<db_key>/` to keep outputs isolated per database.
