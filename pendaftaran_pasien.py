import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import plotly.express as px

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps", page_icon="🏥", layout="wide")

# --- 2. DATABASE SETUP ---
def get_connection():
    return sqlite3.connect('klinik_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabel User (Admin/Staff)
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    # Tabel Master
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    # Tabel Pasien Utama
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE, nama_lengkap TEXT, nik TEXT, pernah_berobat TEXT, 
                    perusahaan TEXT, departemen TEXT, jabatan TEXT)''')
    # Tabel Data Dinamis
    c.execute('''CREATE TABLE IF NOT EXISTS pasien_custom_data (
                    pasien_id INTEGER, field_name TEXT, field_value TEXT)''')
    # Tabel SKD
    c.execute('''CREATE TABLE IF NOT EXISTS skd_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_pasien TEXT, departemen TEXT, nama_file TEXT,
                    file_data BLOB, tgl_upload TIMESTAMP, bulan_skd INTEGER, tahun_skd INTEGER)''')
    
    # User default admin (Jika belum ada)
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', 'admin123', 'Admin'))
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNGSI DATA ---
def get_master(kategori):
    conn = get_connection()
    df = pd.read_sql(f"SELECT id, nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
    conn.close()
    return df

# --- 4. MANAJEMEN LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None

def login_page():
    st.markdown("<h2 style='text-align: center;'>🔐 Login Klinik Apps</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            conn = get_connection()
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
            conn.close()
            if res:
                st.session_state['logged_in'] = True
                st.session_state['username'] = res[0]
                st.session_state['role'] = res[2] # Ambil role dari database
                st.rerun()
            else:
                st.error("Username atau Password salah")

# --- 5. LOGIKA NAVIGASI ---
if not st.session_state['logged_in']:
    # Tombol akses cepat Pendaftaran tanpa login
    if st.sidebar.button("📝 Buka Form Pendaftaran"):
        st.session_state['page_guest'] = "Pendaftaran"
    
    if st.session_state.get('page_guest') == "Pendaftaran":
        menu = "Pendaftaran / 登记"
    else:
        login_page()
        st.stop()
else:
    # Sidebar Info
    st.sidebar.success(f"Login: {st.session_state['username']} ({st.session_state['role']})")
    
    # Filter Menu Berdasarkan Role
    if st.session_state['role'] == "Admin":
        menu_list = ["Pendaftaran / 登记", "Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]
    else:
        # Akun Biasa (Staff) hanya bisa lihat Pendaftaran & SKD
        menu_list = ["Pendaftaran / 登记", "SKD / 医生证明"]
    
    menu = st.sidebar.radio("Pilih Halaman", menu_list)
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.session_state['role'] = None
        st.rerun()

# --- 6. MENU PENDAFTARAN (BILINGUAL) ---
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
    
    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()
    custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

    pernah = st.radio(
        "PERNAH BEROBAT DISINI? / 您以前在这里看过病吗？", 
        ["Iya Sudah / 是的", "Belum Pernah / 从未"], 
        horizontal=True
    )

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            jenis_kunjungan = st.selectbox("Jenis Kunjungan / 就诊类型", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"])
            nama_lengkap = st.text_input("Nama Lengkap / 全名")
            nik = st.text_input("NIK / ID Card / 身份证号")
            no_hp = st.text_input("No HP / WhatsApp / 电话号码")
            agama = st.selectbox("Agama / 宗教", ["Islam", "Kristen", "Hindu", "Buddha", "Katolik", "Lainnya"])
        
        with col2:
            gender = st.radio("Jenis Kelamin / 性别", ["Laki-laki", "Perempuan"], horizontal=True)
            tgl_lahir = st.text_input("Tempat & Tgl Lahir / 出生地点日期 (Obi, 01-01-1990)")
            perusahaan = st.selectbox("Perusahaan / 公司", opts_perusahaan if opts_perusahaan else ["-"])
            dept = st.selectbox("Departemen / 部门", opts_dept if opts_dept else ["-"])
            jabatan = st.selectbox("Jabatan / 职位", opts_jabatan if opts_jabatan else ["-"])

        st.divider()
        alergi = st.multiselect("Jenis Alergi / 过敏类型", ["Makanan", "Obat", "Cuaca", "Tidak Ada"])
        gol_darah = st.selectbox("Golongan Darah / 血型", ["A", "B", "AB", "O", "-"])
        lokasi_kerja = st.text_area("Lokasi Kerja Spesifik / 具体工作地点")
            
        responses = {}
        if pernah == "Belum Pernah / 从未":
            st.subheader("📋 Informasi Tambahan / 附加信息")
            for field in custom_fields:
                responses[field] = st.text_input(f"{field.upper()}")
        else:
            responses = {field: "" for field in custom_fields}

        submit_btn = st.form_submit_button("KIRIM PENDAFTARAN / 提交登记")

        if submit_btn:
            if nama_lengkap and nik:
                conn = get_connection(); cur = conn.cursor()
                try:
                    cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan) 
                                 VALUES (?,?,?,?,?,?,?)''', 
                                 (datetime.now().date(), nama_lengkap, nik, pernah, perusahaan, dept, jabatan))
                    last_id = cur.lastrowid
                    for f_name, f_val in responses.items():
                        cur.execute("INSERT INTO pasien_custom_data (pasien_id, field_name, field_value) VALUES (?,?,?)", (last_id, f_name, f_val))
                    conn.commit()
                    st.success("Berhasil Terdaftar! / 登记成功！"); st.balloons()
                except Exception as e: st.error(f"Error: {e}")
                finally: conn.close()
            else: st.warning("Nama dan NIK wajib diisi!")

# --- 7. MENU REKAM MEDIS (Hanya Admin) ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Data Rekam Medis")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pasien", conn)
    conn.close()
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 8. MENU SKD (Admin & Staff) ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    # ... (Gunakan kode SKD Anda yang lama di sini) ...
    st.info("Fitur SKD dapat diakses oleh Admin dan Staff.")

# --- 9. PENGATURAN MASTER (Hanya Admin) ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Pengaturan")
    t1, t2, t3 = st.tabs(["Master List", "Fitur Pendaftaran", "Manajemen Akun"])
    
    with t3:
        st.subheader("👥 Manajemen Akun Tim")
        with st.form("tambah_user_form"):
            un = st.text_input("Username Baru")
            up = st.text_input("Password Baru", type="password")
            role_pilih = st.selectbox("Role Akun", ["Staff", "Admin"])
            if st.form_submit_button("Buat Akun"):
                if un and up:
                    conn = get_connection()
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?)", (un, up, role_pilih))
                        conn.commit(); st.success(f"Akun {un} ({role_pilih}) Berhasil Dibuat"); st.rerun()
                    except: st.error("Username sudah terdaftar!")
                    finally: conn.close()
        
        st.write("Daftar Akun:")
        conn = get_connection()
        u_df = pd.read_sql("SELECT username, role FROM users", conn); conn.close()
        for i, row in u_df.iterrows():
            if row['username'] != 'admin':
                cx, cy = st.columns([3, 1])
                cx.text(f"👤 {row['username']} - Role: {row['role']}")
                if cy.button("Hapus", key=f"u_del_{row['username']}"):
                    conn = get_connection(); conn.execute("DELETE FROM users WHERE username=?", (row['username'],)); conn.commit(); conn.close(); st.rerun()
