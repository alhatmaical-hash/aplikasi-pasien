import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import time
import plotly.express as px

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
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
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
                    file_data BLOB, tgl_upload TIMESTAMP, 
                    bulan_skd INTEGER, tahun_skd INTEGER)''')
    
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', 'admin123', 'Admin'))
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNGSI DATA ---
def get_master(kategori):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT id, nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
        return df
    except:
        return pd.DataFrame(columns=['id', 'nama'])
    finally:
        conn.close()

# --- 4. MANAJEMEN LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

def login_page():
    st.markdown("<h2 style='text-align: center;'>🔐 Login Klinik Apps</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            conn = get_connection()
            res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
            conn.close()
            if res:
                st.session_state['logged_in'] = True
                st.session_state['username'] = res[0]
                st.session_state['user_role'] = res[2]
                st.rerun()
            else:
                st.error("Username atau Password salah")

if not st.session_state['logged_in']:
    if st.sidebar.button("📝 Buka Form Pendaftaran Pasien"):
        st.session_state['page'] = "Pendaftaran"
    if st.session_state.get('page') == "Pendaftaran":
        menu = "Pendaftaran / 登记"
    else:
        login_page(); st.stop()
else:
    st.sidebar.success(f"Login: {st.session_state.get('username')}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False; st.rerun()

# --- 5. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 Menu Utama")
menu_list = ["Pendaftaran / 登记"]
if st.session_state['logged_in']:
    menu_list += ["Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]
menu = st.sidebar.radio("Pilih Halaman", menu_list)

# --- 6. MENU PENDAFTARAN ---
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
    # Ambil kategori dinamis dari master_data
    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()

    pernah = st.radio("PERNAH BEROBAT DISINI?", ["Iya Sudah / 是nya", "Belum Pernah / 从未"], horizontal=True)

    with st.form("form_reg", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk"])
            nama = st.text_input("NAMA LENGKAP")
            nik = st.text_input("NIK IDCARD")
        with c2:
            perusahaan = st.selectbox("PERUSAHAAN", opts_perusahaan if opts_perusahaan else ["Default"])
            dept = st.selectbox("DEPARTEMEN", opts_dept if opts_dept else ["Default"])
            jabatan = st.selectbox("JABATAN", opts_jabatan if opts_jabatan else ["Default"])

        if st.form_submit_button("KIRIM PENDAFTARAN"):
            if nama and nik:
                conn = get_connection(); now = datetime.now()
                conn.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, jenis_kunjungan, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan) 
                             VALUES (?,?,?,?,?,?,?,?,?)''', (now.date(), now.strftime("%B %Y"), kunjungan, nama, nik, pernah, perusahaan, dept, jabatan))
                conn.commit(); conn.close()
                st.success("Berhasil Terdaftar!"); st.balloons()

# --- 7. MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Data Rekam Medis")
    conn = get_connection(); df = pd.read_sql("SELECT * FROM pasien", conn); conn.close()
    if not df.empty:
        st.subheader("📈 Tren Kunjungan Harian")
        df['tgl_daftar'] = pd.to_datetime(df['tgl_daftar'])
        count_df = df.groupby(['tgl_daftar', 'departemen']).size().reset_index(name='Jumlah')
        st.plotly_chart(px.line(count_df, x='tgl_daftar', y='Jumlah', color='departemen', markers=True), use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Data masih kosong.")

# --- 8. MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    list_dept = get_master("Departemen")['nama'].tolist()
    
    # Filter Waktu Global
    col_f1, col_f2 = st.columns(2)
    f_bulan = col_f1.selectbox("Filter Bulan", range(1, 13), index=datetime.now().month-1)
    f_tahun = col_f2.selectbox("Filter Tahun", [2024, 2025, 2026], index=2)

    cols = st.columns(4)
    for idx, d in enumerate(list_dept):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True):
            st.session_state['sel_dept'] = d

    if 'sel_dept' in st.session_state:
        st.divider()
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target} (Bulan {f_bulan}/{f_tahun})")
        
        # Upload
        with st.expander("➕ Upload SKD Baru"):
            with st.form("up_skd", clear_on_submit=True):
                u_nama = st.text_input("Nama Pasien")
                u_file = st.file_uploader("Pilih PDF", type=['pdf'])
                if st.form_submit_button("Simpan ke Folder"):
                    if u_nama and u_file:
                        conn = get_connection()
                        conn.execute("INSERT INTO skd_files (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) VALUES (?,?,?,?,?,?,?)",
                                     (u_nama, target, u_file.name, u_file.read(), datetime.now(), f_bulan, f_tahun))
                        conn.commit(); conn.close(); st.success("File Tersimpan!"); st.rerun()

        # List Files dengan Filter
        conn = get_connection()
        files_df = pd.read_sql(f"SELECT id, nama_pasien, nama_file, tgl_upload FROM skd_files WHERE departemen='{target}' AND bulan_skd={f_bulan} AND tahun_skd={f_tahun}", conn)
        conn.close()
        
        if not files_df.empty:
            st.write("Daftar File:")
            for i, row in files_df.iterrows():
                c_a, c_b = st.columns([4, 1])
                c_a.text(f"📄 {row['nama_pasien']} - {row['nama_file']}")
                if c_b.button("Hapus", key=f"del_file_{row['id']}"):
                    conn = get_connection(); conn.execute("DELETE FROM skd_files WHERE id=?", (row['id'],)); conn.commit(); conn.close(); st.rerun()
        else:
            st.info("Tidak ada file di periode ini.")

# --- 9. PENGATURAN MASTER ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Pengaturan Sistem")
    t_master, t_akun = st.tabs(["Master Data", "Manajemen Akun"])
    
    with t_master:
        # Input kategori baru jika tidak ada di list
        st.subheader("Kelola Komponen Form")
        list_kategori_default = ["Perusahaan", "Departemen", "Jabatan", "Lokasi Kerja", "Jenis Penyakit"]
        kat_pilihan = st.selectbox("Pilih Kategori Komponen", list_kategori_default)
        
        col_in, col_list = st.columns([1, 2])
        with col_in:
            n_baru = st.text_input(f"Tambah Data {kat_pilihan}")
            if st.button("➕ Simpan"):
                if n_baru:
                    conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", (kat_pilihan, n_baru)); conn.commit(); conn.close(); st.rerun()
        with col_list:
            st.write(f"Daftar {kat_pilihan}:")
            df_m = get_master(kat_pilihan)
            for i, r in df_m.iterrows():
                ca, cb = st.columns([4, 1])
                ca.text(r['nama'])
                if cb.button("🗑️", key=f"del_m_{r['id']}"):
                    conn = get_connection(); conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()

    with t_akun:
        st.subheader("👥 Akun Tim")
        with st.form("add_user"):
            nu, np = st.text_input("User Baru"), st.text_input("Pass Baru", type="password")
            if st.form_submit_button("Buat Akun"):
                try:
                    conn = get_connection(); conn.execute("INSERT INTO users VALUES (?,?,?)", (nu, np, 'Staff')); conn.commit(); conn.close(); st.success("Akun dibuat!")
                except: st.error("User sudah ada")
        
        conn = get_connection(); u_df = pd.read_sql("SELECT username FROM users", conn); conn.close()
        for i, row in u_df.iterrows():
            if row['username'] != 'admin':
                cx, cy = st.columns([4, 1])
                cx.text(f"👤 {row['username']}")
                if cy.button("Hapus", key=f"del_u_{row['username']}"):
                    conn = get_connection(); conn.execute("DELETE FROM users WHERE username=?", (row['username'],)); conn.commit(); conn.close(); st.rerun()
