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
    toi =
