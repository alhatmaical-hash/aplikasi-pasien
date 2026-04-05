import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps - Barber Johnson", layout="wide")

# --- 2. FUNGSI PERHITUNGAN ---
def hitung_barber_johnson(hp, pasien_keluar, tt, periode):
    # Rumus Standar Rekam Medis
    bor = (hp / (tt * periode)) * 100
    avlos = hp / pasien_keluar
    toi = ((tt * periode) - hp) / pasien_keluar
    bto = pasien_keluar / tt
    
    # Indikator Efisiensi (Standar Depkes RI)
    is_efisien = (60 <= bor <= 85) and (6 <= avlos <= 9) and (1 <= toi <= 3) and (bto >= 40)
    
    return {
        "BOR": round(bor, 2),
        "AVLOS": round(avlos, 2),
        "TOI": round(toi, 2),
        "BTO": round(bto, 2),
        "Status": "Efisien" if is_efisien else "Tidak Efisien"
    }

# --- 3. FUNGSI GRAFIK ---
def buat_grafik(bor, avlos, toi, bto):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Judul dan Label
    ax.set_title('Grafik Barber Johnson', fontsize=16, pad=20, fontweight='bold')
    ax.set_xlabel('TOI (Hari)', fontsize=12)
    ax.set_ylabel('AVLOS (Hari)', fontsize=12)
    
    # Batas Skala agar tidak zoom-in terlalu dalam (0 - 15 hari)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 15)
    
    # Gambar Kotak Efisiensi (Hijau)
    # x=1 (TOI min), y=6 (AVLOS min), width=2 (sampai TOI 3), height=3 (sampai AVLOS 9)
    rect = plt.Rectangle((1, 6), 2, 3, color='green', alpha=0.15, label='Daerah Efisien (Depkes)')
    ax.add_patch(rect)
    
    # Garis Bantu BOR (Diagonal)
    x_vals = np.linspace(0.1, 15, 100)
    for b in [70, 75, 80, 85]:
        y_vals = (b / (100 - b)) * x_vals
        ax.plot(x_vals, y_vals, '--', color='gray', alpha=0.4, linewidth=1)
        if y_vals[-1] < 15:
            ax.text(x_vals[-1], y_values[-1], f' {b}%', fontsize=9, verticalalignment='center')

    # Plot Titik Posisi Klinik (Merah)
    ax.scatter(toi, avlos, color='red', s=200, edgecolors='black', zorder=10, label='Posisi Saat Ini')
    
    # Garis Putus-putus ke arah Sumbu
    ax.plot([toi, toi], [0, avlos], 'r--', alpha=0.3)
    ax.plot([0, toi], [avlos, avlos], 'r--', alpha=0.3)
    
    # Anotasi angka di titik
    ax.annotate(f'({toi}, {avlos})', (toi, avlos), textcoords="offset points", xytext=(0,15), ha='center', fontweight='bold')

    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right')
    
    return fig

# --- 4. TAMPILAN UI STREAMLIT ---
st.title("🏥 Modul Efisiensi Barber Johnson")
st.write("Gunakan form di bawah untuk menghitung indikator efisiensi tempat tidur.")

with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        tt = st.number_input("Jumlah Tempat Tidur (TT)", min_value=1, value=50)
        periode = st.number_input("Periode Waktu (Hari)", min_value=1, value=30)
    with col2:
        hp = st.number_input("Total Hari Perawatan (HP)", min_value=1, value=1200)
        pasien_keluar = st.number_input("Pasien Keluar (Hidup + Mati)", min_value=1, value=150)
    
    submit = st.form_submit_button("Hitung & Tampilkan Grafik")

if submit:
    # Hitung Data
    hasil = hitung_barber_johnson(hp, pasien_keluar, tt, periode)
    
    # Tampilkan Indikator dalam Kolom
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BOR", f"{hasil['BOR']}%")
    m2.metric("AVLOS", f"{hasil['AVLOS']} Hari")
    m3.metric("TOI", f"{hasil['TOI']} Hari")
    m4.metric("BTO", f"{hasil['BTO']} Kali")
    
    # Status Efisiensi
    if hasil["Status"] == "Efisien":
        st.success(f"✅ Status: **{hasil['Status']}** (Masuk dalam daerah efisien)")
    else:
        st.warning(f"⚠️ Status: **{hasil['Status']}** (Di luar range ideal Depkes)")

    # Tampilkan Grafik
    st.subheader("Visualisasi Grafik Barber Johnson")
    fig_bj = buat_grafik(hasil["BOR"], hasil["AVLOS"], hasil["TOI"], hasil["BTO"])
    st.pyplot(fig_bj, use_container_width=True)
