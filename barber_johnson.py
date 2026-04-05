import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import hashlib
import datetime
from io import BytesIO

# --- 1. KEAMANAN TANGGAL ---
deadline = datetime.date(2026, 4, 28) 
if datetime.date.today() > deadline:
    st.error("Masa berlaku aplikasi habis!")
    st.stop()

# --- 2. KODE AKTIVASI SIDEBAR ---
if st.sidebar.text_input("🔑 Kode Aktivasi", type="password") != "Rahasia123":
    st.info("Masukkan kode aktivasi di sidebar.")
    st.stop()

# --- 3. DATABASE & LOGIN ---
def create_user_table():
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    hashed_pw = hashlib.sha256(str.encode('admin123')).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
    conn.commit()
    conn.close()

create_user_table()

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
            st.session_state['logged_in'], st.session_state['username'], st.session_state['role'] = True, user, data[2]
            st.rerun()
        else:
            st.error("Salah!")
    st.stop()

# --- 4. CONFIG HALAMAN ---
st.set_page_config(page_title="Klinik Apps", layout="wide")

# --- 5. FUNGSI PERHITUNGAN ---
def hitung_bj(hp, pk, tt, p):
    bor = (hp / (tt * p)) * 100
    avlos = hp / pk
    toi = ((tt * p) - hp) / pk
    bto = pk / tt
    efisien = (60 <= bor <= 85) and (6 <= avlos <= 9) and (1 <= toi <= 3) and (bto >= 40)
    return {"BOR": round(bor, 2), "AVLOS": round(avlos, 2), "TOI": round(toi, 2), "BTO": round(bto, 2), "Status": efisien}

# --- 6. TAMPILAN UTAMA ---
st.title("🏥 Modul Efisiensi Barber Johnson")

with st.form("input_form"):
    c1, c2 = st.columns(2)
    tt = c1.number_input("TT", value=50)
    p = c1.number_input("Periode", value=30)
    hp = c2.number_input("HP", value=1200)
    pk = c2.number_input("Pasien Keluar", value=150)
    if st.form_submit_button("Hitung"):
        h = hitung_bj(hp, pk, tt, p)
        st.write(f"BOR: {h['BOR']}% | AVLOS: {h['AVLOS']} | TOI: {h['TOI']} | BTO: {h['BTO']}")
        
        # Grafik Sederhana (Anti Error)
        fig, ax = plt.subplots()
        ax.set_xlim(0, 15); ax.set_ylim(0, 15)
        ax.add_patch(plt.Rectangle((1, 6), 2, 3, color='green', alpha=0.2)) # Area Efisien
        ax.scatter(h['TOI'], h['AVLOS'], color='red', s=100)
        ax.set_xlabel("TOI"); ax.set_ylabel("AVLOS")
        st.pyplot(fig)
