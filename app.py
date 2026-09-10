import streamlit as st
import datetime
import json
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import os
import re

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="AeroSurvey Pro - Pelaporan Survey Udara",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS for polished Aerospace UI
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }
    
    /* Custom header banner */
    .app-header {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .app-title {
        font-size: 1.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .app-subtitle {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-top: 2px;
    }

    /* Phase cards */
    .phase-box {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .phase-box.active {
        border-color: #0284c7;
        background-color: #fafcff;
    }
    
    .phase-box.completed {
        border-color: #059669;
        background-color: #f6fcf8;
    }

    .badge-step {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background-color: #0284c7;
        color: white;
        font-weight: bold;
        font-size: 0.85rem;
        margin-right: 8px;
    }
    
    .badge-step.green {
        background-color: #059669;
    }

    /* Callout & alerts */
    .exif-card {
        background-color: #eff6ff;
        border: 1.5px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #1e3a8a;
    }
    
    .info-card {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 0.85rem;
        margin: 0.85rem 0;
        font-size: 0.9rem;
    }
   /* Sembunyikan GitHub / badge Cloud / Deploy — JANGAN hide header penuh */
    #GithubIcon,
    a[href*="github.com"],
    .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_,
    .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
      display: none !important;
      visibility: hidden !important;
    }

    .stDeployButton,
    .stAppDeployButton,
    [data-testid="stAppDeployButton"] {
      display: none !important;
      visibility: hidden !important;
    }

    /* Toolbar kanan (menu ⋮) boleh disembunyikan jika tidak perlu */
    [data-testid="stToolbar"] {
      visibility: hidden !important;
      height: 0 !important;
    }

    /* PASTIKAN tombol buka sidebar tetap terlihat */
    [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"],
    button[kind="header"] {
      visibility: visible !important;
      display: inline-flex !important;
    }
</style>
""", unsafe_allow_html=True)

# Safe Secrets Helper
def get_secret(key, default_val=""):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            val = st.secrets[key]
            if isinstance(val, str):
                return val
            return str(val)
    except Exception:
        pass
    return default_val

# ==============================================================================
# DEFAULT CONFIG & SESSION STATE
# ==============================================================================
# Label bulan HARUS sama dengan backend Code.gs (parseMonthLabel)
# Backend: ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
now = datetime.datetime.now()
current_month_label = f"{MONTH_NAMES[now.month - 1]} {now.year}"

if "config" not in st.session_state:
    st.session_state.config = {
        "ADMIN_EMAIL": get_secret("ADMIN_EMAIL", "alex.kelana@gmail.com"),
        "APPS_SCRIPT_URL": get_secret("APPS_SCRIPT_URL", ""),
        "ADMIN_PIN": get_secret("ADMIN_PIN", "1234"),
    }

if "role" not in st.session_state:
    st.session_state.role = "petugas"  # 'petugas' or 'admin'

if "is_phase1_completed" not in st.session_state:
    st.session_state.is_phase1_completed = False

if "is_phase2_enabled" not in st.session_state:
    st.session_state.is_phase2_enabled = False

if "site" not in st.session_state:
    st.session_state.site = ""

if "pilot_name" not in st.session_state:
    st.session_state.pilot_name = ""

if "pilot_email" not in st.session_state:
    st.session_state.pilot_email = ""

if "drone_model" not in st.session_state:
    st.session_state.drone_model = "DJI Mavic 3 Enterprise (M3E)"

if "custom_drone" not in st.session_state:
    st.session_state.custom_drone = ""

if "created_folder_url" not in st.session_state:
    st.session_state.created_folder_url = ""

if "coords" not in st.session_state:
    st.session_state.coords = "-6.208800, 106.845600"

if "lat" not in st.session_state:
    st.session_state.lat = -6.208800

if "lng" not in st.session_state:
    st.session_state.lng = 106.845600

if "reports" not in st.session_state:
    st.session_state.reports = []

# List of Drones
DRONE_OPTIONS = [
    "DJI Mavic 3 Enterprise (M3E)",
    "DJI Mavic 3 Thermal (M3T)",
    "DJI Mavic 3 Pro",
    "DJI Mavic 3 Classic",
    "DJI Mavic 3",
    "DJI Air 3",
    "DJI Air 2S",
    "DJI Mini 4 Pro",
    "DJI Mini 3 Pro",
    "DJI Phantom 4 Pro V2.0",
    "DJI Phantom 4 RTK",
    "DJI Matrice 350 RTK",
    "DJI Matrice 300 RTK",
    "DJI Matrice 30T",
    "Autel EVO II Pro V3",
    "Autel EVO MAX 4T",
    "Lainnya..."
]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", (email or "").strip()))


def create_drive_folder(site_name, month_str, email_pilot):
    """Call Google Apps Script backend to create folder and grant permissions.
    Payload keys MUST match Code.gs: site, monthLabelStr, pilotEmail
    """
    api_url = st.session_state.config.get("APPS_SCRIPT_URL", "").strip()

    if api_url:
        try:
            payload = {
                "action": "createFolder",
                "site": site_name,
                "monthLabelStr": month_str,   # ✅ match backend
                "pilotEmail": email_pilot     # ✅ match backend
            }
            res = requests.post(
                api_url,
                json=payload,                 # Content-Type: application/json
                timeout=25
            )
            data = res.json()
            return data
        except Exception as e:
            return {"success": False, "message": f"Koneksi backend gagal: {str(e)}"}
    else:
        # Fallback simulation if Apps Script URL is not set yet
        mock_id = f"mock_{site_name.replace(' ', '_').lower()}_{int(datetime.datetime.now().timestamp())}"
        mock_url = f"https://drive.google.com/drive/folders/{mock_id}"
        return {
            "success": True,
            "folderUrl": mock_url,
            "folderId": mock_id,
            "message": f"[DEMO] Folder '{site_name}' berhasil disiapkan (mode offline)."
        }


def submit_survey_report(report_data):
    """Submit report to Google Apps Script and record to local session.
    Payload keys MUST match Code.gs submitReport signature + extraData.
    """
    api_url = st.session_state.config.get("APPS_SCRIPT_URL", "").strip()

    # Save to local session history (always)
    st.session_state.reports.insert(0, report_data)

    if api_url:
        try:
            # Map frontend fields → backend expected names
            payload = {
                "action": "submitReport",
                "pilot": report_data.get("pilot", ""),
                "drone": report_data.get("drone", ""),
                "site": report_data.get("site", ""),
                "coords": report_data.get("koordinat", ""),          # ✅ backend: coords
                "monthLabelStr": report_data.get("monthLabel", ""),  # ✅ backend: monthLabelStr
                # extraData fields (dibaca di submitReport via extraData)
                "pilotEmail": report_data.get("pilotEmail", ""),
                "surveyType": report_data.get("surveyType", "Orthophoto"),
                "notes": report_data.get("notes", ""),
                "copilot": report_data.get("copilot", ""),
                "droneSerial": report_data.get("droneSerial", ""),
                "client": report_data.get("client", ""),
                "altitude": report_data.get("altitude", ""),
                "weather": report_data.get("weather", ""),
                "windSpeed": report_data.get("windSpeed", ""),
                "flightDuration": report_data.get("flightDuration", ""),
            }
            res = requests.post(
                api_url,
                json=payload,
                timeout=45
            )
            return res.json()
        except Exception as e:
            return {
                "success": True,
                "offline": True,
                "message": f"Laporan tersimpan di memori lokal. Sinkronisasi server gagal: {str(e)}",
                "copied": 0,
                "skipped": 0
            }
    else:
        return {
            "success": True,
            "offline": True,
            "message": "Laporan berhasil dicatat (Mode Demo / Mandiri)!",
            "copied": 0,
            "skipped": 0
        }


# ==============================================================================
# SIDEBAR NAVIGATION & CONTROLS
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/drone.png", width=64)
    st.markdown("### **AeroSurvey Pro**")
    st.caption("Sistem Pelaporan Survey Lapangan Aerial")
    st.divider()

    # Mode Switcher
    if st.session_state.role == "admin":
        st.success("🔒 **Mode: ADMINISTRATOR**")
        if st.button("🔒 Kunci ke Mode Petugas", use_container_width=True):
            st.session_state.role = "petugas"
            st.rerun()
    else:
        st.info("👤 **Mode: PETUGAS LAPANGAN**")
        with st.expander("🔑 Akses Administrator"):
            pin_input = st.text_input("Masukkan PIN Admin", type="password")
            if st.button("Buka Akses Admin", use_container_width=True):
                expected_pin = st.session_state.config.get("ADMIN_PIN", "")
                if expected_pin and pin_input == expected_pin:
                    st.session_state.role = "admin"
                    st.success("Akses Admin Terbuka!")
                    st.rerun()
                else:
                    st.error("PIN tidak sesuai.")

    st.divider()

    # Quick Links & PDF
    st.markdown("#### **Tautan Cepat & Dokumen**")

    st.markdown("""
        <a href="https://www.google.com/maps/d/edit?mid=1yT10qibBTAx1W6d369YWkFsK8l2cD74&usp=drive_link" target="_blank" style="text-decoration:none;">
            <button style="width:100%; padding:8px; border-radius:6px; background-color:#eff6ff; color:#0284c7; border:1px solid #bfdbfe; font-weight:600; cursor:pointer; margin-bottom:8px;">
                🗺️ Buka Order Sites Map ↗
            </button>
        </a>
    """, unsafe_allow_html=True)

    pdf_path = os.path.join(os.path.dirname(__file__), "SOP_Pelaporan_Survey_Aerial.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            st.download_button(
                label="📄 Unduh Dokumen SOP (PDF)",
                data=pdf_bytes,
                file_name="SOP_Pelaporan_Survey_Aerial.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    st.caption("v2.5 - Aerial Jaya (patched)")

# ==============================================================================
# MAIN PAGE ROUTING (PETUGAS vs ADMIN)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. ADMIN DASHBOARD VIEW
# ------------------------------------------------------------------------------
if st.session_state.role == "admin":
    st.markdown("## 📊 Dashboard Administrator & Rekapitulasi Survey")
    st.caption("Kelola data laporan survey, ekspor data, dan konfigurasi Google Apps Script")

    tab1, tab2, tab3 = st.tabs(["📋 Riwayat Laporan", "⚙️ Konfigurasi Backend", "📝 Formulir Petugas"])

    with tab1:
        st.subheader("Rekapitulasi Survey Lapangan")

        total_reports = len(st.session_state.reports)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Laporan", f"{total_reports}")
        col2.metric("Bulan Aktif", current_month_label)
        col3.metric("Status Backend", "Tersambung" if st.session_state.config.get("APPS_SCRIPT_URL") else "Lokal/Demo")
        col4.metric("Kamera EXIF", "Wajib Aktif")

        if total_reports > 0:
            df = pd.DataFrame(st.session_state.reports)
            st.dataframe(df, use_container_width=True)

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Ekspor Data ke CSV (Excel)",
                data=csv_data,
                file_name=f"Rekap_Survey_{current_month_label.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Belum ada data laporan survey yang tersimpan di sesi ini.")

    with tab2:
        st.subheader("Pengaturan Integrasi Google Drive & Apps Script")
        new_apps_url = st.text_input(
            "URL Deployment Google Apps Script (Web App)",
            value=st.session_state.config.get("APPS_SCRIPT_URL", "")
        )
        new_admin_email = st.text_input(
            "Email Notifikasi Admin",
            value=st.session_state.config.get("ADMIN_EMAIL", "")
        )
        new_admin_pin = st.text_input(
            "PIN Administrator",
            value=st.session_state.config.get("ADMIN_PIN", "1234"),
            type="password"
        )

        if st.button("Simpan Pengaturan"):
            st.session_state.config["APPS_SCRIPT_URL"] = new_apps_url.strip()
            st.session_state.config["ADMIN_EMAIL"] = new_admin_email.strip()
            st.session_state.config["ADMIN_PIN"] = new_admin_pin.strip()
            st.success("Pengaturan berhasil disimpan!")

    with tab3:
        st.info("Anda dapat menguji alur pengisian form petugas di bawah:")

# ------------------------------------------------------------------------------
# 2. OFFICER 2-PHASE REPORTING FORM (PETUGAS VIEW)
# ------------------------------------------------------------------------------
st.markdown(f"""
<div class="app-header">
    <div>
        <h1 class="app-title">✈️ Formulir Pelaporan Survey Aerial</h1>
        <div class="app-subtitle">Alur 2-Tahap: Buat Folder Google Drive ➔ Verifikasi EXIF ➔ Kirim Laporan</div>
    </div>
    <div style="text-align:right;">
        <span style="background:rgba(255,255,255,0.2); padding:4px 10px; border-radius:20px; font-size:0.8rem; font-weight:600;">
            📅 {current_month_label}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAHAP 1: BUAT FOLDER UPLOAD
# ------------------------------------------------------------------------------
st.markdown("### **Tahap 1: Buat Folder Upload di Google Drive**")

col_site, col_email = st.columns([1, 1])

with col_site:
    input_site = st.text_input(
        "Nama Site / ID Tower *",
        value=st.session_state.site,
        placeholder="Contoh: SITE-A atau PK1276",
        disabled=st.session_state.is_phase1_completed,
        help="Masukkan kode atau nama lokasi tower survey"
    )

with col_email:
    input_pilot_email = st.text_input(
        "Email Pilot (Akun Google) *",
        value=st.session_state.pilot_email,
        placeholder="pilot.drone@gmail.com",
        disabled=st.session_state.is_phase1_completed,
        help="Wajib akun Google untuk mendapatkan akses editor folder upload"
    )

btn_create_folder = st.button(
    "📁 Buat Folder Upload",
    type="primary",
    disabled=st.session_state.is_phase1_completed or not input_site.strip() or not input_pilot_email.strip()
)

if btn_create_folder:
    if not is_valid_email(input_pilot_email):
        st.error("Format email pilot tidak valid.")
    else:
        with st.spinner("Sedang membuat folder bulanan & site di Google Drive..."):
            res = create_drive_folder(
                input_site.strip(),
                current_month_label,
                input_pilot_email.strip()
            )

            if res.get("success"):
                st.session_state.site = input_site.strip()
                st.session_state.pilot_email = input_pilot_email.strip()
                st.session_state.created_folder_url = res.get("folderUrl", "")
                msg = res.get("message", "Folder upload berhasil dibuat!")
                if res.get("editorGranted") is False:
                    st.warning(msg + " (Catatan: izin editor mungkin gagal karena kebijakan domain.)")
                else:
                    st.success(msg)
            else:
                st.error(res.get("message", "Gagal membuat folder."))

# Jika folder sudah dibuat, tampilkan link Drive, Box EXIF, dan Tombol Konfirmasi Selesai
if st.session_state.created_folder_url:
    st.markdown(f"""
        <div style="text-align:center; margin: 1rem 0;">
            <a href="{st.session_state.created_folder_url}" target="_blank" style="text-decoration:none;">
                <button style="padding:10px 20px; font-size:0.95rem; font-weight:700; color:#0284c7; background:#ffffff; border:2px solid #0284c7; border-radius:8px; cursor:pointer;">
                    🔗 Buka Folder Upload di Google Drive ↗
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

    # EXIF Metadata Verification Callout Box
    st.markdown("""
    <div class="exif-card">
        <h4 style="margin:0 0 6px 0; color:#1d4ed8;">🛑 Aturan Wajib: Verifikasi Metadata EXIF (GPS & Ketinggian)</h4>
        <p style="margin:0 0 8px 0; font-size:0.87rem; line-height:1.45;">
            Sebelum mengunggah berkas ke Google Drive, Pilot <strong>wajib memastikan metadata EXIF (Koordinat GPS, Ketinggian/Altitude, Tanggal & Jam)</strong> tertanam pada seluruh foto (7 foto) & video (1 video). Berkas tanpa metadata geotag akan <strong>ditolak oleh QC Studio</strong>.
        </p>
        <div style="background:#ffffff; border:1px solid #bfdbfe; border-radius:6px; padding:8px 12px; font-size:0.82rem;">
            <strong>🛠️ Alat Cek Metadata Gratis (Rekomendasi):</strong><br>
            • <a href="https://play.google.com/store/apps/details?id=net.xnano.android.photoexifeditor" target="_blank">📱 Android: Photo EXIF Editor ↗</a> | 
            • <a href="https://apps.apple.com/app/exif-metadata/id1455197364" target="_blank">🍏 iOS: Exif Metadata ↗</a> | 
            • <a href="https://exiftool.org/" target="_blank">💻 Desktop: ExifTool ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tombol Konfirmasi Selesai Upload
    if not st.session_state.is_phase1_completed:
        if st.button("✓ Selesai Upload (Lanjut ke Tahap 2)", type="primary", use_container_width=True):
            st.session_state.is_phase1_completed = True
            st.session_state.is_phase2_enabled = True
            st.rerun()

st.divider()

# ------------------------------------------------------------------------------
# TAHAP 2: KIRIM LAPORAN (TERKUNCI SEBELUM TAHAP 1 SELESAI)
# ------------------------------------------------------------------------------
st.markdown("### **Tahap 2: Pengisian Data Laporan & Koordinat Lokasi**")

if not st.session_state.is_phase2_enabled:
    st.info("🔒 **Tahap 2 Terkunci:** Selesaikan Tahap 1 dan klik tombol *'Selesai Upload'* untuk membuka formulir ini.")
else:
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        val_pilot = st.text_input(
            "Nama Pilot *",
            value=st.session_state.pilot_name,
            placeholder="Nama Lengkap Pilot (RPIC)",
            key="input_pilot_name"
        )
        # Sync ke session_state
        if val_pilot is not None:
            st.session_state.pilot_name = val_pilot.strip()

    with col_p2:
        # Cari index drone yang tersimpan
        try:
            drone_idx = DRONE_OPTIONS.index(st.session_state.drone_model)
        except ValueError:
            drone_idx = 0

        val_drone = st.selectbox(
            "Model Drone *",
            options=DRONE_OPTIONS,
            index=drone_idx,
            key="select_drone_model"
        )
        st.session_state.drone_model = val_drone

    val_custom_drone = ""
    if val_drone == "Lainnya...":
        val_custom_drone = st.text_input(
            "Ketik Model Drone Kustom *",
            value=st.session_state.custom_drone,
            placeholder="Contoh: Custom FPV Quad",
            key="input_custom_drone"
        )
        st.session_state.custom_drone = val_custom_drone.strip()

    val_site2 = st.text_input("Nama Site (Sama dengan Tahap 1)", value=st.session_state.site, disabled=True)

    # Coordinate Input & GPS
    st.markdown("#### **Titik Koordinat Lokasi (Lat, Long)**")
    coord_input = st.text_input(
        "Koordinat Desimal (Format: Latitude, Longitude) *",
        value=st.session_state.coords,
        key="coord_text_input"
    )

    # Parse coordinate for Folium map
    try:
        parts = [float(x.strip()) for x in coord_input.split(",")]
        if len(parts) == 2 and -90 <= parts[0] <= 90 and -180 <= parts[1] <= 180:
            current_lat, current_lng = parts[0], parts[1]
            # Sync text input ke session_state (tanpa force rerun)
            st.session_state.coords = f"{current_lat}, {current_lng}"
            st.session_state.lat = current_lat
            st.session_state.lng = current_lng
        else:
            current_lat, current_lng = st.session_state.lat, st.session_state.lng
    except Exception:
        current_lat, current_lng = st.session_state.lat, st.session_state.lng

    # Interactive Folium Map
    st.caption("📍 Peta Interaktif (Klik pada peta untuk memilih titik lokasi survey):")
    m = folium.Map(location=[current_lat, current_lng], zoom_start=15, control_scale=True)
    folium.Marker(
        [current_lat, current_lng],
        popup=f"Titik Survey: {st.session_state.site}",
        tooltip="Titik Lokasi Terpilih",
        icon=folium.Icon(color="blue", icon="plane", prefix="fa")
    ).add_to(m)

    try:
        map_data = st_folium(m, height=280, use_container_width=True, key="survey_leaflet_map")
        if map_data and isinstance(map_data, dict) and map_data.get("last_clicked"):
            clicked_lat = round(map_data["last_clicked"]["lat"], 6)
            clicked_lng = round(map_data["last_clicked"]["lng"], 6)
            new_coords = f"{clicked_lat}, {clicked_lng}"
            if new_coords != st.session_state.coords:
                st.session_state.coords = new_coords
                st.session_state.lat = clicked_lat
                st.session_state.lng = clicked_lng
                st.rerun()
    except Exception:
        st.caption(f"Peta statis aktif: {current_lat}, {current_lng}")

    submit_btn = st.button("🚀 Kirim Laporan", type="primary", use_container_width=True)

    if submit_btn:
        final_pilot = (st.session_state.pilot_name or val_pilot or "").strip()
        if not final_pilot:
            st.error("Nama Pilot wajib diisi.")
        else:
            final_drone = (
                st.session_state.custom_drone.strip()
                if val_drone == "Lainnya..." and st.session_state.custom_drone.strip()
                else val_drone
            )

            with st.spinner("Sedang menyinkronkan laporan survey ke database..."):
                rep_id = f"REP-{datetime.datetime.now().strftime('%Y%m%d')}-{st.session_state.site}"
                report_payload = {
                    "id": rep_id,
                    "tanggal": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "monthLabel": current_month_label,
                    "pilot": final_pilot,
                    "pilotEmail": st.session_state.pilot_email,
                    "drone": final_drone,
                    "site": st.session_state.site,
                    "surveyType": "Orthophoto & BTS Documentation",
                    "koordinat": st.session_state.coords,   # akan di-map ke "coords" di helper
                    "folderUrl": st.session_state.created_folder_url,
                    "status": "Submitted"
                }

                result = submit_survey_report(report_payload)

                if result.get("success"):
                    # Backend mengembalikan "copied" / "skipped"
                    copied = result.get("copied", result.get("copiedFiles", 0))
                    skipped = result.get("skipped", result.get("skippedFiles", 0))
                    offline = result.get("offline", False)

                    st.success(f"🎉 Laporan Berhasil Dikirim! (ID: {rep_id})")

                    if offline:
                        st.warning(
                            "Mode offline / gagal sinkron ke server. "
                            "Data hanya tersimpan di memori sesi browser ini."
                        )

                    st.markdown(f"""
                    <div class="info-card">
                        <strong>Rekap Sinkronisasi:</strong><br>
                        • File Disalin ke Backup: <strong>{copied}</strong> berkas<br>
                        • File Duplikat Dilewati: <strong>{skipped}</strong> berkas<br>
                        • Tercatat di Google Sheet & Email Notifikasi Admin.
                    </div>
                    """, unsafe_allow_html=True)

                    if result.get("folderUrl"):
                        st.markdown(f"[📂 Buka Folder Backup]({result['folderUrl']})")
                else:
                    st.error("Gagal mengirim laporan: " + result.get("message", "Terjadi kesalahan"))

    # Reset button for next survey
    if st.button("🔄 Buat Laporan Baru (Reset)", use_container_width=True):
        st.session_state.is_phase1_completed = False
        st.session_state.is_phase2_enabled = False
        st.session_state.site = ""
        st.session_state.created_folder_url = ""
        st.session_state.pilot_name = ""
        st.session_state.pilot_email = ""
        st.session_state.custom_drone = ""
        st.session_state.coords = "-6.208800, 106.845600"
        st.session_state.lat = -6.208800
        st.session_state.lng = 106.845600
        st.rerun()
