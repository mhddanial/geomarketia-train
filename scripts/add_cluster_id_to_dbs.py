import os
import sqlite3
from typing import Dict, Iterable, Tuple

import pandas as pd

RAW_DIR = os.path.join("content", "data", "raw")
OUT_DIR = os.path.join("content", "data", "processed", "db_with_cluster")
FEATURE_STORE_PATH = os.path.join("content", "data", "processed", "feature_store.csv")

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

SQLITE_INTERNAL_TABLES = {"sqlite_sequence", "sqlite_stat1", "sqlite_stat4", "sqlite_master"}

KEY_ROUND_DECIMALS = 5


def load_feature_store_mapping() -> pd.DataFrame:
    if not os.path.exists(FEATURE_STORE_PATH):
        raise FileNotFoundError(f"Feature store not found: {FEATURE_STORE_PATH}")

    fs = pd.read_csv(FEATURE_STORE_PATH)
    required = {"name", "latitude", "longitude", "cluster_id"}
    missing = required - set(fs.columns)
    if missing:
        raise ValueError(f"Feature store missing required columns: {sorted(missing)}")

    fs = fs.copy()
    fs["name_key"] = fs["name"].astype(str).str.strip()
    fs["lat_key"] = fs["latitude"].round(KEY_ROUND_DECIMALS)
    fs["lon_key"] = fs["longitude"].round(KEY_ROUND_DECIMALS)

    fs_key = fs[["name_key", "lat_key", "lon_key", "cluster_id"]].drop_duplicates()
    return fs_key


def list_user_tables(conn: sqlite3.Connection) -> Iterable[str]:
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn,
    )["name"].tolist()
    return [t for t in tables if t not in SQLITE_INTERNAL_TABLES]


def add_cluster_id_to_table(df_raw: pd.DataFrame, fs_key: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    df_mapped = df_raw.rename(columns=COLUMN_MAPPING)

    if not {"name", "latitude", "longitude"}.issubset(df_mapped.columns):
        df_out = df_raw.copy()
        df_out["cluster_id"] = pd.NA
        return df_out, 0, len(df_out)

    df_keys = df_mapped.copy()
    df_keys["name_key"] = df_keys["name"].astype(str).str.strip()
    df_keys["lat_key"] = pd.to_numeric(df_keys["latitude"], errors="coerce").round(KEY_ROUND_DECIMALS)
    df_keys["lon_key"] = pd.to_numeric(df_keys["longitude"], errors="coerce").round(KEY_ROUND_DECIMALS)

    merged = df_keys.merge(
        fs_key,
        how="left",
        on=["name_key", "lat_key", "lon_key"],
    )

    df_out = df_raw.copy()
    df_out["cluster_id"] = merged["cluster_id"].astype("Int64")

    matched = int(df_out["cluster_id"].notna().sum())
    total = int(len(df_out))
    return df_out, matched, total


def process_db_file(db_path: str, fs_key: pd.DataFrame) -> None:
    filename = os.path.basename(db_path)
    out_path = os.path.join(OUT_DIR, filename)

    with sqlite3.connect(db_path) as conn:
        tables = list_user_tables(conn)
        if not tables:
            print(f"[skip] No user tables in {filename}")
            return

        table_outputs: Dict[str, pd.DataFrame] = {}
        stats = []
        for table in tables:
            df_raw = pd.read_sql(f"SELECT * FROM [{table}]", conn)
            df_out, matched, total = add_cluster_id_to_table(df_raw, fs_key)
            table_outputs[table] = df_out
            stats.append((table, matched, total))

    os.makedirs(OUT_DIR, exist_ok=True)
    with sqlite3.connect(out_path) as out_conn:
        for table, df_out in table_outputs.items():
            df_out.to_sql(table, out_conn, index=False, if_exists="replace")

    for table, matched, total in stats:
        print(f"{filename} :: {table} -> matched {matched}/{total}")


def main() -> None:
    if not os.path.isdir(RAW_DIR):
        raise FileNotFoundError(f"Raw DB folder not found: {RAW_DIR}")

    fs_key = load_feature_store_mapping()
    db_files = [
        os.path.join(RAW_DIR, f)
        for f in os.listdir(RAW_DIR)
        if f.lower().endswith(".db")
    ]

    if not db_files:
        print(f"No .db files found in {RAW_DIR}")
        return

    print(f"Found {len(db_files)} .db files")
    for db_path in sorted(db_files):
        process_db_file(db_path, fs_key)

    print(f"\nDone. Output folder: {OUT_DIR}")


if __name__ == "__main__":
    main()
