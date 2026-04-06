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

# --- 2. DATABASE SETUP ---
def get_connection():
    # Menggunakan check_same_thread=False untuk menghindari error pada akses bersamaan
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

# --- 3. FUNGSI DATA ---
def get_master(kategori):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
        return df['nama'].tolist()
    except:
        return []
    finally:
        conn.close()

# --- 4. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 Menu Utama")
menu = st.sidebar.radio("Pilih Halaman", ["Pendaftaran", "Rekam Medis", "Pengaturan Master"])

# --- 5. MENU PENDAFTARAN ---
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
            perusahaan = st.selectbox("PERUSAHAAN", opts_perusahaan if opts_perusahaan else ["Default"])
            dept = st.selectbox("DEPARTEMEN", opts_dept if opts_dept else ["Default"])
            jabatan = st.selectbox("JABATAN", opts_jabatan if opts_jabatan else ["Default"])
            alergi = st.selectbox("JENIS ALERGI", ["Tidak Ada", "Makanan", "Obat", "Cuaca"])
            darah = st.selectbox("GOLONGAN DARAH", ["A", "B", "AB", "O", "Tidak Tahu"])
            
        lokasi = st.text_area("LOKASI AREA KERJA")
        
        # Tombol submit standar (Tanpa CSS kustom agar tidak error)
        if st.form_submit_button("KIRIM PENDAFTARAN"):
            if nama and hp:
                conn = get_connection()
                c = conn.cursor()
                now = datetime.now()
                c.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, jenis_kunjungan, nama_lengkap, no_hp, blok_mes, agama, nik, gender, pernah_berobat, tempat_tgl_lahir, perusahaan, departemen, jabatan, alergi, gol_darah, lokasi_kerja) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (now.date(), now.strftime("%B %Y"), kunjungan, nama, hp, blok, agama, nik, gender, pernah, ttl, perusahaan, dept, jabatan, alergi, darah, lokasi))
                conn.commit()
                conn.close()
                st.success("Pendaftaran berhasil! Silakan menunggu. Semoga lekas sembuh.")
                st.balloons()
            else:
                st.error("Nama dan No HP tidak boleh kosong!")

# --- 6. MENU REKAM MEDIS ---
elif menu == "Rekam Medis":
    st.header("📊 Rekam Medis")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        # Filter Tanggal sederhana
        f_bln = st.multiselect("Filter Bulan", df['bulan_daftar'].unique())
        if f_bln:
            df = df[df['bulan_daftar'].isin(f_bln)]
            
        st.dataframe(df, use_container_width=True)
        
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 Download Excel", data=towrite.getvalue(), file_name="Data_Pasien.xlsx")
    else:
        st.info("Belum ada data.")

# --- 7. PENGATURAN MASTER ---
elif menu == "Pengaturan Master":
    st.header("⚙️ Master Data")
    kat = st.selectbox("Pilih Kategori", ["Perusahaan", "Departemen", "Jabatan"])
    
    c1, c2 = st.columns(2)
    with c1:
        n_baru = st.text_input(f"Tambah {kat} Baru")
        if st.button("Simpan Baru"):
            if n_baru:
                conn = get_connection()
                conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kat, n_baru))
                conn.commit()
                conn.close()
                st.rerun()
    with c2:
        d_lama = get_master(kat)
        p_hapus = st.selectbox("Hapus Data", ["-- Pilih --"] + d_lama)
        if st.button("Hapus Terpilih"):
            if p_hapus != "-- Pilih --":
                conn = get_connection()
                conn.execute("DELETE FROM master_data WHERE kategori=? AND nama=?", (kat, p_hapus))
                conn.commit()
                conn.close()
                st.rerun()
