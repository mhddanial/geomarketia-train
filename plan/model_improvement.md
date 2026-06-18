# Final Plan: Regression-Based Business Location Recommendation

## Summary
This project will build a **Location Suitability Prediction** system that ranks potential business locations in Batam. The model will predict a continuous `suitability_score` between `0` and `1`, then convert that score into `Low`, `Medium`, or `High` bands for user display.

The final model will use six feature groups:

1. Market Demand
2. Competition
3. Commercial Activity
4. Accessibility
5. Land Suitability
6. Market Structure

The system will use regression models because the main task is ranking candidate locations, not directly classifying locations.

## Research Variables

| Variable Name | Data Type | Data Source |
|---|---|---|
| `population_density` | Numeric, continuous | Batam population density data |
| `nearby_review_count_log_sum_500m` | Numeric, continuous | Business POI dataset |
| `nearby_review_count_log_mean_500m` | Numeric, continuous | Business POI dataset |
| `nearby_avg_rating_500m` | Numeric, continuous | Business POI dataset |
| `same_category_density_250m` | Numeric, continuous | Business POI dataset |
| `same_category_density_500m` | Numeric, continuous | Business POI dataset |
| `same_category_density_1000m` | Numeric, continuous | Business POI dataset |
| `nearest_same_category_distance_m` | Numeric, continuous | Business POI dataset |
| `competitor_saturation_index` | Numeric, continuous | Business POI dataset |
| `business_density_250m` | Numeric, continuous | Business POI dataset |
| `business_density_500m` | Numeric, continuous | Business POI dataset |
| `business_density_1000m` | Numeric, continuous | Business POI dataset |
| `nearest_business_distance_m` | Numeric, continuous | Business POI dataset |
| `poi_diversity_index` | Numeric, continuous | OpenStreetMap: amenity, shop, office, tourism |
| `nearest_road_distance_m` | Numeric, continuous | OpenStreetMap road network |
| `road_density_500m` | Numeric, continuous | OpenStreetMap road network |
| `intersection_density_500m` | Numeric, continuous | OpenStreetMap road network |
| `road_access_score` | Numeric, continuous | Derived from OpenStreetMap road network |
| `is_valid_land` | Binary, 0/1 | RBI land-use data |
| `distance_to_water_body_m` | Numeric, continuous | RBI hydrography data |
| `distance_to_forest_or_green_area_m` | Numeric, continuous | RBI land-use data |
| `commercial_land_ratio_500m` | Numeric, continuous | RBI land-use data |
| `residential_land_ratio_500m` | Numeric, continuous | RBI land-use data |
| `cluster_centroid_distance_m` | Numeric, continuous | DBSCAN clustering result |
| `nearest_cluster_size` | Numeric, continuous | DBSCAN clustering result |
| `is_noise_area` | Binary, 0/1 | DBSCAN clustering result |

## Feature Groups

| Feature Group | Variables |
|---|---|
| Market Demand | `population_density`, `nearby_review_count_log_sum_500m`, `nearby_review_count_log_mean_500m`, `nearby_avg_rating_500m` |
| Competition | `same_category_density_250m`, `same_category_density_500m`, `same_category_density_1000m`, `nearest_same_category_distance_m`, `competitor_saturation_index` |
| Commercial Activity | `business_density_250m`, `business_density_500m`, `business_density_1000m`, `nearest_business_distance_m`, `poi_diversity_index` |
| Accessibility | `nearest_road_distance_m`, `road_density_500m`, `intersection_density_500m`, `road_access_score` |
| Land Suitability | `is_valid_land`, `distance_to_water_body_m`, `distance_to_forest_or_green_area_m`, `commercial_land_ratio_500m`, `residential_land_ratio_500m` |
| Market Structure | `cluster_centroid_distance_m`, `nearest_cluster_size`, `is_noise_area` |

## Datasets

| Dataset | Data Type | Function |
|---|---|---|
| Batam business POI dataset | Point spatial data | Measures competition, business density, nearby ratings, and nearby reviews |
| Batam population data | Tabular/spatial data | Measures population density as a market demand indicator |
| RBI data | Polygon and line spatial data | Measures land suitability, water bodies, restricted areas, and land use |
| OpenStreetMap | Road network and POI spatial data | Measures road accessibility and surrounding POI diversity |
| DBSCAN clustering result | Derived spatial data | Measures market structure and business concentration patterns |

## Removed Variables
The following variables will not be used in the final model:

| Removed Variable | Reason |
|---|---|
| `female_ratio` | Removed for fairness and potential gender-bias concerns |
| `has_phone` | Represents data completeness, not location quality |
| `has_url` | Represents data completeness, not location quality |
| `has_open_hours` | Not available for new candidate locations |
| `price_level` | Too sparse in the dataset, around `1.88%` nonzero values |
| `nearby_price_level_median_500m` | Depends on sparse `price_level` data |
| `hotspot_score` | Showed no meaningful contribution in the initial SHAP analysis |
| `cluster_id` | DBSCAN label is not ordinal and has no direct numeric meaning |

## Target Variable
The target variable is:

```text
Location Suitability Score
```

This is a continuous value from `0` to `1`.

The score is a proxy target created from business success indicators in the existing POI dataset, mainly:

- normalized rating
- normalized review count

Final system output:

```text
Suitability Score
-> Location Ranking
-> Top-N Recommendation
-> Low / Medium / High suitability band
```

## Model Comparison
The final research will compare five regression models:

| Model | Role |
|---|---|
| Linear Regression | Baseline model |
| Random Forest Regressor | Traditional ensemble model |
| Extra Trees Regressor | Randomized ensemble model |
| LightGBM Regressor | Gradient boosting model |
| XGBoost Regressor | Advanced gradient boosting model |

The final model will be selected using both regression and ranking metrics.

## Evaluation Metrics
Regression metrics:

- `MAE`
- `RMSE`
- `R2`

Ranking metrics:

- `Spearman rank correlation`
- `Precision@K`
- `Top-K overlap`

Recommendation sanity checks:

- Recommended locations must be on valid land.
- Recommended locations should be close to road access.
- Recommended locations should not be in over-saturated competition areas.
- Removed variables must not appear in model features, SHAP output, API response, or UI.

## Implementation Plan
- Update the notebook feature engineering pipeline.
- Remove classifier training and replace it with regression training.
- Generate the final feature store with English feature names.
- Train and compare all five regression models.
- Save model comparison results for academic reporting.
- Save the best model, metadata, feature schema, score thresholds, and SHAP explanation.
- Update FastAPI to serve regression-based recommendations.
- Update frontend labels and recommendation cards to match the new feature schema.

## Final Academic Narrative
This research predicts business location suitability using regression because the system aims to rank candidate locations. The features represent six dimensions of location quality: market demand, competition, commercial activity, accessibility, land suitability, and market structure. These variables are engineered from business POI data, population density data, RBI spatial data, OpenStreetMap data, and DBSCAN clustering results.
