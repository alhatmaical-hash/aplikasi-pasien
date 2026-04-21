import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime
import io
import pytz
import base64
from datetime import datetime, time, timedelta


# --- TEMPEL DI SINI ---
def tampilkan_pdf_base64(file_data):
    """Fungsi untuk menampilkan PDF tanpa menyebabkan MediaFileStorageError"""
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
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_connection():
    # Ini akan menyimpan database di folder yang sama dengan file kodingan Anda
    path_database = "klinik_data.db"
    # check_same_thread=False wajib untuk Streamlit
    conn = sqlite3.connect(path_database, check_same_thread=False)
    # Aktifkan WAL mode untuk performa lebih baik
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_db():
    conn = get_connection() # Ambil koneksi dari cache
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
    kolom_tambahan = [
        ("no_hp", "TEXT"), ("agama", "TEXT"), ("dokter", "TEXT"),
        ("gender", "TEXT"), ("blok_mes", "TEXT"), ("tgl_lahir", "TEXT"),
        ("alergi", "TEXT"), ("gol_darah", "TEXT"), ("lokasi_kerja", "TEXT"),
        ("lokasi_mcu", "TEXT"), ("is_authorized", "INTEGER DEFAULT 0"),
        ("jenis_kunjungan", "TEXT")
    ]
    
    for kolom, tipe in kolom_tambahan:
        try:
            c.execute(f"ALTER TABLE pasien ADD COLUMN {kolom} {tipe}")
        except:

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
    
    conn.commit() # Simpan semua perubahan di akhir
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
        page_mode = st.sidebar.radio("Navigasi", ["Login Staff", "Form Pendaftaran"])

        if page_mode == "Form Pendaftaran":
            menu = "Pendaftaran / 登记"
        else:
            st.markdown("<h2 style='text-align: center;'>🔐 Login Klinik Apps</h2>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                user = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.button("Login"):
                    conn = get_connection()
                    res = conn.execute("SELECT username, role FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
                    if res:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = res[0]
                        st.session_state['role'] = res[1]
                        st.rerun()
                    else:
                        st.error("Username atau Password salah")
            st.stop()
# --- 5. LOGIKA HALAMAN ---

# --- MENU PENDAFTARAN (Admin & Publik) ---
if menu in ["Pendaftaran Pasien", "Pendaftaran / 登记"]:
    st.header("📝 PENDAFTARAN PASIEN CUKUP SATU KALI DAFTAR TIDAK USAH BERKALI2")
    
    # --- TEMPEL DI SINI ---
    # Ambil data dokter dari session_state yang diisi di menu Rekam Medis
    dokter_jaga = st.session_state.get('dokter_jaga_aktif', [])

    dokter_terpilih = "Belum Ditentukan"
    conn = get_connection()
        try:
            df_dr = pd.read_sql("SELECT nama_dokter FROM dokter_jaga_harian", conn)
            dokter_jaga = df_dr['nama_dokter'].tolist()
        except:
            dokter_jaga = []

    dokter_terpilih = "Belum Ditentukan"
    if dokter_jaga:
        conn = get_connection()
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
        st.error("⚠️ Sistem pendaftaran belum siap (Dokter jaga belum diatur). Silakan hubungi petugas klinik.")
        st.stop()

    # --- LANJUTAN KODE ASLI ANDA ---
    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()
    custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

    # Pastikan teks di sini SAMA PERSIS dengan yang di dalam IF nanti
    pernah = st.radio("PERNAH BEROBAT DISINI? / 您以前在这里看过病吗？", ["Iya Sudah / 是的", "Belum Pernah / 从未"], horizontal=True)
    with st.form("form_reg", clear_on_submit=False):
        # Ambil data langsung dari database master
        opts_perusahaan = [""] + get_master("Perusahaan")['nama'].tolist()
        opts_dept = [""] + get_master("Departemen")['nama'].tolist()
        opts_jabatan = [""] + get_master("Jabatan")['nama'].tolist()
        # PERBAIKAN: Menggunakan pengecekan teks yang tepat
        if pernah == "Iya Sudah / 是的": # Teks ini harus COPAS persis dari radio button di atas
            st.subheader("📌 Form Pasien Lama (Ringkas)")
            col1, col2 = st.columns(2)
            with col1:
                jenis_kunjungan = st.selectbox("Jenis Kunjungan", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名 *", value=st.session_state.nama_lengkap)
                no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码 *", value=st.session_state.no_hp)
                nik = st.text_input("NIK ID Card Perusahaan / 身份证号 *", value=st.session_state.nik)
                agama = st.selectbox("Agama / 宗教", ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"])
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
                gol_darah = st.selectbox("Golongan Darah / 血型", ["A", "B", "AB", "O", "-"])
            
            with col4:
                lokasi_mcu = st.selectbox("Lokasi MCU Pertama Kali", ["Klinik HJF", "Klinik HPAL", "Klinik Luar Obi"])
                lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik / 具体工作地点 *", value=st.session_state.lokasi_kerja)
            st.subheader("📋 Informasi Tambahan / 附加信息")
            responses = {field: st.text_input(f"{field.upper()}") for field in custom_fields}
            

        else:
            st.subheader("📑 Form Pasien Baru (Lengkap)")
            col1, col2 = st.columns(2)
            with col1:
                jenis_kunjungan = st.selectbox("Jenis Kunjungan", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名 *", value=st.session_state.nama_lengkap)
                no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码 *", value=st.session_state.no_hp)
                nik = st.text_input("NIK ID Card Perusahaan / 身份证号 *", value=st.session_state.nik)
                agama = st.selectbox("Agama / 宗教", ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"])
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
                gol_darah = st.selectbox("Golongan Darah / 血型", ["A", "B", "AB", "O", "-"])
            
            with col4:
                lokasi_mcu = st.selectbox("Lokasi MCU Pertama Kali", ["Klinik HJF", "Klinik HPAL", "Klinik Luar Obi"])
                lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik / 具体工作地点 *", value=st.session_state.lokasi_kerja)
            
            st.subheader("📋 Informasi Tambahan / 附加信息")
            responses = {field: st.text_input(f"{field.upper()}") for field in custom_fields}
        
        submit_btn = st.form_submit_button("KIRIM PENDAFTARAN / 提交登记")
        
        if submit_btn:
            # 1. Kunci agar tidak double click
            if st.session_state.get('proses_simpan', False):
                st.stop()
            st.session_state['proses_simpan'] = True

            # 2. Definisikan required fields (DITAMBAHKAN SEMUA YANG BERTANDA *)
            # Kita buat daftar kolom wajib agar blok_mes dll tidak bisa dikosongkan
            if pernah == "Iya Sudah / 是的": 
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
                    "Area Kerja": lokasi_kerja
                }
            else:
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
                    "Area Kerja": lokasi_kerja
                }
            
            # Cek apakah ada yang kosong (termasuk None untuk tanggal dan [] untuk multiselect)
            empty_fields = [k for k, v in required.items() if str(v).strip() in ["", "None", "[]"] or v is None]

            if empty_fields:
                st.error(f"⚠️ Gagal! Kolom berikut wajib diisi: {', '.join(empty_fields)}")
                st.session_state['proses_simpan'] = False
                st.stop() # Berhenti di sini jika ada yang kosong

            # 3. Jika TIDAK ADA yang kosong, baru lanjut ke proses database
            if not empty_fields:
                try:
                    tz_wit = pytz.timezone('Asia/Jayapura')
                    waktu_sekarang = datetime.now(tz_wit)
                    tgl_hari_ini = waktu_sekarang.strftime("%Y-%m-%d")

                    conn = get_connection()
                        # --- LANJUTKAN KODE DATABASE ANDA DI SINI ---
                        
                        # A. Cek Double Input
                        check_query = "SELECT is_authorized FROM pasien WHERE nik = ? AND tgl_daftar LIKE ? ORDER BY id DESC LIMIT 1"
                        existing_data = conn.execute(check_query, (nik, f"{tgl_hari_ini}%")).fetchone()

                        if existing_data:
                            auth_status = existing_data[0]
                            if auth_status == 0 or auth_status is None:
                                st.error(f"⚠️ NIK {nik} sudah terdaftar...")
                                st.session_state['proses_simpan'] = False
                                st.stop()
                            else:
                                st.info("ℹ️ Pendaftaran ulang diizinkan oleh Admin.")

                        # B. Hitung Antrian (Round Robin)
                        query_count = "SELECT COUNT(*) FROM pasien WHERE tgl_daftar LIKE ?"
                        jml_pasien = conn.execute(query_count, (f"{tgl_hari_ini}%",)).fetchone()[0]
                        
                        if dokter_jaga:
                            idx_dokter = (jml_pasien // 5) % len(dokter_jaga)
                            dokter_final = dokter_jaga[idx_dokter]
                        else:
                            dokter_final = "Belum Ada Dokter"

                        # C. Proses Simpan (INSERT)
                        cur = conn.cursor()
                        # ... jalankan cur.execute pendaftaran Anda di sini menggunakan dokter_final ...
                        conn.commit()
                        # --- BATAS AKHIR BLOK WITH ---

                    # D. Finishing (Di luar with)
                    st.success(f"✅ Berhasil! Dokter Anda: {dokter_final}")
                    st.cache_data.clear()
                    # --- END FITUR BARU ---

                    # Persiapan Data
                    tgl_str = tgl_lahir_val.strftime("%d-%m-%Y") if tgl_lahir_val else ""
                    tgl_gabung = f"{tmpt_lahir}, {tgl_str}"
                    
                    conn = get_connection()
                        cur = conn.cursor()
                        # Update INSERT dengan kolom is_authorized (Ada 19 kolom & 19 tanda tanya)
                        cur.execute('''INSERT INTO pasien (
                                            tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, 
                                            departemen, jabatan, no_hp, agama, gender, 
                                            blok_mes, tgl_lahir, alergi, gol_darah, lokasi_kerja, 
                                            lokasi_mcu, status_antrian, dokter, is_authorized, jenis_kunjungan)
                                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                       (waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S"), nama_lengkap, nik, pernah, perusahaan, dept, jabatan, 
                                        no_hp, agama, gender, blok_mes, tgl_gabung, str(alergi), gol_darah, lokasi_kerja, lokasi_mcu, "Normal", dokter_terpilih, 0, jenis_kunjungan))
                        
                        last_id = cur.lastrowid
                        for f_name, f_val in responses.items():
                            cur.execute("INSERT INTO pasien_custom_data (pasien_id, field_name, field_value) VALUES (?,?,?)", (last_id, f_name, f_val))
                        conn.commit()

                    st.success(f"✅ Pendaftaran Sukses Dikirim! \n\n Silakan ke: **{dokter_terpilih}**")
                    st.balloons()
                    st.cache_data.clear()
                    
                    # Reset Form
                    for key in ['nama_lengkap', 'nik', 'no_hp', 'blok_mes', 'tgl_lahir', 'lokasi_kerja']:
                        st.session_state[key] = ""
                    
                    import time
                    time.sleep(2)
                    st.session_state['proses_simpan'] = False 
                    st.rerun()

                except Exception as e:
                    st.session_state['proses_simpan'] = False 
                    st.error(f"Gagal menyimpan: {e}")
            else:
                # Jika ada kolom kosong
                st.session_state['proses_simpan'] = False 
                kolom_kosong = ", ".join(empty_fields)
                st.warning(f"⚠️ Mohon lengkapi kolom: **{kolom_kosong}**")
  
# --- MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    # 1. Pastikan layout lebar agar tabel tidak terpotong (Tambahkan ini di paling atas file jika belum ada)
    # st.set_page_config(layout="wide") 

    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="datarefresh") # Refresh tiap 5 detik
    
    st.header("📊 Menu Rekam Medis")

    # --- BAGIAN 1: ATUR DOKTER JAGA ---
    with st.expander("👨‍⚕️ Atur Dokter Jaga Hari Ini", expanded=False):
        opts_dr_raw = get_master("Dokter")['nama'].tolist()
        opts_dr = sorted(list(set(opts_dr_raw)))
        conn = get_connection()
            try:
                dr_aktif_db = pd.read_sql("SELECT nama_dokter FROM dokter_jaga_harian", conn)['nama_dokter'].tolist()
            except:
                dr_aktif_db = []
        pilihan = st.multiselect("Pilih Dokter yang Bertugas", opts_dr, default=dr_aktif_db, placeholder="Pilih dokter...")
        if st.button("Simpan Jadwal Dokter"):
            conn = get_connection()
                conn.execute("DELETE FROM dokter_jaga_harian")
                for dr in pilihan:
                    conn.execute("INSERT INTO dokter_jaga_harian (nama_dokter) VALUES (?)", (dr,))
                conn.commit()
            st.success("Jadwal Berhasil Disimpan!")
            st.rerun()

    # --- BAGIAN 2: OTORISASI DAFTAR ULANG ---
    with st.expander("🔐 Otorisasi Daftar Ulang"):
        st.info("Gunakan fitur ini untuk memberi izin pendaftaran ulang kepada NIK yang sudah terdaftar hari ini.")
        nik_izin = st.text_input("Masukkan NIK Pasien yang ingin diberi izin")
        if st.button("Berikan Izin Akses"):
            if nik_izin:
                conn = get_connection()
                    tz_wit = pytz.timezone('Asia/Jayapura')
                    tgl_skrg = datetime.now(tz_wit).strftime("%Y-%m-%d")
                    conn.execute("UPDATE pasien SET is_authorized = 1 WHERE nik = ? AND tgl_daftar LIKE ?", (nik_izin, f"{tgl_skrg}%"))
                    conn.commit()
                st.success(f"Berhasil! NIK {nik_izin} sekarang diizinkan mendaftar ulang.")
            else:
                st.warning("Silakan masukkan NIK terlebih dahulu.")

    # --- BAGIAN 3: TABEL ANTRIAN (VERSI AUTO-RESET BULANAN) ---
    st.write("---")
    st.subheader("📋 Daftar Antrian Pasien")
    
    # 1. DEFINISIKAN FUNGSI WARNA
    def color_row(row):
        status = row.get('status_antrian', '')
        if status == "Menunggu Konsul Dokter": 
            return ['background-color: #ffff00; color: black'] * len(row)
        elif status == "Menunggu Hasil Lab & Radiologi": 
            return ['background-color: #00b0f0; color: white'] * len(row)
        elif status == "Batas Download SKD": 
            return ['background-color: #ff9900; color: white'] * len(row)
        elif status == "Batas Operan & Daftar Pasien": 
            return ['background-color: #c8e6c9; color: black'] * len(row)
        elif status == "Batal Berobat": 
            return ['background-color: #ff4b4b; color: white'] * len(row)
        return [''] * len(row)

    # 2. FILTER LAYOUT
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1], gap="small")
    with col_f1:
        search_term = st.text_input("🔍 Cari Nama Pasien / 查找病人姓名", "", key="search_rekam_medis")
    with col_f2:
        list_bulan = ["Semua", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        bulan_sekarang = datetime.now().month
        bulan_selected = st.selectbox("Pilih Bulan", list_bulan, index=bulan_sekarang)
    with col_f3:
        list_tahun = ["Semua"] + [str(t) for t in range(2025, 2035)]
        tahun_sekarang = str(datetime.now().year)
        idx_tahun = list_tahun.index(tahun_sekarang) if tahun_sekarang in list_tahun else 0
        tahun_selected = st.selectbox("Pilih Tahun", list_tahun, index=idx_tahun)

    # 3. AMBIL DATA
    conn = get_connection()
        query = """
        SELECT id, tgl_daftar AS 'Tgl Daftar', jenis_kunjungan, nama_lengkap AS 'Nama Lengkap', 
               nik AS 'NIK/ID', no_hp AS 'WhatsApp', perusahaan AS 'Perusahaan', 
               departemen AS 'Departemen', jabatan AS 'Jabatan', pernah_berobat AS 'Status',
               agama AS 'Agama', dokter AS 'Dokter', gender AS 'Gender', tgl_lahir AS 'TTL',
               alergi AS 'Alergi', gol_darah AS 'Gol Darah', blok_mes AS 'Blok/Kamar',
               lokasi_kerja AS 'Area Kerja', lokasi_mcu AS 'Lokasi Mcu Pertama Kali', status_antrian
        FROM pasien ORDER BY id DESC
        """
        df = pd.read_sql(query, conn)

    if not df.empty:
        # 4. KONVERSI TANGGAL UNTUK FILTER
        df['tgl_dt'] = pd.to_datetime(df['Tgl Daftar'], errors='coerce')
        df_tampil = df.copy()

        # 5. EKSEKUSI FILTER
        if search_term:
            df_tampil = df_tampil[df_tampil['Nama Lengkap'].str.contains(search_term, case=False, na=False)]
        
        if bulan_selected != "Semua":
            idx_bulan = list_bulan.index(bulan_selected)
            df_tampil = df_tampil[df_tampil['tgl_dt'].dt.month == idx_bulan]
            
        if tahun_selected != "Semua":
            df_tampil = df_tampil[df_tampil['tgl_dt'].dt.year == int(tahun_selected)]

        # 6. TAMPILKAN TABEL
        st.dataframe(
            df_tampil.style.apply(color_row, axis=1), 
            width="stretch", 
            hide_index=True,
            column_config={
                "id": None, 
                "tgl_dt": None,
                "Tgl Daftar": st.column_config.DatetimeColumn("Tanggal", format="DD/MM/YY HH:mm"),
                "status_antrian": st.column_config.TextColumn("Status Antrian")
            }
        )
        st.caption(f"Menampilkan {len(df_tampil)} data untuk periode {bulan_selected} {tahun_selected}.")

        # --- 2. KOTAK KETERANGAN WARNA (LEGEND) ---
        st.markdown("### 📋 Keterangan Status")
        col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
        with col_k1:
            st.info("🟡 **Kuning**: Menunggu Konsul Dokter")
        with col_k2:
            st.info("🔵 **Biru**: Menunggu Hasil Lab & Radiologi")
        with col_k3:
            st.warning("🟠 **Orange**: Batas Download SKD")
        with col_k4:
            st.success("🟢 **Hijau**: Batas Operan & Daftar Pasien")
        with col_k5:
            st.error("🔴 Merah: Batal Berobat")

        # --- 3. FITUR UNDUH (CSV) ---
        csv = df_tampil.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv,
            file_name='data_rekam_medis.csv',
            mime='text/csv',
        )

        # --- FITUR EDIT / RENAME NAMA PASIEN ---
        st.divider()
        with st.expander("✏️ Edit / Rename Nama Pasien"):
            # PENTING: Gunakan df_tampil (data hasil filter pencarian) bukan df
            if not df_tampil.empty:
                with st.form("edit_nama_form_v2"):
                    st.info("Gunakan fitur ini untuk memperbaiki kesalahan penulisan nama.")
                    
                    # Kita gunakan df_tampil agar pilihannya sama dengan yang ada di tabel atas
                    opsi_edit = df_tampil.apply(lambda x: f"{x['id']} | {x['Nama Lengkap']}", axis=1).tolist()
                    data_terpilih = st.selectbox("Pilih Pasien yang akan diperbaiki namanya", opsi_edit)
                    
                    # Logika pecah ID dan Nama
                    id_target_edit = int(data_terpilih.split(" | ")[0])
                    nama_lama = data_terpilih.split(" | ")[1]
                    
                    nama_baru = st.text_input("Input Nama yang Benar", value=nama_lama)
                    
                    btn_rename = st.form_submit_button("Simpan Perubahan Nama")
                    
                    if btn_rename:
                        if not nama_baru.strip():
                            st.error("Nama tidak boleh kosong!")
                        else:
                            try:
                                conn = get_connection()
                                    cur = conn.cursor()
                                    # Gunakan .strip() agar tidak ada spasi tidak sengaja di awal/akhir
                                    cur.execute("UPDATE pasien SET nama_lengkap = ? WHERE id = ?", (nama_baru.strip(), id_target_edit))
                                    conn.commit()
                                    
                                st.success(f"Berhasil! Nama telah diubah menjadi '{nama_baru}'")
                                st.balloons()
                                # Rerun sangat penting agar tabel di atas langsung berubah namanya
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal memperbarui nama: {e}")
            else:
                st.warning("Cari nama pasien terlebih dahulu di kolom pencarian di atas agar muncul di sini.")

        # --- 4. FORM UPDATE STATUS ---
        st.divider()
        with st.expander("🔄 Ganti Status Pasien (Ubah Warna)"):
            with st.form("update_status_form"):
                # Daftar nama di sini akan otomatis ikut terfilter jika Anda mencari nama di atas
                nama_p = st.selectbox("Pilih Nama Pasien", df['Nama Lengkap'].tolist())
                status_baru = st.selectbox("Pilih Status Baru", [
                    "Normal", 
                    "Menunggu Konsul Dokter", 
                    "Menunggu Hasil Lab & Radiologi", 
                    "Batas Download SKD",
                    "Batas Operan & Daftar Pasien",
                    "Batal Berobat"
                ])
                btn_update = st.form_submit_button("Simpan Perubahan")
                
                if btn_update:
                    cur = conn.cursor()
                    cur.execute("UPDATE pasien SET status_antrian = ? WHERE nama_lengkap = ?", (status_baru, nama_p))
                    conn.commit()
                    st.success(f"Status {nama_p} berhasil diubah ke {status_baru}!")
                    st.rerun()


       # --- 5. FORM HAPUS DATA (DIPERBAIKI) ---
        st.divider()
        with st.expander("🗑️ Hapus Data Pasien"):
            with st.form("hapus_pasien_form"):
                st.warning("Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
                
                # Buat list pilihan yang unik (ID - Tanggal - Nama)
                # Ini agar kita tahu persis mana yang dihapus (misal ada 2 Alhatma di tgl berbeda)
                pilihan_hapus = df.apply(lambda x: f"{x['id']} | {x['Tgl Daftar']} | {x['Nama Lengkap']}", axis=1).tolist()
                
                selected_data = st.selectbox("Pilih Data Spesifik yang akan dihapus", pilihan_hapus)
                konfirmasi = st.checkbox(f"Saya yakin ingin menghapus data tersebut")
                
                btn_hapus = st.form_submit_button("Hapus Data Pasien")
                
                if btn_hapus:
                    if konfirmasi:
                        try:
                            # Ambil ID saja dari teks pilihan (angka paling depan)
                            id_target = int(selected_data.split(" | ")[0])
                            
                            conn = get_connection()
                                cur = conn.cursor()
                                # HAPUS BERDASARKAN ID (Bukan Nama)
                                cur.execute("DELETE FROM pasien WHERE id = ?", (id_target,))
                                conn.commit()
                                
                            st.success(f"Data dengan ID {id_target} telah berhasil dihapus.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menghapus data: {e}")
                    else:
                        st.error("Silakan centang kotak konfirmasi sebelum menghapus.")


       	# --- 6. FITUR CETAK FORMULIR OTOMATIS (VERSI PERBAIKAN BASE64) ---
        st.divider()
        with st.expander("🖨️ Cetak Formulir Pendaftaran Pasien"):
            st.info("Pilih pasien untuk membuat formulir otomatis dari data rekam medis.")
            
            # Gunakan st.form agar input lebih rapi
            with st.form("cetak_form_pendaftaran"):
                nama_p_cetak = st.selectbox("Pilih Pasien", df['Nama Lengkap'].tolist())
                petugas = st.selectbox("Pilih Petugas", ["TAUFIK", "WAWAN", "ALHATMA", "DELI"])
                btn_cetak = st.form_submit_button("Buat Formulir Sekarang")
                
                if btn_cetak:
                    from form_generator import buat_formulir_otomatis
                    try:
                        row = df[df['Nama Lengkap'] == nama_p_cetak].iloc[0]
                        data_pasien = {
                            "nama": row['Nama Lengkap'],
                            "tempat_lahir": row['TTL'].split(',')[0] if ',' in row['TTL'] else row['TTL'],
                            "tgl_lahir": row['TTL'].split(',')[1] if ',' in row['TTL'] else row['TTL'],
                            "gender": row.get('Gender', '-'),
                            "agama": row.get('Agama', '-'),
                            "no_hp": row.get('WhatsApp', '-'),
                            "nik": row['NIK/ID'],
                            "perusahaan": row['Perusahaan'],
                            "departemen": row['Departemen'],
                            "jabatan": row['Jabatan'],
                            "blok_mes": row.get('Blok/Kamar', '-'),
                            "alergi": row.get('Alergi', '-'),
                            "lokasi_kerja": row['Area Kerja'],
                            "gol_darah": row.get('Gol Darah', '-')
                        }
                        # Simpan hasil ke session_state agar tahan refresh
                        st.session_state['pdf_cetak_aktif'] = buat_formulir_otomatis(data_pasien, petugas)
                        st.session_state['nama_p_aktif'] = nama_p_cetak
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat mengambil data: {e}")

        # TAMPILKAN PDF (Diletakkan di luar expander/form agar muncul di layar)
        if 'pdf_cetak_aktif' in st.session_state:
            st.success(f"✅ Formulir untuk {st.session_state['nama_p_aktif']} siap!")
            
            c1, c2 = st.columns([1, 4])
            with c1:
                st.download_button(
                    label="📥 Download PDF",
                    data=st.session_state['pdf_cetak_aktif'],
                    file_name=f"Formulir_{st.session_state['nama_p_aktif'].replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
            with c2:
                if st.button("❌ Tutup Tampilan"):
                    del st.session_state['pdf_cetak_aktif']
                    st.rerun()

            # PANGGIL FUNGSI BASE64 UNTUK TAMPIL DI LAYAR
            tampilkan_pdf_base64(st.session_state['pdf_cetak_aktif'])


        # --- 7. FORM HAPUS SEMUA DATA (HANYA ADMIN) ---
        st.divider()
        with st.expander("🚨 Hapus Seluruh Database (Admin Only)"):
            st.error("PERINGATAN: Tindakan ini akan menghapus SELURUH data pasien tanpa kecuali!")
            
            # Input sandi admin
            input_sandi = st.text_input("Masukkan Sandi Admin", type="password", key="sandi_delete_all")
            
            # Checkbox konfirmasi tambahan agar tidak sengaja terpencet
            konfirmasi_total = st.checkbox("Saya benar-benar ingin menghapus SEMUA data di database")
            
            btn_hapus_semua = st.button("HAPUS SEMUA DATA SEKARANG", type="primary")
            
            if btn_hapus_semua:
                # Ganti 'admin123' dengan sandi yang Anda inginkan
                if input_sandi == "admin123": 
                    if konfirmasi_total:
                        try:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM pasien")
                            conn.commit()
                            st.success("Seluruh database berhasil dikosongkan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal mengosongkan data: {e}")
                    else:
                        st.warning("Silakan centang kotak konfirmasi terlebih dahulu.")
                else:
                    st.error("Sandi Admin salah! Akses ditolak.")

            else:
                st.info("Belum ada data pasien / 还没有病人数据。")
    
        conn.close()


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
                        conn = get_connection()
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
                    conn = get_connection()
                        conn.execute("DELETE FROM skd_files WHERE bulan_skd=? AND tahun_skd=?", (f_bulan, f_tahun))
                        conn.commit()
                    st.success(f"Berhasil! Data periode {f_nama_bulan} {f_tahun} telah dibersihkan.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menghapus: {e}")
            else:
                st.error("Password Salah!")

    # 3. Ambil Daftar Departemen (Folder)
    try:
        # Gunakan f_bulan dan f_tahun di bawah ini jika ingin memfilter daftar folder berdasarkan data yang ada
        conn = get_connection()
            df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
            daftar_folder = df_dept['nama'].tolist()
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]

    # 3. Ambil Daftar Departemen (Folder)
    try:
        conn = get_connection()
            df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
            daftar_folder = df_dept['nama'].tolist()
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]

    st.write("### Pilih Departemen:")
    cols = st.columns(4)
    
    # Ambil daftar folder (pastikan daftar_folder sudah ada di script Anda)
    for idx, d in enumerate(daftar_folder):
        # Tambahan: Ambil jumlah file per departemen untuk periode aktif
        conn = get_connection()
            cnt_query = "SELECT COUNT(*) FROM skd_files WHERE departemen=? AND bulan_skd=? AND tahun_skd=?"
            res = conn.execute(cnt_query, (d, f_bulan, f_tahun)).fetchone()
            jml = res[0] if res else 0
        
        # Tombol dengan label yang sudah termasuk jumlah (misal: 📂 PRODUCTION (5))
        if cols[idx % 4].button(f"📂 {d} ({jml})", width="stretch", key=f"fldr_{d}_{idx}"):
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
                            
                            conn = get_connection()
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

        # --- BAGIAN PENCARIAN & DAFTAR ---
        st.write("### Daftar File:")
        search_q = st.text_input("🔍 Cari Nama Pasien...", placeholder="Ketik nama untuk mencari...", key="search_skd_final")

        conn = get_connection()
            query = f"SELECT * FROM skd_files WHERE departemen='{target}' AND bulan_skd={f_bulan} AND tahun_skd={f_tahun} ORDER BY nama_file ASC"
            files = pd.read_sql(query, conn)
            
            if search_q:
                files = files[files['nama_pasien'].str.contains(search_q, case=False, na=False)]

            if not files.empty:
                for i, r in files.iterrows():
                    # Baris Utama
                    c_n, c_v, c_d, c_x = st.columns([4, 1.2, 1.2, 0.8])
                    c_n.text(f"📄 {r['nama_file']}") 
                    
                    # Logika Tombol Lihat (Toggle)
                    if c_v.button("👁️ Lihat", key=f"v_btn_{r['id']}_{i}"):
                        if st.session_state.get('view_id') == r['id']:
                            st.session_state['view_id'] = None # Tutup jika diklik lagi
                        else:
                            st.session_state['view_id'] = r['id'] # Buka
                        st.rerun()
                    
                    c_d.download_button("📥 Unduh", data=r['file_data'], file_name=r['nama_file'], mime='application/pdf', key=f"dl_d_{i}")

                    if c_x.button("🗑️", key=f"del_btn_{i}"):
                        cur = conn.cursor()
                        cur.execute("DELETE FROM skd_files WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

                    # --- PRATINJAU TEPAT DI BAWAH BARIS ---
                    if st.session_state.get('view_id') == r['id']:
                        with st.container():
                            st.info(f"Melihat SKD: {r['nama_file']}")
                            tampilkan_pdf_base64(r['file_data'])
                            if st.button("❌ Tutup Pratinjau", key=f"close_{i}"):
                                st.session_state['view_id'] = None
                                st.rerun()
                        st.markdown("---") 
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
                    conn = get_connection()
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
            conn = get_connection()
                df_res = pd.read_sql("SELECT id, nama FROM master_data WHERE kategori = ?", conn, params=(kat_pilihan,))
            
            if not df_res.empty:
                for idx, row in df_res.iterrows():
                    ca, cb = st.columns([4, 1])
                    ca.info(f"📍 {row['nama']}")
                    if cb.button("Hapus", key=f"del_master_{row['id']}"):
                        conn = get_connection()
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
                    conn = get_connection()
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
                    conn = get_connection()
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
                        conn = get_connection()
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
        conn = get_connection()
            u_df = pd.read_sql("SELECT username, role FROM users", conn)
        
        for i, row in u_df.iterrows():
            if row['username'] != 'admin': # Admin utama tidak bisa dihapus
                cx, cy = st.columns([4, 1])
                cx.text(f"👤 {row['username']} ({row['role']})")
                if cy.button("Hapus", key=f"u_del_{row['username']}"):
                    conn = get_connection()
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
    conn = get_connection()
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

# --- HAK CIPTA ESTETIK DI SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #00b38f; 
        border: 1px solid #e0e0e0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
        <p style="margin: 0; font-size: 12px; color: #444;">© 2026 Copyright:</p>
        <p style="margin: 5px 0; font-size: 14px; font-weight: bold; color: #008f73;">
            👨‍⚕️ Di Buat Oleh Alhatma, A.Md. RMIK
        </p>
        <p style="margin: 0; font-size: 11px; line-height: 1.4; color: #555; font-style: italic;">
            "Aplikasi ini dibuat secara khusus. Dilarang keras menyalahgunakan sistem ini."
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
