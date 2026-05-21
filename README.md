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
    processed/      # Outputs: feature_store.csv, rejected_rows.csv, plots
  models/           # Model artifacts and metadata JSON
geomarketia_train.ipynb  # Main training notebook
prd.md                   # Product requirements or design notes
README.md                # This document
```

## Main Notebook

The notebook `geomarketia_train.ipynb` is the single source of truth for training. It contains these main stages:

1) Ingestion and validation
- Loads all SQLite files from `content/data/raw`.
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
- Saves the feature store to `content/data/processed/feature_store.csv`.

5) Random Forest training
- Builds a proxy suitability label (High/Medium/Low).
- Performs spatial split using grid-based grouping.
- Trains a Random Forest model and saves artifacts to `content/models/`.

## Key Outputs

- `content/data/processed/feature_store.csv`
- `content/data/processed/rejected_rows.csv`
- `content/data/processed/clustering_result.png`
- `content/data/processed/k_distance_graph.png`
- `content/models/clustering_metadata.json`
- `content/models/rf_location_reco_v*.joblib`
- `content/models/rf_metadata.json`

## Latest Run Snapshot

This snapshot is taken from the latest saved metadata in `content/models/`.

- Data: 11,094 raw rows → 10,768 valid (326 rejected)
- DBSCAN: eps=150m, min_samples=10, clusters=118, noise=3,935 (36.54%)
- Clustering quality: silhouette=0.3424, Davies-Bouldin=0.5229
- Random Forest: F1 macro=0.9859, accuracy=0.9857

## How to Run

1) Place SQLite files under `content/data/raw/`.
2) Open `geomarketia_train.ipynb` in VS Code.
3) Run cells in order from top to bottom.
4) Verify outputs in `content/data/processed/` and `content/models/`.

## Notes

- DBSCAN parameters (`EPS_METER`, `MIN_SAMPLES`) are defined in the notebook and can be tuned with the k-distance plot and grid search.
- The Random Forest uses a spatial split to reduce geographic leakage.
- Model labels are proxy labels built from PRD scoring rules, not direct ground truth.
