import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('klinik_utama.db')
    c = conn.cursor()
    # Tabel Pasien Baru & Identitas Lengkap
    c.execute('''CREATE TABLE IF NOT EXISTS data_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT, tgl_daftar DATE)''')
    
    # Tabel Antrean
    c.execute('''CREATE TABLE IF NOT EXISTS antrean 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut INTEGER, tgl_antre DATE)''')
    conn.commit()
    conn.close()

# Fungsi untuk mengambil nomor antrean berikutnya (1-200)
def get_next_antrean():
    conn = sqlite3.connect('klinik_utama.db')
    c = conn.cursor()
    today = date.today()
    c.execute("SELECT MAX(no_urut) FROM antrean WHERE tgl_antre = ?", (today,))
    result = c.fetchone()[0]
    conn.close()
    
    if result is None or result >= 200:
        return 1
    return result + 1

init_db()

# --- 2. ANTARMUKA (UI) ---
st.set_page_config(page_title="Sistem Klinik Perusahaan", layout="wide")

st.title("🏥 Sistem Pendaftaran Klinik Digital")
st.sidebar.title("Menu Utama")
mode = st.sidebar.selectbox("Pilih Status Pasien:", ["Pasien Baru", "Pasien Lama", "Admin (Cek Data)"])

# --- ALUR PASIEN BARU ---
if mode == "Pasien Baru":
    st.subheader("Formulir Pendaftaran Pasien Baru")
    st.warning("Semua kolom di bawah ini WAJIB diisi.")

    with st.form("form_baru", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nama = st.text_input("Nama Lengkap Pasien")
            nik = st.text_input("NIK / ID Card")
            tempat_lahir = st.text_input("Tempat Lahir")
            tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
            gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            agama = st.selectbox("Agama", ["Islam", "Kristen", "Katolik", "Hindu", "Budha", "Khonghucu"])
            gol_darah = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
            no_hp = st.text_input("Nomor HP Aktif")
            
        with col2:
            perusahaan = st.text_input("Perusahaan")
            departemen = st.text_input("Departemen")
            jabatan = st.text_input("Jabatan")
            blok_mes = st.text_input("Blok Mes")
            no_kamar = st.text_input("Nomor Kamar")
            area_kerja = st.text_input("Area Lokasi Kerja")
            riwayat_penyakit = st.text_area("Riwayat Penyakit")
            riwayat_alergi = st.text_area("Riwayat Alergi")

        submit = st.form_submit_button("Simpan & Ambil Antrean")

    if submit:
        # Validasi Semua Field Wajib
        fields = [nama, nik, tempat_lahir, no_hp, perusahaan, departemen, jabatan, blok_mes, no_kamar, area_kerja, riwayat_penyakit, riwayat_alergi]
        if all(fields):
            try:
                conn = sqlite3.connect('klinik_utama.db')
                c = conn.cursor()
                # Simpan Data Pasien
                c.execute("INSERT INTO data_pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (nik, nama, tempat_lahir, str(tgl_lahir), gender, agama, no_hp, perusahaan, 
                           departemen, jabatan, blok_mes, no_kamar, riwayat_penyakit, riwayat_alergi, 
                           area_kerja, gol_darah, date.today()))
                
                # Buat Antrean
                no_urut = get_next_antrean()
                c.execute("INSERT INTO antrean (nik, no_urut, tgl_antre) VALUES (?,?,?)", (nik, no_urut, date.today()))
                
                conn.commit()
                conn.close()
                
                st.success(f"Pendaftaran Berhasil! Nomor Antrean Anda: {no_urut:02d}")
                st.balloons()
            except sqlite3.IntegrityError:
                st.error("NIK ini sudah terdaftar sebagai Pasien Lama!")
        else:
            st.error("Gagal! Mohon lengkapi SELURUH data tanpa terkecuali.")

# --- ALUR PASIEN LAMA ---
elif mode == "Pasien Lama":
    st.subheader("Pendaftaran Pasien Lama")
    cari_nik = st.text_input("Masukkan NIK Anda untuk Verifikasi")
    
    if st.button("Cek Data & Ambil Antrean"):
        conn = sqlite3.connect('klinik_utama.db')
        c = conn.cursor()
        c.execute("SELECT nama, perusahaan FROM data_pasien WHERE nik = ?", (cari_nik,))
        user = c.fetchone()
        
        if user:
            no_urut = get_next_antrean()
            c.execute("INSERT INTO antrean (nik, no_urut, tgl_antre) VALUES (?,?,?)", (cari_nik, no_urut, date.today()))
            conn.commit()
            st.success(f"Selamat Datang Kembali, {user[0]} ({user[1]})")
            st.info(f"Nomor Antrean Anda Hari Ini: {no_urut:02d}")
        else:
            st.error("NIK tidak ditemukan. Silakan daftar sebagai Pasien Baru.")
        conn.close()

# --- ADMIN VIEW ---
else:
    st.subheader("Data Rekapitulasi Klinik")
    conn = sqlite3.connect('klinik_utama.db')
    df = pd.read_sql_query("SELECT a.no_urut, p.nama, p.nik, p.poli_tujuan, a.tgl_antre FROM antrean a JOIN data_pasien p ON a.nik = p.nik WHERE a.tgl_antre = date('now')", conn)
    st.write("Antrean Hari Ini:")
    st.table(df)
    conn.close()
