import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import pytz
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Klinik Apps", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

def get_connection():
    return sqlite3.connect("klinik_data.db", check_same_thread=False)

# 1. INISIALISASI DATABASE
def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tgl_daftar TIMESTAMP,
                        nama_mandarin TEXT,
                        nama_lengkap TEXT, 
                        nik TEXT, 
                        gender TEXT,
                        wechat_id TEXT,
                        gol_darah TEXT,
                        perusahaan TEXT, 
                        departemen TEXT, 
                        jabatan TEXT,
                        blok_mes TEXT,
                        agama TEXT,
                        tempat_lahir TEXT,
                        tgl_lahir TEXT,
                        status_antrian TEXT DEFAULT 'Normal')''')
        
        c.execute('CREATE TABLE IF NOT EXISTS master_pt (nama TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS master_dept (nama TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS master_jabatan (nama TEXT UNIQUE)')
        conn.commit()

init_db()

# --- FUNGSI HELPER ---
def get_master(table):
    with get_connection() as conn:
        return [r[0] for r in conn.execute(f"SELECT nama FROM {table} ORDER BY nama ASC").fetchall()]

# --- SIDEBAR LOGIN & NAVIGASI ---
st.sidebar.title("🔐 Akses Sistem")

# 1. Input Password di Sidebar
pwd_input = st.sidebar.text_input("Password Petugas", type="password", help="Masukkan password untuk membuka menu Admin")

# 2. Logika Penentuan Menu yang Muncul
if pwd_input == "admin123":
    st.sidebar.success("Mode: Petugas/Admin")
    menu_options = ["📝 Pendaftaran Pasien", "📋 Data Pasien (Admin)", "⚙️ Pengaturan Master"]
else:
    # Jika password salah atau kosong, hanya muncul menu pendaftaran
    menu_options = ["📝 Pendaftaran Pasien"]
    if pwd_input != "":
        st.sidebar.error("Password Salah")

pilihan = st.sidebar.radio("Pilih Halaman:", menu_options)

# --- HALAMAN 1: PENDAFTARAN (UNTUK PASIEN CINA) ---
if pilihan == "📝 Pendaftaran Pasien":
    st.markdown("<h2 style='text-align: center;'>CN 挂号表 / Formulir Pendaftaran</h2>", unsafe_allow_html=True)
    
    list_pt = get_master("master_pt")
    list_dept = get_master("master_dept")
    list_jabatan = get_master("master_jabatan")

    if not list_pt:
        st.warning("⚠️ Data Master Perusahaan belum diisi. Silakan hubungi admin.")
    
    with st.form("form_pendaftaran", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama_m = st.text_input("中文姓名 / Nama Mandarin", placeholder="例: 王小明")
            nama_l = st.text_input("英文姓名 / Nama Sesuai Paspor (Latin) *").upper()
            nik = st.text_input("证件号码 / NIK atau No. Paspor *")
            gender = st.radio("性别 / Jenis Kelamin", ["男 (Laki-laki)", "女 (Perempuan)"], horizontal=True)
            wechat = st.text_input("微信 ID / ID WeChat atau No. HP *")
        
        with col2:
            pt = st.selectbox("公司 / Perusahaan *", list_pt if list_pt else ["-"])
            dept = st.selectbox("部门 / Departemen *", list_dept if list_dept else ["-"])
            jab = st.selectbox("职位 / Jabatan *", list_jabatan if list_jabatan else ["-"])
            mes = st.text_input("宿舍号 / Blok & No. Kamar Mes *").upper()
            agama = st.selectbox("宗教 / Agama", ["Islam", "Kristen", "Katolik", "Hindu", "Buddha", "Konghucu", "Lainnya"])

        st.write("📅 **出生信息 / Informasi Kelahiran**")
        c3, c4 = st.columns(2)
        tmpt = c3.text_input("出生地点 / Tempat Lahir")
        tgl = c4.date_input("出生日期 / Tanggal Lahir", value=datetime(1995, 1, 1))

        if st.form_submit_button("提交 / KIRIM PENDAFTARAN", use_container_width=True):
            if not nama_l or not nik or not wechat or not list_pt:
                st.error("❌ Mohon lengkapi data wajib (*)")
            else:
                tz_wit = pytz.timezone('Asia/Jayapura')
                waktu = datetime.now(tz_wit).strftime("%Y-%m-%d %H:%M:%S")
                with get_connection() as conn:
                    conn.execute("INSERT INTO pasien (tgl_daftar, nama_mandarin, nama_lengkap, nik, gender, wechat_id, perusahaan, departemen, jabatan, blok_mes, agama, tempat_lahir, tgl_lahir) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                                 (waktu, nama_m, nama_l, nik, gender, wechat, pt, dept, jab, mes, agama, tmpt, str(tgl)))
                    conn.commit()
                st.success("✅ Berhasil! Data Anda telah tersimpan. / 提交成功！")

# --- HALAMAN 2: DATA PASIEN (HANYA JIKA LOGIN) ---
elif pilihan == "📋 Data Pasien (Admin)":
    st.header("📋 Database Pasien Terdaftar")
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Tombol Download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Download Excel", data=buffer.getvalue(), file_name="data_pasien.xlsx")
        
        # Fitur Hapus
        st.divider()
        id_hapus = st.selectbox("Pilih ID untuk dihapus", ["-- Pilih --"] + df['id'].tolist())
        if st.button("Hapus Permanen"):
            if id_hapus != "-- Pilih --":
                with get_connection() as conn:
                    conn.execute("DELETE FROM pasien WHERE id = ?", (id_hapus,))
                    conn.commit()
                st.rerun()
    else:
        st.info("Belum ada data pasien.")

# --- UPDATE PADA HALAMAN 3: PENGATURAN MASTER ---
elif pilihan == "⚙️ Pengaturan Master":
    st.header("⚙️ Kelola List Perusahaan, Dept & Jabatan")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.subheader("🏢 Perusahaan")
        pt_input = st.text_input("Tambah PT")
        if st.button("Simpan PT"):
            if pt_input:
                with get_connection() as conn:
                    conn.execute("INSERT OR IGNORE INTO master_pt VALUES (?)", (pt_input.upper(),))
                st.rerun()
        
        # --- TAMBAHAN TOMBOL HAPUS PT ---
        list_pt_hapus = get_master("master_pt")
        pt_hapus = st.selectbox("Pilih PT untuk dihapus", ["-- Pilih --"] + list_pt_hapus)
        if st.button("Hapus PT", type="secondary"):
            if pt_hapus != "-- Pilih --":
                with get_connection() as conn:
                    conn.execute("DELETE FROM master_pt WHERE nama = ?", (pt_hapus,))
                    conn.commit()
                st.rerun()

    with col_b:
        st.subheader("📁 Departemen")
        dept_input = st.text_input("Tambah Dept")
        if st.button("Simpan Dept"):
            if dept_input:
                with get_connection() as conn:
                    conn.execute("INSERT OR IGNORE INTO master_dept VALUES (?)", (dept_input.upper(),))
                st.rerun()
        
        # --- TAMBAHAN TOMBOL HAPUS DEPT ---
        list_dept_hapus = get_master("master_dept")
        dept_hapus = st.selectbox("Pilih Dept untuk dihapus", ["-- Pilih --"] + list_dept_hapus)
        if st.button("Hapus Dept", type="secondary"):
            if dept_hapus != "-- Pilih --":
                with get_connection() as conn:
                    conn.execute("DELETE FROM master_dept WHERE nama = ?", (dept_hapus,))
                    conn.commit()
                st.rerun()

    with col_c:
        st.subheader("💼 Jabatan")
        jab_input = st.text_input("Tambah Jabatan")
        if st.button("Simpan Jabatan"):
            if jab_input:
                with get_connection() as conn:
                    conn.execute("INSERT OR IGNORE INTO master_jabatan VALUES (?)", (jab_input.upper(),))
                st.rerun()
        
        # --- TAMBAHAN TOMBOL HAPUS JABATAN ---
        list_jab_hapus = get_master("master_jabatan")
        jab_hapus = st.selectbox("Pilih Jabatan untuk dihapus", ["-- Pilih --"] + list_jab_hapus)
        if st.button("Hapus Jabatan", type="secondary"):
            if jab_hapus != "-- Pilih --":
                with get_connection() as conn:
                    conn.execute("DELETE FROM master_jabatan WHERE nama = ?", (jab_hapus,))
                    conn.commit()
                st.rerun()
