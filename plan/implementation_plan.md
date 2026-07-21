# Implementation Plan: Per-Database DBSCAN + Random Forest

## Goals
- Train DBSCAN and Random Forest using a single database per run to reduce noise.
- Use `category` as the category signal (not `source_category`).
- Preprocess and validate each database before it is used in training.
- Exclude rows with empty required columns; exclude entirely empty columns from the training feature set.

## Non-Goals
- Change model hyperparameters or scoring formulas unless required for per-db support.
- Change downstream API logic (outside this notebook) in this pass.

## Proposed Design
1. Add explicit per-db configuration
   - Introduce a `TARGET_DB_FILE` (exact filename) or `TARGET_DB_KEY` (prefix before .db).
   - Optionally add `PROCESS_MODE = "single" | "all"` if batch processing per-db is desired later.

2. Normalize the category column per database
   - Normalize `category` (trim + lowercase) after column mapping.
   - Set `CAT_COL = "category"`.
   - Keep `source_category` only as metadata (optional), not as the modeling category.

3. Preprocess each database before it enters the training DataFrame
   - For each table inside the target .db:
     - Apply `COLUMN_MAPPING`.
     - Trim whitespace and normalize empty strings to nulls.
     - Add `source_file` (and optionally `source_table`) for traceability.
   - Normalize `category` values after mapping.
   - Drop rows with null/empty values in required columns: `latitude`, `longitude`, `name`, and `category`.
   - Convert numeric columns (`latitude`, `longitude`, `rating`, etc.) to numeric before validation.

4. Update validation gate and required columns
   - Replace `REQUIRED_COLS_FINAL` / `REQUIRED_COLS` to use `category`.
   - Keep the existing validation rules (null check, duplicates, rating range), but scope them to the per-db `df`.

5. DBSCAN and feature engineering on per-db data
   - Ensure DBSCAN uses only the single-db `df` built in Steps 2–4.
   - `CAT_COL` points to `category`, which is per-db.
   - Density features (`same_category_density_*`) reflect the per-db category values.

6. Feature store and model artifacts per database
    - Save outputs to db-specific paths under `content/runs/<db_key>/`:
       - `content/runs/<db_key>/data/feature_store.csv`
       - `content/runs/<db_key>/models/clustering_metadata.json`
       - `content/runs/<db_key>/models/rf_location_reco_v*.joblib`
   - Update Random Forest loading to read the db-specific feature store.
   - Exclude any feature columns that are entirely null for that database.

7. Feature store path consolidation
   - All outputs use db-specific paths under `content/runs/<db_key>/`.
   - No legacy copy at `content/data/processed/` (removed in cleanup).

## Implementation Steps (Notebook)
1. Add per-db configuration block (target db + output suffixing).
2. Refactor ingestion to load only the target db, and apply preprocessing per table before concatenation.
3. Normalize `category` values after mapping.
4. Update required columns, validation gate, and null checks for per-db data.
5. Ensure `CAT_COL` remains `category` in DBSCAN, feature engineering, and feature store sections.
6. Update feature store and model save/load paths to be db-specific.
7. Add a short per-db summary (rows kept, rows rejected, category distribution).

## Decisions Applied
- Single DB per run via `TARGET_DB_FILE`.
- Category uses `category` only.
- `source_category` remains as metadata only.
- Feature store and model artifacts live under `content/runs/<db_key>/`.
