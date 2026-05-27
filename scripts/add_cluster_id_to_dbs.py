"""
add_cluster_id_to_dbs.py
========================
Reads per-DB training results from content/runs/<db_key>/data/feature_store.csv,
joins cluster_id back into the original SQLite database, and writes the enriched
copy to content/runs/<db_key>/data/db_with_cluster/<filename>.db.

Modes:
  - Set TARGET_DB_FILE to process a single database.
  - Leave TARGET_DB_FILE empty and set PROCESS_ALL = True to batch-process every
    database that has a completed training run.

Join strategy:
  The feature store 'id' column maps directly to the raw DB's 'places.id'
  primary key. This is the safest join key (integer, unique, assigned during
  ingestion). A name+lat+lon fallback is available for edge cases.
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pandas as pd

# ──────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────
RAW_DIR = os.path.join("content", "data", "raw")
RUNS_DIR = os.path.join("content", "runs")

# Set ONE of these:
TARGET_DB_FILE = ""          # e.g. "Indonesia.Batam.Kuliner.202406162232.db"
PROCESS_ALL = True           # Process every DB that has a training run

COLUMN_MAPPING = {
    "lat": "latitude",
    "lng": "longitude",
    "lon": "longitude",
    "long": "longitude",
    "nama": "name",
    "place_name": "name",
    "title": "name",
    "cat": "category",
    "type": "category",
    "jenis": "category",
    "rate": "rating",
    "score": "rating",
    "ulasan": "reviews",
    "review_count": "reviews",
    "total_reviews": "reviews",
}

SQLITE_INTERNAL_TABLES = {
    "sqlite_sequence", "sqlite_stat1", "sqlite_stat4", "sqlite_master",
}

KEY_ROUND_DECIMALS = 5


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def load_feature_store(fs_path: str) -> pd.DataFrame:
    """Load the feature store CSV and return a mapping of id -> cluster_id."""
    if not os.path.exists(fs_path):
        raise FileNotFoundError(f"Feature store not found: {fs_path}")

    fs = pd.read_csv(fs_path)
    required = {"id", "cluster_id"}
    missing = required - set(fs.columns)
    if missing:
        raise ValueError(f"Feature store missing columns: {sorted(missing)}")

    return fs[["id", "cluster_id"]].drop_duplicates(subset=["id"])


def load_feature_store_name_fallback(fs_path: str) -> pd.DataFrame:
    """Fallback: build name+lat+lon -> cluster_id mapping."""
    fs = pd.read_csv(fs_path)
    fs = fs.copy()
    fs["name_key"] = fs["name"].astype(str).str.strip()
    fs["lat_key"] = fs["latitude"].round(KEY_ROUND_DECIMALS)
    fs["lon_key"] = fs["longitude"].round(KEY_ROUND_DECIMALS)
    return fs[["name_key", "lat_key", "lon_key", "cluster_id"]].drop_duplicates()


def list_user_tables(conn: sqlite3.Connection) -> List[str]:
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'", conn,
    )["name"].tolist()
    return [t for t in tables if t not in SQLITE_INTERNAL_TABLES]


def add_cluster_id_by_pk(
    df_raw: pd.DataFrame,
    fs_id_map: pd.DataFrame,
) -> Tuple[pd.DataFrame, int, int]:
    """Join cluster_id using the integer 'id' primary key."""
    df_out = df_raw.copy()

    # Drop old cluster column if present (we'll replace it with cluster_id)
    if "cluster" in df_out.columns:
        df_out = df_out.drop(columns=["cluster"])

    merged = df_out.merge(
        fs_id_map, how="left", on="id", suffixes=("", "_fs"),
    )

    # If there was already a cluster_id column, overwrite it
    if "cluster_id_fs" in merged.columns:
        merged["cluster_id"] = merged["cluster_id_fs"]
        merged = merged.drop(columns=["cluster_id_fs"])

    matched = int(merged["cluster_id"].notna().sum())
    total = len(merged)
    return merged, matched, total


def add_cluster_id_by_name(
    df_raw: pd.DataFrame,
    fs_name_map: pd.DataFrame,
) -> Tuple[pd.DataFrame, int, int]:
    """Fallback: join cluster_id using name + lat + lon composite key."""
    df_mapped = df_raw.rename(columns=COLUMN_MAPPING)
    df_out = df_raw.copy()

    if not {"name", "latitude", "longitude"}.issubset(df_mapped.columns):
        df_out["cluster_id"] = pd.NA
        return df_out, 0, len(df_out)

    df_keys = df_mapped.copy()
    df_keys["name_key"] = df_keys["name"].astype(str).str.strip()
    df_keys["lat_key"] = pd.to_numeric(df_keys["latitude"], errors="coerce").round(KEY_ROUND_DECIMALS)
    df_keys["lon_key"] = pd.to_numeric(df_keys["longitude"], errors="coerce").round(KEY_ROUND_DECIMALS)

    merged = df_keys.merge(fs_name_map, how="left", on=["name_key", "lat_key", "lon_key"])

    if "cluster" in df_out.columns:
        df_out = df_out.drop(columns=["cluster"])
    df_out["cluster_id"] = merged["cluster_id"].astype("Int64")

    matched = int(df_out["cluster_id"].notna().sum())
    return df_out, matched, len(df_out)


# ──────────────────────────────────────────────────────────────────
# Process one database
# ──────────────────────────────────────────────────────────────────

def process_db(db_filename: str) -> Dict:
    """
    Process a single DB file:
      1. Read feature store from its run folder.
      2. Join cluster_id into every table of the raw DB.
      3. Write enriched DB to runs/<db_key>/data/db_with_cluster/.
      4. Return stats dict.
    """
    db_key = os.path.splitext(db_filename)[0]
    raw_path = os.path.join(RAW_DIR, db_filename)
    run_dir = os.path.join(RUNS_DIR, db_key)
    fs_path = os.path.join(run_dir, "data", "feature_store.csv")
    out_dir = os.path.join(run_dir, "data", "db_with_cluster")
    out_path = os.path.join(out_dir, db_filename)

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw DB not found: {raw_path}")
    if not os.path.exists(fs_path):
        raise FileNotFoundError(f"Feature store not found: {fs_path}")

    # Load feature store mappings
    fs_id_map = load_feature_store(fs_path)
    fs_name_map = load_feature_store_name_fallback(fs_path)

    # Read all tables from raw DB
    with sqlite3.connect(raw_path) as conn:
        tables = list_user_tables(conn)
        if not tables:
            print(f"  [skip] No user tables in {db_filename}")
            return {"db": db_filename, "status": "skipped", "tables": []}

        table_outputs: Dict[str, pd.DataFrame] = {}
        table_stats = []

        for table in tables:
            df_raw = pd.read_sql(f"SELECT * FROM [{table}]", conn)

            # Try ID-based join first
            if "id" in df_raw.columns:
                df_out, matched, total = add_cluster_id_by_pk(df_raw, fs_id_map)
            else:
                df_out, matched, total = add_cluster_id_by_name(df_raw, fs_name_map)

            table_outputs[table] = df_out
            table_stats.append({
                "table": table,
                "matched": matched,
                "total": total,
                "match_pct": round(matched / total * 100, 1) if total else 0,
            })

    # Write enriched DB
    os.makedirs(out_dir, exist_ok=True)
    with sqlite3.connect(out_path) as out_conn:
        for table, df_out in table_outputs.items():
            df_out.to_sql(table, out_conn, index=False, if_exists="replace")

    # Print summary
    for s in table_stats:
        print(f"  {s['table']}: {s['matched']}/{s['total']} matched ({s['match_pct']}%)")

    return {
        "db": db_filename,
        "db_key": db_key,
        "status": "success",
        "output_path": out_path,
        "tables": table_stats,
    }


# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────

def main() -> None:
    if not os.path.isdir(RAW_DIR):
        raise FileNotFoundError(f"Raw DB folder not found: {RAW_DIR}")

    # Determine which DBs to process
    if TARGET_DB_FILE:
        db_files = [TARGET_DB_FILE]
    elif PROCESS_ALL:
        # Find all run dirs that have a feature_store.csv
        db_files = []
        for d in sorted(os.listdir(RUNS_DIR)):
            run_dir = os.path.join(RUNS_DIR, d)
            fs = os.path.join(run_dir, "data", "feature_store.csv")
            raw = os.path.join(RAW_DIR, d + ".db")
            if os.path.isdir(run_dir) and os.path.exists(fs) and os.path.exists(raw):
                db_files.append(d + ".db")
        if not db_files:
            raise ValueError("No training runs found with feature_store.csv")
    else:
        raise ValueError(
            "Set TARGET_DB_FILE to a specific .db filename, "
            "or set PROCESS_ALL = True to batch-process all."
        )

    print(f"Processing {len(db_files)} database(s)...\n")

    all_results = []
    for db_file in db_files:
        print(f"=== {db_file} ===")
        try:
            result = process_db(db_file)
            all_results.append(result)
        except Exception as e:
            print(f"  [ERROR] {e}")
            all_results.append({"db": db_file, "status": "error", "error": str(e)})
        print()

    # Write summary JSON
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed": len(all_results),
        "successful": sum(1 for r in all_results if r["status"] == "success"),
        "results": all_results,
    }
    summary_path = os.path.join(RUNS_DIR, "cluster_sync_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Done. Summary saved to: {summary_path}")
    total_matched = sum(
        s["matched"] for r in all_results if r.get("tables") for s in r["tables"]
    )
    total_rows = sum(
        s["total"] for r in all_results if r.get("tables") for s in r["tables"]
    )
    print(f"Total: {total_matched}/{total_rows} rows enriched with cluster_id across {len(db_files)} databases.")


if __name__ == "__main__":
    main()
