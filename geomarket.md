# GeoMarket AI — Pipeline Specification & Code Documentation

## Project Overview

**Project:** GeoMarket AI — IF-4PD-04  
**Purpose:** Build an AI-powered location recommendation system for businesses in Batam, Indonesia.  
**Pipeline:** DBSCAN spatial clustering + Random Forest classification to predict location suitability (High/Medium/Low).

---

## Current Per-DB Training Summary

The current pipeline runs one SQLite database per training run and stores all outputs under a per-db folder. Detailed metrics live in the run artifacts, not in this document.

**Key configuration (general):**
- `TARGET_DB_FILE` selects the single database to train.
- `category` is the modeling column; `source_category` remains metadata only.
- DBSCAN and Random Forest parameters are configured in the notebook (no hard-coded values in this doc).

**Per-run output structure:**
```
content/
    runs/
        <db_key>/
            data/
                feature_store.csv
                rejected_rows.csv
                category_distribution.json
                category_distribution_valid.json
            reports/
                clustering_result.png
                cluster_vs_noise.png
                category_distribution_top10.png
                rf_confusion_matrix.png
                rf_shap_summary.png
                rf_shap_waterfall.png
                rf_shap_importance.csv
            models/
                clustering_metadata.json
                rf_location_reco_v*.joblib
                rf_metadata.json
```

**Note:** The sections below document the legacy merged-db pipeline and are preserved for historical reference.

---

## Architecture & Pipeline Flow

```
SQLite (.db files)
    └─ [Tahap 1-2] Ingestion & EDA
    └─ [Tahap 3]   Validation Gate
    └─ [Tahap 4]   Preprocessing & Coordinate Conversion (WGS84 → UTM)
    └─ [Tahap 5]   DBSCAN Clustering
    └─ [Tahap 6]   Visualization & Parameter Tuning
    └─ [Tahap 7]   Feature Store Export
    └─ [Tahap 8]   Quality Gate
    └─ [Tahap 9]   Random Forest Training & Model Export
```

---

## Data Sources

| File | Category | Size |
|------|----------|------|
| Indonesia.Batam.Kuliner.202406162232.db | F&B | 4080 KB |
| Indonesia.Batam.Kesehatan.202408050759.db | Healthcare | 1332 KB |
| Indonesia.Batam.School.202408060757.db | Education | 1020 KB |
| Indonesia.Batam.Toko Bangunan.202408021219.db | Retail | 780 KB |
| Indonesia.Batam.PT.202408042212.db | Company | 752 KB |
| Indonesia.Batam.Hotel.202408042041.db | Hospitality | 720 KB |
| Indonesia.Batam.Cosmetics.202410290644.db | Retail | 700 KB |
| Indonesia.Batam.Toko Komputer.202410170720.db | Retail | 364 KB |

**Total raw data:** 11,094 rows from 8 SQLite databases  
**After validation:** 10,768 rows (326 rejected)

---

## Tahap 1-2: Ingestion & Exploratory Data Analysis

### What it does
- Scans `content/data/raw/` for `.db` files
- Maps each file to a business category via `CATEGORY_MAPPING`
- Reads all tables from each SQLite file
- Applies `COLUMN_MAPPING` to standardize column names across files
- Merges all data into a single DataFrame

### Column Mapping (standardization)
```python
"lat"/"lng"/"lon"/"long" → "latitude"/"longitude"
"nama"/"place_name"/"title" → "name"
"cat"/"type"/"jenis" → "category"
"rate"/"score" → "rating"
"ulasan"/"review_count"/"total_reviews" → "reviews"
```

### Required columns after mapping
`latitude`, `longitude`, `name`, `category`, `source_category`

---

## Tahap 3: Validation Gate

Four rules applied sequentially to ensure data quality:

| Rule | Description | Rows Removed |
|------|-------------|--------------|
| 1 | Null values in required columns (lat, lon, name, category) | 0 |
| 2 | Duplicate within same file (name + lat + lon + source_file) | 0 |
| 3 | Cross-file duplicates (name + lat + lon) | 326 |
| 4 | Rating outside 0.0–5.0 range | 0 |

**Output:** `content/data/processed/rejected_rows.csv` — all rejected rows with rejection reason.

### Why validation matters for DBSCAN
DBSCAN is sensitive to outlier coordinates. A single point at `(0.0, 0.0)` would form its own meaningless cluster and distort the entire result.

---

## Tahap 4: Preprocessing & Coordinate Conversion

### 4.1 WGS84 → UTM Zone 48N

**Problem:** DBSCAN uses Euclidean distance. If raw lat/lon (degrees) are used, `eps=0.001°` means ~111m at the equator but varies by latitude. This makes the radius inconsistent.

**Solution:** Convert to UTM Zone 48N (EPSG:32648) where units are meters. Batam falls within UTM Zone 48N (lon 102°E–108°E, northern hemisphere).

```python
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True)
df['x_utm'], df['y_utm'] = transformer.transform(lon_values, lat_values)
```

After conversion, `eps=120` literally means 120 meters in all directions.

### 4.2 Feature Preparation
- `review_log = log(1 + reviews)` — reduces skewness of review counts
- `rating` — null values filled with median
- Category names normalized to lowercase + stripped whitespace

---

## Tahap 5: DBSCAN Clustering

### Algorithm: DBSCAN (Density-Based Spatial Clustering of Applications with Noise)

**Parameters:**
| Parameter | Value | Meaning |
|-----------|-------|---------|
| `eps` | 150 meters | Neighborhood search radius |
| `min_samples` | 10 | Minimum points to form a core point |
| `metric` | euclidean | Distance metric (valid because UTM is in meters) |
| `algorithm` | ball_tree | Efficient for geospatial data |

### Point Classification

| Type | Condition | cluster_id |
|------|-----------|------------|
| Core point | ≥ min_samples neighbors within eps | ≥ 0 |
| Border point | Within eps of a core point, but < min_samples neighbors | ≥ 0 (joins nearest cluster) |
| Noise point | Neither core nor border | -1 |

### Results
- **118 clusters** formed
- **6,833 points** assigned to clusters
- **3,935 noise points** (36.54% noise ratio)
- Silhouette Score: **0.3424** (acceptable, target > 0.3)
- Davies-Bouldin Index: **0.5229** (good, target < 1.0)

### Why noise points are kept
Points with `cluster_id = -1` represent isolated businesses — either untapped market opportunities or genuinely low-traffic areas. They remain in the feature store as a distinct signal for Random Forest.

### Why no StandardScaler
Input is only two columns (x_utm, y_utm) both in meters — same unit, no scaling needed. Scaling would be required only if mixing features with different units.

---

## Tahap 5.3-5.4: Derived Spatial Features

### Centroid Distance
For each clustered point, compute Euclidean distance to its cluster's centroid (mean x_utm, y_utm of all points in that cluster). Noise points get distance = 0.

```
dist_to_cluster_centroid_m = sqrt((x - centroid_x)² + (y - centroid_y)²)
```

### Density Features (via BallTree)
| Feature | Description |
|---------|-------------|
| `competitor_density_500m` | All businesses within 500m radius |
| `competitor_density_1km` | All businesses within 1km radius |
| `same_category_density_500m` | Same-category businesses within 500m |
| `nearest_neighbor_dist_m` | Distance to nearest business (any category) |

BallTree provides O(n log n) neighbor queries vs O(n²) brute force — critical for 10k+ points.

---

## Tahap 6: Visualization & Parameter Tuning

### K-Distance Graph
Plots the distance to the k-th nearest neighbor (k = min_samples) for all points, sorted descending. The "elbow" of this curve indicates the optimal EPS value.

### Grid Search Results (Top 5)
Grid search output depends on the run. Refer to the notebook cell **Tahap 7.3 — Tuning Grid DBSCAN** for the latest table.

The chosen parameters (eps=150, min_samples=10) balance noise ratio and cluster quality.

---

## Tahap 7: Feature Store

### Output: `content/data/processed/feature_store.csv`

**16 columns, 10,768 rows, ~1,677 KB**

| Column | Type | Description |
|--------|------|-------------|
| id | int64 | Original record ID |
| name | str | Business name |
| source_category | str | Mapped business category |
| latitude | float64 | WGS84 latitude |
| longitude | float64 | WGS84 longitude |
| x_utm | float64 | UTM Zone 48N easting (meters) |
| y_utm | float64 | UTM Zone 48N northing (meters) |
| cluster_id | int64 | DBSCAN cluster assignment (-1 = noise) |
| dist_to_cluster_centroid_m | float64 | Distance to cluster center |
| competitor_density_500m | int64 | Businesses within 500m |
| competitor_density_1km | int64 | Businesses within 1km |
| same_category_density_500m | int64 | Same-category within 500m |
| nearest_neighbor_dist_m | float64 | Distance to nearest business |
| rating | float64 | Google Maps rating (0-5) |
| review_log | float64 | log(1 + review_count) |
| price_level | int64 | Price level indicator |

---

## Tahap 8: Quality Gate

Automated checks before proceeding to Random Forest:
- Noise ratio < 40% — PASS (36.54%)
- Silhouette Score > 0.3 — PASS (0.3424)

---

## Tahap 9: Random Forest Training

### 9.1 Label Generation (Proxy)

Since there's no ground-truth "good location" label, a proxy suitability score is computed:

```python
suitability_score = (
    rating * 0.25 +
    review_log * 0.20 +
    hotspot_score * 0.25 -          # KDE density (bandwidth=500m)
    same_category_density_500m * 0.20 -
    saturation_index * 0.10         # same_cat_density / area_km²
)
```

Then quantile-binned into 3 classes:
- **Low** (bottom 33%): score < -7.32
- **Medium** (middle 33%): -7.32 to -1.64
- **High** (top 33%): score > -1.64

Distribution: High=3,661 | Medium=3,553 | Low=3,554

### 9.2 Spatial Split

**Problem:** Random train/test split causes spatial leakage — nearby points end up in both sets, inflating metrics.

**Solution:** Group-based split using 1km grid cells. All points in the same grid cell go to either train or test, never both.

```python
grid_id = f"{int(x_utm // 1000)}_{int(y_utm // 1000)}"
GroupShuffleSplit(test_size=0.2, groups=grid_id)
```

Split: 8,465 train / 2,303 test

### 9.3 Model Configuration

```python
RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
```

### 9.4 Results

| Metric | Value |
|--------|-------|
| F1 Macro | **0.9859** |
| Accuracy | **0.9857** |

**Per-class performance:**
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| High | 1.00 | 0.98 | 0.99 | 779 |
| Low | 0.99 | 0.99 | 0.99 | 720 |
| Medium | 0.97 | 0.99 | 0.98 | 804 |

**Confusion Matrix:**
```
            Predicted
            Low  Med  High
Actual Low  [713   7    0]
    Med  [  5 796    3]
      High  [  0  18  761]
```

### Feature Importance (ranked)
The model relies most heavily on spatial density features, confirming that geospatial context is the primary driver of location suitability.

---

## Output Files

```
content/
├── data/
│   ├── raw/                          ← 8 SQLite databases
│   └── processed/
│       ├── feature_store.csv         ← 10,768 rows × 16 features
│       ├── rejected_rows.csv         ← 326 rejected rows with reasons
│       ├── clustering_result.png     ← Cluster scatter plot
│       └── k_distance_graph.png      ← EPS tuning guide
└── models/
    ├── clustering_metadata.json      ← DBSCAN run metadata
    ├── rf_location_reco_v1.joblib    ← Trained Random Forest model
    └── rf_metadata.json              ← RF training metadata
```

---

## Key Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| pandas | 3.0.2 | Data manipulation |
| numpy | 2.4.4 | Numerical operations |
| geopandas | 1.1.3 | Geospatial data handling |
| scikit-learn | 1.8.0 | DBSCAN, Random Forest, metrics |
| pyproj | — | Coordinate system transformation |
| scipy | — | Spatial distance calculations |
| matplotlib | — | Visualization |

---

## Tuning Guide

| Symptom | Solution |
|---------|----------|
| Too much noise (>40%) | Increase EPS_METER or decrease MIN_SAMPLES |
| Everything in one giant cluster | Decrease EPS_METER |
| Too many tiny clusters | Increase MIN_SAMPLES |
| Negative Silhouette Score | EPS too large, clusters overlapping |

---

## Reproducibility

All parameters are centralized in Tahap 2 (Configuration cell). Key seeds and settings:
- `RANDOM_SEED = 42`
- `EPS_METER = 120`
- `MIN_SAMPLES = 8`
- CRS: WGS84 (EPSG:4326) → UTM 48N (EPSG:32648)
- Spatial split grid: 1km cells
- Metadata JSON files record exact parameters and metrics for each run
