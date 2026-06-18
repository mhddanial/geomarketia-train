import json, sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')

runs_dir = "content/runs"
run_dirs = sorted(os.listdir(runs_dir))

print(f"Total runs: {len(run_dirs)}\n")

for db_key in run_dirs:
    if not os.path.isdir(os.path.join(runs_dir, db_key)):
        continue
    model_dir = os.path.join(runs_dir, db_key, "models")
    data_dir  = os.path.join(runs_dir, db_key, "data")
    report_dir = os.path.join(runs_dir, db_key, "reports")

    print(f"=== {db_key} ===")

    # Check regression model
    reg_models = glob.glob(os.path.join(model_dir, "reg_location_reco_v*.joblib"))
    rf_models  = glob.glob(os.path.join(model_dir, "rf_location_reco_v*.joblib"))

    reg_meta_path = os.path.join(model_dir, "regression_metadata.json")
    rf_meta_path  = os.path.join(model_dir, "rf_metadata.json")

    # Prefer regression metadata
    if os.path.exists(reg_meta_path):
        with open(reg_meta_path, 'r') as f:
            meta = json.load(f)
        model_type = meta.get("model_type", "unknown")
        selected = meta.get("selected_model", "N/A")
        schema_ver = meta.get("feature_schema_version", "N/A")
        features = meta.get("features", [])
        removed = meta.get("removed_features", [])
        thresholds = meta.get("suitability_band_thresholds", {})
        metrics = meta.get("metrics", {})
        best = metrics.get("best_model", {})

        print(f"  Type             : {model_type}")
        print(f"  Selected model   : {selected}")
        print(f"  Schema version   : {schema_ver}")
        print(f"  Feature count    : {len(features)}")
        print(f"  Removed features : {removed}")
        print(f"  Band thresholds  : {thresholds}")
        if best:
            print(f"  Best RMSE        : {best.get('rmse', 'N/A')}")
            print(f"  Best R2          : {best.get('r2', 'N/A')}")
            print(f"  Best Spearman    : {best.get('spearman_rank', 'N/A')}")
            print(f"  Best P@20        : {best.get('precision_at_20', 'N/A')}")
    elif os.path.exists(rf_meta_path):
        with open(rf_meta_path, 'r') as f:
            meta = json.load(f)
        model_type = meta.get("model_type", "classifier-old")
        features = meta.get("features", [])
        print(f"  Type             : {model_type}")
        print(f"  Feature count    : {len(features)}")
        if "metrics" in meta:
            f1 = meta["metrics"].get("f1_macro", "N/A")
            print(f"  F1 macro (OLD)   : {f1}")
    else:
        print("  NO METADATA FOUND")

    # Check key files
    fs_path = os.path.join(data_dir, "feature_store.csv")
    grid_path = os.path.join(data_dir, "base_candidate_grid.parquet")
    mc_path = os.path.join(report_dir, "model_comparison.csv")
    shap_path = os.path.join(report_dir, "reg_shap_importance.csv")

    print(f"  feature_store.csv: {'YES (' + str(round(os.path.getsize(fs_path)/1024)) + ' KB)' if os.path.exists(fs_path) else 'MISSING'}")
    print(f"  base_candidate_grid.parquet: {'YES' if os.path.exists(grid_path) else 'MISSING'}")
    print(f"  model_comparison.csv: {'YES' if os.path.exists(mc_path) else 'MISSING'}")
    print(f"  reg_shap_importance.csv: {'YES' if os.path.exists(shap_path) else 'MISSING'}")
    print(f"  Regression models: {len(reg_models)} | Old RF models: {len(rf_models)}")
    print()
