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
    initial_sidebar_state="collapsed"
)

# Custom CSS — tanpa sidebar, sembunyikan chrome GitHub/Deploy
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }

    /* Sembunyikan sidebar & tombol expand */
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }

    /* Sembunyikan GitHub / Deploy / toolbar Cloud */
    #GithubIcon,
    a[href*="github.com"],
    .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_,
    .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK,
    .stDeployButton,
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }

    .app-header {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
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

    .role-pill {
        background: rgba(255,255,255,0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }

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
</style>
""", unsafe_allow_html=True)


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
# Label bulan HARUS sama dengan backend Code.gs
MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
now = datetime.datetime.now()
current_month_label = f"{MONTH_NAMES[now.month - 1]} {now.year}"

DEFAULT_ORDER_SITES_MAP = (
    "https://www.google.com/maps/d/edit?mid=1yT10qibBTAx1W6d369YWkFsK8l2cD74&usp=drive_link"
)

if "config" not in st.session_state:
    st.session_state.config = {
        "ADMIN_EMAIL": get_secret("ADMIN_EMAIL", "alex.kelana@gmail.com"),
        "APPS_SCRIPT_URL": get_secret("APPS_SCRIPT_URL", ""),
        "ADMIN_PIN": get_secret("ADMIN_PIN", "1234"),
        # ID Drive / Sheet (default sama dengan Code.gs; bisa diubah di tab Pengaturan)
        "UPLOAD_ROOT_FOLDER_ID": get_secret(
            "UPLOAD_ROOT_FOLDER_ID", "1GA6jN45s12IjgkXDGvdYthEButlFzzPg"
        ),
        "ADMIN_BACKUP_ROOT_FOLDER_ID": get_secret(
            "ADMIN_BACKUP_ROOT_FOLDER_ID", "1yxQR6lFiYlTxgaw582mqJHN4NsDRM4mJ"
        ),
        "SUMMARY_SHEET_ID": get_secret(
            "SUMMARY_SHEET_ID", "16gL_bDtrJSuJ_wyyVmX5oVNSVvAY0j_p464L8XBBnLM"
        ),
        "ORDER_SITES_MAP_URL": get_secret("ORDER_SITES_MAP_URL", DEFAULT_ORDER_SITES_MAP),
        "SOP_DRIVE_URL": get_secret("SOP_DRIVE_URL", ""),
    }

# Migrasi sesi lama: pastikan key baru ada
if "SOP_DRIVE_URL" not in st.session_state.config:
    st.session_state.config["SOP_DRIVE_URL"] = get_secret("SOP_DRIVE_URL", "")

if "role" not in st.session_state:
    st.session_state.role = "petugas"

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


def backend_config_payload():
    """Kirim ID folder/sheet ke backend (whitelist di Code.gs ALLOWED_CONFIG_OVERRIDE)."""
    cfg = st.session_state.config
    out = {}
    for key in (
        "ADMIN_EMAIL",
        "UPLOAD_ROOT_FOLDER_ID",
        "ADMIN_BACKUP_ROOT_FOLDER_ID",
        "SUMMARY_SHEET_ID",
    ):
        val = (cfg.get(key) or "").strip()
        if val:
            out[key] = val
    return out


def create_drive_folder(site_name, month_str, email_pilot):
    """Payload keys MUST match Code.gs: site, monthLabelStr, pilotEmail"""
    api_url = st.session_state.config.get("APPS_SCRIPT_URL", "").strip()

    if api_url:
        try:
            payload = {
                "action": "createFolder",
                "site": site_name,
                "monthLabelStr": month_str,
                "pilotEmail": email_pilot,
                "config": backend_config_payload(),
            }
            res = requests.post(api_url, json=payload, timeout=25)
            return res.json()
        except Exception as e:
            return {"success": False, "message": f"Koneksi backend gagal: {str(e)}"}
    else:
        mock_id = f"mock_{site_name.replace(' ', '_').lower()}_{int(datetime.datetime.now().timestamp())}"
        mock_url = f"https://drive.google.com/drive/folders/{mock_id}"
        return {
            "success": True,
            "folderUrl": mock_url,
            "folderId": mock_id,
            "message": f"[DEMO] Folder '{site_name}' berhasil disiapkan (mode offline)."
        }


def submit_survey_report(report_data):
    """Payload keys MUST match Code.gs submitReport + extraData"""
    api_url = st.session_state.config.get("APPS_SCRIPT_URL", "").strip()
    st.session_state.reports.insert(0, report_data)

    if api_url:
        try:
            payload = {
                "action": "submitReport",
                "pilot": report_data.get("pilot", ""),
                "drone": report_data.get("drone", ""),
                "site": report_data.get("site", ""),
                "coords": report_data.get("koordinat", ""),
                "monthLabelStr": report_data.get("monthLabel", ""),
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
                "config": backend_config_payload(),
            }
            res = requests.post(api_url, json=payload, timeout=45)
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
# HEADER
# ==============================================================================
role_label = "🔒 ADMINISTRATOR" if st.session_state.role == "admin" else "👤 PETUGAS LAPANGAN"

st.markdown(f"""
<div class="app-header">
    <div>
        <h1 class="app-title">✈️ AeroSurvey Pro</h1>
        <div class="app-subtitle">Pelaporan Survey Aerial</div>
    </div>
    <div style="text-align:right; display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
        <span class="role-pill">{role_label}</span>
        <span class="role-pill">📅 {current_month_label}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# MAIN TABS (menggantikan sidebar)
# ==============================================================================
tab_form, tab_settings, tab_help = st.tabs([
    "✈️ Formulir Survey",
    "⚙️ Pengaturan",
    "📄 Bantuan & Dokumen"
])

# ------------------------------------------------------------------------------
# TAB 1: FORMULIR SURVEY
# ------------------------------------------------------------------------------
with tab_form:
    st.markdown("### **Tahap 1: Buat Folder Upload di Google Drive**")

    col_site, col_email = st.columns([1, 1])

    with col_site:
        input_site = st.text_input(
            "Nama Site / ID Tower *",
            value=st.session_state.site,
            placeholder="Contoh: SITE-A atau PK1276",
            disabled=st.session_state.is_phase1_completed,
            help="Masukkan kode atau nama lokasi tower survey",
            key="form_site"
        )

    with col_email:
        input_pilot_email = st.text_input(
            "Email Pilot (Akun Google) *",
            value=st.session_state.pilot_email,
            placeholder="pilot.drone@gmail.com",
            disabled=st.session_state.is_phase1_completed,
            help="Wajib akun Google untuk mendapatkan akses editor folder upload",
            key="form_pilot_email"
        )

    btn_create_folder = st.button(
        "📁 Buat Folder Upload",
        type="primary",
        disabled=st.session_state.is_phase1_completed or not input_site.strip() or not input_pilot_email.strip(),
        key="btn_create_folder"
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

        if not st.session_state.is_phase1_completed:
            if st.button("✓ Selesai Upload (Lanjut ke Tahap 2)", type="primary", use_container_width=True, key="btn_finish_phase1"):
                st.session_state.is_phase1_completed = True
                st.session_state.is_phase2_enabled = True
                st.rerun()

    st.divider()

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
            if val_pilot is not None:
                st.session_state.pilot_name = val_pilot.strip()

        with col_p2:
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

        if val_drone == "Lainnya...":
            val_custom_drone = st.text_input(
                "Ketik Model Drone Kustom *",
                value=st.session_state.custom_drone,
                placeholder="Contoh: Custom FPV Quad",
                key="input_custom_drone"
            )
            st.session_state.custom_drone = val_custom_drone.strip()

        st.text_input("Nama Site (Sama dengan Tahap 1)", value=st.session_state.site, disabled=True, key="site_readonly")

        st.markdown("#### **Titik Koordinat Lokasi (Lat, Long)**")
        coord_input = st.text_input(
            "Koordinat Desimal (Format: Latitude, Longitude) *",
            value=st.session_state.coords,
            key="coord_text_input"
        )

        try:
            parts = [float(x.strip()) for x in coord_input.split(",")]
            if len(parts) == 2 and -90 <= parts[0] <= 90 and -180 <= parts[1] <= 180:
                current_lat, current_lng = parts[0], parts[1]
                st.session_state.coords = f"{current_lat}, {current_lng}"
                st.session_state.lat = current_lat
                st.session_state.lng = current_lng
            else:
                current_lat, current_lng = st.session_state.lat, st.session_state.lng
        except Exception:
            current_lat, current_lng = st.session_state.lat, st.session_state.lng

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

        submit_btn = st.button("🚀 Kirim Laporan", type="primary", use_container_width=True, key="btn_submit_report")

        if submit_btn:
            final_pilot = (st.session_state.pilot_name or "").strip()
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
                        "koordinat": st.session_state.coords,
                        "folderUrl": st.session_state.created_folder_url,
                        "status": "Submitted"
                    }

                    result = submit_survey_report(report_payload)

                    if result.get("success"):
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

        if st.button("🔄 Buat Laporan Baru (Reset)", use_container_width=True, key="btn_reset_report"):
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

# ------------------------------------------------------------------------------
# TAB 2: PENGATURAN (mode + config + riwayat admin)
# ------------------------------------------------------------------------------
with tab_settings:
    st.subheader("Mode Akses")

    if st.session_state.role == "admin":
        st.success("Anda sedang dalam **Mode Administrator**.")
        if st.button("🔒 Kembali ke Mode Petugas", use_container_width=True, key="btn_lock_petugas"):
            st.session_state.role = "petugas"
            st.rerun()
    else:
        st.info("Mode saat ini: **Petugas Lapangan**. Masukkan PIN untuk membuka fitur admin.")
        pin_input = st.text_input("PIN Administrator", type="password", key="pin_input_settings")
        if st.button("Buka Akses Admin", use_container_width=True, key="btn_unlock_admin"):
            expected_pin = st.session_state.config.get("ADMIN_PIN", "")
            if expected_pin and pin_input == expected_pin:
                st.session_state.role = "admin"
                st.success("Akses Admin terbuka.")
                st.rerun()
            else:
                st.error("PIN tidak sesuai.")

    st.divider()

    if st.session_state.role == "admin":
        st.subheader("Konfigurasi Backend & Google Drive")
        new_apps_url = st.text_input(
            "URL Deployment Google Apps Script (Web App)",
            value=st.session_state.config.get("APPS_SCRIPT_URL", ""),
            key="cfg_apps_url"
        )
        new_admin_email = st.text_input(
            "Email Notifikasi Admin (bisa beberapa, pisah koma)",
            value=st.session_state.config.get("ADMIN_EMAIL", ""),
            key="cfg_admin_email"
        )
        new_admin_pin = st.text_input(
            "PIN Administrator",
            value=st.session_state.config.get("ADMIN_PIN", "1234"),
            type="password",
            key="cfg_admin_pin"
        )

        st.markdown("##### ID Folder & Sheet Google")
        new_upload_folder = st.text_input(
            "ID Folder Upload (root bulanan)",
            value=st.session_state.config.get("UPLOAD_ROOT_FOLDER_ID", ""),
            help="ID folder Google Drive tempat folder bulan + site dibuat untuk pilot upload",
            key="cfg_upload_folder"
        )
        new_backup_folder = st.text_input(
            "ID Folder Backup Admin",
            value=st.session_state.config.get("ADMIN_BACKUP_ROOT_FOLDER_ID", ""),
            help="ID folder root backup admin (hasil dedup copy)",
            key="cfg_backup_folder"
        )
        new_sheet_id = st.text_input(
            "ID Google Sheet Rekap",
            value=st.session_state.config.get("SUMMARY_SHEET_ID", ""),
            help="ID spreadsheet rekap laporan. Kosongkan hanya jika ingin backend auto-create.",
            key="cfg_sheet_id"
        )
        new_map_url = st.text_input(
            "Link Order Sites Map",
            value=st.session_state.config.get("ORDER_SITES_MAP_URL", DEFAULT_ORDER_SITES_MAP),
            help="URL Google My Maps / peta order sites (tampil di tab Bantuan)",
            key="cfg_map_url"
        )
        new_sop_drive_url = st.text_input(
            "Link SOP di Google Drive",
            value=st.session_state.config.get("SOP_DRIVE_URL", ""),
            help="URL file SOP (share link). Contoh: https://drive.google.com/file/d/FILE_ID/view",
            key="cfg_sop_drive_url"
        )

        if st.button("Simpan Pengaturan", key="btn_save_config"):
            st.session_state.config["APPS_SCRIPT_URL"] = new_apps_url.strip()
            st.session_state.config["ADMIN_EMAIL"] = new_admin_email.strip()
            st.session_state.config["ADMIN_PIN"] = new_admin_pin.strip()
            st.session_state.config["UPLOAD_ROOT_FOLDER_ID"] = new_upload_folder.strip()
            st.session_state.config["ADMIN_BACKUP_ROOT_FOLDER_ID"] = new_backup_folder.strip()
            st.session_state.config["SUMMARY_SHEET_ID"] = new_sheet_id.strip()
            st.session_state.config["ORDER_SITES_MAP_URL"] = new_map_url.strip() or DEFAULT_ORDER_SITES_MAP
            st.session_state.config["SOP_DRIVE_URL"] = new_sop_drive_url.strip()
            st.success(
                "Pengaturan disimpan untuk sesi ini. "
                "ID folder/sheet akan dikirim ke backend saat create folder & submit laporan."
            )

        st.caption(
            "Perubahan di sini berlaku di sesi browser ini. "
            "Agar permanen: set di `.streamlit/secrets.toml` / Cloud Secrets, "
            "dan pastikan `Code.gs` sudah di-deploy dengan whitelist CONFIG terbaru."
        )

        st.divider()
        st.subheader("Rekapitulasi Survey (Sesi Ini)")

        total_reports = len(st.session_state.reports)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Laporan", f"{total_reports}")
        c2.metric("Bulan Aktif", current_month_label)
        c3.metric(
            "Status Backend",
            "Tersambung" if st.session_state.config.get("APPS_SCRIPT_URL") else "Lokal/Demo"
        )

        if total_reports > 0:
            df = pd.DataFrame(st.session_state.reports)
            st.dataframe(df, use_container_width=True)
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Ekspor Data ke CSV (Excel)",
                data=csv_data,
                file_name=f"Rekap_Survey_{current_month_label.replace(' ', '_')}.csv",
                mime="text/csv",
                key="btn_export_csv"
            )
        else:
            st.info("Belum ada data laporan survey yang tersimpan di sesi ini.")
    else:
        st.caption("Fitur konfigurasi backend dan rekap hanya tersedia setelah masuk Mode Administrator.")

# ------------------------------------------------------------------------------
# TAB 3: BANTUAN & DOKUMEN
# ------------------------------------------------------------------------------
with tab_help:
    st.subheader("Tautan Cepat")
    map_url = st.session_state.config.get("ORDER_SITES_MAP_URL", DEFAULT_ORDER_SITES_MAP)
    st.markdown(f"""
    <a href="{map_url}"
       target="_blank" style="text-decoration:none;">
        <button style="width:100%; max-width:420px; padding:10px 14px; border-radius:8px;
                       background-color:#eff6ff; color:#0284c7; border:1px solid #bfdbfe;
                       font-weight:600; cursor:pointer; margin-bottom:12px;">
            🗺️ Buka Order Sites Map ↗
        </button>
    </a>
    """, unsafe_allow_html=True)

    st.subheader("Dokumen SOP")

    sop_drive_url = (st.session_state.config.get("SOP_DRIVE_URL") or "").strip()
    if sop_drive_url:
        # Konversi link /view menjadi /preview agar nyaman di tab baru / embed
        sop_open_url = sop_drive_url
        if "/view" in sop_drive_url:
            sop_open_url = sop_drive_url.replace("/view", "/preview")
        st.markdown(f"""
        <a href="{sop_drive_url}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;">
            <button style="width:100%; max-width:420px; padding:10px 14px; border-radius:8px;
                           background-color:#ecfdf5; color:#047857; border:1px solid #a7f3d0;
                           font-weight:600; cursor:pointer; margin-bottom:8px;">
                📂 Buka SOP di Google Drive ↗
            </button>
        </a>
        """, unsafe_allow_html=True)
        with st.expander("Preview SOP dari Google Drive", expanded=False):
            st.markdown(
                f"""
                <iframe
                    src="{sop_open_url}"
                    width="100%"
                    height="640"
                    style="border:1px solid #e2e8f0; border-radius:8px;"
                    allow="autoplay"
                    title="Preview SOP Google Drive">
                </iframe>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Jika preview diblokir Chrome, gunakan tombol buka di Google Drive atau unduh di bawah.")
    else:
        st.caption(
            "Link SOP Google Drive belum diatur. "
            "Admin dapat mengisinya di tab **Pengaturan** (setelah PIN)."
        )

    pdf_path = os.path.join(os.path.dirname(__file__), "SOP_Pelaporan_Survey_Aerial.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        st.download_button(
            label="📄 Unduh Dokumen SOP (PDF)",
            data=pdf_bytes,
            file_name="SOP_Pelaporan_Survey_Aerial.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_download_sop"
        )
    else:
        st.info("File SOP lokal belum tersedia di server app (`SOP_Pelaporan_Survey_Aerial.pdf`).")

    st.divider()
    st.markdown("""
    **Alur kerja singkat**
    1. Tab **Formulir Survey** → buat folder upload  
    2. Upload foto/video (pastikan EXIF GPS aktif)  
    3. Klik *Selesai Upload* → isi data & koordinat → kirim laporan  
    4. Admin menerima email + data masuk Google Sheet / folder backup  
    """)
    
    st.caption("AeroSurvey Pro v2.7 by Aerial Jaya")
