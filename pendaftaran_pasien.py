import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS CUSTOM (UNTUK TAMPILAN MENARIK) ---
st.markdown("""
    <style>
    /* Mengatur font dan background */
    .main {
        background-color: #f5f7f9;
    }
    
    /* Membuat tombol simpan/kirim berwarna biru profesional */
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        width: 100%;
        height: 3em;
        font-weight: bold;
        border: none;
    }
    
    /* Efek hover tombol */
    div.stButton > button:first-child:hover {
        background-color: #0056b3;
        color: white;
    }

    /* Menyembunyikan baris indeks di tabel pandas */
    .row_heading.level0 {display:none}
    .blank {display:none}

    /* Mengatur padding untuk mobile agar tidak terlalu rapat */
    @media (max-width: 640px) {
        .block-container {
            padding: 1rem 1rem;
        }
    }
    </style>
    """, unsafe_with_html=True)

# --- 3. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_pendaftaran.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE,
                    bulan_daftar TEXT,
                    jenis_kunjungan TEXT, nama_lengkap TEXT, no_hp TEXT,
                    blok_mes TEXT, agama TEXT, nik TEXT, gender TEXT,
                    pernah_berobat TEXT, tempat_tgl_lahir TEXT,
                    perusahaan TEXT, departemen TEXT, jabatan TEXT,
                    alergi TEXT, gol_darah TEXT, lokasi_kerja TEXT,
                    file_skd_path TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. FUNGSI HELPER ---
def get_master(kategori):
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
    conn.close()
    return df['nama'].tolist()

def add_master(kategori, nama):
    if nama:
        conn = sqlite3.connect('klinik_pendaftaran.db')
        c = conn.cursor()
        c.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kategori, nama))
        conn.commit()
        conn.close()

def delete_master(kategori, nama):
    conn = sqlite3.connect('klinik_pendaftaran.db')
    c = conn.cursor()
    c.execute("DELETE FROM master_data WHERE kategori=? AND nama=?", (kategori, nama))
    conn.commit()
    conn.close()

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🏥 Menu Klinik")
    menu = st.radio("Navigasi:", 
        ["Pendaftaran Pasien", "Rekam Medis (Admin)", "Upload SKD", "Pusat SKD Publik", "Pengaturan Master"])
    st.info("Aplikasi ini dioptimalkan untuk scan QR Code melalui Smartphone.")

# --- 6. LOGIK MENU ---

if menu == "Pendaftaran Pasien":
    st.subheader("📝 Form Pendaftaran Mandiri")
    st.write("Silakan lengkapi data Anda untuk mendapatkan layanan.")
    
    with st.form("form_pendaftaran", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat luka"])
            nama = st.text_input("NAMA LENGKAP", placeholder="Sesuai KTP")
            hp = st.text_input("NO HP AKTIF (WhatsApp)", placeholder="0812...")
            agama = st.selectbox("AGAMA", ["Islam", "Kristen", "Hindu", "Buddah", "Katolik", "Tidak Diketahui"])
            nik = st.text_input("NIK / ID CARD")
            gender = st.selectbox("JENIS KELAMIN", ["Laki-laki", "Perempuan"])
            pernah = st.radio("SUDAH PERNAH BEROBAT?", ["Iya Sudah", "Belum Pernah"], horizontal=True)

        with col2:
            blok = st.text_input("BLOK MES & NO KAMAR")
            ttl = st.text_input("TEMPAT & TANGGAL LAHIR")
            perusahaan = st.selectbox("PERUSAHAAN", get_master("Perusahaan"))
            dept = st.selectbox("DE
