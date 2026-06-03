import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime
import io
import pytz
import base64
from datetime import datetime, time, timedelta



def get_fallback(row, keys, default="-"):
    """Fungsi ini mencoba mengambil data dari beberapa kolom secara berurutan, 
    dan mengabaikan tanda '-' atau kosong."""
    for key in keys:
        val = row.get(key)
        # Jika ada data dan bukan "-", bukan kosong, bukan "nan"
        if val is not None and str(val).strip() not in ["", "-", "nan", "None"]:
            return str(val)
    return default

# --- FUNGSI PDF ---
def tampilkan_pdf_base64(file_data):
    base64_pdf = base64.b64encode(file_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)



# --- LANGKAH 0: INISIALISASI (TARUH PALING ATAS SETELAH IMPORT) ---
# Ini harus ada supaya komputer lain tidak bingung mencari variabelnya
keys_to_init = ['nama_lengkap', 'nik', 'no_hp', 'blok_mes', 'tgl_lahir', 'lokasi_kerja']
for key in keys_to_init:
    if key not in st.session_state:
        st.session_state[key] = ""

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps", page_icon="🏥", layout="wide")
st.markdown("""
    <style>
    /* Mengatur teks label utama (PERNAH BEROBAT DISINI?) */
    div[data-testid="stWidgetLabel"] p {
        font-size: 22px !important;
        font-weight: bold !important;
        color: #1E1E1E;
    }
    
    /* Mengatur teks pilihan (Iya Sudah / Belum Pernah) */
    div[data-testid="stMarkdownContainer"] p {
        font-size: 20px !important;
        font-weight: 600 !important;
    }

    /* === KHUSUS: MENGUBAH TOMBOL FORM SUBMIT MENJADI WARNA HIJAU === */
    form[data-testid="stForm"] button[data-testid="baseButton-secondaryFormSubmit"],
    .stFormSubmitButton > button {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 0.5rem 2rem !important;
        width: 100% !important;
        border-radius: 6px !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1) !important;
        transition: background-color 0.3s ease !important;
    }
    
    /* Efek saat tombol disentuh mouse atau ditekan (Hover) */
    form[data-testid="stForm"] button[data-testid="baseButton-secondaryFormSubmit"]:hover,
    .stFormSubmitButton > button:hover {
        background-color: #218838 !important;
        color: white !important;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

def get_connection():
    # Ini akan menyimpan database di folder yang sama dengan file kodingan Anda (Drive C)
    path_database = "klinik_data.db"
    
    # Hubungkan ke database
    return sqlite3.connect(path_database, check_same_thread=False)
def init_db():
    # Menggunakan 'with' agar koneksi otomatis tertutup jika terjadi error
    with get_connection() as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        c = conn.cursor()
        
        # 1. Tabel User
        c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
        
        # 2. Tabel Master
        c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
        
        # 3. Tabel Pasien Utama
        c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tgl_daftar TIMESTAMP,
                        status_antrian TEXT,
                        nama_lengkap TEXT, 
                        nik TEXT, 
                        pernah_berobat TEXT, 
                        perusahaan TEXT, 
                        departemen TEXT, 
                        jabatan TEXT)''')
        
        c.execute('CREATE TABLE IF NOT EXISTS dokter_jaga_harian (id INTEGER PRIMARY KEY, nama_dokter TEXT)')

        # --- Update Schema (Kolom Baru) ---
        # Saya sudah menambahkan 'tempat_lahir' dan 'jenis_kelamin' di sini
        kolom_tambahan = [
            ("no_hp", "TEXT"), ("agama", "TEXT"), ("gender", "TEXT"),
            ("blok_mes", "TEXT"), ("tgl_lahir", "TEXT"), ("alergi", "TEXT"),
            ("gol_darah", "TEXT"), ("lokasi_kerja", "TEXT"), ("lokasi_mcu", "TEXT"),
            ("is_authorized", "INTEGER DEFAULT 0"), ("jenis_kunjungan", "TEXT"),
            ("tempat_lahir", "TEXT"), ("jenis_kelamin", "TEXT")
        ]
        
        for kolom, tipe in kolom_tambahan:
            try:
                c.execute(f"ALTER TABLE pasien ADD COLUMN {kolom} {tipe}")
            except:
                # Diamkan saja jika kolom sudah ada
                pass

        # --- Isi Data Master Dokter ---
        daftar_dokter = ["DR. JOKO", "DR. DEDEK", "DR. KARTIKA", "DR. DOMINICUS", "DR. ANDIKA", "DR. RANDY"]
        for nama_dr in daftar_dokter:
            c.execute("INSERT OR IGNORE INTO master_data (kategori, nama) VALUES (?,?)", ("Dokter", nama_dr))
        
        # 4. Tabel Data Dinamis
        c.execute('''CREATE TABLE IF NOT EXISTS pasien_custom_data (
                        pasien_id INTEGER, field_name TEXT, field_value TEXT)''')
        
        # 5. Tabel SKD
        c.execute('''CREATE TABLE IF NOT EXISTS skd_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nama_pasien TEXT, departemen TEXT, nama_file TEXT,
                        file_data BLOB, tgl_upload TIMESTAMP, bulan_skd INTEGER, tahun_skd INTEGER)''')
        
        # Tambah Admin Default
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', 'admin123', 'Admin'))
        
        conn.commit()

# Jalankan inisialisasi database SEKALI SAJA
init_db()
# --- 3. FUNGSI DATA (DENGAN CACHE) ---

def get_master(kategori):
    with get_connection() as conn:
        query = "SELECT id, nama FROM master_data WHERE kategori = ?"
        return pd.read_sql(query, conn, params=(kategori,))
# --- 4. MANAJEMEN LOGIN & DETEKSI BARCODE ---
params = st.query_params
is_pasien_mode = params.get("mode") == "pasien"

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIKA NAVIGASI ---

# 1. JIKA MODE PASIEN (DARI BARCODE) -> LANGSUNG ATUR MENU
if is_pasien_mode:
    menu = "Pendaftaran / 登记"
    st.markdown("### 🏥 Sistem Pendaftaran Mandiri")
    st.info("Silakan isi formulir di bawah ini dengan data yang benar.")
    
    # Bungkus CSS dalam st.markdown dengan benar
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
# 2. JIKA SUDAH LOGIN (STAFF/ADMIN)
elif st.session_state['logged_in']:
    role_user = st.session_state.get('role')
    st.sidebar.success(f"🔓 {role_user}: {st.session_state['username']}")
    
    if role_user == "Admin":
        menu_list = ["Pendaftaran Pasien", "Rekam Medis / 病历", "SKD / 医生证明", "Dashboard Analitik", "Pengaturan Master / 设置"]
    else:
        menu_list = ["SKD / 医生证明"]
    
    menu = st.sidebar.selectbox("Pilih Menu", menu_list)
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# 3. JIKA BELUM LOGIN & BUKAN MODE PASIEN
else:
    st.sidebar.title("🏥 Klinik Apps")
    # Pasien yang tidak lewat barcode masih bisa memilih form pendaftaran di sidebar
    page_mode = st.sidebar.radio("Navigasi", ["Login Staff", "Form Pendaftaran"])
    
    if page_mode == "Form Pendaftaran":
        menu = "Pendaftaran / 登记"
    else:
        st.markdown("<h2 style='text-align: center;'>🔐 Login Klinik Apps</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.button("Login", width="stretch"):
                with get_connection() as conn:
                    res = conn.execute("SELECT username, role FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
                if res:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = res[0]
                    st.session_state['role'] = res[1]
                    st.rerun()
                else:
                    st.error("Username atau Password salah")
        
        # PENTING: st.stop() hanya dijalankan jika user memilih "Login Staff" 
        # dan belum berhasil login. Jika memilih "Form Pendaftaran", stop dilewati.
        st.stop()

# --- 5. LOGIKA HALAMAN (Gateway/Router) ---

if 'menu' not in locals():
    # Fallback jika menu belum terdefinisikan (misal di halaman login)
    menu = "Login"

if menu == "Pendaftaran / 登记":
    # Pastikan fungsi pendaftaran Anda dipanggil di sini
    st.header("Formulir Pendaftaran")
    # ... panggil fungsi form_pendaftaran() Anda ...

elif menu == "Rekam Medis / 病历":
    # Pastikan query SQL menggunakan nama kolom yang SAMA dengan init_db
    # Perhatikan: di init_db Anda pakai 'gender' dan 'alergi', bukan 'jenis_kelamin'/'jenis_alergi'
    query_medis = """
    SELECT id, tgl_daftar, nama_lengkap, nik, no_hp, 
           agama, gender, blok_mes, tgl_lahir, perusahaan, 
           departemen, jabatan, alergi, gol_darah, 
           lokasi_kerja, lokasi_mcu, status_antrian
    FROM pasien ORDER BY id DESC
    """

# --- MENU PENDAFTARAN (Admin & Publik) ---
if menu in ["Pendaftaran Pasien", "Pendaftaran / 登记"]:
# --- 1. INISIALISASI STATE ---
    # Taruh paling atas agar aplikasi tahu status pendaftaran sejak awal
    if 'daftar_berhasil' not in st.session_state:
        st.session_state['daftar_berhasil'] = False
    if 'dokter_final_state' not in st.session_state:
        st.session_state['dokter_final_state'] = ""

    # --- 2. LOGIKA TAMPILAN (TEMPEL DI SINI) ---
    # Ini adalah "Gatekeeper". Jika sukses, dia akan muncul dan 
    # st.stop() akan mencegah kode di bawahnya (form) dieksekusi.
    if st.session_state['daftar_berhasil']:
        st.balloons()
        st.markdown(f"""
            <div style="background-color: #d4edda; padding: 30px; border-radius: 15px; border: 2px solid #c3e6cb; text-align: center; margin-top: 20px;">
                <h1 style="color: #155724; font-size: 50px; margin-bottom: 10px;">✅</h1>
                <h2 style="color: #155724; font-family: sans-serif;">Pendaftaran Anda Sukses!</h2>
                <h3 style="color: #155724; font-family: sans-serif; margin-bottom: 20px;">登记成功</h3>
                <p style="color: #155724; font-size: 18px; font-weight: bold;">
                    Dokter Anda: {st.session_state['dokter_final_state']}<br>
                    Silahkan tunggu panggilan petugas. / 请耐心等待叫号。
                </p>
                <hr style="border: 0.5px solid #c3e6cb; margin: 20px 0;">
                <p style="color: #155724; font-size: 16px;">Terima kasih, semoga lekas sembuh.<br>感谢您，祝您早日康复。</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Daftar Kembali Jika Di Arahkan Oleh Petugas Klinik Jangan Daftar Ulang Sendiri!!! / 重新登记", width="stretch"):
            st.session_state['daftar_berhasil'] = False
            st.rerun()
        st.stop() # AMAT PENTING: Menghentikan render Form di bawah

    st.header("📝 MOHON PERHATIAN CUKUP SATU KALI DAFTAR SAJA 病人登记")
    submit_btn = False
    kontainer_layar_utama = st.empty()
    # --- TEMPEL DI SINI ---
    # Ambil data dokter dari session_state yang diisi di menu Rekam Medis
    dokter_jaga = st.session_state.get('dokter_jaga_aktif', [])

    dokter_terpilih = "Belum Ditentukan"
    with get_connection() as conn:
        try:
            df_dr = pd.read_sql("SELECT nama_dokter FROM dokter_jaga_harian", conn)
            dokter_jaga = df_dr['nama_dokter'].tolist()
        except:
            dokter_jaga = []

    dokter_terpilih = "Belum Ditentukan"
    if dokter_jaga:
        with get_connection() as conn:
            tz_wit = pytz.timezone('Asia/Jayapura')
            waktu_sekarang = datetime.now(tz_wit)
            tgl_hari_ini = waktu_sekarang.strftime("%Y-%m-%d")
            # Menghitung jumlah pasien hari ini
            query = "SELECT COUNT(*) FROM pasien WHERE tgl_daftar LIKE ?"
            res = conn.execute(query, (f"{tgl_hari_ini}%",)).fetchone()
            jml_pasien = res[0] if res else 0
            
            # Setiap 5 pasien, ganti dokter (Round Robin)
            idx_dokter = (jml_pasien // 5) % len(dokter_jaga)
            dokter_terpilih = dokter_jaga[idx_dokter]
        
        st.info(f"Pasien ini akan diarahkan ke: **{dokter_terpilih}**")
    else:
        # Jika tabel dokter kosong, tampilkan error dan hentikan proses
        st.error("⚠️ Sistem pendaftaran belum siap per jam 12.00-13.30 Lagi Istirahat Sholat Dan Makan silahkan daftar lagi ketika jam 13.30.")
        st.stop()
    with kontainer_layar_utama.container():
        opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
        opts_dept = get_master("Departemen")['nama'].tolist()
        opts_jabatan = get_master("Jabatan")['nama'].tolist()
        custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

        # Pastikan teks di sini SAMA PERSIS dengan yang di dalam IF nanti
        responses = {}
        pernah = st.radio("PERNAH BEROBAT DISINI? / 您以前在这里看过病吗？", ["Iya Sudah / 是的", "Belum Pernah / 从未"], horizontal=True)
        with st.form("form_reg", clear_on_submit=False):
            # Ambil data langsung dari database master
            opts_perusahaan = [""] + get_master("Perusahaan")['nama'].tolist()
            opts_dept = [""] + get_master("Departemen")['nama'].tolist()
            opts_jabatan = [""] + get_master("Jabatan")['nama'].tolist()
            # PERBAIKAN: Menggunakan pengecekan teks yang tepat
            if pernah == "Iya Sudah / 是的": 
                st.subheader("📌 Form Pasien Lama (Ringkas)")
                col1, col2 = st.columns(2)
                with col1:
                    # Menambahkan * pada label "Jenis Kunjungan"
                    jenis_kunjungan = st.selectbox(
                        "Jenis Kunjungan *", 
                        ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"],
                        index=None,
                        placeholder="Pilih Jenis Kunjungan..."
                    )
                    nama_lengkap = st.text_input("Nama Lengkap / 全名 *", value=st.session_state.nama_lengkap)
                    no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码 *", value=st.session_state.no_hp)
                    nik = st.text_input("NIK ID CARD PERUSAHAAN CONTOH (F0523005205) *", value=st.session_state.nik)
                    agama = st.selectbox(
                        "Agama / 宗教", 
                        ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"],
                        index=None,
                        placeholder="Pilih Agama..."
                    )
                    gender = st.radio("Jenis Kelamin / 性别", ["Laki-laki / 男", "Perempuan / 女"], horizontal=True)
                
                with col2:
                    blok_mes = st.text_input("Blok Mes dan No Kamar / 宿舍楼 dan 房间号 *", value=st.session_state.blok_mes)
                    tmpt_lahir = st.text_input("Tempat Lahir / 出生地点 *")
                    tgl_lahir_val = st.date_input("Tanggal Lahir / 出生日期 *", value=None, min_value=datetime(1950, 1, 1), max_value=datetime.now(), format="DD/MM/YYYY")
                    perusahaan = st.selectbox("Perusahaan / 公司 *", opts_perusahaan)
                    dept = st.selectbox("Departemen / 部门 *", opts_dept)
                    jabatan = st.selectbox("Jabatan / 职位 *", opts_jabatan)
                
                st.divider()
                col3, col4 = st.columns(2)
                
                with col3:
                    alergi = st.multiselect("Jenis Alergi / 过敏类型 *", ["Makanan / 食物", "Obat / 药物", "Cuaca / 天气", "Tidak Ada / 无"])
                    
                    # Menambahkan '*' pada label Golongan Darah
                    gol_darah = st.selectbox(
                        "Golongan Darah / 血型 *", 
                        ["A", "B", "AB", "O", "BELUM TAHU"],
                        index=None,
                        placeholder="Pilih Golongan Darah..."
                    )

                with col4:
                    # Menambahkan '*' pada label Lokasi MCU
                    lokasi_mcu = st.selectbox(
                        "Lokasi MCU Pertama Kali *", 
                        ["Klinik HJF", "Klinik HPAL", "Klinik Luar Obi"],
                        index=None,
                        placeholder="Pilih Lokasi Klinik..."
                    )
                    lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik / 具体工作地点 *", value=st.session_state.lokasi_kerja)
                
            else:
                st.subheader("📑 Form Pasien Baru (Lengkap)")
                col1, col2 = st.columns(2)
                with col1:
                    # Menambahkan * pada label "Jenis Kunjungan"
                    jenis_kunjungan = st.selectbox(
                        "Jenis Kunjungan *", 
                        ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"],
                        index=None,
                        placeholder="Pilih Jenis Kunjungan..."
                    )
                    nama_lengkap = st.text_input("Nama Lengkap / 全名 *", value=st.session_state.nama_lengkap)
                    no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码 *", value=st.session_state.no_hp)
                    nik = st.text_input("NIK ID CARD PERUSAHAAN CONTOH (F0523005205) *", value=st.session_state.nik)
                    agama = st.selectbox(
                        "Agama / 宗教", 
                        ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"],
                        index=None,
                        placeholder="Pilih Agama..."
                    )
                    gender = st.radio("Jenis Kelamin / 性别", ["Laki-laki / 男", "Perempuan / 女"], horizontal=True)

                with col2:
                    blok_mes = st.text_input("Blok Mes dan No Kamar / 宿舍楼和房间号 *", value=st.session_state.blok_mes)
                    tmpt_lahir = st.text_input("Tempat Lahir / 出生地点 *")
                    tgl_lahir_val = st.date_input("Tanggal Lahir / 出生日期 *", value=None, min_value=datetime(1950, 1, 1), max_value=datetime.now(), format="DD/MM/YYYY")
                    perusahaan = st.selectbox("Perusahaan / 公司 *", opts_perusahaan)
                    dept = st.selectbox("Departemen / 部门 *", opts_dept)
                    jabatan = st.selectbox("Jabatan / 职位 *", opts_jabatan)

                st.divider()
                col3, col4 = st.columns(2)
                with col3:
                    alergi = st.multiselect("Jenis Alergi / 过敏类型 *", ["Makanan / 食物", "Obat / 药物", "Cuaca / 天气", "Tidak Ada / 无"])
                    
                    # Menambahkan tanda * pada Golongan Darah
                    gol_darah = st.selectbox(
                        "Golongan Darah / 血型 *", 
                        ["A", "B", "AB", "O", "BELUM TAHU"],
                        index=None,
                        placeholder="Pilih Golongan Darah..."
                    )

                with col4:
                    # Menambahkan tanda * pada Lokasi MCU
                    lokasi_mcu = st.selectbox(
                        "Lokasi MCU Pertama Kali *", 
                        ["Klinik HJF", "Klinik HPAL", "Klinik Luar Obi"],
                        index=None,
                        placeholder="Pilih Lokasi Klinik..."
                    )
                    lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik / 具体工作地点 *", value=st.session_state.lokasi_kerja)
                
                st.subheader("📋 Informasi Tambahan / 附加信息")
                responses = {field: st.text_input(f"{field.upper()}") for field in custom_fields}
            submit_btn = st.form_submit_button("KIRIM PENDAFTARAN / 提交登记")
        
            if submit_btn:
                # 1. Kunci agar tidak double click
                if st.session_state.get('proses_simpan', False):
                    st.stop()
                st.session_state['proses_simpan'] = True

                # 2. Definisikan required fields (Sesuai kode asli Anda)
                required = {
                    "Nama": nama_lengkap, 
                    "NIK": nik, 
                    "No HP": no_hp,
                    "Agama": agama,
                    "Jenis Kelamin": gender,
                    "Blok Mes": blok_mes, 
                    "Tempat Lahir": tmpt_lahir,
                    "Tanggal Lahir": tgl_lahir_val,
                    "Perusahaan": perusahaan, 
                    "Dept": dept,
                    "Jabatan": jabatan,
                    "Alergi": alergi,
                    "Area Kerja": lokasi_kerja,
                    "Golongan Darah": gol_darah,  
                    "Lokasi MCU": lokasi_mcu,
                    "Jenis Kunjungan": jenis_kunjungan
                }
                
                # Cek apakah ada yang kosong
                empty_fields = [k for k, v in required.items() if str(v).strip() in ["", "None", "[]"] or v is None]

                if empty_fields:
                    st.error(f"⚠️ Gagal! Kolom berikut wajib diisi: {', '.join(empty_fields)}")
                    st.session_state['proses_simpan'] = False
                    st.stop() 

                # 3. Jika TIDAK ADA yang kosong, baru lanjut ke proses database
                try:
                    tz_wit = pytz.timezone('Asia/Jayapura')
                    waktu_sekarang = datetime.now(tz_wit)
                    tgl_hari_ini = waktu_sekarang.strftime("%Y-%m-%d")
                    tgl_str = tgl_lahir_val.strftime("%d-%m-%Y") if tgl_lahir_val else ""
                    tgl_gabung = f"{tmpt_lahir}, {tgl_str}"

                    # --- MULAI BLOK DATABASE ---
                    with get_connection() as conn:
                        # A. Cek Double Input
                        check_query = "SELECT is_authorized FROM pasien WHERE nik = ? AND tgl_daftar LIKE ? ORDER BY id DESC LIMIT 1"
                        existing_data = conn.execute(check_query, (nik, f"{tgl_hari_ini}%")).fetchone()

                        if existing_data:
                            auth_status = existing_data[0]
                            if auth_status == 0 or auth_status is None:
                                st.error(f"⚠️ NIK {nik} sudah terdaftar hari ini.")
                                st.session_state['proses_simpan'] = False
                                st.stop()
                        
                        # B. Hitung Antrian & Dokter
                        query_count = "SELECT COUNT(*) FROM pasien WHERE tgl_daftar LIKE ?"
                        jml_pasien = conn.execute(query_count, (f"{tgl_hari_ini}%",)).fetchone()[0]
                        
                        if dokter_jaga:
                            idx_dokter = (jml_pasien // 5) % len(dokter_jaga)
                            dokter_final = dokter_jaga[idx_dokter]
                        else:
                            dokter_final = "Belum Ada Dokter"

                        # C. Proses Simpan Utama
                        cur = conn.cursor()
                        cur.execute('''INSERT INTO pasien (
                                            tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, 
                                            departemen, jabatan, no_hp, agama, gender, 
                                            blok_mes, tgl_lahir, alergi, gol_darah, lokasi_kerja, 
                                            lokasi_mcu, status_antrian, dokter, is_authorized, jenis_kunjungan,
                                            tempat_lahir, jenis_kelamin)
                                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                    (waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S"), 
                                    nama_lengkap, nik, pernah, perusahaan, dept, jabatan, no_hp, agama, gender,
                                    blok_mes, tgl_gabung, str(alergi), gol_darah, lokasi_kerja, 
                                    lokasi_mcu, "Normal", dokter_final, 0, jenis_kunjungan, tmpt_lahir, gender))
                        conn.commit()

                    # --- PERUBAHAN KRUSIAL DI SINI ---
                    st.session_state['dokter_final_state'] = dokter_final
                    st.session_state['daftar_berhasil'] = True
                    st.session_state['proses_simpan'] = False
                    st.rerun() # Ini akan membersihkan form dan memicu layar sukses di atas

                except Exception as e:
                    st.session_state['proses_simpan'] = False
                    st.error(f"Terjadi kesalahan sistem: {e}")
            
#  --- FUNGSI GLOBAL (Letakkan di bagian atas script) ---
def color_row(row):
    # Ambil status, ubah ke lowercase
    status = str(row['status_antrian']).strip().lower()
    
    # Inisialisasi daftar style kosong (sebanyak jumlah kolom)
    styles = [''] * len(row)
    
    # Cari indeks kolom "Nama Lengkap"
    # Menggunakan try-except agar tidak error jika nama kolom berubah
    try:
        # Cari urutan kolom 'Nama Lengkap' dalam baris
        idx_nama = row.index.get_loc('Nama Lengkap')
        
        color = ''
        if status == 'menunggu konsul':
            color = 'background-color: #FFFF66; color: black; font-weight: bold;' # Kuning
        elif status == 'menunggu lab':
            color = 'background-color: #66CCFF; color: black; font-weight: bold;' # Biru
        elif status == 'skd':
            color = 'background-color: #FFB366; color: black; font-weight: bold;' # Oranye
        elif status == 'operan':
            color = 'background-color: #77DD77; color: black; font-weight: bold;' # Hijau
        elif status == 'batal':
            color = 'background-color: #FF6666; color: black; font-weight: bold;' # Merah
        
        # Masukkan warna hanya ke kolom Nama Lengkap
        styles[idx_nama] = color
    except:
        pass
        
    return styles

@st.fragment(run_every="5s")
def display_table_pasien(bulan_selected, tahun_selected, search_term):
    # 1. Siapkan Filter SQL Dinamis
    list_bulan = ["Semua", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    conditions = []
    params = []

    # --- PERBAIKAN: Pencarian Nama atau NIK langsung di SQL ---
    if search_term:
        # Mencari di nama_lengkap ATAU nik
        conditions.append("(nama_lengkap LIKE ? OR nik LIKE ?)")
        params.append(f"%{search_term}%")
        params.append(f"%{search_term}%")

    if bulan_selected != "Semua":
        idx_bulan = list_bulan.index(bulan_selected)
        conditions.append("strftime('%m', tgl_daftar) = ?")
        params.append(f"{idx_bulan:02d}")
        
    if tahun_selected != "Semua":
        conditions.append("strftime('%Y', tgl_daftar) = ?")
        params.append(str(tahun_selected))

    # Gabungkan kriteria filter
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    with get_connection() as conn:
        query = f"""
        SELECT id, 
               tgl_daftar AS 'Tgl Daftar',
               jenis_kunjungan AS 'Jenis Kunjungan', 
               nama_lengkap AS 'Nama Lengkap', 
               nik AS 'NIK/ID', 
               jenis_kelamin AS 'Jenis Kelamin',
               no_hp AS 'WhatsApp',
               gol_darah, 
               agama, 
               blok_mes,
               tempat_lahir AS 'Tempat Lahir', 
               tgl_lahir, 
               perusahaan AS 'Perusahaan', 
               departemen AS 'Departemen', 
               jabatan AS 'Jabatan',
               pernah_berobat, 
               lokasi_mcu, 
               alergi, 
               lokasi_kerja, 
               status_antrian
        FROM pasien 
        {where_clause}
        ORDER BY id DESC 
        LIMIT 100
        """
        df_tampil = pd.read_sql(query, conn, params=params)

    if not df_tampil.empty:
        # Mapping kolom tambahan untuk UI
        df_tampil['Riwayat Berobat'] = df_tampil['pernah_berobat'].apply(
            lambda x: "Iya Sudah" if "Iya" in str(x) else "Belum Pernah"
        )
        
        # TABEL INTERAKTIF
        event = st.dataframe(
            df_tampil.style.apply(color_row, axis=1),
            width="stretch", 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "id": None, 
                "pernah_berobat": None,
                "Tgl Daftar": st.column_config.DatetimeColumn("Tanggal", format="DD/MM/YY HH:mm"),
            }
        )

        # Tangkap baris yang diklik
        if len(event.selection.rows) > 0:
            row_idx = event.selection.rows[0]
            st.session_state['pasien_terpilih_id'] = int(df_tampil.iloc[row_idx]['id'])
            st.session_state['pasien_terpilih_nama'] = df_tampil.iloc[row_idx]['Nama Lengkap']
        
        st.caption(f"Menampilkan {len(df_tampil)} hasil. 💡 Gunakan kolom cari untuk Nama atau NIK.")
    else:
        st.info(f"Data tidak ditemukan. Silakan cek kembali nama/NIK atau filter periode.")
        
if menu == "Rekam Medis / 病历":
    st.header("📊 Menu Rekam Medis")

    # --- BAGIAN 1: DOKTER & OTORISASI (Tetap sama) ---
    with st.expander("👨‍⚕️ Atur Dokter Jaga & Otorisasi"):
        c_a, c_b = st.columns(2)
        with c_a:
            opts_dr = sorted(list(set(get_master("Dokter")['nama'].tolist())))
            with get_connection() as conn:
                try: dr_aktif_db = pd.read_sql("SELECT nama_dokter FROM dokter_jaga_harian", conn)['nama_dokter'].tolist()
                except: dr_aktif_db = []
            pilihan = st.multiselect("Pilih Dokter Jaga", opts_dr, default=dr_aktif_db)
            if st.button("Simpan Jadwal"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM dokter_jaga_harian")
                    for dr in pilihan: conn.execute("INSERT INTO dokter_jaga_harian (nama_dokter) VALUES (?)", (dr,))
                    conn.commit()
                st.rerun()
        with c_b:
            nik_izin = st.text_input("Otorisasi NIK (Daftar Ulang)")
            if st.button("Berikan Izin"):
                with get_connection() as conn:
                    conn.execute("UPDATE pasien SET is_authorized = 1 WHERE nik = ?", (nik_izin,))
                    conn.commit()
                st.success("Izin diberikan.")

    # --- BAGIAN 2: TABEL ANTRIAN ---
    st.write("---")
    st.subheader("📋 Daftar Antrian Pasien")
    
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1: search_term = st.text_input("🔍 Cari Pasien", "", key="search_rekam_medis")
    with col_f2: bulan_selected = st.selectbox("Bulan", ["Semua", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"], index=datetime.now().month)
    with col_f3: tahun_selected = st.selectbox("Tahun", ["Semua"] + [str(t) for t in range(2026, 2035)], index=1)
    
    # PANGGIL FUNGSI INI SAJA (Hapus query manual lainnya di bagian ini)
    display_table_pasien(bulan_selected, tahun_selected, search_term)

    # --- BAGIAN TOMBOL WARNA (DI LUAR FRAGMENT) ---
    if 'pasien_terpilih_id' in st.session_state:
        pid = st.session_state['pasien_terpilih_id']
        pname = st.session_state['pasien_terpilih_nama']
        
        st.markdown(f"### ⚡ Ubah Status Untuk: **{pname}**")
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            def update_warna(new_status):
                with get_connection() as conn:
                    conn.execute("UPDATE pasien SET status_antrian = ? WHERE id = ?", (new_status, pid))
                    conn.commit()
                st.toast(f"Berhasil diubah ke {new_status}")
                # Hapus dari session state agar tombol hilang setelah klik
                del st.session_state['pasien_terpilih_id']
                st.rerun()

            if c1.button("⚪ Normal", width="stretch"): update_warna("Normal")
            if c2.button("🟡 Konsul", width="stretch"): update_warna("Menunggu Konsul")
            if c3.button("🔵 Lab", width="stretch"): update_warna("Menunggu Lab")
            if c4.button("🟠 SKD", width="stretch"): update_warna("SKD")
            if c5.button("🟢 Operan", width="stretch"): update_warna("Operan")
            if c6.button("🔴 Batal", width="stretch"): update_warna("Batal")
    # --- BAGIAN 3: OPERASI DATA ---
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
    
    # UBAH INI (Ganti '-' dengan '')
    df['tempat_lahir'] = df['tempat_lahir'].fillna('')
    df['jenis_kelamin'] = df['jenis_kelamin'].fillna('')

    if not df.empty:
        st.markdown("### 📋 Keterangan Status")
        st.info("🟡 Menunggu Konsul Dokter | 🔵 Menunggu Hasil Lab & Radiologi | 🟠 Batas Download SKD | 🟢 Operan Sift | 🔴 Batal Berobat")
        
        st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name='rekam_medis.csv', mime='text/csv')

        with st.expander("⚙️ Operasi Data (Edit/Hapus/Cetak)"):
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Edit Nama", "Ganti Status", "Cetak", "🗑️ Hapus Data", "Ubah Kunjungan"])
            
            with tab1: # Edit Nama
                opsi_edit = df.apply(lambda x: f"{x['id']} | {x['nama_lengkap']}", axis=1).tolist()
                data_pilih = st.selectbox("Pilih pasien", opsi_edit)
                nama_baru = st.text_input("Nama baru")
                if st.button("Simpan Nama"):
                    with get_connection() as conn:
                        conn.execute("UPDATE pasien SET nama_lengkap = ? WHERE id = ?", (nama_baru, int(data_pilih.split(" | ")[0])))
                        conn.commit()
                    st.rerun()

            with tab2: # Ganti Status
                st.subheader("Ubah Status & Warna Nama Pasien")
                
                # Dropdown pilih pasien
                opsi_edit = df.apply(lambda x: f"{x['id']} | {x['nama_lengkap']}", axis=1).tolist()
                data_pilih = st.selectbox("Pilih Pasien", opsi_edit, key="select_status_warna")
                
                st.write("Klik Status di bawah untuk mengubah warna Nama:")
                
                # Membuat grid tombol untuk status
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                
                status_update = None
                
                if c1.button("⚪ Normal"):
                    status_update = "Normal"
                if c2.button("🟡 Konsul"):
                    status_update = "Menunggu Konsul"
                if c3.button("🔵 Lab"):
                    status_update = "Menunggu Lab"
                if c4.button("🟠 SKD"):
                    status_update = "SKD"
                if c5.button("🟢 Operan"):
                    status_update = "Operan"
                if c6.button("🔴 Batal"):
                    status_update = "Batal"

                if status_update:
                    id_target = int(data_pilih.split(" | ")[0])
                    with get_connection() as conn:
                        conn.execute("UPDATE pasien SET status_antrian = ? WHERE id = ?", (status_update, id_target))
                        conn.commit()
                    st.success(f"Nama {data_pilih.split('|')[1]} sekarang berstatus {status_update}")
                    st.rerun()

            with tab3:
                st.info("Pilih pasien untuk membuat formulir otomatis.")
    
                # 1. Pilihan Pasien dan Petugas
                daftar_nama = df['nama_lengkap'].tolist() if not df.empty else []
                nama_cetak = st.selectbox("Pilih Pasien", daftar_nama, key="select_pasien_pdf")
                petugas = st.selectbox("Pilih Petugas", ["ALHATMA", "WAWAN", "TAUFIK", "DELI"])
    
                # 2. Tombol Aksi (Hanya untuk Generate)
                if st.button("Generate & Tampilkan PDF"):
                    # Filter data terlebih dahulu
                    filtered_df = df[df['nama_lengkap'] == nama_cetak]
                    
                    if not filtered_df.empty:
                        # Ambil baris pertama jika data ditemukan
                        row = filtered_df.iloc[0]
                        
                        try:
                            # Mapping data
                            data_pasien = {
                                "nama": get_fallback(row, ['nama_lengkap']),
                                "nik": get_fallback(row, ['nik', 'NIK', 'NIK/ID']),
                                "perusahaan": get_fallback(row, ['perusahaan']),
                                "departemen": get_fallback(row, ['departemen']),
                                "tgl_lahir": get_fallback(row, ['tgl_lahir']),
                                "tempat_lahir": get_fallback(row, ['tempat_lahir']),
                                "jenis_kelamin": get_fallback(row, ['jenis_kelamin', 'gender']),
                                "agama": get_fallback(row, ['agama']),
                                "no_hp": get_fallback(row, ['no_hp', 'whatsapp']),
                                "jabatan": get_fallback(row, ['jabatan']),
                                "blok_mes": get_fallback(row, ['blok_mes']),
                                "alergi": get_fallback(row, ['alergi']),
                                "gol_darah": get_fallback(row, ['gol_darah']),
                                "lokasi_mcu": get_fallback(row, ['lokasi_mcu']),
                            }
                
                            from form_generator import buat_formulir_otomatis
                            st.session_state['pdf_cetak_aktif'] = buat_formulir_otomatis(data_pasien, petugas)
                            st.session_state['nama_p_aktif'] = nama_cetak
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Gagal generate PDF: {e}")
                    else:
                        st.error(f"Data untuk '{nama_cetak}' tidak ditemukan di database saat ini.")

                # 3. Tampilkan Hasil (Hanya satu blok ini saja)
                if 'pdf_cetak_aktif' in st.session_state:
                    st.success(f"✅ Formulir untuk {st.session_state['nama_p_aktif']} siap!")
        
                    c1, c2 = st.columns(2)
                    with c1:
                            st.download_button(
                                label="📥 Download PDF",
                                data=st.session_state['pdf_cetak_aktif'],
                                file_name=f"Formulir_{st.session_state['nama_p_aktif'].replace(' ', '_')}.pdf",
                                mime="application/pdf"
                            )
                    with c2:
                            if st.button("❌ Tutup Pratinjau"):
                                del st.session_state['pdf_cetak_aktif']
                                st.rerun()
        
                    # Tampilkan PDF
                    tampilkan_pdf_base64(st.session_state['pdf_cetak_aktif'])
            with tab4: # Hapus Data
                # --- 1. HAPUS PER NAMA (TANPA PASSWORD) ---
                st.subheader("🗑️ Hapus Pasien Spesifik")
                if not df.empty:
                    # Membuat daftar pilihan: ID | Nama
                    opsi_hapus = df.apply(lambda x: f"{x['id']} | {x['nama_lengkap']}", axis=1).tolist()
                    pasien_terpilih = st.selectbox("Pilih pasien yang akan dihapus", opsi_hapus, key="select_hapus_satuan")
                    
                    if st.button("Hapus Pasien Ini"):
                        id_target = int(pasien_terpilih.split(" | ")[0])
                        with get_connection() as conn:
                            conn.execute("DELETE FROM pasien WHERE id = ?", (id_target,))
                            conn.commit()
                        st.success(f"Berhasil menghapus pasien dengan ID: {id_target}")
                        st.rerun()
                else:
                    st.info("Data pasien kosong.")
                
                st.divider()

                # --- 2. HAPUS DATA PER BULAN (FITUR BARU DENGAN PASSWORD) ---
                st.warning("⚠️ Zona Berbahaya - Hanya Admin yang dapat mengakses menu hapus massal ini.")
                
                col_del1, col_del2 = st.columns(2)
                with col_del1:
                    list_bulan_del = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
                    bulan_hapus = st.selectbox("Pilih Bulan Yang Akan Dihapus", list_bulan_del, index=datetime.now().month - 1, key="bulan_hapus_rekam_medis")
                with col_del2:
                    tahun_hapus = st.selectbox("Pilih Tahun Yang Akan Dihapus", [str(t) for t in range(2026, 2035)], index=0, key="tahun_hapus_rekam_medis")
                
                pwd_admin = st.text_input("Masukkan Password Admin untuk Konfirmasi Hapus", type="password", key="pwd_hapus_admin")
                
                if pwd_admin == "admin123": # Sesuaikan password Anda
                    st.error(f"🔒 Akses Admin Diberikan. Anda bersiap menghapus seluruh data pasien pada bulan **{bulan_hapus} {tahun_hapus}**!")
                    
                    # Konversi nama bulan ke format angka dua digit (01-12) untuk filter SQL strftime
                    idx_bulan_del = list_bulan_del.index(bulan_hapus) + 1
                    format_bulan = f"{idx_bulan_del:02d}"
                    
                    if st.button(f"🚨 HAPUS DATA PASIEN BULAN {bulan_hapus.upper()} {tahun_hapus}", type="primary"):
                        try:
                            with get_connection() as conn:
                                # Menghapus data pasien berdasarkan bulan dan tahun dari kolom tgl_daftar
                                cursor_del = conn.cursor()
                                cursor_del.execute(
                                    "DELETE FROM pasien WHERE strftime('%m', tgl_daftar) = ? AND strftime('%Y', tgl_daftar) = ?",
                                    (format_bulan, str(tahun_hapus))
                                )
                                rows_affected = cursor_del.rowcount
                                conn.commit()
                            
                            if rows_affected > 0:
                                st.success(f"🔥 Berhasil! Sebanyak {rows_affected} data pasien periode {bulan_hapus} {tahun_hapus} telah dibersihkan.")
                            else:
                                st.info(f"Tidak ada data pasien yang terdaftar pada periode {bulan_hapus} {tahun_hapus}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menghapus data: {e}")
                else:
                    st.info("Menu 'Hapus Data Per Bulan' terkunci. Masukkan password admin untuk membuka.")
            with tab5: # --- FITUR BARU: UBAH KUNJUNGAN ---
                    st.subheader("Ubah Jenis Kunjungan")
                    opsi_kunjungan = ["Berobat", "UGD", "Kontrol Rawat Luka", "Kontrol MCU"] 
                    opsi_pasien = df.apply(lambda x: f"{x['id']} | {x['nama_lengkap']}", axis=1).tolist()
                    
                    pasien_pilih = st.selectbox("Pilih pasien", opsi_pasien, key="kunjungan_select_tab5")
                    kunjungan_baru = st.selectbox("Pilih Jenis Kunjungan Baru", opsi_kunjungan, key="kunjungan_baru_select_tab5")
        
                    if st.button("Update Kunjungan"):
                        id_target = int(pasien_pilih.split(" | ")[0])
                        with get_connection() as conn:
                            conn.execute("UPDATE pasien SET jenis_kunjungan = ? WHERE id = ?", (kunjungan_baru, id_target))
                            conn.commit()
                        st.success(f"Jenis kunjungan pasien ID {id_target} diubah menjadi: {kunjungan_baru}")
                        st.rerun()        
# --- MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    
   # 1. Tambah Departemen Baru dengan Proteksi Password
    with st.expander("➕ Tambah Folder Departemen Baru"):
        # Input Nama Departemen
        new_f = st.text_input("Nama Departemen Baru", key="input_nama_dept_skd")
        
        # Tambahkan Input Password
        pwd_tambah_dept = st.text_input("Hanya Petugas Rekam Medis Yang Bisa Menambahkan Folder", 
                                       type="password", 
                                       key="pwd_tambah_dept_skd")
        
        if st.button("Buat Folder", key="btn_save_dept_skd"):
            # Cek apakah password benar
            if pwd_tambah_dept == "admin123": # Sesuaikan dengan password Anda
                if new_f:
                    try:
                        with get_connection() as conn:
                            # Pastikan tabel 'master_data' memiliki kolom 'kategori' dan 'nama'
                            conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", 
                                       ("Departemen", new_f))
                            conn.commit()
                        st.success(f"Folder '{new_f}' berhasil dibuat!")
                        # Rerun sangat penting agar daftar di bawahnya langsung terupdate
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Gagal membuat folder: {e}")
                else:
                    st.warning("Nama departemen tidak boleh kosong.")
            else:
                st.error("Sandi Admin Salah! Akses ditolak.")

    # 2. Filter Waktu
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    
    tahun_sekarang = datetime.now().year
    opsi_tahun = list(range(2024, tahun_sekarang + 2))

    col_f1, col_f2 = st.columns(2)
    
    # Pilih Nama Bulan
    f_nama_bulan = col_f1.selectbox(
        "Filter Bulan", 
        options=daftar_bulan, 
        index=datetime.now().month - 1
    )
    
    # Pilih Tahun (Otomatis update tiap tahun)
    f_tahun = col_f2.selectbox(
        "Filter Tahun", 
        options=opsi_tahun, 
        index=opsi_tahun.index(tahun_sekarang)
    )

    # Konversi Nama Bulan ke Angka untuk kebutuhan Database (1-12)
    f_bulan = daftar_bulan.index(f_nama_bulan) + 1
    # --- FITUR HAPUS SEMUA DATA (TEMPEL DI SINI) ---
    st.markdown("---")
    with st.expander("🗑️ Zona Bahaya: Hanya Petugas Rekam Medis Yang Bisa Akses Ini"):
        st.error(f"PERINGATAN: Anda akan menghapus SELURUH file SKD periode {f_nama_bulan} {f_tahun}!")
        pwd_admin = st.text_input("Masukkan Password Admin", type="password", key="pwd_del_all")
        
        if st.button("KONFIRMASI HAPUS SEMUA DATA", type="primary"):
            if pwd_admin == "admin123": # Ganti password sesuai keinginan
                try:
                    with get_connection() as conn:
                        conn.execute("DELETE FROM skd_files WHERE bulan_skd=? AND tahun_skd=?", (f_bulan, f_tahun))
                        conn.commit()
                    st.success(f"Berhasil! Data periode {f_nama_bulan} {f_tahun} telah dibersihkan.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menghapus: {e}")
            else:
                st.error("Password Salah!")

    # 3. Ambil Daftar Departemen (Folder) DAN Hitung Jumlah File
    try:
        with get_connection() as conn:
            # Ambil daftar folder
            df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
            daftar_folder = df_dept['nama'].tolist()
            
            # Hitung jumlah file per departemen untuk periode terpilih agar lebih efisien
            df_counts = pd.read_sql_query(
                "SELECT departemen, COUNT(*) as total FROM skd_files WHERE bulan_skd=? AND tahun_skd=? GROUP BY departemen", 
                conn, params=(f_bulan, f_tahun)
            )
            # Buat dictionary agar mudah diakses: {'NAMA_DEPT': jumlah}
            count_map = dict(zip(df_counts['departemen'], df_counts['total']))
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]
        count_map = {}

    st.write("### Pilih Departemen:")
    cols = st.columns(4)
    for idx, d in enumerate(daftar_folder):
        # Ambil jumlah, jika tidak ada file anggap 0
        jumlah = count_map.get(d, 0)
        if cols[idx % 4].button(f"📂 {d} ({jumlah})", width="stretch", key=f"fldr_{d}_{idx}"):
            st.session_state['sel_dept'] = d
            st.rerun()

    # 4. Tampilkan Isi Folder Jika Sudah Dipilih
    if 'sel_dept' in st.session_state:
        # Baris 488: Semua kode di bawah ini HARUS menjorok ke dalam
        st.divider() 
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target} ({f_bulan}/{f_tahun})")
    
       # Form Upload (Bagian yang sudah ditambahkan saringan double upload)
        with st.expander("➕ Upload PDF Baru"):
            with st.form("upload_skd_form", clear_on_submit=True):
                u_files = st.file_uploader("Pilih PDF", type=['pdf'], accept_multiple_files=True)
            
                if st.form_submit_button("Simpan Ke Folder"):
                    if u_files:
                        try:
                            files_saved = 0
                            files_skipped = []
                            
                            with get_connection() as conn:
                                for u_f in u_files:
                                    # --- PROSES SARINGAN ---
                                    # Cek apakah file dengan nama yang sama sudah ada di departemen & periode ini
                                    check_q = """
                                        SELECT COUNT(*) FROM skd_files 
                                        WHERE nama_file = ? AND departemen = ? AND bulan_skd = ? AND tahun_skd = ?
                                    """
                                    exists = conn.execute(check_q, (u_f.name, target, f_bulan, f_tahun)).fetchone()[0]
                                    
                                    if exists > 0:
                                        files_skipped.append(u_f.name)
                                        continue # Skip file ini, lanjut ke file berikutnya
                                    
                                    # Jika lolos saringan, baru simpan
                                    file_content = u_f.read()
                                    conn.execute("""
                                        INSERT INTO skd_files 
                                        (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) 
                                        VALUES (?,?,?,?,?,?,?)""", 
                                        (u_f.name, target, u_f.name, file_content, 
                                         datetime.now(pytz.timezone('Asia/Jayapura')).strftime("%Y-%m-%d %H:%M:%S"), 
                                         f_bulan, f_tahun))
                                    files_saved += 1
                                
                                conn.commit()

                            # Pesan feedback untuk user
                            if files_saved > 0:
                                st.success(f"Berhasil menyimpan {files_saved} file baru!")
                            
                            if files_skipped:
                                st.warning(f"Saringan: {len(files_skipped)} file tidak diupload karena sudah ada: {', '.join(files_skipped)}")
                            
                            if files_saved > 0:
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Silakan pilih file terlebih dahulu.")

        # --- BAGIAN PENCARIAN & DAFTAR (PAGINATION + NOMOR) ---
        st.write("### 📂 Daftar File:")

        # 1. Setup Pagination State (OPTIMASI: Diubah menjadi 100 data per layar utama)
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        items_per_page = 100

        search_q = st.text_input("🔍 Cari Nama Pasien...", placeholder="Ketik nama untuk mencari...", key="search_skd_final")

        # Reset ke halaman 1 jika user mengubah pencarian
        if 'last_search' not in st.session_state:
            st.session_state.last_search = search_q
        if search_q != st.session_state.last_search:
            st.session_state.current_page = 1
            st.session_state.last_search = search_q

        with get_connection() as conn:
            # 2. Siapkan filter query menggunakan parameter aman (?)
            conditions = ["departemen = ?", "bulan_skd = ?", "tahun_skd = ?"]
            params = [target, f_bulan, f_tahun]
            
            if search_q:
                conditions.append("nama_pasien LIKE ?")
                params.append(f"%{search_q}%")
            
            filter_clause = "WHERE " + " AND ".join(conditions)
            
            # 3. Hitung total data (Sangat cepat di SQLite)
            count_query = f"SELECT COUNT(*) FROM skd_files {filter_clause}"
            total_records = conn.execute(count_query, tuple(params)).fetchone()[0]
            total_pages = max(1, (total_records // items_per_page) + (1 if total_records % items_per_page > 0 else 0))

            # --- KOTAK INFORMASI UTAMA DENGAN TULISAN BESAR (MUDAH DIBACA DOKTER) ---
            st.markdown(f"""
                <div style="background-color: #EBF5FB; padding: 18px; border-radius: 8px; border-left: 6px solid #2980B9; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #1B4F72; font-size: 24px; font-weight: bold;">📊 Total Arsip Terdata: {total_records} Pasien</h2>
                    <p style="margin: 8px 0 0 0; color: #2C3E50; font-size: 16px; line-height: 1.5;">
                        Layar utama dibatasi menampilkan <b>{items_per_page} data terbaru</b> per halaman agar aplikasi tetap cepat. <br>
                        Data lama tidak hilang, Anda dapat mencarinya kapan saja menggunakan kolom <b>Cari Nama Pasien</b> di atas.
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # 4. Tampilkan Navigasi (Sistem Grup Angka Dinamis)
            nav1, nav2, nav3 = st.columns([1, 4, 1])
            
            with nav1:
                if st.button("⬅️ Sebelumnya", disabled=(st.session_state.current_page == 1), width="stretch"):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with nav2:
                # Tentukan ukuran grup tombol navigasi angka
                group_size = 5
                
                # Hitung angka awal dan akhir untuk grup halaman saat ini
                start_page = ((st.session_state.current_page - 1) // group_size) * group_size + 1
                end_page = min(start_page + group_size - 1, total_pages)
                
                # Buat kolom sebanyak jumlah angka yang akan tampil di grup ini
                num_buttons = end_page - start_page + 1
                cols_angka = st.columns(num_buttons) 
                
                for i, col_hal in enumerate(cols_angka):
                    page_num = start_page + i
                    # Indikator halaman aktif: Bold dan tombol tipe Primary
                    label_hal = f"**{page_num}**" if page_num == st.session_state.current_page else str(page_num)
                    type_button = "primary" if page_num == st.session_state.current_page else "secondary"
                    
                    if col_hal.button(label_hal, key=f"btn_page_{page_num}", type=type_button, width="stretch"):
                        st.session_state.current_page = page_num
                        st.rerun()
                
                # Info tambahan posisi halaman berukuran tebal
                st.markdown(f"<p style='text-align: center; font-size: 15px; font-weight: bold; color: #34495E; margin-top: 5px;'>Halaman {st.session_state.current_page} dari {total_pages}</p>", unsafe_allow_html=True)

            with nav3:
                if st.button("Selanjutnya ➡️", disabled=(st.session_state.current_page == total_pages), width="stretch"):
                    st.session_state.current_page += 1
                    st.rerun()

            # 5. Ambil Data (OPTIMASI LAZY LOADING: Hanya ambil teks ringkas, JANGAN ambil data biner 'file_data')
            offset = (st.session_state.current_page - 1) * items_per_page
            query = f"SELECT id, nama_pasien, departemen, nama_file, tgl_upload, bulan_skd, tahun_skd FROM skd_files {filter_clause} ORDER BY tgl_upload DESC LIMIT {items_per_page} OFFSET {offset}"
            files = pd.read_sql(query, conn, params=tuple(params))

            # 6. Tampilkan Daftar (PAKSA WARNA PUTIH TERANG UNTUK TEMA GELAP)
            if not files.empty:
                for i, r in files.iterrows():
                    # Perhitungan nomor urut pasien
                    nomor = ((st.session_state.current_page - 1) * items_per_page) + (i + 1)
                    
                    # Layout Kolom didalam container
                    with st.container(border=True):
                        c_no_name, c_tgl, c_v, c_d, c_x = st.columns([4, 1.5, 1, 1, 0.5])
                        
                        # SOLUSI MUTLAK: color: #FFFFFF !important memaksa teks menjadi putih terang benderang
                        c_no_name.markdown(f"""
                            <div style="line-height: 1.6; padding: 5px;">
                                <span style="font-size: 20px; font-weight: bold; color: #FFFFFF !important;">{nomor}. 👤 {r['nama_pasien']}</span> 
                                <span style="font-size: 14px; color: #5DADE2; font-weight: bold; margin-left: 5px;">({r['departemen']})</span><br>
                                <span style="font-size: 15px; color: #EAEDED !important;">📄 File: {r['nama_file']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Tanggal dibuat putih abu agar tetap terbaca jelas
                        c_tgl.markdown(f"""
                            <div style="margin-top: 12px; font-size: 14px; font-weight: bold; color: #BDC3C7 !important;">
                                📅 {str(r['tgl_upload'])[:16]}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Tombol Lihat Pratinjau
                        if c_v.button("👁️ Lihat", key=f"v_btn_{r['id']}", width="stretch"):
                            if st.session_state.get('view_id') == r['id']:
                                st.session_state['view_id'] = None
                            else:
                                st.session_state['view_id'] = r['id']
                            st.rerun()
                        
                        # LAZY LOADING: Ambil biner file_data dari database HANYA saat pratinjau aktif ATAU tombol unduh diklik
                        file_binary = None
                        if st.session_state.get('view_id') == r['id'] or c_d.button("📥 Ambil", key=f"btn_dl_init_{r['id']}", width="stretch"):
                            with get_connection() as conn_lazy:
                                res_file = conn_lazy.execute("SELECT file_data FROM skd_files WHERE id = ?", (r['id'],)).fetchone()
                                if res_file:
                                    file_binary = res_file[0]
                        
                        # Jika file biner sudah ditarik, tampilkan tombol download yang asli
                        if file_binary and st.session_state.get('view_id') != r['id']:
                            c_d.download_button("💾 Simpan", data=file_binary, file_name=r['nama_file'], mime='application/pdf', key=f"dl_d_{r['id']}")
                        
                        # Tombol Hapus Data
                        if c_x.button("🗑️", key=f"del_btn_{r['id']}"):
                            with get_connection() as conn_del:
                                cur = conn_del.cursor()
                                cur.execute("DELETE FROM skd_files WHERE id=?", (r['id'],))
                                conn_del.commit()
                            st.rerun()

                        # Area Tampilan Kontainer Pratinjau PDF
                        if st.session_state.get('view_id') == r['id'] and file_binary:
                            with st.container(border=True):
                                st.info(f"Melihat SKD Pasien: {r['nama_pasien']}")
                                tampilkan_pdf_base64(file_binary)
                                if st.button("❌ Tutup Pratinjau", key=f"close_{r['id']}"):
                                    st.session_state['view_id'] = None
                                    st.rerun()
            else:
                st.info("Tidak ada file ditemukan.")
# --- MENU PENGATURAN MASTER ---
elif menu == "Pengaturan Master / 设置":
    
    t1, t2, t3 = st.tabs(["🏢 Master List", "🛠 Fitur Pendaftaran", "👥 Manajemen Akun"])
    
  # --- TAB 1: MASTER LIST (REVISI FINAL) ---
    with t1:
        st.subheader("Data Master")
        # Kita beri key unik agar tidak tertukar cache
        kat_pilihan = st.selectbox("Pilih Kategori", ["Perusahaan", "Departemen", "Jabatan"], key="kat_master_box")
        
        c_input, c_list = st.columns([1, 2])
        
        with c_input:
            nama_baru = st.text_input(f"Tambah {kat_pilihan} Baru", key="input_nama_master")
            if st.button("Simpan Data", key="simpan_btn"):
                if nama_baru:
                    bersih = nama_baru.strip().upper()
                    with get_connection() as conn:
                        # CEK: Apakah nama ini sudah ada di kategori manapun?
                        cek_data = conn.execute("SELECT kategori FROM master_data WHERE nama = ?", (bersih,)).fetchone()
                        
                        if cek_data:
                            # Ini akan memberi tahu Anda jika data ternyata masuk ke kategori lain
                            st.warning(f"⚠️ {bersih} sudah ada di kategori: {cek_data[0]}!")
                        else:
                            conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kat_pilihan, bersih))
                            conn.commit()
                            st.success(f"✅ {bersih} berhasil disimpan!")
                            st.rerun()
                else:
                    st.warning("Silakan isi nama terlebih dahulu.")

        with c_list:
            st.write(f"**Daftar {kat_pilihan} Aktif:**")
            # AMBIL DATA LANGSUNG (Tanpa Fungsi get_master agar tidak kena cache)
            with get_connection() as conn:
                df_res = pd.read_sql("SELECT id, nama FROM master_data WHERE kategori = ?", conn, params=(kat_pilihan,))
            
            if not df_res.empty:
                for idx, row in df_res.iterrows():
                    ca, cb = st.columns([4, 1])
                    ca.info(f"📍 {row['nama']}")
                    if cb.button("Hapus", key=f"del_master_{row['id']}"):
                        with get_connection() as conn:
                            conn.execute("DELETE FROM master_data WHERE id = ?", (row['id'],))
                            conn.commit()
                        st.rerun()
            else:
                st.info(f"Belum ada data untuk {kat_pilihan}.")

    # --- TAB 2: FITUR PENDAFTARAN ---
    with t2:
        st.subheader("Kustomisasi Form Pendaftaran")
        st.info("Tambahkan kolom input tambahan (misal: Suku, Agama, No. HP) yang akan muncul di form pendaftaran.")
        c_i2, c_l2 = st.columns([1, 2])
        with c_i2:
            f_baru = st.text_input("Nama Kolom Baru")
            if st.button("Simpan Fitur", key="btn_add_fitur"):
                if f_baru:
                    f_clean = f_baru.strip().upper()
                    with get_connection() as conn:
                        cek_f = conn.execute("SELECT 1 FROM master_data WHERE kategori='Fitur Pendaftaran' AND nama=?", (f_clean,)).fetchone()
                        if not cek_f:
                            conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Fitur Pendaftaran", f_clean))
                            conn.commit()
                            st.success("✅ Kolom ditambahkan")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.warning("Fitur sudah ada!")
        with c_l2:
            df_f = get_master("Fitur Pendaftaran")
            for i, r in df_f.iterrows():
                ca, cb = st.columns([4, 1])
                ca.text(f"⚙️ {r['nama']}")
                if cb.button("Hapus", key=f"fit_del_{r['id']}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],))
                        conn.commit()
                    st.cache_data.clear()
                    st.rerun()

    # --- TAB 3: MANAJEMEN AKUN ---
    with t3:
        st.subheader("Manajemen Akser User")
        with st.form("tambah_user_form"):
            un = st.text_input("Username")
            up = st.text_input("Password", type="password")
            ur = st.selectbox("Role", ["Admin", "Staff"])
            if st.form_submit_button("Daftarkan Akun"):
                if un and up:
                    try:
                        with get_connection() as conn:
                            conn.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (un, up, ur))
                            conn.commit()
                        st.success(f"Akun {un} berhasil dibuat!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {un} mungkin sudah terdaftar.")
                else:
                    st.warning("Lengkapi data!")

        st.divider()
        st.write("### Daftar Akun Tim")
        with get_connection() as conn:
            u_df = pd.read_sql("SELECT username, role FROM users", conn)
        
        for i, row in u_df.iterrows():
            if row['username'] != 'admin': # Admin utama tidak bisa dihapus
                cx, cy = st.columns([4, 1])
                cx.text(f"👤 {row['username']} ({row['role']})")
                if cy.button("Hapus", key=f"u_del_{row['username']}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM users WHERE username=?", (row['username'],))
                        conn.commit()
                    st.rerun()
elif menu == "Dashboard Analitik":
    st.header("📊 Analisis Data Kunjungan Pasien")
    
    # --- 1. FILTER PERIODE SHIFT (Sudah Menjorok ke Dalam) ---
    with st.container(border=True):
        st.subheader("⏱️ Pilih Waktu Laporan")
        col_shift, col_tgl = st.columns([1, 2])
        
        with col_shift:
            shift = st.radio(
                "Pilih Shift:", 
                [
                    "Pagi (07:00 - 18:00)", 
                    "Jam Malam (1) 18:00 - 22:00", 
                    "Jam Malam (2) 22:00 - 06:00",
                    "Malam Full (18:00 - 07:00)"
                ], 
                horizontal=False
            )
            
        with col_tgl:
            tgl_laporan = st.date_input("📅 Tanggal Laporan", datetime.now())

        # --- Logika Jam & Rentang Data ---
        if "Pagi" in shift:
            j1, j2 = "07:00:00", "18:00:00"
            t1, t2 = tgl_laporan, tgl_laporan
        elif "(1)" in shift:
            j1, j2 = "18:00:00", "22:00:00"
            t1, t2 = tgl_laporan, tgl_laporan
        elif "(2)" in shift:
            j1, j2 = "22:00:01", "06:00:00"
            t1, t2 = tgl_laporan, tgl_laporan + timedelta(days=1)
        else:
            j1, j2 = "18:00:00", "07:00:00"
            t1, t2 = tgl_laporan, tgl_laporan + timedelta(days=1)

        dt_mulai, dt_selesai = f"{t1} {j1}", f"{t2} {j2}"
        st.caption(f"🔎 Rentang Data: **{dt_mulai}** s/d **{dt_selesai}**")

    # --- 2. AMBIL DATA ---
    with get_connection() as conn:
        df_dash = pd.read_sql("SELECT * FROM pasien WHERE tgl_daftar BETWEEN ? AND ?", conn, params=(dt_mulai, dt_selesai))

    if not df_dash.empty:
        # --- 3. PROSES DATA ---
        df_dash['jk'] = df_dash['jenis_kunjungan'].fillna('').astype(str).str.upper()
        df_dash['pb'] = df_dash['pernah_berobat'].fillna('').astype(str).str.upper()

        df_dash['Berobat'] = df_dash['jk'].apply(lambda x: 1 if x == 'BEROBAT' else 0)
        list_k = ['KONTROL', 'RAWAT LUKA', 'POST', 'MCU']
        df_dash['Pasien Kontrol'] = df_dash['jk'].apply(lambda x: 1 if any(k in x for k in list_k) else 0)
        df_dash['UGD'] = df_dash['jk'].apply(lambda x: 1 if 'UGD' in x else 0)
        df_dash['Baru'] = df_dash['pb'].apply(lambda x: 1 if 'BELUM' in x else 0)
        df_dash['Lama'] = df_dash['pb'].apply(lambda x: 1 if 'IYA' in x or 'SUDAH' in x else 0)

        # --- 4. TAMPILKAN METRICS ---
        st.subheader(f"📌 Ringkasan Shift {'Pagi' if 'Pagi' in shift else 'Malam'}")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Pasien", len(df_dash))
        m2.metric("Berobat", int(df_dash['Berobat'].sum()))
        m3.metric("Kontrol", int(df_dash['Pasien Kontrol'].sum()))
        m4.metric("Masuk UGD", int(df_dash['UGD'].sum()))
        m5.metric("Pasien Baru", int(df_dash['Baru'].sum()))
        m6.metric("Pasien Lama", int(df_dash['Lama'].sum()))

        st.divider()

        # --- 5. TABEL RINCIAN ---
        st.subheader("📋 Rincian Departemen & Perusahaan")
        summary = df_dash.groupby(['perusahaan', 'departemen']).agg({
            'Baru': 'sum', 'Lama': 'sum', 'Berobat': 'sum', 'Pasien Kontrol': 'sum', 'UGD': 'sum'
        }).reset_index()
        summary['Total'] = summary[['Berobat', 'Pasien Kontrol', 'UGD']].sum(axis=1)
        st.dataframe(summary.sort_values('Total', ascending=False), width="stretch", hide_index=True)

        # --- 6. GRAFIK ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏢 Per Perusahaan")
            pt_data = df_dash.groupby('perusahaan').size().reset_index(name='Jml')
            st.bar_chart(pt_data.set_index('perusahaan'))
        with c2:
            st.subheader("📁 Per Departemen")
            dept_data = df_dash.groupby('departemen').size().reset_index(name='Jml')
            st.bar_chart(dept_data.set_index('departemen'))
    else:
        st.warning(f"⚠️ Tidak ada data pendaftaran untuk shift ini.")

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="
        background-color: #FDF5E6; 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 5px solid #8B4513; 
        font-family: 'Times New Roman', Times, serif;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    ">
        <p style="margin: 0; font-size: 12px; color: #666;">© 2026 Copyright:</p>
        <p style="margin: 5px 0; font-size: 15px; font-weight: bold; color: #2F4F4F;">
            👨‍⚕️ Alhatma, A.Md. RMIK
        </p>
        <p style="margin: 0; font-size: 11px; line-height: 1.4; color: #555; font-style: italic;">
            "Aplikasi ini dibuat secara khusus. Dilarang keras menyalahgunakan sistem ini."
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
