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
    # Tabel Pasien (Struktur Dasar)
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE, nama_lengkap TEXT, nik TEXT, pernah_berobat TEXT, 
                    perusahaan TEXT, departemen TEXT, jabatan TEXT)''')
    # Tabel untuk menampung data dinamis (Custom Fields)
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
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

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
            else: st.error("Login Gagal")

if not st.session_state['logged_in']:
    if st.sidebar.button("📝 Buka Form Pendaftaran"): st.session_state['page'] = "Pendaftaran"
    if st.session_state.get('page') == "Pendaftaran": menu = "Pendaftaran / 登记"
    else: login_page(); st.stop()
else:
    st.sidebar.success(f"Login: {st.session_state.get('username')}")
    if st.sidebar.button("🚪 Logout"): st.session_state['logged_in'] = False; st.rerun()

# --- 5. NAVIGASI ---
menu_list = ["Pendaftaran / 登记"]
if st.session_state['logged_in']: menu_list += ["Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]
menu = st.sidebar.radio("Pilih Halaman", menu_list)

# --- 6. MENU PENDAFTARAN ---
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
    
    # Ambil list dinamis untuk dropdown
    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()
    # Ambil field tambahan yang dibuat user di Pengaturan
    custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

    pernah = st.radio("PERNAH BEROBAT DISINI?", ["Iya Sudah / 是nya", "Belum Pernah / 从未"], horizontal=True)

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("NAMA LENGKAP")
            nik = st.text_input("NIK / NO KTP")
            perusahaan = st.selectbox("PERUSAHAAN", opts_perusahaan if opts_perusahaan else ["Default"])
        with col2:
            dept = st.selectbox("DEPARTEMEN", opts_dept if opts_dept else ["Default"])
            jabatan = st.selectbox("JABATAN", opts_jabatan if opts_jabatan else ["Default"])
            
        # Tampilkan Field Tambahan Secara Dinamis (Nama Orang Tua, HP, dll)
        st.subheader("Informasi Tambahan")
        responses = {}
        for field in custom_fields:
            responses[field] = st.text_input(field.upper())

        if st.form_submit_button("KIRIM PENDAFTARAN"):
            if nama and nik:
                conn = get_connection(); cur = conn.cursor()
                cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan) 
                             VALUES (?,?,?,?,?,?,?)''', (datetime.now().date(), nama, nik, pernah, perusahaan, dept, jabatan))
                last_id = cur.lastrowid
                # Simpan data dinamis
                for f_name, f_val in responses.items():
                    cur.execute("INSERT INTO pasien_custom_data VALUES (?,?,?)", (last_id, f_name, f_val))
                conn.commit(); conn.close()
                st.success("Berhasil Terdaftar!"); st.balloons()

# --- 8. MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    
    # Tombol Tambah Folder (Departemen)
    with st.expander("➕ Tambah Folder Departemen Baru"):
        new_f = st.text_input("Nama Departemen Baru")
        if st.button("Buat Folder"):
            if new_f:
                conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Departemen", new_f)); conn.commit(); conn.close(); st.rerun()

    col_f1, col_f2 = st.columns(2)
    f_bulan = col_f1.selectbox("Filter Bulan", range(1, 13), index=datetime.now().month-1)
    f_tahun = col_f2.selectbox("Filter Tahun", [2024, 2025, 2026], index=2)

    list_dept = get_master("Departemen")['nama'].tolist()
    cols = st.columns(4)
    for idx, d in enumerate(list_dept):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True): st.session_state['sel_dept'] = d

    if 'sel_dept' in st.session_state:
        st.divider()
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target} ({f_bulan}/{f_tahun})")
        
        with st.expander("➕ Upload PDF Baru"):
            with st.form("up"):
                u_n = st.text_input("Nama Pasien"); u_f = st.file_uploader("Pilih PDF", type=['pdf'])
                if st.form_submit_button("Upload"):
                    if u_n and u_f:
                        conn = get_connection(); conn.execute("INSERT INTO skd_files (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) VALUES (?,?,?,?,?,?,?)", (u_n, target, u_f.name, u_f.read(), datetime.now(), f_bulan, f_tahun)); conn.commit(); conn.close(); st.rerun()

        conn = get_connection()
        files = pd.read_sql(f"SELECT id, nama_pasien, nama_file FROM skd_files WHERE departemen='{target}' AND bulan_skd={f_bulan} AND tahun_skd={f_tahun}", conn)
        conn.close()
        for i, r in files.iterrows():
            c_a, c_b = st.columns([4, 1])
            c_a.text(f"📄 {r['nama_pasien']} - {r['nama_file']}")
            if c_b.button("Hapus", key=f"f_{r['id']}"):
                conn = get_connection(); conn.execute("DELETE FROM skd_files WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()

# --- 9. PENGATURAN MASTER ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Pengaturan")
    t1, t2, t3 = st.tabs(["Master List (Perusahaan/Dept)", "Fitur Pendaftaran", "Manajemen Akun"])
    
    with t1:
        kat = st.selectbox("Kategori", ["Perusahaan", "Departemen", "Jabatan"])
        c_i, c_l = st.columns([1, 2])
        with c_i:
            n = st.text_input(f"Tambah {kat}")
            if st.button("Tambah", key="btn_t1"):
                conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", (kat, n)); conn.commit(); conn.close(); st.rerun()
        with c_l:
            df = get_master(kat)
            for i, r in df.iterrows():
                ca, cb = st.columns([3, 1])
                ca.text(r['nama'])
                if cb.button("Hapus", key=f"m_{r['id']}"):
                    conn = get_connection(); conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()

    with t2:
        st.subheader("🛠 Tambah Kolom Form Pendaftaran")
        st.info("Contoh: Tambah 'Nama Orang Tua' atau 'No HP' agar muncul di form pendaftaran.")
        c_i2, c_l2 = st.columns([1, 2])
        with c_i2:
            f_baru = st.text_input("Nama Kolom Baru (Contoh: No HP)")
            if st.button("Tambah Kolom", key="btn_t2"):
                conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Fitur Pendaftaran", f_baru)); conn.commit(); conn.close(); st.rerun()
        with c_l2:
            df_f = get_master("Fitur Pendaftaran")
            for i, r in df_f.iterrows():
                ca, cb = st.columns([3, 1])
                ca.text(r['nama'])
                if cb.button("Hapus", key=f"fit_{r['id']}"):
                    conn = get_connection(); conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()

    with t3:
        st.subheader("👥 Akun Tim")
        with st.form("u"):
            un, up = st.text_input("User"), st.text_input("Pass", type="password")
            if st.form_submit_button("Buat Ak
