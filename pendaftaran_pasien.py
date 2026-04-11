import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import pytz
from datetime import datetime, time, timedelta


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

# --- 2. DATABASE SETUP ---
def get_connection():
    return sqlite3.connect('klinik_data.db', check_same_thread=False)

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
        
        conn.commit()

# Jalankan inisialisasi database SEKALI SAJA
init_db()

# --- 3. FUNGSI DATA (DENGAN CACHE) ---
@st.cache_data
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
            if st.button("Login", use_container_width=True):
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
# --- 5. LOGIKA HALAMAN ---

# --- MENU PENDAFTARAN (Admin & Publik) ---
if menu in ["Pendaftaran Pasien", "Pendaftaran / 登记"]:
    st.header("📝 Pendaftaran Pasien / 病人登记")
    
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
                nik = st.text_input("NIK / ID Card / 身份证号 *", value=st.session_state.nik)
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
                nik = st.text_input("NIK / ID Card / 身份证号 *", value=st.session_state.nik)
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

            # 2. Definisikan required fields
            if pernah == "Iya Sudah / 是的": 
                required = {"Nama": nama_lengkap, "NIK": nik, "Perusahaan": perusahaan, "Dept": dept}
            else:
                required = {"Nama": nama_lengkap, "NIK": nik, "No HP": no_hp, "Perusahaan": perusahaan, "Area": lokasi_kerja}
            
            empty_fields = [k for k, v in required.items() if str(v).strip() in ["", "None", "[]"]]

            if not empty_fields:
                try:
                    tz_wit = pytz.timezone('Asia/Jayapura')
                    waktu_sekarang = datetime.now(tz_wit)
                    tgl_hari_ini = waktu_sekarang.strftime("%Y-%m-%d")

                    with get_connection() as conn:
                        # --- SEMUA KODE DI BAWAH INI HARUS MASUK KE DALAM (INDENTASI) ---
                        
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
                    
                    with get_connection() as conn:
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
        with get_connection() as conn:
            try:
                dr_aktif_db = pd.read_sql("SELECT nama_dokter FROM dokter_jaga_harian", conn)['nama_dokter'].tolist()
            except:
                dr_aktif_db = []
        pilihan = st.multiselect("Pilih Dokter yang Bertugas", opts_dr, default=dr_aktif_db, placeholder="Pilih dokter...")
        if st.button("Simpan Jadwal Dokter"):
            with get_connection() as conn:
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
                with get_connection() as conn:
                    tz_wit = pytz.timezone('Asia/Jayapura')
                    tgl_skrg = datetime.now(tz_wit).strftime("%Y-%m-%d")
                    conn.execute("UPDATE pasien SET is_authorized = 1 WHERE nik = ? AND tgl_daftar LIKE ?", (nik_izin, f"{tgl_skrg}%"))
                    conn.commit()
                st.success(f"Berhasil! NIK {nik_izin} sekarang diizinkan mendaftar ulang.")
            else:
                st.warning("Silakan masukkan NIK terlebih dahulu.")
   # --- BAGIAN 3: TABEL ANTRIAN DENGAN FILTER PERIODE ---
    st.write("---")
    st.subheader("📋 Daftar Antrian Pasien")

    # Membuat 3 kolom agar filter sejajar (Bulan, Tahun, Cari Nama)
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])

    with col_f1:
        list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                      "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        bulan_idx = datetime.now().month - 1
        bulan_pilih = st.selectbox("📅 Bulan", list_bulan, index=bulan_idx, key="filter_bln_rm")
        mapping_bulan = {nama: str(i+1).zfill(2) for i, nama in enumerate(list_bulan)}
        filter_bln = mapping_bulan[bulan_pilih]

    with col_f2:
        tahun_skrg = datetime.now().year
        list_tahun = [str(t) for t in range(2026, tahun_skrg + 6)]
        tahun_pilih = st.selectbox("🗓️ Tahun", list_tahun, key="filter_thn_rm")

    with col_f3:
        # Pindahkan cari nama ke sini agar rapi dan beri KEY UNIK
        search_term = st.text_input("🔍 Cari Nama Pasien", "", key="cari_nama_pasien_rm")

    # Kueri database yang sudah difilter berdasarkan bulan dan tahun
    with get_connection() as conn:
        query = f"""
        SELECT id, tgl_daftar AS 'Tgl Daftar', jenis_kunjungan, nama_lengkap AS 'Nama Lengkap', 
               nik AS 'NIK/ID', no_hp AS 'WhatsApp', perusahaan AS 'Perusahaan', 
               departemen AS 'Departemen', jabatan AS 'Jabatan', pernah_berobat AS 'Status',
               agama AS 'Agama', dokter AS 'Dokter', gender AS 'Gender', tgl_lahir AS 'TTL',
               alergi AS 'Alergi', gol_darah AS 'Gol Darah', blok_mes AS 'Blok/Kamar',
               lokasi_kerja AS 'Area Kerja', lokasi_mcu AS 'Lokasi Mcu Pertama Kali', status_antrian
        FROM pasien 
        WHERE strftime('%m', tgl_daftar) = '{filter_bln}' 
          AND strftime('%Y', tgl_daftar) = '{tahun_pilih}'
        ORDER BY id ASC
        """
        df = pd.read_sql(query, conn)

    # Menjalankan filter nama di level dataframe (jika ada input di kotak cari nama)
    if not df.empty:
        if search_term:
            df = df[df['Nama Lengkap'].str.contains(search_term, case=False, na=False)]

        # Logika Warna
        def color_row(row):
            status = row['status_antrian']
            if status == "Menunggu Konsul Dokter": return ['background-color: #ffff00; color: black'] * len(row)
            elif status == "Menunggu Hasil Lab & Radiologi": return ['background-color: #00b0f0; color: white'] * len(row)
            elif status == "Batas Download SKD": return ['background-color: #ff9900; color: white'] * len(row)
            elif status == "Batas Operan & Daftar Pasien": return ['background-color: #c8e6c9'] * len(row)
            elif status == "Batal Berobat": return ['background-color: #ff4b4b; color: white'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df.style.apply(color_row, axis=1), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "id": None, 
                "Tgl Daftar": st.column_config.DatetimeColumn("Tanggal", format="DD/MM/YY HH:mm"),
                "status_antrian": st.column_config.TextColumn("Status Antrian") # Saya munculkan agar terlihat di tabel
            }
        )

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
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv,
            file_name='data_rekam_medis.csv',
            mime='text/csv',
        )

         # --- FITUR EDIT / RENAME NAMA PASIEN ---
        st.divider()
        with st.expander("✏️ Edit / Rename Nama Pasien"):
            with st.form("edit_nama_form"):
                st.info("Gunakan fitur ini untuk memperbaiki kesalahan penulisan nama.")
                
                # Pilihan pasien berdasarkan data yang sedang tampil di tabel
                # Format: ID | Nama (agar unik)
                opsi_edit = df.apply(lambda x: f"{x['id']} | {x['Nama Lengkap']}", axis=1).tolist()
                data_terpilih = st.selectbox("Pilih Pasien yang akan diperbaiki namanya", opsi_edit)
                
                # Ambil nama lama sebagai default value
                nama_lama = data_terpilih.split(" | ")[1]
                id_target_edit = int(data_terpilih.split(" | ")[0])
                
                nama_baru = st.text_input("Input Nama yang Benar", value=nama_lama)
                
                btn_rename = st.form_submit_button("Simpan Perubahan Nama")
                
                if btn_rename:
                    if nama_baru.strip() == "":
                        st.error("Nama tidak boleh kosong!")
                    else:
                        try:
                            with get_connection() as conn:
                                cur = conn.cursor()
                                # Update nama di tabel pasien
                                cur.execute("UPDATE pasien SET nama_lengkap = ? WHERE id = ?", (nama_baru, id_target_edit))
                                conn.commit()
                                
                            st.success(f"Berhasil! Nama telah diubah dari '{nama_lama}' menjadi '{nama_baru}'")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal memperbarui nama: {e}")



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
                            
                            with get_connection() as conn:
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

    
        # --- 6. FITUR CETAK FORMULIR OTOMATIS (VERSI BARU) ---
        st.divider()
        with st.expander("🖨️ Cetak Formulir Pendaftaran Pasien"):
            st.info("Pilih pasien untuk membuat formulir otomatis dari data rekam medis.")
            hasil_cetak = None
    
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
                        hasil_cetak = buat_formulir_otomatis(data_pasien, petugas)
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat mengambil data: {e}")

            if hasil_cetak:
                st.success(f"✅ Formulir untuk {nama_p_cetak} siap dicetak!")
                
                # Karena hasil_cetak sekarang berisi data PDF (bytes), 
                # kita gunakan st.download_button dengan mime pdf
                st.download_button(
                    label="🖨️ Klik di sini untuk Buka & Cetak PDF",
                    data=hasil_cetak,
                    file_name=f"Formulir_{nama_p_cetak.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
                # Info tambahan untuk user
                st.info("💡 Setelah klik tombol di atas, PDF akan terbuka. Gunakan tombol 'Print' di browser atau tekan Ctrl+P.")

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

    # 3. Ambil Daftar Departemen (Folder)
    try:
        # Gunakan f_bulan dan f_tahun di bawah ini jika ingin memfilter daftar folder berdasarkan data yang ada
        with get_connection() as conn:
            df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
            daftar_folder = df_dept['nama'].tolist()
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]

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
        # Baris 488: Semua kode di bawah ini HARUS menjorok ke dalam
        st.divider() 
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target} ({f_bulan}/{f_tahun})")
    
        # Form Upload (juga harus menjorok)
        with st.expander("➕ Upload PDF Baru"):
            with st.form("upload_skd_form", clear_on_submit=True):
                u_files = st.file_uploader("Pilih PDF", type=['pdf'], accept_multiple_files=True)
            
                if st.form_submit_button("Simpan Ke Folder"):
                    if u_files:
                        try:
                            with get_connection() as conn:
                                for u_f in u_files:
                                    file_content = u_f.read()
                                    conn.execute("""
                                        INSERT INTO skd_files 
                                        (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) 
                                        VALUES (?,?,?,?,?,?,?)""", 
                                        (u_f.name, target, u_f.name, file_content, datetime.now(), f_bulan, f_tahun))
                                conn.commit()
                            st.success(f"Berhasil menyimpan {len(u_files)} file!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                else:
                        st.warning("Silakan pilih file terlebih dahulu.")

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
# --- MENU PENGATURAN ---
elif menu == "Pengaturan Master / 设置":
    
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
                    with get_connection() as conn:
                        conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()

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
                    with get_connection() as conn:
                        conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()

    with t3:
        st.subheader("👥 Manajemen Akun Tim")
        with st.form("tambah_user_form"):
            un = st.text_input("Username Baru")
            up = st.text_input("Password Baru", type="password")
            # Menambahkan pilihan Role
            ur = st.selectbox("Role", ["Admin", "Staff"])
            
            submit_user = st.form_submit_button("Tambah User")
            
            if submit_user:
                if un and up:
                    try:
                        with get_connection() as conn:
                            conn.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (un, up, ur))
                            conn.commit()
                        st.success(f"User {un} berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah user: {e}")
                else:
                    st.warning("Mohon isi username dan password.")

        # Menampilkan daftar user yang ada
        st.write("---")
        st.write("### Daftar User Aktif")
        with get_connection() as conn:
            df_users = pd.read_sql("SELECT username, role FROM users", conn)
            st.table(df_users)
        
        st.write("Daftar Akun:")
        conn = get_connection()
        # Ambil username dan role untuk ditampilkan
        u_df = pd.read_sql("SELECT username, role FROM users", conn)
        conn.close()
        
        for i, row in u_df.iterrows():
            # Jangan hapus admin utama
            if row['username'] != 'admin':
                cx, cy = st.columns([3, 1])
                # Menampilkan username dan role-nya
                cx.text(f"👤 {row['username']} ({row['role']})")
                if cy.button("Hapus Akun", key=f"u_del_{row['username']}"):
                    conn = get_connection()
                    conn.execute("DELETE FROM users WHERE username=?", (row['username'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
        # update files check 09-04-2026
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
        st.dataframe(summary.sort_values('Total', ascending=False), use_container_width=True, hide_index=True)

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
