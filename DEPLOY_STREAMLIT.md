# Panduan Hosting Aplikasi AeroSurvey Pro di Streamlit Community Cloud

Aplikasi **AeroSurvey Pro** versi Streamlit telah disiapkan di dalam folder `streamlit_app/`. Anda dapat meng-hosting aplikasi ini secara **100% GRATIS** di **Streamlit Community Cloud** agar dapat diakses oleh seluruh pilot drone dan surveyor di lapangan melalui browser HP maupun laptop.

---

## 📁 Berkas Aplikasi Streamlit
Di dalam folder `streamlit_app/` telah tersedia:
- `app.py`: Kode utama aplikasi Streamlit (Alur 2-Tahap, Peta Folium Interaktif, Box EXIF, Integrasi Google Drive & Apps Script, Dashboard Admin).
- `requirements.txt`: Daftar dependensi Python (`streamlit`, `folium`, `streamlit-folium`, `requests`, `pandas`).
- `SOP_Pelaporan_Survey_Aerial.pdf`: Dokumen SOP resmi yang tersemat langsung untuk diunduh.
- `.streamlit/config.toml`: Konfigurasi tema warna Aerospace Blue.

---

## 🚀 Langkah-langkah Hosting ke Streamlit Community Cloud (Gratis)

### **Langkah 1: Upload / Push Kode ke Repositori GitHub**
1. Buat repositori baru di akun [GitHub](https://github.com/) Anda (bisa berstatus **Public** atau **Private**), misalnya dengan nama `aerosurvey-app`.
2. Push berkas di dalam folder `streamlit_app` ke repositori tersebut:
   ```bash
   cd /Users/alex.kelana/.gemini/antigravity/scratch/geo-survey-app/streamlit_app
   git init
   git add .
   git commit -m "Initial commit for Streamlit hosting"
   git branch -M main
   git remote add origin https://github.com/USERNAME-ANDA/aerosurvey-app.git
   git push -u origin main
   ```

---

### **Langkah 2: Hubungkan ke Streamlit Community Cloud**
1. Buka [https://share.streamlit.io/](https://share.streamlit.io/) dan login menggunakan akun GitHub Anda.
2. Klik tombol **"Create app"** atau **"New app"**.
3. Pilih opsi **"I already have an app"** / hubungkan repositori Anda:
   - **Repository**: Pilih repositori Anda (misal `USERNAME-ANDA/aerosurvey-app`).
   - **Branch**: `main`
   - **Main file path**: `app.py` (atau `streamlit_app/app.py` jika di-push dari root).
   - **App URL**: Anda dapat menyesuaikan subdomain kustom (misal `aerosurvey-geo.streamlit.app`).

---

### **Langkah 3: Konfigurasi Secrets / Variabel Lingkungan (Opsional tapi Direkomendasikan)**
Sebelum menekan Deploy, klik **"Advanced settings..."** ➔ **Secrets**, lalu masukkan konfigurasi backend Anda:
```toml
ADMIN_EMAIL = "alex.kelana@gmail.com"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx.../exec"
ADMIN_PIN = "1234"
```
*(Nilai ini akan otomatis dibaca oleh `st.secrets` sehingga Anda tidak perlu mengetiknya berulang-ulang).*

---

### **Langkah 4: Deploy & Bagikan!**
1. Klik tombol **"Deploy!"**.
2. Streamlit Cloud akan menginstal dependensi dari `requirements.txt` dan mengaktifkan aplikasi dalam waktu ~1–2 menit.
3. Setelah selesai, Anda akan mendapatkan tautan publik permanen dengan SSL gratis (HTTPS), contoh:
   👉 **`https://aerosurvey-geo.streamlit.app/`**
4. Bagikan link tersebut kepada seluruh pilot drone dan tim lapangan!

---

## 💻 Cara Menjalankan Secara Lokal (Uji Coba di Komputer Sendiri)
Jika ingin menguji aplikasi di laptop sebelum di-deploy ke Cloud:
1. Buka terminal di folder `streamlit_app/`:
   ```bash
   cd /Users/alex.kelana/.gemini/antigravity/scratch/geo-survey-app/streamlit_app
   ```
2. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```
4. Aplikasi akan terbuka di browser pada `http://localhost:8501`.
