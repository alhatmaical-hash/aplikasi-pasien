import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import time

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide"
)

# --- 2. DATABASE SETUP ---
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
    # Tabel baru untuk menyimpan file SKD
    c.execute('''CREATE TABLE IF NOT EXISTS skd_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_pasien TEXT,
                    departemen TEXT,
                    nama_file TEXT,
                    file_data BLOB,
                    tgl_upload TIMESTAMP)''')
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

def save_skd_file(nama, dept, file_name, data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO skd_files (nama_pasien, departemen, nama_file, file_data, tgl_upload) VALUES (?,?,?,?,?)",
              (nama, dept, file_name, data, datetime.now()))
    conn.commit()
    conn.close()

# --- 4. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 Menu Utama")

# Tautan untuk Barcode/Distribusi
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Link Akses")
# Link ini otomatis menyesuaikan dengan domain tempat Anda deploy (Streamlit Cloud/Local)
base_url = "https://aplikasi-pasien.streamlit.app/" 
st.sidebar.info(f"**Link Pendaftaran:**\n{base_url}?page=daftar")
st.sidebar.info(f"**Link SKD:**\n{base_url}?page=skd")
st.sidebar.markdown("---")

menu = st.sidebar.radio("Pilih Halaman", [
    "Pendaftaran / 登记", 
    "Rekam Medis / 病历", 
    "SKD / 医生证明", 
    "Pengaturan Master / 设置"
])

# --- 5. MENU PENDAFTARAN ---
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
    opts_perusahaan = get_master("Perusahaan")
    opts_dept = get_master("Departemen")
    opts_jabatan = get_master("Jabatan")

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat luka"])
            nama = st.text_input("NAMA LENGKAP")
            hp = st.text_input("NO HP AKTIF")
            nik = st.text_input("NIK IDCARD")
        with col2:
            perusahaan = st.selectbox("PERUSAHAAN", opts_perusahaan if opts_perusahaan else ["Default"])
            dept = st.selectbox("DEPARTEMEN", opts_dept if opts_dept else ["Default"])
            jabatan = st.selectbox("JABATAN", opts_jabatan if opts_jabatan else ["Default"])
            
        if st.form_submit_button("KIRIM PENDAFTARAN"):
            if nama and hp:
                conn = get_connection()
                c = conn.cursor()
                now = datetime.now()
                c.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, nama_lengkap, no_hp, nik, perusahaan, departemen, jabatan) 
                             VALUES (?,?,?,?,?,?,?,?)''', (now.date(), now.strftime("%B %Y"), nama, hp, nik, perusahaan, dept, jabatan))
                conn.commit()
                conn.close()
                st.success("Berhasil Terdaftar!")
                st.balloons()

# --- 7. MENU SKD (SISTEM FOLDER) ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD per Departemen")
    
    # Tombol Buat Folder Baru
    with st.expander("➕ Buat Folder Departemen Baru"):
        new_folder = st.text_input("Nama Departemen")
        if st.button("Buat Folder"):
            if new_folder:
                conn = get_connection()
                conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", ("Departemen", new_folder))
                conn.commit()
                conn.close()
                st.toast(f"Folder {new_folder} dibuat!")
                time.sleep(1)
                st.rerun()

    st.markdown("---")
    
    # Tampilan Folder
    list_dept = get_master("Departemen")
    if not list_dept:
        st.warning("Belum ada folder departemen. Silakan buat folder di atas.")
    else:
        # Menampilkan Folder dalam Grid
        cols = st.columns(4)
        for idx, dept_name in enumerate(list_dept):
            with cols[idx % 4]:
                if st.button(f"📂 {dept_name}", use_container_width=True, key=f"btn_{dept_name}"):
                    st.session_state['view_dept'] = dept_name

    # Area Isi Folder (Jika Folder Diklik)
    if 'view_dept' in st.session_state:
        target_dept = st.session_state['view_dept']
        st.markdown(f"### 📁 Isi Folder: {target_dept}")
        
        # Opsi Upload ke Folder Ini
        with st.expander(f"📤 Upload PDF SKD ke {target_dept}"):
            u_nama = st.text_input("Nama Pasien")
            u_file = st.file_uploader("Pilih File PDF", type=['pdf'])
            if st.button("Proses Upload"):
                if u_nama and u_file:
                    save_skd_file(u_nama, target_dept, u_file.name, u_file.read())
                    st.success("File tersimpan!")
                    time.sleep(1)
                    st.rerun()

        # Daftar File dalam Folder
        conn = get_connection()
        files_df = pd.read_sql(f"SELECT id, nama_pasien, nama_file, tgl_upload FROM skd_files WHERE departemen='{target_dept}'", conn)
        conn.close()

        if not files_df.empty:
            st.table(files_df[['nama_pasien', 'nama_file', 'tgl_upload']])
            # Tombol Download untuk file terakhir (sebagai contoh akses)
            for i, row in files_df.iterrows():
                col_file, col_dl = st.columns([3, 1])
                col_file.write(f"📄 {row['nama_file']} ({row['nama_pasien']})")
                
                # Fungsi ambil data biner untuk download
                conn = get_connection()
                res = conn.execute("SELECT file_data FROM skd_files WHERE id=?", (row['id'],)).fetchone()
                conn.close()
                
                col_dl.download_button("Lihat/Unduh", data=res[0], file_name=row['nama_file'], key=f"dl_{row['id']}")
        else:
            st.info("Folder kosong.")

# --- 8. PENGATURAN MASTER ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Master Data")
    kat = st.selectbox("Pilih Kategori", ["Perusahaan", "Departemen", "Jabatan"])
    # ... (Sama seperti kode sebelumnya untuk tambah/hapus)
    n_baru = st.text_input(f"Tambah {kat} Baru")
    if st.button("Simpan"):
        if n_baru:
            conn = get_connection()
            conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kat, n_baru))
            conn.commit()
            conn.close()
            st.rerun()
