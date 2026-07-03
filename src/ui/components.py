import streamlit as st
import pandas as pd
from datetime import datetime

#info waktu sekarang untuk nama file ekspor CSV
waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")

def render_metrics_cards(df: pd.DataFrame):
    """Menampilkan ringkasan metrik statistik monitoring ekologi di bagian atas dashboard"""
    if df.empty:
        total_detections = 0
        unique_species = 0
        highest_conf = 0.0
        last_sp = "Belum Ada"
    else:
        total_detections = len(df)
        unique_species = df['scientific_name'].nunique()
        highest_conf = df['confidence'].max() * 100
        last_sp = df['scientific_name'].iloc[0] # Baris teratas adalah data terbaru karena ORDER BY DESC

    # Membuat layout 4 kolom yang responsif
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total Sinyal Diterima", value=f"{total_detections} Sinyal")
    with col2:
        st.metric(label="Keanekaragaman Spesies", value=f"{unique_species} Spesies")
    with col3:
        st.metric(label="Akurasi Tertinggi", value=f"{highest_conf:.1f} %")
    with col4:
        st.metric(label="Deteksi Terakhir", value=last_sp)


def render_data_table_and_export(df: pd.DataFrame):
    """Menampilkan tabel log data hasil filter dan menyediakan tombol ekspor CSV"""
    st.subheader("📋 Log Data Monitoring")
    
    if df.empty:
        st.warning("Tidak ada data monitoring yang cocok dengan filter saat ini.")
        return

    # Tampilkan dataframe di UI dengan kolom yang rapi
    st.dataframe(
        df[['id', 'node_id', 'scientific_name', 'confidence', 'received_at']],
        column_config={
            "id": "ID Paket",
            "node_id": "ID Node Lapangan",
            "scientific_name": "Jenis Burung",
            "confidence": st.column_config.NumberColumn("Confidence Score", format="%.3f"),
            "received_at": "Waktu Diterima Basecamp"
        },
        width='stretch',
        hide_index=True
    )

    # Fitur download CSV satu klik (One-Click CSV Export)
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Ekspor Data Hasil Filter ke CSV",
        data=csv_data,
        file_name=f"apem_filter_{waktu_sekarang}.csv",
        mime="text/csv",
        key="download-csv-btn"
    )