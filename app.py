import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- 1. CONFIG & UI CUSTOMIZATION (BACKGROUND & FONT) ---
st.set_page_config(page_title="Sistem Klinik APD Digital", layout="wide", page_icon="🏥")

def local_css():
    # URL Gambar Tenaga Kesehatan menggunakan APD (Bisa diganti dengan URL gambar lokal Anda)
    bg_image_url = "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?q=80&w=2070&auto=format&fit=crop"
    
    st.markdown(f"""
    <style>
    /* Mengatur Font Global ke Times New Roman */
    * {{
        font-family: 'Times New Roman', Times, serif !important;
    }}

    /* Mengatur Background Gambar dengan Overlay Gelap */
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                    url("{bg_image_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Mengatur Kotak Input/Form agar Transparan & Elegan */
    div[data-testid="stForm"], .main-container {{
        background-color: rgba(255, 255, 255, 0.15); /* Transparansi Putih */
        backdrop-filter: blur(10px); /* Efek Kaca Blur */
        padding: 30px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white !important;
    }}

    /* Mengatur Label Text agar berwarna putih */
    label, p, h1, h2, h3, .stMarkdown {{
        color: white !important;
    }}

    /* Mengatur Kotak Input (TextField) */
    input, select, textarea {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: black !important;
        border-radius: 5px !important;
    }}

    /* Tombol Pendaftaran */
    .stButton>button {{
        background-color: #f1c40f !important; /* Warna Kuning Emas agar Mencolok */
        color: black !important;
        font-weight: bold;
        border: none;
        height: 3.5em;
        font-family: 'Times New Roman', Times, serif !important;
    }}

    /* Tiket Antrean */
    .ticket-style {{
        background: white;
        color: black !important;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 4px double #000;
    }}
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_apd.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS master_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antrean_harian 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status TEXT, tgl_antre DATE)''')
    conn.commit()
    conn.close()

def get_next_number(poli_nama):
    conn = sqlite3.connect('klinik_apd.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM antrean_harian WHERE tgl_antre = ? AND poli = ?", (date.today(), poli_nama))
    count = c.fetchone()[0]
    conn.close()
    return (count % 200) + 1

init_db()

# --- 3. LOGIKA APLIKASI ---
menu = st.sidebar.radio("MENU KLINIK", ["Pendaftaran", "Panggilan Perawat", "Monitor TV"])

if menu == "Pendaftaran":
    st.title("🏥 PENDAFTARAN PASIEN - KLINIK UTAMA")
    status = st.radio("Pilih Status Pasien:", ["Pasien Baru", "Pasien Lama"], horizontal=True)
    
    nik_final = ""
    nama_final = ""
    valid_data = False

    if status == "Pasien Lama":
        search_nik = st.text_input("CARI NIK / ID CARD:")
        if search_nik:
            conn = sqlite3.connect('klinik_apd.db')
            c = conn.cursor()
            c.execute("SELECT nama FROM master_pasien WHERE nik = ?", (search_nik,))
            res = c.fetchone()
            conn.close()
            if res:
                st.success(f"DATA DITEMUKAN: {res[0]}")
                nik_final, nama_final, valid_data = search_nik, res[0], True
            else:
                st.error("DATA TIDAK DITEMUKAN!")
    else:
        st.subheader("DATA IDENTITAS PASIEN BARU")
        c1, c2 = st.columns(2)
        with c1:
            nama_n = st.text_input("Nama Lengkap")
            nik_n = st.text_input("NIK / ID Card")
            t_lahir = st.text_input("Tempat Lahir")
            tg_lahir = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
            gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            no_wa = st.text_input("Nomor WhatsApp")
        with c2:
            pt = st.text_input("Perusahaan")
            dep = st.text_input("Departemen")
            jabat = st.text_input("Jabatan")
            mes = st.text_input("Blok Mes")
            kamar = st.text_input("Nomor Kamar")
            gol = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
        
        penyakit = st.text_area("Riwayat Penyakit")
        alergi = st.text_area("Riwayat Alergi")
        area = st.text_input("Area Lokasi Kerja")
        
        if nama_n and nik_n:
            nik_final, nama_final, valid_data = nik_n, nama_n, True

    if valid_data:
        st.markdown("---")
        poli_pilih = st.selectbox("
