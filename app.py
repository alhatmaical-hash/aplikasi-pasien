import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

# --- 1. KONFIGURASI TAMPILAN & BACKGROUND (UI) ---
st.set_page_config(page_title="Sistem Klinik APD Digital", layout="wide", page_icon="🏥")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_custom_ui(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    st.markdown(f'''
    <style>
    /* Font Global */
    * {{
        font-family: 'Times New Roman', Times, serif !important;
    }}

    /* Background Utama dengan Overlay Gelap */
    .stApp {{
        background-image: linear-gradient(rgba(0, 20, 40, 0.7), rgba(0, 10, 20, 0.9)), 
                          url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Judul Utama */
    .stApp h1 {{
        color: white !important;
        font-weight: bold;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
        text-transform: uppercase;
        margin-bottom: 5px;
    }}

    /* Kotak Form (Glassmorphism): Transparan, Terang, & Jelas */
    div[data-testid="stForm"], .glass-container, .stApp [data-testid="stMarkdownContainer"] p {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        padding: 30px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #e0f7fa !important; /* Biru Cyan Terang */
        font-size: 18px !important;
        font-weight: bold;
    }}

    /* Input Fields */
    input, select, textarea {{
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: black !important;
        font-weight: bold !important;
    }}

    /* Tombol Cari & Daftar */
    .stButton>button {{
        background: linear-gradient(90deg, #00d4ff, #00509d) !important;
        color: white !important;
        border-radius: 10px;
        font-weight: bold;
        height: 3.5em;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        box-shadow: 0 0 15px #00d4ff;
        transform: scale(1.02);
    }}
    </style>
    ''', unsafe_allow_html=True)

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_pro.db')
    c = conn.cursor()
    # Tabel Master Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS master_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    # Tabel Transaksi Antrean (Berkelanjutan & Harian)
    c.execute('''CREATE TABLE IF NOT EXISTS antrean_harian 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status_antre TEXT, tgl DATE)''')
    conn.commit()
    conn.close()

def get_next_number(poli_nama):
    conn = sqlite3.connect('klinik_pro.db')
    c = conn.cursor()
    # Menghitung total antrean di poli tersebut hari ini (maks 300)
    c.execute("SELECT COUNT(*) FROM antrean_harian WHERE tgl = ? AND poli = ?", (date.today(), poli_nama))
    count = c.fetchone()[0]
    conn.close()
    if count >= 300: return 1
    return count + 1

# Inisialisasi Database
init_db()

# Terapkan UI Custom (Gunakan nama file gambar Anda)
try:
    apply_custom_ui('download.jpg')
except:
    st.error("Gambar 'download.jpg' tidak ditemukan! Pastikan file ada di folder aplikasi.")

