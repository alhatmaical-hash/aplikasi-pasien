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
    
    # 1. Tabel User
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # 2. Tabel Master (Perusahaan, Dept, Jabatan, Fitur Pendaftaran)
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    
    # 3. Tabel Pasien Utama (Struktur Dasar)
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE, 
                    nama_lengkap TEXT, 
                    nik TEXT, 
                    pernah_berobat TEXT, 
                    perusahaan TEXT, 
                    departemen TEXT, 
                    jabatan TEXT)''')

    # --- TAMBAHAN: Update Schema untuk Kolom Baru ---
    # Ini memastikan kolom tambahan ada meskipun tabel sudah pernah dibuat sebelumnya
    kolom_tambahan = [
        ("no_hp", "TEXT"),
        ("agama", "TEXT"),
        ("gender", "TEXT"),
        ("blok_mes", "TEXT"),
        ("tgl_lahir", "TEXT"),
        ("alergi", "TEXT"),
        ("gol_darah", "TEXT"),
        ("lokasi_kerja", "TEXT"),
        ("lokasi_mcu", "TEXT")
    ]
    
    for kolom, tipe in kolom_tambahan:
        try:
            c.execute(f"ALTER TABLE pasien ADD COLUMN {kolom} {tipe}")
        except:
            pass # Lewati jika kolom sudah ada

    # 4. Tabel Data Dinamis
    c.execute('''CREATE TABLE IF NOT EXISTS pasien_custom_data (
                    pasien_id INTEGER, field_name TEXT, field_value TEXT)''')
    
    # 5. Tabel SKD
    c.execute('''CREATE TABLE IF NOT EXISTS skd_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_pasien TEXT, departemen TEXT, nama_file TEXT,
                    file_data BLOB, tgl_upload TIMESTAMP, bulan_skd INTEGER, tahun_skd INTEGER)''')
    
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', 'admin123', 'Admin'))
    
    conn.commit()
    conn.close()

# Jalankan inisialisasi
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

if not st.session_state['logged_in']:
    if st.sidebar.button("📝 Buka Form Pendaftaran"):
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
        st.rerun()

# --- 5. NAVIGASI SIDEBAR ---
menu_list = ["Pendaftaran / 登记"]
if st.session_state['logged_in']:
    menu_list += ["Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]
menu = st.sidebar.radio("Pilih Halaman", menu_list)

# --- 6. MENU PENDAFTARAN (BILINGUAL / 双语) ---
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
        if pernah == "Iya Sudah / 是的":
            # --- HANYA INI YANG MUNCUL JIKA PILIH IYA SUDAH ---
            col1, col2 = st.columns(2)
            with col1:
                jenis_kunjungan = st.selectbox("Jenis Kunjungan / 就诊类型", ["Berobat / 治病", "Kontrol MCU / 体检复查", "Masuk UGD / 急诊", "Kontrol Post Rujuk / 转院后复查", "Kontrol Rawat Luka / 伤口护理复查"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名")
                no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码")
                nik = st.text_input("NIK / ID Card / 身份证号")
            
            with col2:
                perusahaan = st.selectbox("Perusahaan / 公司", opts_perusahaan)
                dept = st.selectbox("Departemen / 部门", opts_dept)
                jabatan = st.selectbox("Jabatan / 职位", opts_jabatan)
            
            # Variabel di bawah ini harus di-set kosong agar sistem tidak error saat simpan data
            agama = "Lama"
            gender = "Lama"
            blok_mes = ""
            tgl_lahir = ""
            alergi = []
            gol_darah = "-"
            lokasi_kerja = ""
            responses = {field: "" for field in custom_fields}

        else:
            # --- TAMPILAN LENGKAP JIKA PILIH BELUM PERNAH ---
            col1, col2 = st.columns(2)
            with col1:
                jenis_kunjungan = st.selectbox("Jenis Kunjungan / 就诊类型", ["Berobat / 治病", "Kontrol MCU / 体检复查", "Masuk UGD / 急诊", "Kontrol Post Rujuk / 转院后复查", "Kontrol Rawat Luka / 伤口护理复查"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名")
                no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码")
                agama = st.selectbox("Agama / 宗教", ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"])
                nik = st.text_input("NIK / ID Card / 身份证号")
                gender = st.radio("Jenis Kelamin / 性别", ["Laki-laki / 男", "Perempuan / 女"], horizontal=True)

            with col2:
                blok_mes = st.text_input("Blok Mes dan No Kamar / 宿舍楼和房间号")
                tgl_lahir = st.text_input("Tempat & Tanggal Lahir / 出生地点和日期 (Contoh: Obi, 01-01-1990)")
                perusahaan = st.selectbox("Perusahaan / 公司", opts_perusahaan)
                dept = st.selectbox("Departemen / 部门", opts_dept)
                jabatan = st.selectbox("Jabatan / 职位", opts_jabatan)

            alergi = st.multiselect("Jenis Alergi / 过敏类型", ["Makanan / 食物", "Obat / 药物", "Cuaca / 天气", "Tidak Ada / 无"])
            gol_darah = st.selectbox("Golongan Darah / 血型", ["A", "B", "AB", "O", "-"])
            lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik / 具体工作地点")
            lokasi_mcu = st.selectbox("Lokasi Mcu Pertama Kali / 血型", ["Klinik HJF", "Klinik HPAL", "Klinik Luar Obi"])
            
            st.divider()
            st.subheader("📋 Informasi Tambahan / 附加信息")
            responses = {field: st.text_input(f"{field.upper()}") for field in custom_fields}
        submit_btn = st.form_submit_button("KIRIM PENDAFTARAN / 提交登记")

        if submit_btn:
            if nama_lengkap and nik:
                conn = get_connection()
                cur = conn.cursor()
                try:
                    cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan) 
                                 VALUES (?,?,?,?,?,?,?)''', 
                                 (datetime.now().strftime("%Y-%m-%d"), nama_lengkap, nik, pernah, perusahaan, dept, jabatan))
                    
                    last_id = cur.lastrowid 
                    for f_name, f_val in responses.items():
                        cur.execute("INSERT INTO pasien_custom_data (pasien_id, field_name, field_value) VALUES (?,?,?)", 
                                    (last_id, f_name, f_val))
                    
                    conn.commit()
                    st.success("Berhasil Terdaftar! / 登记成功！")
                    st.balloons()
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
                finally:
                    conn.close()
            else:
                st.warning("Nama dan NIK wajib diisi! / 姓名和身份证号必填！")
# --- 7. MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Data Rekam Medis")
    
    conn = get_connection()
    # Mengambil semua kolom agar data pasien baru terlihat lengkap
    query = """
    SELECT 
        id, 
        tgl_daftar AS 'Tgl Daftar', 
        nama_lengkap AS 'Nama Lengkap', 
        nik AS 'NIK/ID', 
        no_hp AS 'WhatsApp',
        perusahaan AS 'Perusahaan', 
        departemen AS 'Departemen', 
        jabatan AS 'Jabatan',
        pernah_berobat AS 'Status',
        agama AS 'Agama',
        gender AS 'Gender',
        tgl_lahir AS 'TTL',
        alergi AS 'Alergi',
        gol_darah AS 'Gol Darah',
        blok_mes AS 'Blok/Kamar',
        lokasi_kerja AS 'Area Kerja',
        lokasi_mcu AS 'Lokasi Mcu Pertama Kali'
    FROM pasien
    """
    df = pd.read_sql(query, conn)
    conn.close()

    if not df.empty:
        # Menampilkan dataframe dengan pengaturan agar enak dipandang
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True, # Menghilangkan angka index di kiri agar rapi
            column_config={
                "WhatsApp": st.column_config.TextColumn("WhatsApp"),
                "Tgl Daftar": st.column_config.DateColumn("Tanggal"),
            }
        )
        
        # Tambahan fitur unduh ke Excel (opsional)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv,
            file_name='data_rekam_medis.csv',
            mime='text/csv',
        )
    else:
        st.info("Belum ada data pasien / 还没有病人数据。")
# --- 8. MENU SKD / 医生证明 ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    
    # 1. Tambah Departemen Baru
    with st.expander("➕ Tambah Folder Departemen Baru"):
        new_f = st.text_input("Nama Departemen Baru")
        if st.button("Buat Folder"):
            if new_f:
                with get_connection() as conn:
                    conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Departemen", new_f))
                    conn.commit()
                st.rerun()

    # 2. Filter Waktu
    col_f1, col_f2 = st.columns(2)
    f_bulan = col_f1.selectbox("Filter Bulan", range(1, 13), index=datetime.now().month-1)
    f_tahun = col_f2.selectbox("Filter Tahun", [2024, 2025, 2026], index=2)

    # 3. Ambil Daftar Departemen (Folder)
    try:
        with get_connection() as conn:
            df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
            daftar_folder = df_dept['nama'].tolist()
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]

    st.write("### Pilih Departemen:")
    cols = st.columns(4)
    for idx, d in enumerate(daftar_folder):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True, key=f"fldr_{d}_{idx}"):
            st.session_state['sel_dept'] = d
            st.rerun()

    # 4. Tampilkan Isi Folder Jika Sudah Dipilih
    if 'sel_dept' in st.session_state:
        st.divider()
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target} ({f_bulan}/{f_tahun})")
        
        # Form Upload
        with st.expander("➕ Upload PDF Baru"):
            with st.form("upload_skd_form", clear_on_submit=True):
                u_f = st.file_uploader("Pilih PDF", type=['pdf'])
                if st.form_submit_button("Simpan Ke Folder"):
                    if u_f:
                        try:
                            with get_connection() as conn:
                                conn.execute("""
                                    INSERT INTO skd_files 
                                    (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) 
                                    VALUES (?,?,?,?,?,?,?)""", 
                                    (u_f.name, target, u_f.name, u_f.read(), datetime.now(), f_bulan, f_tahun))
                                conn.commit()
                            st.success("Berhasil disimpan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        # --- BAGIAN PENCARIAN & DAFTAR (HANYA SATU KALI) ---
        st.write("### Daftar File:")
        search_q = st.text_input("🔍 Cari Nama Pasien...", placeholder="Ketik nama untuk mencari...", key="search_skd_final")

        with get_connection() as conn:
            query = f"SELECT * FROM skd_files WHERE departemen='{target}' AND bulan_skd={f_bulan} AND tahun_skd={f_tahun}"
            files = pd.read_sql(query, conn)
            
            if search_q:
                files = files[files['nama_pasien'].str.contains(search_q, case=False, na=False)]

        if not files.empty:
            for i, r in files.iterrows():
                c_n, c_v, c_d, c_x = st.columns([4, 1.2, 1.2, 0.8])
                c_n.text(f"📄 {r['nama_file']}") 
                
                # Tombol Lihat
                if c_v.button("👁️ Lihat", key=f"v_btn_{r['id']}_{i}"):
                    st.download_button("Klik untuk Buka", data=r['file_data'], file_name=r['nama_file'], mime='application/pdf', key=f"dl_v_{i}")
                
                # Tombol Unduh
                c_d.download_button("📥 Unduh", data=r['file_data'], file_name=r['nama_file'], mime='application/pdf', key=f"dl_d_{i}")

                # Tombol Hapus
                if c_x.button("🗑️", key=f"del_btn_{i}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM skd_files WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()
        else:
            st.info("Tidak ada file ditemukan.")
# --- 9. PENGATURAN MASTER ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Pengaturan")
    t1, t2, t3 = st.tabs(["Master List", "Fitur Pendaftaran", "Manajemen Akun"])
    
    with t1:
        kat = st.selectbox("Kategori Master", ["Perusahaan", "Departemen", "Jabatan"])
        c_i, c_l = st.columns([1, 2])
        with c_i:
            n = st.text_input(f"Tambah Ke {kat}")
            if st.button("Tambah Data", key="btn_add_master"):
                if n:
                    conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", (kat, n)); conn.commit(); conn.close(); st.rerun()
        with c_l:
            df_master = get_master(kat)
            for i, r in df_master.iterrows():
                ca, cb = st.columns([3, 1])
                ca.text(r['nama'])
                if cb.button("Hapus", key=f"m_del_{r['id']}"):
                    conn = get_connection(); conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()

    with t2:
        st.subheader("🛠 Custom Kolom Form Pendaftaran")
        st.info("Ketik nama kolom baru (misal: 'No WhatsApp' atau 'Nama Ayah') untuk ditambahkan ke form.")
        c_i2, c_l2 = st.columns([1, 2])
        with c_i2:
            f_baru = st.text_input("Nama Fitur Baru")
            if st.button("Simpan Fitur", key="btn_add_fitur"):
                if f_baru:
                    conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Fitur Pendaftaran", f_baru)); conn.commit(); conn.close(); st.rerun()
        with c_l2:
            df_f = get_master("Fitur Pendaftaran")
            for i, r in df_f.iterrows():
                ca, cb = st.columns([3, 1])
                ca.text(r['nama'])
                if cb.button("Hapus", key=f"fit_del_{r['id']}"):
                    conn = get_connection(); conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()

    with t3:
        st.subheader("👥 Manajemen Akun Tim")
        with st.form("tambah_user_form"):
            un = st.text_input("Username Baru")
            up = st.text_input("Password Baru", type="password")
            if st.form_submit_button("Buat Akun"):
                if un and up:
                    conn = get_connection()
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?)", (un, up, 'Staff'))
                        conn.commit(); conn.close(); st.success("Akun Berhasil Dibuat"); st.rerun()
                    except: st.error("Username sudah terdaftar!")
        
        st.write("Daftar Akun:")
        conn = get_connection()
        u_df = pd.read_sql("SELECT username FROM users", conn); conn.close()
        for i, row in u_df.iterrows():
            if row['username'] != 'admin':
                cx, cy = st.columns([3, 1])
                cx.text(f"👤 {row['username']}")
                if cy.button("Hapus Akun", key=f"u_del_{row['username']}"):
                    conn = get_connection(); conn.execute("DELETE FROM users WHERE username=?", (row['username'],)); conn.commit(); conn.close(); st.rerun()
