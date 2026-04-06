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
    # Tabel User
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
                    file_data BLOB, tgl_upload TIMESTAMP)''')
    
    # User Utama (Admin) - Silakan ganti password ini nanti di menu Pengaturan
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

def login_page():
    st.markdown("<h2 style='text-align: center;'>🔐 Login Klinik Apps</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        user = st.text_input("Username", key="login_user")
        pw = st.text_input("Password", type="password", key="login_pw")
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

# Logika Akses: Pasien bisa buka tanpa login via tombol rahasia di sidebar
if not st.session_state['logged_in']:
    if st.sidebar.button("📝 Buka Form Pendaftaran Pasien"):
        st.session_state['page'] = "Pendaftaran"
    
    if st.session_state.get('page') == "Pendaftaran":
        menu = "Pendaftaran / 登记"
    else:
        login_page()
        st.stop()
else:
    st.sidebar.success(f"Login: {st.session_state['username']} ({st.session_state['user_role']})")
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 5. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 Menu Utama")
menu_list = ["Pendaftaran / 登记"]
if st.session_state['logged_in']:
    menu_list += ["Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]

menu = st.sidebar.radio("Pilih Halaman", menu_list)

# --- 6. MENU PENDAFTARAN --- (Tetap Sama)
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
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
            hp = st.text_input("NO HP") if pernah == "Belum Pernah / 从未" else ""
        with c2:
            perusahaan = st.selectbox("PERUSAHAAN", opts_perusahaan if opts_perusahaan else ["Default"])
            dept = st.selectbox("DEPARTEMEN", opts_dept if opts_dept else ["Default"])
            jabatan = st.selectbox("JABATAN", opts_jabatan if opts_jabatan else ["Default"])
            alergi = st.selectbox("ALERGI", ["Tidak Ada", "Makanan", "Obat"]) if pernah == "Belum Pernah / 从未" else ""

        if st.form_submit_button("KIRIM PENDAFTARAN"):
            if nama and nik:
                conn = get_connection()
                now = datetime.now()
                conn.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, jenis_kunjungan, nama_lengkap, no_hp, nik, pernah_berobat, perusahaan, departemen, jabatan, alergi) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)''', 
                          (now.date(), now.strftime("%B %Y"), kunjungan, nama, hp, nik, pernah, perusahaan, dept, jabatan, alergi))
                conn.commit(); conn.close()
                st.success("Pendaftaran Berhasil!")
                st.balloons()

# --- 7. MENU REKAM MEDIS --- (Grafik & Tabel)
elif menu == "Rekam Medis / 病历":
    st.header("📊 Data Rekam Medis & Analisis")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pasien", conn)
    conn.close()

    if not df.empty:
        st.subheader("📈 Grafik Kunjungan per Departemen")
        df['tgl_daftar'] = pd.to_datetime(df['tgl_daftar'])
        count_df = df.groupby(['tgl_daftar', 'departemen']).size().reset_index(name='Jumlah')
        fig = px.line(count_df, x='tgl_daftar', y='Jumlah', color='departemen', markers=True)
        st.plotly_chart(fig, use_container_width=True)

        tab1, tab2 = st.tabs(["Pasien Baru", "Pasien Lama"])
        for tab, status in zip([tab1, tab2], ["Belum Pernah / 从未", "Iya Sudah / 是nya"]):
            with tab:
                df_filt = df[df['pernah_berobat'] == status]
                st.dataframe(df_filt, use_container_width=True)
                towrite = io.BytesIO()
                df_filt.to_excel(towrite, index=False, engine='xlsxwriter')
                st.download_button(f"📥 Download Excel", towrite.getvalue(), f"Data_{status}.xlsx")

# --- 8. MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Manajemen SKD")
    with st.expander("➕ Tambah Folder Departemen"):
        f_baru = st.text_input("Nama Departemen")
        if st.button("Buat Folder"):
            conn = get_connection()
            conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Departemen", f_baru))
            conn.commit(); conn.close(); st.rerun()

    list_dept = get_master("Departemen")['nama'].tolist()
    cols = st.columns(4)
    for idx, d in enumerate(list_dept):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True):
            st.session_state['sel_dept'] = d

    if 'sel_dept' in st.session_state:
        st.divider()
        st.subheader(f"Folder: {st.session_state['sel_dept']}")
        with st.form("upload_skd"):
            u_nama = st.text_input("Nama Pasien")
            u_file = st.file_uploader("Upload PDF", type=['pdf'])
            if st.form_submit_button("Upload"):
                if u_nama and u_file:
                    conn = get_connection(); conn.execute("INSERT INTO skd_files (nama_pasien, departemen, nama_file, file_data, tgl_upload) VALUES (?,?,?,?,?)", (u_nama, st.session_state['sel_dept'], u_file.name, u_file.read(), datetime.now())); conn.commit(); conn.close()
                    st.success("File Berhasil Disimpan!")

# --- 9. PENGATURAN MASTER & MANAJEMEN AKUN ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Pengaturan Sistem")
    
    t_master, t_akun = st.tabs(["Master Data", "Manajemen Akun Tim"])
    
    with t_master:
        kat = st.selectbox("Pilih Kategori", ["Perusahaan", "Departemen", "Jabatan"])
        c_t, c_l = st.columns([1, 2])
        with c_t:
            n_baru = st.text_input(f"Tambah {kat}")
            if st.button("Simpan Master"):
                conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", (kat, n_baru)); conn.commit(); conn.close(); st.rerun()
        with c_l:
            df_m = get_master(kat)
            for i, r in df_m.iterrows():
                col_n, col_d = st.columns([3, 1])
                col_n.text(r['nama'])
                if col_d.button("Hapus", key=f"del_m_{r['id']}"):
                    conn = get_connection(); conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()

    with t_akun:
        st.subheader("👥 Buat Akun Tim")
        with st.form("tambah_user"):
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password Baru", type="password")
            new_role = st.selectbox("Role", ["Admin", "Staff Klinik"])
            if st.form_submit_button("Buat Akun"):
                if new_user and new_pass:
                    try:
                        conn = get_connection()
                        conn.execute("INSERT INTO users VALUES (?,?,?)", (new_user, new_pass, new_role))
                        conn.commit(); conn.close()
                        st.success(f"Akun {new_user} berhasil dibuat!")
                    except:
                        st.error("Username sudah ada!")
        
        st.divider()
        st.subheader("Daftar Akun")
        conn = get_connection()
        users_df = pd.read_sql("SELECT username, role FROM users", conn)
        conn.close()
        for i, row in users_df.iterrows():
            ca, cb = st.columns([3, 1])
            ca.text(f"👤 {row['username']} - {row['role']}")
            if row['username'] != 'admin': # Admin utama tidak bisa dihapus sendiri
                if cb.button("Hapus Akun", key=f"del_u_{row['username']}"):
                    conn = get_connection(); conn.execute("DELETE FROM users WHERE username=?", (row['username'],)); conn.commit(); conn.close(); st.rerun()
