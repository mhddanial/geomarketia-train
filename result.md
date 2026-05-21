# Hasil DBSCAN - GeoMarket AI

## 1) Ringkasan eksekusi
- EPS (meter): 150
- Min samples: 10
- Jumlah cluster: 118
- Titik dalam cluster: 6,833
- Titik noise: 3,935
- Noise ratio (%): 36.54
- Silhouette score: 0.3424
- Davies-Bouldin index: 0.5229

## 2) Interpretasi kualitas hasil
Gunakan panduan ini untuk menyimpulkan apakah hasil sudah baik:
- Silhouette score
  - > 0.5: cluster terpisah dengan baik
  - 0.3-0.5: cukup baik untuk data spasial noisy
  - < 0.3: cluster overlap, perlu tuning
- Davies-Bouldin index
  - < 1.0: cukup baik
  - 1.0-2.0: perlu perbaikan
  - > 2.0: cluster terlalu tumpang tindih
- Noise ratio
  - < 20%: sangat baik
  - 20-40%: masih wajar untuk data lokasi UMKM
  - > 40%: EPS terlalu kecil atau MIN_SAMPLES terlalu besar

## 3) Cara menjelaskan visualisasi

### 3.1 Sebaran titik UTM (Tahap 4.1)
- Tujuan: memastikan konversi WGS84 ke UTM valid dan sebaran titik masuk akal.
- Interpretasi: titik membentuk pola wilayah Batam; tidak ada kelompok besar di koordinat yang aneh.
- Jika ada outlier jauh dari kumpulan utama, cek data sumber atau aturan validasi.

### 3.2 Distribusi rating dan review_log (Tahap 4.2)
- Tujuan: memahami distribusi fitur atribut sebelum dipakai model.
- Interpretasi:
  - Rating biasanya berkumpul di 3-5.
  - Review_log mengurangi skew dari review yang sangat besar.

### 3.3 Ringkasan cluster vs noise (Tahap 5.1)
- Tujuan: melihat proporsi titik yang masuk cluster vs noise.
- Interpretasi:
  - Noise tinggi artinya banyak titik berdiri sendiri.
  - Cluster terlalu sedikit artinya EPS terlalu besar.

### 3.4 Top ukuran cluster (Tahap 5.1)
- Tujuan: mengecek apakah ada cluster raksasa yang tidak realistis.
- Interpretasi:
  - Jika 1 cluster jauh lebih besar dari lainnya, EPS terlalu besar.

### 3.5 Metrik Silhouette dan Davies-Bouldin (Tahap 5.2)
- Tujuan: mengukur separasi cluster secara kuantitatif.
- Interpretasi: gunakan ambang kualitas pada bagian 2.

### 3.6 Distribusi jarak ke centroid (Tahap 5.3)
- Tujuan: melihat seberapa menyebar titik di dalam cluster.
- Interpretasi:
  - Banyak jarak kecil berarti cluster padat.
  - Jarak sangat besar berarti cluster terlalu luas.

### 3.7 Distribusi density (Tahap 5.4)
- Tujuan: memahami kepadatan kompetitor dan kategori.
- Interpretasi:
  - Banyak nilai 0 berarti banyak lokasi terisolasi.
  - Nilai tinggi menunjukkan area kompetisi padat.

### 3.8 Peta sebaran cluster (Tahap 6.1)
- Tujuan: sanity check visual geografis.
- Interpretasi:
  - Cluster muncul di area ramai (Nagoya, Batam Center, Batu Aji).
  - Noise tersebar di pinggiran atau area jarang.

### 3.9 K-distance graph (Tahap 6.2)
- Tujuan: mencari EPS optimal.
- Interpretasi:
  - Cari titik siku (elbow). Nilai Y di siku adalah EPS rekomendasi.
  - Jika EPS saat ini di bawah siku, biasanya noise tinggi.
  - Jika EPS di atas siku, cluster bisa menyatu terlalu besar.

## 4) Rekomendasi tuning hyperparameter

### 4.1 Jika noise ratio terlalu tinggi
- Naikkan EPS_METER bertahap (misal +25m atau +50m).
- Turunkan MIN_SAMPLES (misal dari 5 ke 4).

### 4.2 Jika cluster terlalu sedikit atau menyatu
- Turunkan EPS_METER (misal -25m).

### 4.3 Jika cluster terlalu banyak dan kecil
- Naikkan MIN_SAMPLES (misal 5 ke 6-8).

### 4.4 Cara praktis tuning
- Jalankan k-distance graph setelah setiap perubahan.
- Catat metrik di bagian Ringkasan eksekusi.
- Pilih konfigurasi dengan: noise ratio wajar, silhouette > 0.3, DB index < 1.5.

## 5) Kesimpulan sementara
Dengan EPS = 150 dan MIN_SAMPLES = 10, DBSCAN menghasilkan 118 cluster dengan noise ratio 36.54%. Silhouette score 0.3424 dan Davies-Bouldin 0.5229 menunjukkan cluster sudah cukup terpisah dan layak digunakan untuk tahap Random Forest.

## 6) Final decision
Konfigurasi EPS = 150 dan MIN_SAMPLES = 10 dipilih karena memberikan keseimbangan terbaik antara separasi cluster (Silhouette > 0.3), kompaksi (Davies-Bouldin < 1.0), dan noise ratio yang masih dapat diterima untuk data lokasi usaha yang cenderung sparse.

## 7) Hasil Random Forest
- F1 macro: 0.9859
- Akurasi: 0.9857
- Confusion matrix (Low/Medium/High):
  - Low: 713 benar, 7 salah ke Medium, 0 salah ke High
  - Medium: 796 benar, 5 salah ke Low, 3 salah ke High
  - High: 761 benar, 18 salah ke Medium, 0 salah ke Low

Interpretasi singkat:
- Model sudah sangat stabil dan konsisten untuk ketiga kelas.
- Kesalahan terbesar terjadi antara Medium dan High, yang wajar karena batas label berbasis kuantil.
