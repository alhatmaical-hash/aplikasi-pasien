import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps", layout="wide")

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_pendaftaran.db')
    c = conn.cursor()
    # Tabel Master
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    # Tabel Pasien & Rekam Medis
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
    
    # Pre-fill data perusahaan awal jika kosong
    c.execute("SELECT count(*) FROM master_data WHERE kategori='Perusahaan'")
    if c.fetchone()[0] == 0:
        perusahaan_awal = ["PT. HALMAHERA JAYA FERONIKEL (HJF)", "PT. KARUNIA PERMAI SENTOSA (KPS)", "PT. OBI SINAR TIMUR (OST)"]
        for p in perusahaan_awal:
            c.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", ("Perusahaan", p))
    
    conn.commit()
    conn.close()

init_db()

# --- FUNGSI HELPER ---
def get_master(kategori):
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
    conn.close()
    return df['nama'].tolist()

def add_master(kategori, nama):
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

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏥 Navigasi Klinik")
menu = st.sidebar.radio("Pilih Menu:", 
    ["Pendaftaran Pasien", "Rekam Medis (Admin)", "Upload SKD", "Akses SKD Publik", "Pengaturan Master"])

# --- 1. PENDAFTARAN PASIEN ---
if menu == "Pendaftaran Pasien":
    st.header("📝 Form Pendaftaran Pasien")
    st.write("Silakan isi data kunjungan Anda.")
    
    with st.form("form_pasien", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat luka"])
            nama = st.text_input("NAMA LENGKAP")
            hp = st.text_input("NO HP YANG AKTIF")
            agama = st.selectbox("AGAMA", ["Islam", "Kristen", "Hindu", "Buddah", "Katolik", "Tidak Diketahui"])
            nik = st.text_input("NIK IDCARD")
            gender = st.selectbox("JENIS KELAMIN", ["Laki-laki", "Perempuan"])
            pernah = st.radio("SEBELUMNYA SUDAH PERNAH BEROBAT DISINI?", ["Iya Sudah", "Belum Pernah"], horizontal=True)

        with col2:
            blok = st.text_input("BLOK MES DAN NO KAMAR")
            ttl = st.text_input("TEMPAT DAN TANGGAL LAHIR")
            perusahaan = st.selectbox("PERUSAHAAN TEMPAT ANDA BEKERJA", get_master("Perusahaan"))
            dept = st.selectbox("DEPARTEMEN TEMPAT BEKERJA", get_master("Departemen"))
            jabatan = st.selectbox("JABATAN DAN POSISI ANDA", get_master("Jabatan"))
            alergi = st.selectbox("JENIS ALERGI", ["Tidak Ada", "Makanan", "Obat", "Cuaca"])
            darah = st.selectbox("GOLONGAN DARAH", ["A", "B", "AB", "O", "Tidak Tahu"])
            lokasi = st.text_area("LOKASI AREA BEKERJA")

        submit = st.form_submit_button("KIRIM PENDAFTARAN")
        
    if submit:
        now = datetime.now()
        tgl = now.strftime("%Y-%m-%d")
        bulan = now.strftime("%B %Y")
        
        conn = sqlite3.connect('klinik_pendaftaran.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, jenis_kunjungan, nama_lengkap, no_hp, blok_mes, agama, nik, gender, pernah_berobat, tempat_tgl_lahir, perusahaan, departemen, jabatan, alergi, gol_darah, lokasi_kerja) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                  (tgl, bulan, kunjungan, nama, hp, blok, agama, nik, gender, pernah, ttl, perusahaan, dept, jabatan, alergi, darah, lokasi))
        conn.commit()
        conn.close()
        
        st.success(f"Pendaftaran anda berhasil silahkan menunggu untuk di layani, semoga lekas sembuh")
        st.balloons()

# --- 2. REKAM MEDIS (ADMIN) ---
elif menu == "Rekam Medis (Admin)":
    st.header("📊 Rekam Medis Pasien")
    
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df = pd.read_sql("SELECT * FROM pasien", conn)
    conn.close()

    if not df.empty:
        # Filter
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_bulan = st.multiselect("Filter Bulan", df['bulan_daftar'].unique())
        with col_f2:
            f_tgl = st.date_input("Filter Tanggal", value=[])

        if f_bulan:
            df = df[df['bulan_daftar'].isin(f_bulan)]
        
        st.dataframe(df, use_container_width=True)
        
        # Download Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Rekam Medis')
        st.download_button(label="📥 Download Excel", data=output.getvalue(), file_name=f"Rekam_Medis_{datetime.now().date()}.xlsx")
    else:
        st.warning("Belum ada data pendaftaran.")

# --- 3. UPLOAD SKD ---
elif menu == "Upload SKD":
    st.header("📤 Upload Surat Keterangan Dokter (PDF)")
    
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df_p = pd.read_sql("SELECT id, nama_lengkap, departemen FROM pasien", conn)
    conn.close()
    
    if not df_p.empty:
