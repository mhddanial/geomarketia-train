# PRD — GeoMarket AI
**Implementasi Artificial Intelligence untuk Pengolahan dan Prediksi Data Pasar Berbasis Geospasial**

| Atribut | Keterangan |
|---|---|
| Nomor ID | IF-4PD-04 |
| Program Studi | D3 Teknik Informatika |
| Kejuruan | Artificial Intelligence |
| Manajer Proyek | Agung Riyadi, S.Si., M.Kom |
| Tim AI | Muhammad Danial (3312401042), Ananda Khusnul Hotimah (3312401044) |
| Versi | 1.0 — April 2026 |

---

## 1. Apa yang Ingin Kami Bangun

GeoMarket AI adalah sistem kecerdasan buatan berbasis geospasial yang dirancang untuk menganalisis kondisi pasar dan memberikan rekomendasi lokasi usaha kepada pelaku UMKM di Kota Batam. Sistem ini mengolah data lokasi usaha nyata dari Batam menggunakan Machine Learning (DBSCAN + Random Forest) dan Explainable AI (SHAP), kemudian menyajikan hasilnya melalui REST API yang dikonsumsi oleh dashboard web interaktif.

Sistem ini **bukan** aplikasi peta biasa. Yang membedakannya adalah kemampuan untuk:

- Mengelompokkan zona konsentrasi usaha secara otomatis menggunakan analisis kepadatan spasial
- Menghitung tingkat saturasi pasar di setiap area dan mendeteksi di mana pasar masih kosong
- Memberikan skor kelayakan lokasi untuk kategori usaha tertentu, disertai penjelasan mengapa skor tersebut dihasilkan

Output utama sistem ini adalah **model AI (.joblib) + layanan API (FastAPI)** yang dapat diintegrasikan oleh tim web ke dalam dashboard interaktif.

---

## 2. Permasalahan yang Diselesaikan

Kota Batam memiliki lebih dari 75.575 UMKM aktif (2024), dengan lebih dari 75% bergerak di sektor kuliner. Tingginya persaingan pada kategori usaha yang sama menyebabkan banyak pelaku usaha memilih lokasi secara intuitif tanpa dasar data — yang sering berujung pada kerugian bisnis.

Tiga permasalahan spesifik yang menjadi target sistem ini:

1. Tidak ada alat yang mampu mengidentifikasi secara otomatis area mana yang sudah jenuh (*over-saturated*) dan area mana yang masih berpeluang (*under-served*)
2. Data geospasial yang tersedia dari layanan peta digital hanya disajikan sebagai peta statis, tanpa analisis kecerdasan buatan di atasnya
3. Tidak ada sistem rekomendasi lokasi berbasis data yang dapat diakses oleh pelaku UMKM skala kecil

---

## 3. Pengguna & Aktor Sistem

| Aktor | Deskripsi | Hak Akses |
|---|---|---|
| **Guest** | Pengguna yang belum memiliki akun | Register, Login |
| **Pengguna Umum** | Pelaku UMKM atau stakeholder yang menggunakan fitur analisis | Seluruh fitur analisis pasar dan visualisasi |
| **Admin** | Pengelola sistem yang bertanggung jawab atas kualitas data dan konfigurasi model | Akses penuh: manajemen data, pengguna, konfigurasi AI, log sistem |

---

## 4. Kebutuhan Fungsional

### 4.1 Modul Autentikasi

| Kode | Fitur | Deskripsi |
|---|---|---|
| KF-AUTH-01 | Register akun | Pengguna baru mendaftar dengan nama lengkap, email, password, dan konfirmasi password. Sistem memvalidasi format email, keunikan email (case-insensitive), dan kekuatan password (minimal 8 karakter). Akun dibuat dengan peran default `pengguna_umum`. |
| KF-AUTH-02 | Login | Pengguna login menggunakan email dan password. Sistem menerbitkan JWT token setelah validasi kredensial berhasil. Percobaan login gagal dibatasi maksimal 5x sebelum akun dikunci sementara (15 menit). |
| KF-AUTH-03 | Logout | Pengguna mengakhiri sesi secara eksplisit. Sistem menginvalidasi JWT token aktif dengan memasukkannya ke blacklist sehingga token tidak dapat digunakan kembali setelah logout. |
| KF-AUTH-04 | Otorisasi per endpoint | Setiap endpoint API dilindungi middleware autentikasi JWT. Sistem membedakan akses berdasarkan peran (`pengguna_umum` vs `admin`). Endpoint yang memerlukan hak admin mengembalikan `403 Forbidden` jika diakses oleh pengguna umum. |

**Relasi include pada modul ini:**

- `Register akun` → selalu memanggil `Validasi format input`, `Periksa keunikan email`, `Hash password (bcrypt)`
- `Login` → selalu memanggil `Validasi kredensial`, `Terbitkan JWT token`
- `Logout` → selalu memanggil `Invalidasi JWT token`

---

### 4.2 Modul Admin

| Kode | Fitur | Deskripsi |
|---|---|---|
| KF-ADMIN-01 | Import data lokasi | Admin mengimpor data lokasi usaha dalam format CSV atau JSON. Setiap baris minimal harus mengandung: `latitude`, `longitude`, `nama_tempat`, `kategori`, `price_level`, dan `url`. Sistem memvalidasi format dan kelengkapan sebelum menyimpan. |
| KF-ADMIN-02 | Validasi & bersihkan data | Sistem secara otomatis mendeteksi anomali pada data yang diimpor: koordinat di luar batas wilayah Batam (lat 1.0°–1.3°N, lon 103.9°–104.2°E), duplikat (nama + lat + lon), nilai null pada kolom wajib, dan kategori yang tidak dikenal. Admin menerima data quality report (jumlah baris valid, duplikat, invalid) sebelum memutuskan menyimpan atau membatalkan import. |
| KF-ADMIN-03 | Kelola data lokasi | Admin dapat melihat daftar seluruh data yang telah diimpor, mengedit entri individual (nama, kategori, koordinat), dan menghapus data yang tidak valid atau sudah tidak relevan. Penghapusan bersifat soft-delete untuk menjaga audit trail. |
| KF-ADMIN-04 | Konfigurasi parameter AI | Admin mengatur parameter DBSCAN (`eps` dalam meter, `min_samples`) dan radius analisis kompetitor (500m, 750m, atau 1km) melalui antarmuka konfigurasi. Nilai default mengikuti konfigurasi training terbaru dan tersimpan di riwayat konfigurasi beserta timestamp dan identitas admin yang mengubah. |
| KF-ADMIN-05 | Kelola pengguna | Admin dapat melihat daftar seluruh pengguna terdaftar beserta peran dan status akun. Admin dapat mengubah peran pengguna (`pengguna_umum` ↔ `admin`) dan menonaktifkan akun tanpa menghapus data riwayat aktivitasnya. |
| KF-ADMIN-06 | Monitoring log sistem | Admin dapat melihat log aktivitas sistem yang mencakup: waktu dan IP setiap percobaan login (berhasil maupun gagal), endpoint API yang paling sering dipanggil, error yang terjadi pada proses AI, dan statistik penggunaan harian (jumlah request, rata-rata latensi per endpoint). |
| KF-ADMIN-07 | Trigger retraining model | Admin memicu proses retraining model AI secara manual setelah data baru diimpor dalam jumlah signifikan. Sistem menampilkan status proses (berjalan / selesai / gagal) beserta metrik evaluasi model baru dibandingkan model sebelumnya (Silhouette Score untuk DBSCAN, F1-Score untuk Random Forest). Admin dapat memilih menerapkan model baru atau mempertahankan model lama jika performanya lebih buruk. |

**Relasi include & extend pada modul ini:**

- `Import data lokasi` → selalu memanggil `Validasi & bersihkan data`
- `Konfigurasi parameter AI` → selalu memanggil `Simpan riwayat konfigurasi`
- `Trigger retraining model` → selalu memanggil `Lihat metrik evaluasi perbandingan`
- `Kelola pengguna` → secara opsional memanggil `Ubah peran pengguna` dan `Nonaktifkan akun` (relasi extend)

---

### 4.3 Modul Data & Visualisasi

| Kode | Fitur | Deskripsi |
|---|---|---|
| KF-01 | Get data endpoint | Sistem menyediakan endpoint untuk mengambil data tempat usaha: `latitude`, `longitude`, `nama_tempat`, `kategori`, `price_level`, `rating`, dan `url`. Mendukung pagination untuk dataset besar. |
| KF-02 | Search & filter data | Sistem menyediakan endpoint pencarian dan filter berdasarkan: kategori usaha, rating minimum, price level, keyword nama tempat, dan radius dari koordinat tertentu. |
| KF-03 | Peta sebaran usaha | Sistem menghasilkan data sebaran titik usaha di seluruh wilayah Batam yang dapat divisualisasikan sebagai peta interaktif. Data membedakan area dengan kepadatan tinggi vs rendah. |
| KF-04 | Heatmap keseluruhan | Sistem menghasilkan data grid kepadatan usaha untuk seluruh wilayah Batam menggunakan Kernel Density Estimation (KDE), siap dirender sebagai heatmap layer pada peta. |
| KF-05 | Heatmap per kategori | Sistem menghasilkan heatmap kepadatan yang difilter berdasarkan kategori usaha tertentu (extend dari heatmap keseluruhan — hanya aktif jika parameter kategori disertakan). |
| KF-06 | Komposisi pasar | Sistem menghitung dan mengembalikan persentase tiap kategori usaha di suatu wilayah atau dalam radius tertentu dari koordinat yang diberikan. |
| KF-07 | Kategori dominan per wilayah | Sistem mengembalikan ranking kategori usaha yang paling banyak ditemukan per area (berdasarkan grid, cluster, atau kelurahan), diurutkan dari yang paling dominan. |

---

### 4.4 Modul Analisis AI

| Kode | Fitur | Deskripsi |
|---|---|---|
| KF-08 | Klasterisasi area lokasi | Sistem mengelompokkan seluruh titik usaha ke dalam zona konsentrasi menggunakan algoritma DBSCAN. Setiap titik mendapat `cluster_id` (nilai `-1` untuk titik yang diklasifikasikan sebagai noise). Parameter eps dan min_samples dikonfigurasi oleh admin. |
| KF-09 | Klasterisasi per kategori | Sistem menjalankan proses clustering DBSCAN secara terpisah untuk setiap kategori usaha, sehingga karakteristik zona per segmen pasar dapat diidentifikasi secara independen. |
| KF-10 | Analisis kompetitor | Sistem menghitung jumlah usaha bersaing (kategori sama) dalam radius yang ditentukan (500m / 750m / 1km) dari koordinat yang diberikan, beserta kepadatan per kategori di area tersebut. |
| KF-11 | Deteksi kesenjangan pasar | Sistem mendeteksi area yang memiliki kepadatan aktivitas tinggi namun kekurangan kategori usaha tertentu. Contoh: area padat penduduk tanpa restoran, atau area dengan banyak kafe murah namun tidak ada kafe premium. Gap score dihitung berdasarkan selisih antara demand indicator dan supply actual. |
| KF-12 | Rekomendasi lokasi usaha | Sistem memberikan rekomendasi koordinat lokasi terbaik untuk kategori usaha yang dipilih pengguna, berdasarkan skor kelayakan (suitability score) yang dihasilkan Random Forest. Setiap rekomendasi disertai penjelasan SHAP yang menjelaskan kontribusi masing-masing fitur terhadap skor tersebut (misalnya: "Skor tinggi karena kepadatan kompetitor rendah dan hotspot score area tinggi"). |
| KF-13 | Indeks saturasi pasar | Sistem menghitung Market Saturation Index (MSI) = jumlah usaha kategori X / luas area (km²). Setiap area diberi label: `over-saturated` (MSI di atas threshold), `balanced`, atau `under-served` (MSI di bawah threshold). |
| KF-14 | Identifikasi motif pasar | Sistem mengidentifikasi pola dominan di setiap wilayah dan mengklasifikasikan karakteristik ekonomi area berdasarkan kombinasi kategori usaha, tingkat harga, dan kepadatan — menghasilkan profil pasar per zona. |

**Relasi include pada modul ini:**

- `Klasterisasi area` → selalu memanggil `Jalankan DBSCAN`
- `Analisis kompetitor` → selalu memanggil `Hitung radius pesaing`
- `Deteksi kesenjangan pasar` → selalu memanggil `Hitung saturasi pasar`
- `Rekomendasi lokasi` → selalu memanggil `Scoring model (RF + SHAP)` dan `Hitung saturasi pasar`

---

## 5. Kebutuhan Non-Fungsional

| Kode | Aspek | Keterangan | Metrik Target |
|---|---|---|---|
| KNF-01 | Security | Seluruh endpoint dilindungi JWT. Password di-hash dengan bcrypt cost factor ≥ 10. Input divalidasi dan disanitasi sebelum menyentuh database atau model. Rate limiting diterapkan per IP. | 0 endpoint tanpa autentikasi. Rate limit: 100 req/menit per IP. Login lockout setelah 5x gagal. |
| KNF-02 | Performance | Query analitik berat (heatmap, clustering, saturation) dijalankan sebagai batch dan hasilnya disimpan di cache. Real-time inference hanya untuk prediksi satu titik dan top-N rekomendasi. | Respons endpoint data < 1 detik. Endpoint analisis AI < 5 detik. |
| KNF-03 | Maintainability | Kode mengikuti standar PEP8. Setiap fungsi terdokumentasi. Logging terstruktur pada setiap endpoint dan proses AI. Model dapat diganti versi tanpa mengubah logika API. | Log tersimpan per endpoint. Versi model tercatat di registry dengan metadata lengkap. |
| KNF-04 | Reliability | API tidak crash saat menerima input tidak valid: lat/lon kosong, kategori tidak dikenal, token kedaluwarsa, atau parameter di luar rentang. Semua error dikembalikan dalam format JSON terstandar dengan kode dan pesan deskriptif. | API uptime ≥ 99% pada sesi demo. 0 unhandled exception pada input edge case. |
| KNF-05 | Usability | Seluruh endpoint didokumentasikan otomatis melalui Swagger UI (FastAPI built-in). Pesan error harus informatif dan dapat dipahami oleh developer frontend. | Seluruh endpoint dapat diuji langsung dari Swagger UI. |
| KNF-06 | Scalability | Arsitektur modular: model AI dapat diperbarui atau diganti versi tanpa mengubah kode API. Feature store memastikan konsistensi data antara tahap training dan serving. | Model dapat di-swap tanpa perubahan kode API. Training dan serving menggunakan feature store yang sama. |

---

## 6. Arsitektur Sistem

Sistem dibangun dalam tiga lapisan pipeline yang saling terhubung.

### 6.1 Data Layer

Tanggung jawab lapisan ini adalah memastikan seluruh data masuk dalam kondisi bersih, tervalidasi, dan dalam format yang siap dikonsumsi oleh model.

```
SQLite (.db)
    └─ Ingestion (Pandas read_sql)
        └─ Validation Gate
            ├─ Validasi rentang koordinat (batas wilayah Batam)
            ├─ Deduplikasi (nama + lat + lon)
            ├─ Normalisasi kategori
            └─ [REJECT → Data Quality Report]
        └─ Preprocessing & Feature Engineering (GeoPandas, Shapely, Pyproj)
            ├─ Konversi CRS: WGS84 → UTM (koordinat meter)
            └─ Kalkulasi: review_log = log(1 + review_count)
        └─ Feature Store (tabel terproses, siap dikonsumsi training & serving)
```

**Fitur yang dihasilkan (Feature Store):**

| Kelompok | Nama Fitur | Deskripsi |
|---|---|---|
| Identitas | `id`, `name`, `source_category` | Identitas dasar titik usaha |
| Koordinat | `latitude`, `longitude`, `x_utm`, `y_utm` | Koordinat WGS84 dan UTM (meter) |
| Geospasial | `cluster_id` | Hasil DBSCAN |
| Geospasial | `dist_to_cluster_centroid_m` | Jarak ke centroid cluster |
| Geospasial | `competitor_density_500m` | Jumlah semua usaha dalam radius 500m |
| Geospasial | `competitor_density_1km` | Jumlah semua usaha dalam radius 1km |
| Geospasial | `same_category_density_500m` | Jumlah usaha kategori sama dalam 500m |
| Geospasial | `nearest_neighbor_dist_m` | Jarak ke usaha terdekat (meter) |
| Atribut | `rating` | Rating usaha dari dataset |
| Atribut | `review_log` | log(1 + jumlah review) |
| Atribut | `price_level` | Level harga (jika tersedia) |

**Fitur tambahan saat training Random Forest:**

| Kelompok | Nama Fitur | Deskripsi |
|---|---|---|
| Geospasial | `hotspot_score` | Nilai KDE pada titik usaha (dibuat saat training RF) |
| Turunan | `saturation_index` | `same_category_density_500m` dibagi luas area 500m (km^2) |

---

### 6.2 Model Layer

Lapisan ini bertanggung jawab membangun kecerdasan sistem — dari clustering hingga scoring dan explainability.

```
Feature Store
    └─ DBSCAN Clustering
        ├─ Input: koordinat UTM (lat_m, lon_m)
        ├─ Parameter: eps (meter), min_samples (dari konfigurasi admin)
        ├─ Default training mengikuti konfigurasi admin terbaru (tercatat pada metadata run)
        └─ Output: cluster_id per titik (-1 = noise)
    └─ Feature Merge
        └─ Gabungkan cluster_id + seluruh fitur geospasial ke dalam satu tabel
    └─ Random Forest Training
        ├─ Fitur: rating, review_log, hotspot_score, competitor_density_500m,
        │        same_category_density_500m, nearest_neighbor_dist_m,
        │        dist_to_cluster_centroid_m, cluster_id
        ├─ Label: suitability_score proxy (High / Medium / Low)
        ├─ Strategi split: Spatial Split (grid 1km × 1km)
        ├─ Tujuan: hindari kebocoran data geografis antara train dan test set
        └─ Output: model terlatih
    └─ SHAP (Explainable AI)
        └─ Hitung kontribusi setiap fitur terhadap prediksi model
    └─ Model Registry
        ├─ File: models/rf_location_reco_v{n}.joblib
        └─ Metadata: models/metadata.json
            ├─ tanggal_training
            ├─ versi_dataset
            ├─ parameter_dbscan
            ├─ parameter_rf
            ├─ daftar_fitur
            └─ metrik_evaluasi (Silhouette Score, F1, Confusion Matrix)
```

**Label Proxy — Suitability Score:**

Label dibentuk secara programatik dari kombinasi sinyal pasar yang tersedia, dikondisikan per kategori usaha target (`k`):

```
score(k) = (rating × 0.25)
         + (review_log × 0.20)
         + (hotspot_score × 0.25)
         - (same_category_density_500m(k) × 0.20)
         - (saturation_index(k) × 0.10)

Kuantil:
  - Atas 33%  → High
  - Tengah 33% → Medium
  - Bawah 33%  → Low
```

Label ini bersifat proxy (bukan ground truth lapangan) dan harus didokumentasikan keterbatasannya dalam laporan akhir. Validasi dilakukan secara kualitatif (expert review terhadap top-10 rekomendasi pada peta Batam) dan secara statistik (verifikasi bahwa titik berlabel High memiliki rating lebih tinggi dan kompetitor lebih sedikit dibanding berlabel Low).

---

### 6.3 Application Layer & MLOps

Lapisan ini bertanggung jawab melayani permintaan pengguna dan memantau performa sistem setelah deployment.

```
Model Registry
    └─ Fallback / Rollback Gate
        ├─ Jika model baru lebih baik → terapkan
        └─ Jika model baru lebih buruk atau error → rollback ke versi sebelumnya
    └─ Backend API (FastAPI)
        ├─ Batch Inference (disimpan di Cache Layer)
        │   ├─ DBSCAN clustering results
        │   ├─ Heatmap grid data
        │   ├─ Market gap detection
        │   └─ Saturation index per wilayah
        └─ Real-time Inference (on-demand)
            ├─ Prediksi skor satu titik koordinat
            └─ Top-N location recommendation + SHAP values
    └─ Frontend Dashboard (Next.js) — dikembangkan tim web
    └─ Monitoring
        ├─ Data drift: distribusi fitur penting (density, review_log, rating)
        ├─ Output drift: distribusi skor rekomendasi
        ├─ Sistem: response time, error rate, request volume
        └─ Retrain trigger → loop kembali ke Model Layer
```

**Strategi Fallback:**

Jika model mengalami degradasi atau error saat serving, sistem beralih ke mode heuristik:

```
heuristic_score = (demand_indicator - competitor_density) / normalization_factor
```

di mana `demand_indicator` adalah hotspot score KDE dan `competitor_density` adalah jumlah usaha sejenis dalam radius 500m.

---

## 7. Spesifikasi API Endpoint

Semua endpoint menggunakan prefix `/api/v1`. Format respons: JSON. Endpoint terproteksi memerlukan header `Authorization: Bearer <token>`.

### 7.1 Autentikasi

| Method | Endpoint | Deskripsi | Auth | Response |
|---|---|---|---|---|
| `POST` | `/auth/register` | Daftar akun baru. Body: `nama`, `email`, `password`, `konfirmasi_password` | Tidak | `201` — data akun (tanpa password) |
| `POST` | `/auth/login` | Login dan dapatkan JWT. Body: `email`, `password` | Tidak | `200` — `access_token`, `token_type`, `role` |
| `POST` | `/auth/logout` | Invalidasi token aktif | Ya | `200` — pesan sukses |

### 7.2 Admin

| Method | Endpoint | Deskripsi | Auth |
|---|---|---|---|
| `POST` | `/admin/data/import` | Import data lokasi dari CSV/JSON | Admin |
| `GET` | `/admin/data` | Daftar seluruh data lokasi | Admin |
| `PATCH` | `/admin/data/{id}` | Edit entri data lokasi | Admin |
| `DELETE` | `/admin/data/{id}` | Hapus data lokasi (soft-delete) | Admin |
| `GET` | `/admin/config/ai` | Lihat konfigurasi parameter AI aktif | Admin |
| `PUT` | `/admin/config/ai` | Perbarui parameter DBSCAN dan radius | Admin |
| `GET` | `/admin/users` | Daftar seluruh pengguna | Admin |
| `PATCH` | `/admin/users/{id}/role` | Ubah peran pengguna | Admin |
| `PATCH` | `/admin/users/{id}/status` | Aktifkan / nonaktifkan akun | Admin |
| `GET` | `/admin/logs` | Log aktivitas dan statistik sistem | Admin |
| `POST` | `/admin/model/retrain` | Trigger retraining model AI | Admin |
| `GET` | `/admin/model/retrain/{job_id}` | Cek status dan metrik retraining | Admin |

### 7.3 Analisis (Pengguna Umum)

| Method | Endpoint | Deskripsi | Auth |
|---|---|---|---|
| `GET` | `/places` | Ambil data tempat dengan filter opsional | Ya |
| `GET` | `/places/search` | Pencarian berdasarkan parameter query | Ya |
| `GET` | `/analysis/heatmap` | Data heatmap keseluruhan (KDE grid) | Ya |
| `GET` | `/analysis/heatmap/{kategori}` | Data heatmap per kategori usaha | Ya |
| `GET` | `/analysis/clusters` | Hasil DBSCAN — cluster_id per titik | Ya |
| `GET` | `/analysis/competition` | Jumlah kompetitor dalam radius tertentu | Ya |
| `GET` | `/analysis/market-gap` | Deteksi kesenjangan pasar per area | Ya |
| `GET` | `/analysis/saturation` | Market Saturation Index per wilayah | Ya |
| `GET` | `/analysis/market-motif` | Profil dan klasifikasi pasar per zona | Ya |
| `GET` | `/recommendation/location` | Rekomendasi lokasi + skor + SHAP values | Ya |

---

## 8. Stack Teknologi

| Kategori | Teknologi | Kegunaan |
|---|---|---|
| Backend & API | Python 3.10+, FastAPI | Framework utama layanan API dan logika bisnis |
| Machine Learning | Scikit-learn, SHAP | Implementasi DBSCAN, Random Forest, Explainable AI |
| Geospasial | GeoPandas, Shapely, Pyproj | Transformasi koordinat, perhitungan radius spasial |
| Data Processing | Pandas, NumPy | Manipulasi data, feature engineering, validasi dataset |
| Database | SQLite | Penyimpanan data lokasi usaha dan feature store |
| Model Registry | Format `.joblib` + `metadata.json` | Versioning model AI yang telah dilatih |
| Training | Google Colab, Jupyter Notebook | Eksperimen, training, dan evaluasi performa model |
| IDE | Visual Studio Code | Pengembangan kode utama |
| Autentikasi | JWT, bcrypt | Keamanan sesi dan hashing password |
| Dokumentasi API | Swagger UI (FastAPI built-in) | Dokumentasi dan pengujian endpoint |

---

## 9. Kriteria Penerimaan

Sistem dinyatakan selesai apabila seluruh kriteria berikut terpenuhi pada saat demo akhir.

### 9.1 Modul Autentikasi
- [ ] Register berhasil membuat akun dengan password tersimpan dalam bentuk bcrypt hash
- [ ] Login mengembalikan JWT token valid yang dapat mengakses endpoint terproteksi
- [ ] Logout menginvalidasi token sehingga token tersebut tidak dapat digunakan kembali
- [ ] Endpoint admin mengembalikan `403 Forbidden` jika diakses pengguna umum

### 9.2 Modul Admin
- [ ] Import CSV/JSON berhasil dengan data quality report yang akurat
- [ ] Perubahan parameter DBSCAN tersimpan dan diterapkan pada eksekusi model berikutnya
- [ ] Trigger retraining berhasil memperbarui model dan menampilkan perbandingan metrik
- [ ] Log sistem mencatat seluruh aktivitas login dan akses endpoint

### 9.3 Modul Analisis AI
- [ ] `/analysis/clusters` menghasilkan `cluster_id` berbeda untuk setiap titik berdasarkan DBSCAN
- [ ] `/recommendation/location` menghasilkan rekomendasi disertai SHAP values yang dapat dijelaskan
- [ ] `/analysis/saturation` berhasil membedakan area `over-saturated` dan `under-served`
- [ ] Seluruh endpoint analisis merespons dalam waktu < 5 detik untuk dataset Kota Batam

### 9.4 Non-Fungsional
- [ ] Tidak ada endpoint yang dapat diakses tanpa autentikasi (kecuali `/auth/register` dan `/auth/login`)
- [ ] API tidak crash saat menerima input tidak valid (lat/lon kosong, kategori tidak dikenal, token kedaluwarsa)
- [ ] Seluruh endpoint terdokumentasi dan dapat diuji langsung dari Swagger UI

---

## 10. Ringkasan Training Per-DB (Saat Ini)

Pipeline training saat ini berjalan per database (satu file `.db` per run). Detail metrik dan konfigurasi disimpan di artefak run, bukan di PRD.

**Konfigurasi umum:**
- `TARGET_DB_FILE` memilih database yang diproses.
- Kolom kategori yang digunakan adalah `category` (bukan `source_category`).
- Parameter DBSCAN dan Random Forest diatur di notebook dan direkam ke metadata per run.

**Struktur output per run:**
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

---

## 11. Snapshot Training Legacy (Merged-DB)

Ringkasan ini disimpan sebagai referensi historis dari training gabungan (merged-db).

- Data: 11,094 baris raw → 10,768 valid (326 ditolak)
- DBSCAN: eps=150m, min_samples=10, clusters=118, noise=3,935 (36.54%)
- Kualitas clustering: silhouette=0.3424, Davies-Bouldin=0.5229
- Random Forest: F1 macro=0.9859, accuracy=0.9857

---

*PRD v1.0 — GeoMarket AI · IF-4PD-04*