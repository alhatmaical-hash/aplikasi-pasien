import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import sqlite3
import hashlib
import datetime

# --- 1. KEAMANAN: TANGGAL & KODE AKTIVASI ---
deadline = datetime.date(2026, 4, 28) 
if datetime.date.today() > deadline:
    st.error("Masa berlaku aplikasi telah habis.")
    st.stop()

# --- 2. FUNGSI DATABASE & LOGIN ---
def create_user_table():
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
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

# Jalankan buat tabel
create_user_table()

# --- 3. SISTEM LOGIN ---
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

# --- 4. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(page_title="Klinik Apps", layout="wide")

# Menu Admin
if st.session_state['role'] == 'admin':
    with st.sidebar.expander("🛠️ Menu Admin"):
        new_user = st.text_input("Username Baru")
        new_pw = st.text_input("Password Baru", type="password")
        if st.button("Simpan User"):
            conn = sqlite3.connect('database_klinik.db')
            c = conn.cursor()
            hashed_new_pw = hashlib.sha256(str.encode(new_pw)).hexdigest()
            c.execute("INSERT INTO users VALUES (?, ?, ?)", (new_user, hashed_new_pw, 'user'))
            conn.commit()
            conn.close()
            st.success("User berhasil ditambah!")

# --- 5. ISI MODUL BARBER JOHNSON ---
st.title("🏥 Modul Efisiensi Barber Johnson")
# Masukkan kode input (TT, HP, Pasien Keluar) dan grafik kamu di sini...
