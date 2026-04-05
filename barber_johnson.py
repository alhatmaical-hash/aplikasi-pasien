import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import hashlib
import datetime
from io import BytesIO

# --- 1. KONFIGURASI HALAMAN & KEAMANAN ---
st.set_page_config(page_title="Klinik Apps - Barber Johnson", layout="wide")

# Keamanan Tanggal (Expired)
deadline = datetime.date(2026, 4, 28) 
if datetime.date.today() > deadline:
    st.error("⚠️ Masa berlaku aplikasi telah habis. Silakan hubungi pembuat.")
    st.stop()

# --- 2. DATABASE USER ---
def create_user_table():
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    # Admin default: admin / admin123
    hashed_pw = hashlib.sha256(str.encode('admin123')).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
    conn.commit()
    conn.close()

create_user_table()

# --- 3. SISTEM LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login Klinik Apps")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        hpw = hashlib.sha256(str.encode(pw)).hexdigest()
        conn = sqlite3.connect('database_klinik.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (user, hpw))
        data = c.fetchone()
        conn.close()
        if data:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user
            st.session_state['role'] = data[2]
            st.rerun()
        else:
            st.error("Username atau Password salah!")
    st.stop()

# --- 4. SIDEBAR & MANAJEMEN USER ---
st.sidebar.title(f"👤 {st.session_state['username']}")
st.sidebar.write(f"Role: {st.session_state['role']}")

if st.session_state['role'] == 'admin':
    with st.sidebar.expander("➕ Tambah User Baru"):
        new_user = st.text_input("Username Baru")
        new_pw = st.text_input("Password Baru", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        if st.button("Simpan User"):
            if new_user and new_pw:
                h_new_pw = hashlib.sha256(str.encode(new_pw)).hexdigest()
                try:
                    conn = sqlite3.connect('database_klinik.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO users VALUES (?, ?, ?)", (new_user, h_new_pw, new_role))
                    conn.commit()
                    conn.close()
                    st.sidebar.success(f"User {new_user} berhasil dibuat!")
                except:
                    st.sidebar.error("Username sudah ada!")
            else:
                st.sidebar.warning("Isi semua kolom!")

if st.sidebar.button("🚪 Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 5. FUNGSI PERHITUNGAN & GRAFIK ---
def hitung_bj(hp, pk, tt, p):
    bor = (hp / (tt * p)) * 100
    avlos = hp / pk
    toi = ((tt * p) - hp) / pk
    bto = pk / tt
    # Standar Depkes
    efisien = (60 <= bor <= 85) and (6 <= avlos <= 9) and (1 <= toi <= 3) and (bto >= 40)
    return {"BOR": bor, "AVLOS": avlos, "TOI": toi, "BTO": bto, "Status": efisien}

def buat_grafik(toi, avlos):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 15); ax.set_ylim(0, 15)
    ax.set_xlabel("TOI (Hari)"); ax.set_ylabel("AVLOS (Hari)")
    ax.set_title("Grafik Barber Johnson", fontweight='bold')
    # Area Efisien
    ax.add_patch(plt.Rectangle((1, 6), 2, 3, color='green', alpha=0.2, label='Daerah Efisien'))
    # Titik Posisi
    ax.scatter(toi, avlos, color='red', s=100, edgecolors='black', label='Posisi Klinik')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    return fig

# --- 6. TAMPILAN UTAMA MODUL ---
st.title("🏥 Modul Efisiensi Barber Johnson")
st.write("Gunakan form di bawah untuk menghitung indikator efisiensi tempat tidur.")

with st.form("input_form"):
    c1, c2 = st.columns(2)
    tt = c1.number_input("Jumlah Tempat Tidur (TT)", value=50, min_value=1)
    p = c1.number_input("Periode Waktu (Hari)", value=30, min_value=1)
    hp = c2.number_input("Total Hari Perawatan (HP)", value=1200, min_value=1)
    pk = c2.number_input("Pasien Keluar (Hidup + Mati)", value=150, min_value=1)
    submit = st.form_submit_button("🚀 Hitung & Tampilkan Grafik")

if submit:
    res = hitung_bj(hp, pk, tt, p)
    
    st.subheader("📊 Hasil Indikator")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BOR", f"{res['BOR']:.1f}%")
    m2.metric("AVLOS", f"{res['AVLOS']:.1f} Hari")
    m3.metric("TOI", f"{res['TOI']:.1f} Hari")
    m4.metric("BTO", f"{res['BTO']:.1f} Kali")

    if res['Status']:
        st.success("✅ Status: **Efisien** (Masuk dalam range ideal Depkes)")
    else:
        st.warning("⚠️ Status: **Tidak Efisien** (Di luar range ideal Depkes)")

    # --- FITUR DOWNLOAD ---
    st.subheader("📥 Download Laporan")
    d1, d2 = st.columns(2)
    
    # Excel Download
    df_res = pd.DataFrame([res])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_res.to_excel(writer, index=False, sheet_name='Hasil')
    d1.download_button(label="📄 Download Data (Excel)", data=output.getvalue(), file_name="hasil_bj.xlsx")

    # Grafik Download (JPG)
    fig_bj = buat_grafik(res['TOI'], res['AVLOS'])
    buf = BytesIO()
    fig_bj.savefig(buf, format="jpg")
    d2.download_button(label="🖼️ Download Grafik (JPG)", data=buf.getvalue(), file_name="grafik_bj.jpg", mime="image/jpg")

    st.markdown("---")
    st.subheader("Visualisasi Grafik Barber Johnson")
    st.pyplot(fig_bj)
