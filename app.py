import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- 1. CONFIG & CUSTOM CSS (TAMPILAN MENARIK) ---
st.set_page_config(page_title="Klinik Pratama Digital", layout="wide", page_icon="🏥")

def local_css():
    st.markdown("""
    <style>
    /* Mengatur Background Utama dengan Gradien Medis */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Mengatur Kotak Form agar Melayang dan Putih Bersih */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: none;
    }
    
    /* Mengatur Judul */
    h1 {
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }
    
    /* Mengatur Tombol agar Berwarna Biru Profesional */
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        width: 100%;
        height: 3em;
        font-weight: bold;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #0056b3;
        border: none;
    }

    /* Sticker Antrean */
    .ticket {
        background: #fff;
        border-left: 10px solid #007bff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.05);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('klinik_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antrean 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status TEXT, tgl_antre DATE)''')
    conn.commit()
    conn.close()

def get_next_antrean(poli_kode):
    conn = sqlite3.connect('klinik_pro.db')
    c = conn.cursor()
    today = date.today()
    c.execute("SELECT COUNT(*) FROM antrean WHERE tgl_antre = ? AND poli LIKE ?", (today, f"{poli_kode}%"))
    count = c.fetchone()[0]
    conn.close()
    return (count % 200) + 1

init_db()

# --- 3. LOGIKA NAVIGASI ---
menu = st.sidebar.radio("MENU UTAMA", ["📝 Pendaftaran Pasien", "👩‍⚕️ Ruang Perawat", "📺 Monitor Antrean"])

if menu == "📝 Pendaftaran Pasien":
    st.title("🏥 Pendaftaran Klinik Digital")
    st.write("Silakan pilih status pasien dan isi formulir.")
    
    status = st.radio("Status Pasien:", ["Pasien Baru", "Pasien Lama"], horizontal=True)
    
    with st.form("form_regis"):
        if status == "Pasien Baru":
            st.subheader("📋 Identitas Lengkap (Wajib Isi)")
            c1, c2 = st.columns(2)
            with c1:
                nama = st.text_input("Nama Lengkap")
                nik = st.text_input("NIK / ID Card")
                tempat_lahir = st.text_input("Tempat Lahir")
                tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
                gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
                agama = st.selectbox("Agama", ["Islam", "Kristen", "Katolik", "Hindu", "Budha"])
                no_hp = st.text_input("No. HP / WhatsApp")
                gol_darah = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
            with c2:
                perusahaan = st.text_input("Perusahaan")
                departemen = st.text_input("Departemen")
                jabatan = st.text_input("Jabatan")
                blok_mes = st.text_input("Blok Mes")
                no_kamar = st.text_input("Nomor Kamar")
                area_kerja = st.text_input("Area Lokasi Kerja")
                riwayat_penyakit = st.text_area("Riwayat Penyakit")
                riwayat_alergi = st.text_area("Riwayat Alergi")
        else:
            nik = st.text_input("Masukkan NIK Pasien Lama")
            st.info("Data identitas akan diambil otomatis dari sistem.")

        st.markdown("---")
        poli_tujuan = st.selectbox("Pilih Poli Tujuan:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat In

import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- 1. CONFIG & CUSTOM CSS (BACKGROUND BIRU & GAMBAR) ---
st.set_page_config(page_title="Klinik Pratama Digital", layout="wide", page_icon="🏥")

def local_css():
    st.markdown("""
    <style>
    /* Mengatur Background Utama: Biru Medis Professional */
    .stApp {
        background: linear-gradient(180deg, #003366 0%, #00509d 50%, #f0f2f6 100%);
        background-attachment: fixed;
    }
    
    /* Mengatur Kotak Putih Konten */
    .main-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        margin-top: 20px;
    }
    
    /* Header dengan Gambar Petugas */
    .header-box {
        display: flex;
        align-items: center;
        justify-content: center;
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
    }
    
    .header-text {
        margin-left: 20px;
        color: #003366;
    }

    /* Tombol Custom */
    .stButton>button {
        background: #00509d;
        color: white;
        border-radius: 10px;
        border: none;
        height: 3.5em;
        font-size: 18px;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background: #003366;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('klinik_perusahaan_v2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    c.execute('''CREATE TABLE
