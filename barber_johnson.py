import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import hashlib
import datetime
from io import BytesIO

# =========================================================
# 1. LAPIS KEAMANAN 1: TANGGAL KADALUARSA (EXPIRED)
# =========================================================
deadline = datetime.date(2026, 4, 28) 
if datetime.date.today() > deadline:
    st.error("⚠️ Masa berlaku aplikasi telah habis. Silakan hubungi pembuat (Alhatmaical).")
    st.stop()

# =========================================================
# 2. LAPIS KEAMANAN 2: KODE AKTIVASI SIDEBAR
# =========================================================
password_akses = "Rahasia123"
user_input = st.sidebar.text_input("🔑 Masukkan Kode Aktivasi", type="password")

if user_input != password_akses:
    st.info("💡 Silakan masukkan kode aktivasi di sidebar untuk menggunakan aplikasi.")
    st.stop()

# =========================================================
# 3. SISTEM DATABASE & FUNGSI LOGIN
# =========================================================
def create_user_table():
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    # Admin default (Password: admin123)
    hashed_pw = hashlib.sha256(str.encode('admin123')).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(str.encode(password)).hexdigest()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, hashed_pw))
    data = c.fetchone()
    conn.close()
    return data

# Jalankan inisialisasi database
create_user_table()

# =========================================================
# 4. MODUL LOGIN
# =========================================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login Klinik Apps")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        result = login_user(user, pw)
        if result:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user
            st.session_state['role'] = result[2]
            st.rerun()
        else:
            st.error("Username atau Password salah")
    st.stop()

# =========================================================
# 5. KONFIGURASI HALAMAN UTAMA (SETELAH LOGIN)
# =========================================================
st.set_page_config(page_title="Klinik Apps - Barber Johnson", layout="wide")

# Tombol Logout di Sidebar
if st.sidebar.button("🚪 Log Out"):
    st.session_state['logged_in'] = False
    st.rerun()

# =========================================================
# 6. MENU ADMIN (Hanya muncul jika Role = Admin)
# =========================================================
if st.session_state['role'] == 'admin':
    with st.sidebar.expander("🛠️ Menu Admin: Tambah User"):
        new_user = st.text_input("Username Baru")
        new_pw = st.text_input("Password Baru", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        
        if st.button("Simpan User Baru"):
            conn = sqlite3.connect('database_klinik.db')
            c = conn.cursor()
            hashed_new_pw = hashlib.sha256(str.encode(new_pw)).hexdigest()
            try:
                c.execute("INSERT INTO users VALUES (?, ?, ?)", (new_user, hashed_new_pw, new_role))
                conn.commit()
                st.success(f"User {new_user} berhasil ditambah!")
            except:
                st.error("Username sudah ada!")
            conn.close()

# =========================================================
# 7. LOGIKA PERHITUNGAN & GRAFIK (MODUL ASLI KAMU)
# =========================================================

def hitung_barber_johnson(hp, pasien_keluar, tt, periode):
    bor = (hp / (tt * periode)) * 100
    avlos = hp / pasien_keluar
    toi = ((tt * periode) - hp) / pasien_keluar
    bto = pasien_keluar / tt
    is_efisien = (60 <= bor <= 85) and (6 <= avlos <= 9) and (1 <= toi <= 3) and (bto >= 40)
    return {
        "BOR": round(bor, 2), "AVLOS": round(avlos, 2),
        "TOI": round(toi, 2), "BTO": round(bto, 2),
        "Status": "Efisien" if is_efisien else "Tidak Efisien"
    }

def buat_grafik(bor, avlos, toi, bto):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title('Grafik Barber Johnson', fontsize=16, pad=20, fontweight='bold')
    ax.set_xlabel('TOI (Hari)', fontsize=12)
    ax.set_ylabel('AVLOS (Hari)', fontsize=12)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 15)
    
    # Kotak Efisiensi
    rect = plt.Rectangle((1, 6), 2, 3, color='green', alpha=0.15, label='Daerah Efisien (Depkes)')
    ax.add_patch(rect)
    
    # Garis BOR
    x_vals = np.linspace(0.1, 15, 100)
    for b in [70, 75, 80, 85]:
        y_vals = (b / (100 - b)) * x_vals
        ax.plot(x_vals, y_vals, '--', color='gray', alpha=0.4)
    
    ax.scatter(toi, avlos, color='red', s=200, edgecolors='black', zorder=10, label='Posisi Saat Ini')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    return fig

# =========================================================
# 8. TAMPILAN INTERFACE UTAMA
# =========================================================
st.title("🏥 Modul Efisiensi Barber Johnson")
st.info(f"Logged in as: **{st.session_state['username']}** ({st.session_state['role']})")

with st.form("input_
