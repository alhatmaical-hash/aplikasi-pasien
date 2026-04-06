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
    c.execute('''CREATE TABLE IF NOT EXISTS skd_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_pasien TEXT, departemen TEXT, nama_file TEXT,
                    file_data BLOB, tgl_upload TIMESTAMP)''')
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

st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Link Akses")
base_url = "https://aplikasi-pasien.streamlit.app/" 
st.sidebar.info(f"**Link Pendaftaran:**\n{base_url}")
st.sidebar.info(f"**Link SKD:**\n{base_url}")
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

    # LOGIKA PASIEN LAMA/BARU
    pernah = st.radio("PERNAH BEROBAT DISINI? / 以前来过这里看病吗？", ["Iya Sudah / 是nya", "Belum Pernah / 从未"], horizontal=True)

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat luka"])
            nama = st.text_input("NAMA LENGKAP")
            nik = st.text_input("NIK IDCARD")
            
            # Field tambahan hanya jika Pasien Baru
            if pernah == "Belum Pernah / 从未":
                hp = st.text_input("NO HP AKTIF")
                agama = st.selectbox("AGAMA", ["Islam", "Kristen", "Hindu", "Buddha", "Katolik", "Lainnya"])
                gender = st.selectbox("JENIS KELAMIN", ["Laki-laki", "Perempuan"])
            else:
                hp, agama, gender = "", "", ""

        with col2:
            perusahaan = st.selectbox("PERUSAHAAN", opts_perusahaan if opts_perusahaan else ["Default"])
            dept = st.selectbox("DEPARTEMEN", opts_dept if opts_dept else ["Default"])
            jabatan = st.selectbox("JABATAN", opts_jabatan if opts_jabatan else ["Default"])
            
            # Field tambahan hanya jika Pasien Baru
            if pernah == "Belum Pernah / 从未":
                blok = st.text_input("BLOK MES & NO KAMAR")
                ttl = st.text_input("TEMPAT & TANGGAL LAHIR")
                alergi = st.selectbox("JENIS ALERGI", ["Tidak Ada", "Makanan", "Obat", "Cuaca"])
                darah = st.selectbox("GOLONGAN DARAH", ["A", "B", "AB", "O", "Tidak Tahu"])
            else:
                blok, ttl, alergi, darah = "", "", "", ""

        lokasi = st.text_area("LOKASI AREA KERJA") if pernah == "Belum Pernah / 从未" else ""

        if st.form_submit_button("KIRIM PENDAFTARAN"):
            if nama and nik:
                conn = get_connection()
                c = conn.cursor()
                now = datetime.now()
                c.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, jenis_kunjungan, nama_lengkap, no_hp, blok_mes, agama, nik, gender, pernah_berobat, tempat_tgl_lahir, perusahaan, departemen, jabatan, alergi, gol_darah, lokasi_kerja) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (now.date(), now.strftime("%B %Y"), kunjungan, nama, hp, blok, agama, nik, gender, pernah, ttl, perusahaan, dept, jabatan, alergi, darah, lokasi))
                conn.commit()
                conn.close()
                st.success("Pendaftaran Berhasil! Data sudah masuk ke Rekam Medis.")
                st.balloons()
            else:
                st.error("Nama dan NIK wajib diisi!")

# --- 6. MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Rekam Medis / 病历 Data")
    
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        tab_baru, tab_lama = st.tabs(["Pasien Baru / 新病人", "Pasien Lama / 老病人"])
        
        with tab_baru:
            df_baru = df[df['pernah_berobat'] == "Belum Pernah / 从未"]
            st.dataframe(df_baru, use_container_width=True)
            if not df_baru.empty:
                towrite = io.BytesIO()
                df_baru.to_excel(towrite, index=False, engine='xlsxwriter')
                st.download_button("📥 Download Excel (Pasien Baru)", towrite.getvalue(), "Rekam_Medis_Baru.xlsx")

        with tab_lama:
            df_lama = df[df['pernah_berobat'] == "Iya Sudah / 是nya"]
            # Hanya tampilkan kolom yang relevan untuk pasien lama agar rapi
            cols_lama = ['tgl_daftar', 'nama_lengkap', 'nik', 'perusahaan', 'departemen', 'jabatan', 'jenis_kunjungan']
            st.dataframe(df_lama[cols_lama] if not df_lama.empty else df_lama, use_container_width=True)
            if not df_lama.empty:
                towrite = io.BytesIO()
                df_lama.to_excel(towrite, index=False, engine='xlsxwriter')
                st.download_button("📥 Download Excel (Pasien Lama)", towrite.getvalue(), "Rekam_Medis_Lama.xlsx")
    else:
        st.info("Belum ada data pendaftaran yang masuk.")

# --- 7. MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD per Departemen")
    # ... (Logika folder SKD tetap sama seperti sebelumnya karena sudah OK)
    list_dept = get_master("Departemen")
    cols = st.columns(4)
    for idx, dept_name in enumerate(list_dept):
        with cols[idx % 4]:
            if st.button(f"📂 {dept_name}", use_container_width=True):
                st.session_state['view_dept'] = dept_name

    if 'view_dept' in st.session_state:
        target_dept = st.session_state['view_dept']
        st.subheader(f"Isi Folder: {target_dept}")
        u_file = st.file_uploader("Upload PDF Baru", type=['pdf'])
        u_nama = st.text_input("Nama Pasien untuk PDF")
        if st.button("Simpan ke Folder"):
            if u_file and u_nama:
                conn = get_connection()
                conn.execute("INSERT INTO skd_files (nama_pasien, departemen, nama_file, file_data, tgl_upload) VALUES (?,?,?,?,?)",
                             (u_nama, target_dept, u_file.name, u_file.read(), datetime.now()))
                conn.commit()
                conn.close()
                st.success("File Berhasil diupload!")
                st.rerun()

# --- 8. MASTER DATA ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Pengaturan Master")
    kat = st.selectbox("Kategori", ["Perusahaan", "Departemen", "Jabatan"])
    n_baru = st.text_input(f"Tambah {kat}")
    if st.button("Simpan"):
        conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", (kat, n_baru)); conn.commit(); conn.close()
        st.rerun()
