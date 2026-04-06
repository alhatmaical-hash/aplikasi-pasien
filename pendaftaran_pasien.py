import streamlit as st
import pandas as pd
from datetime import datetime
import io
import plotly.express as px
import psycopg2 

# --- 1. KONEKSI DATABASE (HANYA BOLEH ADA SATU) ---
def get_connection():
    # Gunakan URI dari gambar image_8e8867.png Anda
    # Ganti [YOUR-PASSWORD] dengan Alhatma121299
    uri = "postgresql://postgres:Alhatma121299@db.disaykowxavyegpkosvf.supabase.co:5432/postgres"
    conn = psycopg2.connect(uri)
    return conn

# --- 2. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps", page_icon="🏥", layout="wide")

# --- 3. DATABASE SETUP ---
def init_db():
    try:
        conn = get_connection()
        c = conn.cursor()
        # Kode tabel Anda di sini...
        c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database belum siap (Status: Unhealthy). Tunggu sebentar lalu refresh. Error: {e}")

init_db()

def get_master(kategori):
    conn = get_connection()
    df = pd.read_sql("SELECT id, nama FROM master_data WHERE kategori=%s ORDER BY nama ASC", conn, params=(kategori,))
    conn.close()
    return df

# --- 4. LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_page():
    st.markdown("<h2 style='text-align: center;'>🔐 Login Klinik Apps</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT username FROM users WHERE username=%s AND password=%s", (user, pw))
            res = cur.fetchone()
            conn.close()
            if res:
                st.session_state['logged_in'] = True
                st.session_state['username'] = res[0]
                st.rerun()
            else: st.error("Username atau Password salah")

if not st.session_state['logged_in']:
    if st.sidebar.button("📝 Buka Form Pendaftaran"): st.session_state['page'] = "Pendaftaran"
    if st.session_state.get('page') == "Pendaftaran": menu = "Pendaftaran / 登记"
    else: login_page(); st.stop()
else:
    st.sidebar.success(f"Login: {st.session_state.get('username')}")
    if st.sidebar.button("🚪 Logout"): st.session_state['logged_in'] = False; st.rerun()
    menu = st.sidebar.radio("Pilih Halaman", ["Pendaftaran / 登记", "Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"])

# --- 5. MENU PENDAFTARAN ---
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
    perusahaan_list = get_master("Perusahaan")['nama'].tolist()
    dept_list = get_master("Departemen")['nama'].tolist()
    jabatan_list = get_master("Jabatan")['nama'].tolist()

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            jenis_kunjungan = st.selectbox("Jenis Kunjungan", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"])
            nama_lengkap = st.text_input("Nama Lengkap")
            no_hp = st.text_input("No HP Aktif (WhatsApp)")
        with col2:
            nik = st.text_input("NIK / ID Card")
            pernah_berobat = st.radio("Pernah Berobat Disini?", ["Iya Sudah", "Belum Pernah"], horizontal=True)
            perusahaan = st.selectbox("Perusahaan", perusahaan_list)
            dept = st.selectbox("Departemen", dept_list)
            
        if st.form_submit_button("KIRIM PENDAFTARAN / 提交登记"):
            if nama_lengkap and nik:
                conn = get_connection(); cur = conn.cursor()
                try:
                    cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, no_hp, perusahaan, departemen, jenis_kunjungan, pernah_berobat) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''', 
                                 (datetime.now().date(), nama_lengkap, nik, no_hp, perusahaan, dept, jenis_kunjungan, pernah_berobat))
                    conn.commit(); st.success("Berhasil Terdaftar! / 登记成功！"); st.balloons()
                except Exception as e: st.error(f"Error: {e}")
                finally: conn.close()
            else: st.warning("Nama dan NIK wajib diisi!")

# --- 6. MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Data Rekam Medis")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pasien", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# --- 7. MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    f_bulan = st.selectbox("Filter Bulan", range(1, 13), index=datetime.now().month-1)
    f_tahun = st.selectbox("Filter Tahun", [2024, 2025, 2026], index=2)
    
    list_dept = get_master("Departemen")['nama'].tolist()
    cols = st.columns(4)
    for idx, d in enumerate(list_dept):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True):
            st.session_state['sel_dept'] = d

    if 'sel_dept' in st.session_state:
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target}")
        
        with st.expander("➕ Upload PDF Baru"):
            u_f = st.file_uploader("Pilih PDF", type=['pdf'])
            if st.button("Simpan"):
                if u_f:
                    conn = get_connection(); cur = conn.cursor()
                    cur.execute("""INSERT INTO skd_files (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) 
                                   VALUES (%s,%s,%s,%s,%s,%s,%s)""", 
                                (u_f.name, target, u_f.name, u_f.read(), datetime.now(), f_bulan, f_tahun))
                    conn.commit(); conn.close(); st.success("Tersimpan!"); st.rerun()

        # Pencarian & Tabel
        search = st.text_input("🔍 Cari Nama...")
        conn = get_connection()
        files = pd.read_sql("SELECT * FROM skd_files WHERE departemen=%s AND bulan_skd=%s AND tahun_skd=%s", conn, params=(target, f_bulan, f_tahun))
        conn.close()
        
        if search: files = files[files['nama_pasien'].str.contains(search, case=False)]
        
        for i, r in files.iterrows():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.text(r['nama_file'])
            c2.download_button("👁️ Lihat", data=r['file_data'].tobytes(), file_name=r['nama_file'])
            c3.download_button("📥 Unduh", data=r['file_data'].tobytes(), file_name=r['nama_file'])
            if c4.button("🗑️ Hapus", key=f"del_{r['id']}"):
                conn = get_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM skd_files WHERE id=%s", (r['id'],))
                conn.commit(); conn.close(); st.rerun()

# --- 8. MENU MASTER ---
elif menu == "Pengaturan Master / 设置":
    kat = st.selectbox("Kategori", ["Perusahaan", "Departemen", "Jabatan"])
    n = st.text_input(f"Tambah {kat}")
    if st.button("Simpan"):
        if n:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("INSERT INTO master_data (kategori, nama) VALUES (%s,%s)", (kat, n))
            conn.commit(); conn.close(); st.rerun()
    
    df_m = get_master(kat)
    for i, r in df_m.iterrows():
        ca, cb = st.columns([3, 1])
        ca.text(r['nama'])
        if cb.button("Hapus", key=f"m_{r['id']}"):
            conn = get_connection(); cur = conn.cursor()
            cur.execute("DELETE FROM master_data WHERE id=%s", (r['id'],))
            conn.commit(); conn.close(); st.rerun()
