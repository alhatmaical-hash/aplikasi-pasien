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
    # Tabel User
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    # Tabel Master (Perusahaan, Dept, Jabatan, Fitur Pendaftaran)
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    # Tabel Pasien Utama
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE, nama_lengkap TEXT, nik TEXT, pernah_berobat TEXT, 
                    perusahaan TEXT, departemen TEXT, jabatan TEXT)''')
    # Tabel Data Dinamis (Nomor HP, Nama Orang Tua, dll)
    c.execute('''CREATE TABLE IF NOT EXISTS pasien_custom_data (
                    pasien_id INTEGER, field_name TEXT, field_value TEXT)''')
    # Tabel SKD
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
    
    # Mengambil data master untuk pilihan dropdown
    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()
    custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

    # Pilihan status berobat (Radio Button)
    pernah = st.radio(
        "PERNAH BEROBAT DISINI? / 您以前在这里看过病吗？", 
        ["Iya Sudah / 是的", "Belum Pernah / 从未"], 
        horizontal=True
    )

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            jenis_kunjungan = st.selectbox("Jenis Kunjungan", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"])
            nama_lengkap = st.text_input("Nama Lengkap")
            no_hp = st.text_input("No HP Aktif (WhatsApp)")
            agama = st.selectbox("Agama", ["Islam", "Kristen", "Hindu", "Buddha", "Katolik", "Tidak Diketahui"])
            nik = st.text_input("NIK / ID Card")
            gender = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"], horizontal=True)

        with col2:
            blok_mes = st.text_input("Blok Mes dan No Kamar")
            pernah_berobat = st.radio("Pernah Berobat Disini?", ["Iya Sudah", "Belum Pernah"], horizontal=True)
            tgl_lahir = st.text_input("Tempat & Tanggal Lahir (Contoh: Obi, 01-01-1990)")
            perusahaan = st.selectbox("Perusahaan", get_master("Perusahaan"))
            dept = st.selectbox("Departemen", get_master("Departemen"))
            jabatan = st.selectbox("Jabatan", get_master("Jabatan"))

        alergi = st.multiselect("Jenis Alergi", ["Makanan", "Obat", "Cuaca", "Tidak Ada"])
        gol_darah = st.selectbox("Golongan Darah", ["A", "B", "AB", "O", "-"])
        lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik")
            
        # LOGIKA: Kolom tambahan HANYA muncul jika pilih "Belum Pernah"
        responses = {}
        if pernah == "Belum Pernah / 从未":
            st.divider()
            st.subheader("📋 Informasi Tambahan (Pasien Baru) / 附加信息（新 interaction）")
            # Loop untuk menampilkan fitur tambahan yang Anda buat di Pengaturan Master
            for field in custom_fields:
                responses[field] = st.text_input(f"{field.upper()}")
        else:
            # Jika pasien lama, kolom tambahan tetap disimpan sebagai string kosong
            responses = {field: "" for field in custom_fields}

        # Tombol submit dengan teks Mandarin
        submit_btn = st.form_submit_button("KIRIM PENDAFTARAN / 提交登记")

        if submit_btn:
            if nama and nik:
                conn = get_connection()
                cur = conn.cursor()
                try:
                    # 1. Simpan data utama ke tabel 'pasien'
                    cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan) 
                                 VALUES (?,?,?,?,?,?,?)''', 
                                 (datetime.now().date(), nama, nik, pernah, perusahaan, dept, jabatan))
                    
                    last_id = cur.lastrowid # Ambil ID pasien yang baru saja masuk
                    
                    # 2. Simpan data tambahan ke tabel 'pasien_custom_data'
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
    df = pd.read_sql("SELECT * FROM pasien", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada data pasien.")

# --- 8. MENU SKD / 医生证明 ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    
    # 1. Folder Baru
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

    # 3. Ambil Daftar Departemen untuk Tombol Folder
    try:
        conn = get_connection()
        df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
        conn.close()
        daftar_folder = df_dept['nama'].tolist()
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]

    st.write("### Pilih Departemen:")
    cols = st.columns(4)
    for idx, d in enumerate(daftar_folder):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True, key=f"folder_{d}_{idx}"):
            st.session_state['sel_dept'] = d
            st.rerun()

    # 4. Jika Folder Dipilih, Tampilkan Isi
    if 'sel_dept' in st.session_state:
        st.divider()
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target} ({f_bulan}/{f_tahun})")
        
        # Bagian Upload
        with st.expander("➕ Upload PDF Baru"):
            with st.form("upload_skd_form", clear_on_submit=True):
                u_f = st.file_uploader("Pilih PDF", type=['pdf'])
                submit_upload = st.form_submit_button("Simpan Ke Folder")
                
                if submit_upload:
                    if u_f:
                        try:
                            with get_connection() as conn:
                                conn.execute("""
                                    INSERT INTO skd_files 
                                    (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) 
                                    VALUES (?,?,?,?,?,?,?)""", 
                                    (u_f.name, target, u_f.name, u_f.read(), datetime.now(), f_bulan, f_tahun))
                                conn.commit()
                            st.success(f"Berhasil: {u_f.name} tersimpan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error Database: {e}")
                    else:
                        st.warning("Pilih file PDF!")

        # --- BAGIAN PENCARIAN & LIST ---
        st.write("### Daftar File:")
        search_query = st.text_input("🔍 Cari Nama Pasien...", placeholder="Ketik nama...")

        with get_connection() as conn:
            query = f"SELECT * FROM skd_files WHERE departemen='{target}' AND bulan_skd={f_bulan} AND tahun_skd={f_tahun}"
            files = pd.read_sql(query, conn)
            
            if search_query and not files.empty:
                files = files[files['nama_pasien'].str.contains(search_query, case=False, na=False)]

        if not files.empty:
            for i, r in files.iterrows():
                c_file, c_view, c_down, c_del = st.columns([4, 1.2, 1.2, 1])
                c_file.text(f"📄 {r['nama_file']}") 
                
                if c_view.button("👁️ Lihat", key=f"v_{r['id']}"):
                    st.download_button("Klik untuk Buka", data=r['file_data'], file_name=r['nama_file'], mime='application/pdf', key=f"v_btn_{r['id']}")

                c_down.download_button("📥 Unduh", data=r['file_data'], file_name=r['nama_file'], mime='application/pdf', key=f"d_{r['id']}")

                if c_del.button("🗑️", key=f"f_del_{r['id']}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM skd_files WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()
        else:
            st.info("Tidak ada file di folder ini.")

       # --- BAGIAN PENCARIAN (Garis Panjang) ---
        st.write("### Daftar File:")
        search_query = st.text_input("🔍 Cari Nama Pasien atau Nama File...", placeholder="Masukkan nama untuk mencari...")

        with get_connection() as conn:
            try:
                # Query dasar
                query = f"SELECT * FROM skd_files WHERE departemen='{target}' AND bulan_skd={f_bulan} AND tahun_skd={f_tahun}"
                files = pd.read_sql(query, conn)
                
                # Logika Filter Pencarian
                if search_query:
                    files = files[files['nama_pasien'].str.contains(search_query, case=False, na=False) | 
                                  files['nama_file'].str.contains(search_query, case=False, na=False)]
            except:
                files = pd.DataFrame(columns=['id', 'nama_pasien', 'nama_file', 'file_data'])

      # --- TAMPILAN LIST DENGAN TOMBOL AKSI ---
        if not files.empty:
            for i, r in files.iterrows():
                # Membuat baris dengan kolom
                c_file, c_view, c_down, c_del = st.columns([4, 1.2, 1.2, 1])
                
                c_file.text(f"📄 {r['nama_file']}") 
                
                # PERBAIKAN KEY: Tambahkan index 'i' agar tidak ada yang kembar
                # 1. Tombol Lihat
                if c_view.button("👁️ Lihat", key=f"btn_view_{r['id']}_{i}"):
                    st.download_button(
                        label="Buka PDF", 
                        data=r['file_data'], 
                        file_name=r['nama_file'], 
                        mime='application/pdf', 
                        key=f"dl_view_{r['id']}_{i}"
                    )
                    st.info("Klik tombol di atas untuk membuka.")

                # 2. Tombol Download
                c_down.download_button(
                    label="📥 Unduh",
                    data=r['file_data'],
                    file_name=r['nama_file'],
                    mime='application/pdf',
                    key=f"btn_down_{r['id']}_{i}"
                )

                # 3. Tombol Hapus
                if c_del.button("🗑️", key=f"btn_del_{r['id']}_{i}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM skd_files WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()
        else:
            st.info(f"Tidak ada data ditemukan di folder ini.")
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
