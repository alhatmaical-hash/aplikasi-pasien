import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# 1. Definisikan fungsi hitung di bagian atas
def hitung_barber_johnson(hp, pasien_keluar, tt, periode):
    bor = (hp / (tt * periode)) * 100
    avlos = hp / pasien_keluar
    toi = ((tt * periode) - hp) / pasien_keluar
    bto = pasien_keluar / tt
    return {"BOR": bor, "AVLOS": avlos, "TOI": toi, "BTO": bto}

# 2. Definisikan fungsi grafik
def buat_grafik(bor, avlos, toi, bto):
    fig, ax = plt.subplots()
    # ... (isi kode grafik matplotlib Anda) ...
    ax.scatter(toi, avlos, color='red', s=100) # Titik posisi klinik
    return fig

# 3. Form Input
with st.form("input_data"):
    col1, col2 = st.columns(2)
    with col1:
        tt = st.number_input("Jumlah Tempat Tidur", value=50)
        periode = st.number_input("Periode (Hari)", value=30)
    with col2:
        hp = st.number_input("Hari Perawatan", value=1200)
        pasien_keluar = st.number_input("Pasien Keluar", value=150)
    
    # DISINI VARIABEL 'submit' DIBUAT
    submit = st.form_submit_button("Hitung Indikator")

# 4. Logika Output (Gunakan 'submit' di sini)
if submit:
    hasil = hitung_barber_johnson(hp, pasien_keluar, tt, periode)
    
    # Tampilkan angka
    st.write(f"BOR: {hasil['BOR']:.2f}% | AVLOS: {hasil['AVLOS']:.2f}")
    
    # Tampilkan Grafik
    fig_bj = buat_grafik(hasil['BOR'], hasil['AVLOS'], hasil['TOI'], hasil['BTO'])
    st.pyplot(fig_bj)
