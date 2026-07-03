import streamlit as st
import pandas as pd
import time
import serial.tools.list_ports  # Untuk deteksi otomatis port COM di laptop
from src.database.db_manager import DBManager
from src.serial.lora_listener import LoRaListener
from src.ui.components import render_metrics_cards, render_data_table_and_export
from src.ui.charts import render_species_distribution, render_temporal_activity

# 1. Konfigurasi Awal Halaman Dashboard Streamlit
st.set_page_config(
    page_title="APEM - Basecamp Monitor",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Fungsi Inisialisasi Core Services menggunakan Caching Streamlit
@st.cache_resource
def get_db_manager():
    return DBManager()

@st.cache_resource
def get_lora_listener(port_name, _db_manager):
    return LoRaListener(port=port_name, baudrate=9600, db_manager=_db_manager)

# Instansiasi awal database manager
db_manager = get_db_manager()

# 3. Manajemen Status Jalannya LoRa Listener menggunakan Session State
if "lora_active" not in st.session_state:
    st.session_state.lora_active = False


# ==============================================================================
# --- PANEL SIDEBAR (KONTROL HARDWARE & FILTER) ---
# ==============================================================================
st.sidebar.title("🌿 APEM-Basecamp")
st.sidebar.markdown("---")

st.sidebar.subheader("📡 Konfigurasi Hardware LoRa")

# A. Deteksi otomatis seluruh Port COM yang sedang aktif di laptop Windows Mas
ports_tersedia = serial.tools.list_ports.comports()
daftar_com = [port.device for port in ports_tersedia]

# Fallback jika USB serial belum dicolok agar aplikasi tidak kosong/error
if not daftar_com:
    daftar_com = ["COM5"]  # Jadikan COM5 sebagai pilihan default cadangan

# B. Dropdown Pilihan Port COM di UI
port_terpilih = st.sidebar.selectbox(
    "Pilih Port Serial COM:",
    options=daftar_com,
    index=0,
    disabled=st.session_state.lora_active
)

# Dapatkan instance lora_listener sesuai port yang dipilih di UI
lora_listener = get_lora_listener(port_terpilih, db_manager)

# C. Tombol Kontrol On / Off Sinyal LoRa
if not st.session_state.lora_active:
    st.sidebar.info(f"Status: 🔴 LoRa Disconnected ({port_terpilih})")
    if st.sidebar.button("⚡ Power ON", width="stretch"):
        lora_listener.port = port_terpilih 
        lora_listener.start()
        st.session_state.lora_active = True
        st.rerun()
else:
    st.sidebar.success(f"Status: 🟢 LoRa Active on {port_terpilih}")
    if st.sidebar.button("🛑 Power OFF", width="stretch"):
        lora_listener.stop()
        st.session_state.lora_active = False
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter Data")

# Filter Slider untuk menyingkirkan False Positive data burung di bawah ambang batas akurasi
min_confidence = st.sidebar.slider(
    "Confidence Score",
    min_value=0.0,
    max_value=1.0,
    value=0.70,
    step=0.05,
    help="Data burung dengan skor akurasi di bawah nilai ini akan disembunyikan dari dashboard analitik."
)

st.sidebar.markdown("---")
# Kita siapkan checkbox Auto-refresh di sidebar (logikanya dipindah ke paling bawah script)
auto_refresh = st.sidebar.checkbox("🔄 Auto-Refresh Dashboard", value=True)


# ==============================================================================
# --- HALAMAN UTAMA DASHBOARD ---
# ==============================================================================
st.title("🦅 AI-Powered Ecoacoustic Monitor (APEM)")
st.markdown("---")

# Bungkus seluruh visualisasi ke dalam kontainer fragment dinamis
@st.fragment(run_every=5 if auto_refresh else None)
def render_dashboard_content():
    # 1. Ambil data segar langsung dari SQLite lokal apem_basecamp.db
    raw_data = db_manager.fetch_all_packets()

    # 2. Konversi ke bentuk Pandas Dataframe
    columns = ['id', 'node_id', 'timestamp', 'scientific_name', 'confidence', 'received_at']
    df_all = pd.DataFrame(raw_data, columns=columns)

    # 3. Terapkan filter ambang batas akurasi (Confidence Score) dari sidebar
    if not df_all.empty:
        df_filtered = df_all[df_all['confidence'] >= min_confidence].reset_index(drop=True)
    else:
        df_filtered = df_all

    # 4. Render Komponen Ringkasan KPI Statistik
    render_metrics_cards(df_filtered)
    st.markdown("---")

    # 5. Render Visualisasi Grafik Ekologi (Kolom Kiri-Kanan)
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        render_species_distribution(df_filtered)
    with chart_col2:
        render_temporal_activity(df_filtered)

    st.markdown("---")

    # 6. Render Tabel Utama dan Fitur Download CSV
    render_data_table_and_export(df_filtered)

# Panggil fungsi fragment untuk merender visualisasi secara real-time
render_dashboard_content()
