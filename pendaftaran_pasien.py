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

# --- 2. TAMPILAN CSS (VERSI AMAN) ---
st.markdown("""
<style>
    .stButton>button {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 3em !important;
        width: 100% !important;
    }
    /* Sembunyikan Index Tabel */
    [data-testid="stElementToolbar"] {display: none;}
</style>
""", unsafe_with_html=True)

# --- 3. DATABASE SETUP ---
def get_connection():
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
    df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
    conn.close()
    return df['nama'].tolist()

# --- 5. NAVIGASI SIDEBAR ---
menu = st.sidebar.radio("Navigasi", ["Pendaftaran", "Rekam Medis", "Pengaturan Master"])

# --- 6. MENU PENDAFTARAN ---
if menu == "Pendaftaran":
    st.header("📝 Pendaftaran Pasien")
    
    # Ambil data dropdown dari database
    list_perusahaan = get_master("Perusahaan")
    list_dept = get_master("Departemen")
    list_jabatan = get_master("Jabatan")

    with st.form("form_pendaftaran", clear_on_submit=True):
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
            perusahaan = st.selectbox("PERUSAHAAN", list_perusahaan if list_perusahaan else ["Default"])
            dept = st.selectbox("DEPARTEMEN", list_dept if list_dept else ["Default"])
            jabatan = st.selectbox("JABATAN", list_jabatan if list_jabatan else ["Default"])
            alergi = st.selectbox("JENIS ALERGI", ["Tidak Ada", "Makanan", "Obat", "Cuaca"])
            darah = st.selectbox("GOLONGAN DARAH", ["A", "B", "AB", "O", "Tidak Tahu"])
            
        lokasi = st.text_area("LOKASI AREA KERJA")
        
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
                st.success("Pendaftaran anda berhasil silahkan menunggu untuk di layani, semoga lekas sembuh")
                st.balloons()
            else:
                st.error("Nama dan No HP wajib diisi!")

# --- 7. MENU REKAM MEDIS ---
elif menu == "Rekam Medis":
    st.header("📊 Rekam Medis")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        # Filter Tanggal & Bulan
        col_a, col_b = st.columns(2)
        with col_a:
            filter_bulan = st.multiselect("Filter Bulan", df['bulan_daftar'].unique())
        with col_b:
            filter_tgl = st.date_input("Filter Tanggal", value=[])

        if filter_bulan:
            df = df[df['bulan_daftar'].isin(filter_bulan)]
            
        st.dataframe(df, use_container_width=True)
        
        # Download Excel
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 Download Excel", data=towrite.getvalue(), file_name="Data_Pasien.xlsx")
    else:
        st.info("Belum ada data pendaftaran.")

# --- 8. MENU PENGATURAN MASTER ---
elif menu == "Pengaturan Master":
    st.header("⚙️ Pengaturan Data Master")
    kat = st.selectbox("Kategori", ["Perusahaan", "Departemen", "Jabatan"])
    
    col_in, col_del = st.columns(2)
    with col_in:
        nama_baru = st.text_input(f"Tambah {kat} Baru")
        if st.button("Simpan"):
            if nama_baru:
                conn = get_connection()
                conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kat, nama_baru))
                conn.commit()
                conn.close()
                st.rerun()
    
    with col_del:
        data_lama = get_master(kat)
        pilihan_hapus = st.selectbox("Hapus Data", ["-- Pilih --"] + data_lama)
        if st.button("Hapus"):
            if pilihan_hapus != "-- Pilih --":
                conn = get_connection()
                conn.execute("DELETE FROM master_data WHERE kategori=? AND nama=?", (kat, pilihan_hapus))
                conn.commit()
                conn.close()
                st.rerun()
