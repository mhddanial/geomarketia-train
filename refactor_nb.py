import json
import re

with open('geomarketia_train.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
# Reorder: 0-24, 38-44, 25-37, 45-66
new_cells = cells[0:25] + cells[38:45] + cells[25:38] + cells[45:]

# Step 1: Mapping headers explicitly since automatic regex might miss edges.
# I'll create a mapping of old cell index (in new_cells) to new titles.
mapping = {
    1: {"md": "# Tahap 1 \u2014 Install & Import Library"},
    2: {"cd": "# \u2500\u2500 1.1 Install Libraries \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    3: {"cd": "# \u2500\u2500 1.2 Import & Core \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    4: {"md": "# Tahap 2 \u2014 Exploratory Data Analysis (EDA)"},
    5: {"md": "## 2.1 Scan file dataset .db"},
    6: {"cd": "# \u2500\u2500 2.1 Konfigurasi folder & validasi \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    7: {"md": "## 2.2 Peek skema tiap file"},
    8: {"cd": "# \u2500\u2500 2.2 Peek skema & tabel internal \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    9: {"md": "## 2.3 Definisi mapping kolom"},
    10: {"cd": "# \u2500\u2500 2.3 Standarisasi nama kolom \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    11: {"md": "## 2.4 Gabungkan semua .db jadi Dataframe"},
    12: {"cd": "# \u2500\u2500 2.4 Load dan Gabungkan Semua Tabel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    13: {"md": "## 2.5 Verifikasi hasil gabungan"},
    14: {"cd": "# \u2500\u2500 2.5a Deteksi Missing Values \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    15: {"cd": "# \u2500\u2500 2.5b Cek Baris Kosong pada Kolom Kritis \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    16: {"cd": "# \u2500\u2500 2.5c Hapus Baris Invalid \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    17: {"md": "# Tahap 3 \u2014 Konfigurasi & Konstanta"},
    18: {"cd": "# \u2500\u2500 3.1 Path & Parameter Global \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    19: {"md": "# Tahap 4 \u2014 Ingestion & Validation Gate"},
    20: {"cd": "# \u2500\u2500 4.1 Load Data untuk Validasi \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    21: {"cd": "# \u2500\u2500 4.2 Validation Gate (Aturan 1-6) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    22: {"md": "# Tahap 5 \u2014 Preprocessing & Konversi Koordinat"},
    23: {"cd": "# \u2500\u2500 5.1 Konversi koordinat WGS84 \u2192 UTM Zone 48N \u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    24: {"cd": "# \u2500\u2500 5.2 Persiapan fitur atribut tambahan (Price/Rating) \u2500"},
    
    # These were Tahap 5.5 (indices 25-31 in new_cells)
    25: {"md": "# Tahap 6 \u2014 Integrasi Demografi (RBI & Populasi) & OSM"},
    26: {"cd": "# \u2500\u2500 6.1 Load Population Excel \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    27: {"cd": "# \u2500\u2500 6.2 Load RBI Shapefiles \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    28: {"cd": "# \u2500\u2500 6.3 Build Exclusion Mask (Water + Forests) \u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    29: {"cd": "# \u2500\u2500 6.4 Fetch OSM Road Network (Batam) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    30: {"cd": "# \u2500\u2500 6.5 Pre-compute Base Candidate Grid \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    31: {"cd": "# \u2500\u2500 6.6 Assign Demographics & Road Distance to DataFrame \u2500\u2500"},
    
    # These were Tahap 6, 7 (indices 32-44 in new_cells)
    32: {"md": "# Tahap 7 \u2014 DBSCAN Clustering"},
    33: {"cd": "# \u2500\u2500 7.1 Jalankan DBSCAN \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    34: {"cd": "# \u2500\u2500 7.2 Evaluasi Kualitas Clustering \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    35: {"cd": "# \u2500\u2500 7.3 Hitung Centroid per Cluster & Jarak ke Centroid \u2500\u2500"},
    36: {"cd": "# \u2500\u2500 7.4 Hitung Fitur Density (Kompetitor dalam Radius) \u2500\u2500\u2500"},
    37: {"md": "# Tahap 8 \u2014 Visualisasi Hasil Clustering"},
    38: {"cd": "# \u2500\u2500 8.1 Peta Sebaran Cluster \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    39: {"md": "## 8.2 Tuning Grid DBSCAN (Auto Ranking)"},
    40: {"cd": "# \u2500\u2500 8.3 Tuning Grid DBSCAN (Auto Ranking) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    
    # These were Tahap 8
    41: {"md": "# Tahap 9 \u2014 Simpan ke Feature Store"},
    42: {"cd": "# \u2500\u2500 9.1 Tentukan kolom yang masuk Feature Store \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    43: {"cd": "# \u2500\u2500 9.2 Simpan Feature Store \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    44: {"cd": "# \u2500\u2500 9.3 Simpan Metadata Clustering \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    
    # Summaries & Quality Gate (indices 45-48 in new_cells)
    45: {"md": "## 9.4 Ringkasan & Langkah Selanjutnya"},
    46: {"cd": "# \u2500\u2500 9.5 Final Sanity Check \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    47: {"md": "# Tahap 10 \u2014 Quality Gate DBSCAN"},
    48: {"cd": "# \u2500\u2500 10.1 Quality Gate DBSCAN \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    
    # RF Training (indices 49-66)
    49: {"md": "# Tahap 11 \u2014 Random Forest Training (Rekomendasi Lokasi)"},
    50: {"md": "### 11.1 Load Feature Store & Label Proxy"},
    51: {"cd": "# \u2500\u2500 11.1 Load Feature Store + Buat Label Proxy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    52: {"md": "### 11.2 Ringkasan Label (Ambang Batas)"},
    53: {"cd": "# \u2500\u2500 11.2 Tampilkan batas kuantil yang digunakan \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    54: {"md": "### 11.3 Negative Sampling"},
    55: {"cd": "# \u2500\u2500 11.3 Sample Negative Points (No Roads / Zero Pop) \u2500\u2500\u2500"},
    56: {"cd": "# \u2500\u2500 11.4 Ringkasan Distribusi Label Setelah Sampling \u2500\u2500\u2500\u2500\u2500"},
    57: {"md": "### 11.5 Spatial Split & Train Random Forest"},
    58: {"cd": "# \u2500\u2500 11.5 Spatial Split + Train Random Forest \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    59: {"md": "### 11.6 Evaluasi Model (Table & Visual)"},
    60: {"cd": "# \u2500\u2500 11.6 Evaluasi Model Output \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    61: {"md": "### 11.7 SHAP Explainability (Global + Local)"},
    62: {"cd": "# \u2500\u2500 11.7 SHAP Explainability \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
    63: {"md": "### 11.8 Simpan Model & Metadata"},
    64: {"cd": "# \u2500\u2500 11.8 Simpan Model + Metadata \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"},
}

for i, cell in enumerate(new_cells):
    if i in mapping:
        source = cell.get('source', [])
        changes = mapping[i]
        
        if cell['cell_type'] == 'markdown' and 'md' in changes:
            # Replace the first heading or the first line
            new_header = changes['md']
            if source:
                found = False
                for j, line in enumerate(source):
                    if line.strip().startswith('#'):
                        source[j] = new_header + ('\\n' if line.endswith('\\n') else '')
                        found = True
                        break
                if not found:
                    source.insert(0, new_header + '\\n')
            else:
                source.append(new_header + '\\n')
            cell['source'] = source
            
        elif cell['cell_type'] == 'code' and 'cd' in changes:
            new_comment = changes['cd']
            if source:
                # Replace the first comment or insert it at top
                found = False
                for j, line in enumerate(source):
                    if line.strip().startswith('#'):
                        # Keep newlines intact
                        source[j] = new_comment + ('\\n' if line.endswith('\\n') else '')
                        found = True
                        break
                if not found:
                    source.insert(0, new_comment + '\\n')
            else:
                source.append(new_comment + '\\n')
            cell['source'] = source

nb['cells'] = new_cells

with open('geomarketia_train.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook successfully refactored and reordered!")
