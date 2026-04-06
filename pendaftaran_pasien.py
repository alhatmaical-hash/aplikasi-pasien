import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide"
)

# --- 2. TAMPILAN CSS (VERSI AMAN UNTUK PYTHON 3.14) ---
# Menggunakan f-string sederhana untuk menghindari masalah karakter multiline
css_code = """
<style>
    .stButton>button {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    [data-testid="stElementToolbar"] {display: none;}
</style>
"""
st.markdown(css_code, unsafe_with_html=True)

# --- 3. DATABASE SETUP ---
def get_connection():
    # check_same_thread=False sangat penting untuk aplikasi web
    return sqlite3.connect('klinik_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE, bulan_daftar TEXT, jenis_kunjungan TEXT, 
                    nama_lengkap TEXT, no_hp TEXT, blok_mes TEXT, agama TEXT, 
                    nik TEXT, gender TEXT, pernah_berobat TEXT, tempat_tgl_lahir TEXT,
                    perusahaan TEXT, departemen TEXT, jabatan TEXT,
                    alergi TEXT, gol_darah TEXT, lokasi_kerja TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. FUNGSI DATA ---
def get_master(kategori):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
        return df['nama'].tolist()
    except:
        return []
    finally:
        conn.close()

# --- 5. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 Menu Utama")
menu = st.sidebar.radio("Pilih Halaman", ["Pendaftaran", "Rekam Medis", "Pengaturan Master"])

# --- 6. MENU PENDAFTARAN ---
if menu == "Pendaftaran":
    st.header("📝 Pendaftaran Pasien")
    
    # Ambil data dropdown
    opts_perusahaan = get_master("Perusahaan")
    opts_dept = get_master("Departemen")
    opts_jabatan = get_master("Jabatan")

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat luka"])
            nama = st.text_input("NAMA LENGKAP")
            hp = st.text_input("NO HP AKTIF")
            agama = st.selectbox("AGAMA", ["Islam", "Kristen", "Hindu", "Buddah", "Katolik", "Tidak Diketahui"])
            nik = st.text_input("NIK IDCARD")
            gender = st.selectbox("JENIS KELAMIN", ["Laki-laki", "Perempuan"])
            pernah = st.radio("PERNAH BEROBAT DISINI?", ["Iya Sudah", "Belum Pernah"], horizontal=True)

        with col2:
            blok = st.text_input("BLOK MES & NO KAMAR")
            ttl = st.text_input("TEMPAT & TANGGAL LAHIR")
            perusahaan = st.selectbox("PERUSAHAAN", opts_perusahaan if opts_perusahaan else ["Isi di Pengaturan Master"])
            dept = st.selectbox("DEPARTEMEN", opts_dept if opts_dept else ["Isi di Pengaturan Master"])
            jabatan = st.selectbox("JABATAN", opts_jabatan if opts_jabatan else ["Isi di Pengaturan Master"])
            alergi = st.selectbox("JENIS ALERGI", ["Tidak Ada", "Makanan", "Obat", "Cuaca"])
            darah = st.selectbox("GOLONGAN DARAH", ["A", "B", "AB", "O", "Tidak Tahu"])
            
        lokasi = st.text
