import streamlit as st
import pandas as pd

def hitung_barber_johnson(hp, pasien_keluar, tt, periode):
    # Perhitungan Indikator
    bor = (hp / (tt * periode)) * 100
    avlos = hp / pasien_keluar
    toi = ((tt * periode) - hp) / pasien_keluar
    bto = pasien_keluar / tt
    
    # Logika Efisiensi (Standar Depkes)
    is_efisien = (60 <= bor <= 85) and (6 <= avlos <= 9) and (1 <= toi <= 3) and (bto >= 40)
    
    return {
        "BOR (%)": round(bor, 2),
        "AVLOS (Hari)": round(avlos, 2),
        "TOI (Hari)": round(toi, 2),
        "BTO (Kali)": round(bto, 2),
        "Status": "Efisien" if is_efisien else "Tidak Efisien"
    }

st.title("🏥 Modul Efisiensi Barber Johnson")

with st.form("input_data"):
    col1, col2 = st.columns(2)
    with col1:
        tt = st.number_input("Jumlah Tempat Tidur (TT)", min_value=1, value=50)
        periode = st.number_input("Periode Waktu (Hari)", min_value=1, value=30)
    with col2:
        hp = st.number_input("Total Hari Perawatan (HP)", min_value=1, value=1200)
        pasien_keluar = st.number_input("Pasien Keluar (Hidup + Mati)", min_value=1, value=150)
    
    submit = st.form_submit_button("Hitung Indikator")

if submit:
    hasil = hitung_barber_johnson(hp, pasien_keluar, tt, periode)
    
    # Menampilkan Metric Card
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("BOR", f"{hasil['BOR (%)']}%")
    c2.metric("AVLOS", f"{hasil['AVLOS (Hari)']} hari")
    c3.metric("TOI", f"{hasil['TOI (Hari)']} hari")
    c4.metric("BTO", f"{hasil['BTO (Kali)']} kali")
    
    # Status Efisiensi
    if hasil["Status"] == "Efisien":
        st.success(f"✅ Status: **{hasil['Status']}** (Memenuhi standar Depkes)")
    else:
        st.warning(f"⚠️ Status: **{hasil['Status']}** (Di luar range ideal)")
