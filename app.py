import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- 1. KONFIGURASI TAMPILAN (UI) ---
st.set_page_config(page_title="Sistem Pendaftaran Klinik", layout="wide")

def local_css():
    st.markdown("""
    <style>
    /* Mengatur Background Abu-abu */
    .stApp {
        background-color: #4b4b4b; /* Abu-abu Gelap agar teks putih menonjol */
    }

    /* Mengatur Font Global ke Times New Roman */
    * {
        font-family: 'Times New Roman', Times, serif !important;
    }

    /* Kotak Form (Glassmorphism) agar teks terang dan jelas */
    div[data-testid="stForm"], .main-box {
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Teks Putih Terang & Jelas */
    h1, h2, h3, label, p, .stMarkdown {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }

    /* Input Fields agar kontras */
    input, select, textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* Tombol Pendaftaran Kuning Emas */
    .stButton>button {
        background-color: #f1c40f !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none;
        height: 3em;
        width: 100%;
    }
    
    /* Tiket Antrean */
    .ticket {
        background: white;
        color: black !important;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border-left: 10px solid #f1c40f;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('klinik_abu.db')
    c = conn.cursor()
    # Tabel Data Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS master_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    # Tabel Antrean
    c.execute('''CREATE TABLE IF NOT EXISTS antrean_harian 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status TEXT, tgl DATE)''')
    conn.commit()
    conn.close()

def get_next_antrean(poli_nama
