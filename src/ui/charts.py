import streamlit as st
import pandas as pd
import plotly.express as px

def render_species_distribution(df: pd.DataFrame):
    """Menampilkan grafik batang distribusi jumlah deteksi per spesies"""
    st.subheader("📊 Distribusi Kemunculan Spesies")
    
    if df.empty:
        st.info("Belum ada data untuk membuat grafik distribusi.")
        return

    # Hitung total kemunculan setiap spesies
    species_counts = df['scientific_name'].value_counts().reset_index()
    species_counts.columns = ['Spesies', 'Jumlah Deteksi']

    # Buat grafik batang interaktif menggunakan Plotly Express
    fig = px.bar(
        species_counts, 
        x='Jumlah Deteksi', 
        y='Spesies', 
        orientation='h',
        labels={'Spesies': 'Jenis Burung', 'Jumlah Deteksi': 'Frekuensi Kemunculan'},
        template="plotly_dark"
    )
    
    # Perbaikan visual layout agar teks tidak terpotong
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, width='stretch')


def render_temporal_activity(df: pd.DataFrame):
    """Menampilkan grafik tren aktivitas kemunculan burung berdasarkan waktu (Jam)"""
    st.subheader("📈 Tren Aktivitas Burung")
    
    if df.empty:
        st.info("Belum ada data untuk membuat grafik tren waktu.")
        return

    # Konversi kolom waktu ke tipe datetime lokal
    df_temporal = df.copy()
    df_temporal['datetime'] = pd.to_datetime(df_temporal['received_at'])
    df_temporal['Jam'] = df_temporal['datetime'].dt.hour

    # Kelompokkan data per jam untuk melihat pola aktivitas harian
    hourly_activity = df_temporal.groupby('Jam').size().reset_index(name='Total Deteksi')

    # Buat grafik garis tren temporal
    fig = px.line(
        hourly_activity,
        x='Jam',
        y='Total Deteksi',
        markers=True,
        labels={'Jam': 'Waktu Pengamatan', 'Total Deteksi': 'Jumlah Deteksi'},
        template="plotly_dark"
    )
    
    fig.update_xaxes(tickmode='linear', tick0=0, dtick=1, range=[0, 23])
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, width='stretch')