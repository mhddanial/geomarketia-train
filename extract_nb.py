import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('geomarketia_train.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Patch Cell 65
cell65 = nb['cells'][65]
src65 = ''.join(cell65.get('source', []))

NEW_SRC_65 = """\
# ── 11.2 Tampilkan batas kuantil yang digunakan ────────
if 'q1' not in globals():
    q1, q2 = df_fs["suitability_score"].quantile([0.33, 0.66])

print("=== Ambang Kuantil untuk Label ===")
print(f"Q1 (Batas Bawah Medium) : {q1:.2f}")
print(f"Q2 (Batas Bawah Tinggi) : {q2:.2f}\\n")

# Hitung dan tampilkan distribusi label
print("=== Distribusi Label Suitability ===")
distribusi_label = df_fs['suitability_band'].value_counts().reset_index()
distribusi_label.columns = ['Label', 'Jumlah Baris']
distribusi_label['Persentase'] = (distribusi_label['Jumlah Baris'] / len(df_fs) * 100).round(2).astype(str) + '%'
display(distribusi_label)
"""

# Patch Cell 69
cell69 = nb['cells'][69]
src69 = ''.join(cell69.get('source', []))

NEW_SRC_69 = """\
from IPython.display import display

if 'q1' not in globals():
    q1, q2 = df_fs["suitability_score"].quantile([0.33, 0.66])

label_counts = df_fs["suitability_band"].value_counts(dropna=False)
label_pct = (label_counts / label_counts.sum() * 100).round(2)
label_summary = pd.DataFrame({"count": label_counts, "pct": label_pct})

thresholds = pd.DataFrame({"q1": [q1], "q2": [q2]})

display(label_summary)
display(thresholds)
"""

cell65['source'] = [NEW_SRC_65]
cell69['source'] = [NEW_SRC_69]

with open('geomarketia_train.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("✓ Cells 65 and 69 patched (suitability_band instead of label, and q1 safe guard).")
