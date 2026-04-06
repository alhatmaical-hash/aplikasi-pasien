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
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE, 
                    jenis_kunjungan TEXT,
                    nama_lengkap TEXT, 
                    nik TEXT, 
                    pernah_berobat TEXT, 
                    perusahaan TEXT, 
                    departemen TEXT, 
                    jabatan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pasien_custom_data (
                    pasien_id INTEGER, field_name TEXT, field_value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS skd_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_pasien TEXT, departemen TEXT, nama_file TEXT,
                    file_data BLOB, tgl_upload TIMESTAMP, bulan_skd INTEGER, tahun_skd INTEGER)''')
    
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
                st.rerun()
            else:
                st.error("Username atau Password salah")

# --- 5. NAVIGASI & SIDEBAR ---
if not st.session_state['logged_in']:
    if st.sidebar.button("📝 Buka Form Pendaftaran / 填写登记表"):
        st.session_state['page'] = "Pendaftaran"
    
    if st.session_state.get('page') == "Pendaftaran":
        menu = "Pendaftaran / 登记"
    else:
        login_page()
        st.stop()
else:
    st.sidebar.success(f"Login: {st.session_state.get('username')}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.session_state['page'] = "Login"
        st.rerun()

# List Menu Utama
menu_list = ["Pendaftaran / 登记"]
if st.session_state['logged_in']:
    menu_list += ["Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]

menu = st.sidebar.radio("Pilih Halaman / 选择页面", menu_list)

# Tombol Kembali (Hanya muncul jika tidak sedang di halaman Login)
if st.sidebar.button("⬅️ Kembali ke Login / 返回登录"):
    st.session_state['page'] = 'Login'
    st.session_state['logged_in'] = False
    st.rerun()

# --- 6. MENU PENDAFTARAN (BILINGUAL & LOGIKA KOLOM) ---
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")

    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()
    custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

    # Status Berobat
    pernah = st.radio(
        "PERNAH BEROBAT DISINI? / 您以前在这里看过病吗？", 
        ["Iya Sudah / 是的", "Belum Pernah / 从未"], 
        horizontal=True
    )

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            jenis_kunjungan = st.selectbox("JENIS KUNJUNGAN / 访问类型", ["Rawat Jalan / 门诊", "Emergency / 急诊", "MCU / 体检"])
            nama = st.text_input("NAMA LENGKAP / 全名")
            nik = st.text_input("NIK / NO KTP / 身份证号")
        with col2:
            perusahaan = st.selectbox("PERUSAHAAN / 公司", opts_perusahaan if opts_perusahaan else ["-"])
            dept = st.selectbox("DEPARTEMEN / 部门", opts_dept if opts_dept else ["-"])
            jabatan = st.selectbox("JABATAN / 职位", opts_jabatan if opts_jabatan else ["-"])
            
        # LOGIKA: Kolom tambahan muncul jika Pasien Baru (Belum Pernah)
        responses = {}
        if pernah == "Belum Pernah / 从未":
            st.divider()
            st.subheader("📋 Informasi Tambahan (Pasien Baru) / 附加信息")
            for field in custom_fields:
                responses[field] = st.text_input(f"{field.upper()}")
        else:
            responses = {field: "" for field in custom_fields}

        submit = st.form_submit_button("KIRIM PENDAFTARAN / 提交登记")
        
        if submit:
            if nama and nik:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute('''INSERT INTO pasien (tgl_daftar, jenis_kunjungan, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan) 
                             VALUES (?,?,?,?,?,?,?,?)''', (datetime.now().date(), jenis_kunjungan, nama, nik, pernah, perusahaan, dept, jabatan))
                last_id = cur.lastrowid
                
                for f_name, f_val in responses.items():
                    cur.execute("INSERT INTO pasien_custom_data (pasien_id, field_name, field_value) VALUES (?,?,?)", 
                                (last_id, f_name, f_val))
                
                conn.commit()
                conn.close()
                st.success("Berhasil Terdaftar! / 登记成功！")
                st.balloons()
            else:
                st.error("Nama dan NIK wajib diisi! / 姓名和身份证号必填！")

# --- 7. MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Data Rekam Medis / 病历数据")
    conn = get_connection()
    df_pasien = pd.read_sql("SELECT * FROM pasien", conn)
    df_custom = pd.read_sql("SELECT * FROM pasien_custom_data", conn)
    conn.close()

    if not df_pasien.empty:
        if not df_custom.empty:
            df_custom_pivot = df_custom.pivot(index='pasien_id', columns='field_name', values='field_value').reset_index()
            df_final = pd.merge(df_pasien, df_custom_pivot, left_on='id', right_on='pasien_id', how='left')
            if 'pasien_id' in df_final.columns:
                df_final = df_final.drop(columns=['pasien_id'])
        else:
            df_final = df_pasien

        st.dataframe(df_final, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ Hapus Data Pasien"):
            id_hapus = st.number_input("ID Pasien", min_value=1, step=1)
            if st.button("Hapus"):
                conn = get_connection()
                conn.execute("DELETE FROM pasien WHERE id=?", (id_hapus,))
                conn.execute("DELETE FROM pasien_custom_data WHERE pasien_id=?", (id_hapus,))
                conn.commit(); conn.close(); st.success("Terhapus!"); st.rerun()
    else:
        st.info("Belum ada data.")

# --- 8. MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD / 医生证明存档")
    list_dept = get_master("Departemen")['nama'].tolist()
    
    col_f1, col_f2 = st.columns(2)
    f_bulan = col_f1.selectbox("Bulan / 月份", range(1, 13), index=datetime.now().month-1)
    f_tahun = col_f2.selectbox("Tahun / 年份", [2024, 2025, 2026], index=2)

    cols = st.columns(4)
    for idx, d in enumerate(list_dept):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True):
            st.session_state['sel_dept'] = d

    if 'sel_dept' in st.session_state:
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target}")
        
        with st.expander("➕ Upload PDF"):
            with st.form("u_skd"):
                u_n = st.text_input("Nama Pasien")
                u_f = st.file_uploader("PDF", type=['pdf'])
                if st.form_submit_button("Simpan"):
                    if u_n and u_f:
                        conn = get_connection()
                        conn.execute("INSERT INTO skd_files (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) VALUES (?,?,?,?,?,?,?)", 
                                     (u_n, target, u_f.name, u_f.read(), datetime.now(), f_bulan, f_tahun))
                        conn.commit(); conn.close(); st.success("Berhasil!"); st.rerun()

# --- 9. PENGATURAN MASTER ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Pengaturan / 设置")
    t1, t2, t3 = st.tabs(["Master List", "Fitur Pendaftaran", "Akun"])
    
    with t1:
        kat = st.selectbox("Kategori", ["Perusahaan", "Departemen", "Jabatan"])
        n = st.text_input(f"Tambah ke {kat}")
        if st.button("Simpan"):
            if n:
                conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", (kat, n)); conn.commit(); conn.close(); st.rerun()

    with t2:
        st.subheader("🛠 Tambah Kolom Baru (WhatsApp, Alamat, dll)")
        f_baru = st.text_input("Nama Kolom Baru")
        if st.button("Tambah Kolom"):
            if f_baru:
                conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Fitur Pendaftaran", f_baru)); conn.commit(); conn.close(); st.rerun()
        
        df_f = get_master("Fitur Pendaftaran")
        st.write("Daftar Kolom Tambahan saat ini:")
        st.table(df_f['nama'])

    with t3:
        st.subheader("👥 Manajemen Akun")
        # Bagian ini tetap sama sesuai kode awal Anda
