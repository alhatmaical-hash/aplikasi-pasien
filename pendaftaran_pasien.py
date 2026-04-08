import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import plotly.express as px

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
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tabel User
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # 2. Tabel Master
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    
    # 3. Tabel Pasien Utama
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE,
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
        ("lokasi_mcu", "TEXT")
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
    
    # Tambah Admin
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', 'admin123', 'Admin'))
    
    # SIMPAN DAN TUTUP (Hanya di akhir fungsi)
    conn.commit()
    conn.close()

# Jalankan fungsinya
init_db()


# --- 3. FUNGSI DATA ---
def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        # Baris ini yang WAJIB ada:
        c.execute('CREATE TABLE IF NOT EXISTS dokter_jaga_harian (id INTEGER PRIMARY KEY, nama_dokter TEXT)')
        
        # ... kode pembuatan tabel lainnya (pasien, master_dokter, dll) ...
        conn.commit()

def get_master(kategori):
    with get_connection() as conn:
        # Mengambil data dari tabel master berdasarkan kategori
        query = "SELECT id, nama FROM master_data WHERE kategori = ?"
        return pd.read_sql(query, conn, params=(kategori,))

init_db()

# --- 4. MANAJEMEN LOGIN & DETEKSI BARCODE ---
# Ambil parameter dari URL
params = st.query_params
is_pasien_mode = params.get("mode") == "pasien"
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# JIKA MODE PASIEN (DARI BARCODE)
if is_pasien_mode:
    # Langsung tetapkan menu ke Pendaftaran tanpa sidebar navigasi
    menu = "Pendaftaran / 登记"
    st.info("Sistem Pendaftaran Mandiri Pasien")
    # Bagian kode pendaftaran Anda akan berjalan di bawah (setelah blok login ini)

# JIKA BUKAN MODE PASIEN DAN BELUM LOGIN (TAMPILAN NORMAL)
elif not st.session_state['logged_in']:
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
        st.stop()

# JIKA SUDAH LOGIN (STAFF/ADMIN)
else:
    role_user = st.session_state.get('role')
    st.sidebar.success(f"🔓 {role_user}: {st.session_state['username']}")
    
    if role_user == "Admin":
        menu_list = ["Pendaftaran Pasien", "Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]
    else:
        menu_list = ["SKD / 医生证明"]
    
    menu = st.sidebar.selectbox("Pilih Menu", menu_list)
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
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
            tgl_hari_ini = datetime.now().strftime("%Y-%m-%d")
            # Menghitung jumlah pasien hari ini
            res = conn.execute("SELECT COUNT(*) FROM pasien WHERE tgl_daftar=?", (tgl_hari_ini,)).fetchone()
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
                jenis_kunjungan = st.selectbox("Jenis Kunjungan / 就诊类型", ["Berobat / 治病", "Kontrol MCU / 体检复查", "Masuk UGD / 急诊", "Kontrol Post Rujuk / 转院后复查", "Kontrol Rawat Luka / 伤口护理复查"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名 *", value=st.session_state.nama_lengkap)
                no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码 *", value=st.session_state.no_hp)
                nik = st.text_input("NIK / ID Card / 身份证号 *", value=st.session_state.nik)
                agama = st.selectbox("Agama / 宗教", ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"])
                gender = st.radio("Jenis Kelamin / 性别", ["Laki-laki / 男", "Perempuan / 女"], horizontal=True)
            
            with col2:
                blok_mes = st.text_input("Blok Mes dan No Kamar / 宿舍楼和房间号 *", value=st.session_state.blok_mes)
                tmpt_lahir = st.text_input("Tempat Lahir / 出生地点 *")
                tgl_lahir = st.date_input("Tanggal Lahir / 出生日期 *", value=None, min_value=datetime(1950, 1, 1), max_value=datetime.now(), format="DD/MM/YYYY")
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
                jenis_kunjungan = st.selectbox("Jenis Kunjungan / 就诊类型", ["Berobat / 治病", "Kontrol MCU / 体检复查", "Masuk UGD / 急诊", "Kontrol Post Rujuk / 转院后复查", "Kontrol Rawat Luka / 伤口护理复查"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名 *", value=st.session_state.nama_lengkap)
                no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码 *", value=st.session_state.no_hp)
                nik = st.text_input("NIK / ID Card / 身份证号 *", value=st.session_state.nik)
                agama = st.selectbox("Agama / 宗教", ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"])
                gender = st.radio("Jenis Kelamin / 性别", ["Laki-laki / 男", "Perempuan / 女"], horizontal=True)

            with col2:
                blok_mes = st.text_input("Blok Mes dan No Kamar / 宿舍楼和房间号 *", value=st.session_state.blok_mes)
                tmpt_lahir = st.text_input("Tempat Lahir / 出生地点 *")
                tgl_lahir = st.date_input("Tanggal Lahir / 出生日期 *", value=None, min_value=datetime(1950, 1, 1), max_value=datetime.now(), format="DD/MM/YYYY")
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

                # 2. Definisikan empty_fields di SINI (pindahkan dari atas ke dalam sini)
                if pernah == "Iya Sudah / 是的":
                    required = {"Nama": nama_lengkap, "NIK": nik, "Perusahaan": perusahaan, "Dept": dept}
                else:
                    required = {"Nama": nama_lengkap, "NIK": nik, "No HP": no_hp, "Perusahaan": perusahaan, "Area": lokasi_kerja}
            
                empty_fields = [k for k, v in required.items() if str(v).strip() in ["", "None", "[]"]]

                # 3. Jalankan simpan HANYA jika kolom lengkap
                if not empty_fields:
                    try:
                        tgl_str = tgl_lahir_val.strftime("%d-%m-%Y") if tgl_lahir_val else ""
                        tgl_gabung = f"{tmpt_lahir}, {tgl_str}"
                        with get_connection() as conn:
                            cur = conn.cursor()
                            cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan, no_hp, agama, gender, blok_mes, tgl_lahir, alergi, gol_darah, lokasi_kerja, lokasi_mcu, status_antrian, dokter) 
                                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                       (datetime.now().strftime("%Y-%m-%d"), nama_lengkap, nik, pernah, perusahaan, dept, jabatan, 
                                        no_hp, agama, gender, blok_mes, tgl_gabung, str(alergi), gol_darah, lokasi_kerja, lokasi_mcu, "Normal", dokter_terpilih))
                        
                            last_id = cur.lastrowid
                            for f_name, f_val in responses.items():
                                cur.execute("INSERT INTO pasien_custom_data (pasien_id, field_name, field_value) VALUES (?,?,?)", (last_id, f_name, f_val))
                            conn.commit()

                        st.success(f"✅ Pendaftaran Sukses Dikirim! \n\n Silakan ke: **{dokter_terpilih}**")
                        st.balloons()
                    
                        # Reset Form
                        for key in ['nama_lengkap', 'nik', 'no_hp', 'blok_mes', 'tgl_lahir', 'lokasi_kerja']:
                            st.session_state[key] = ""
                    
                        import time
                        time.sleep(2)
                        st.session_state['proses_simpan'] = False # Buka kunci sebelum rerun
                        st.rerun()

                    except Exception as e:
                        st.session_state['proses_simpan'] = False # Buka kunci jika gagal agar bisa coba lagi
                        st.error(f"Gagal menyimpan: {e}")
                else:
                    # Jika ada kolom kosong
                    st.session_state['proses_simpan'] = False # Buka kunci agar user bisa perbaiki lalu klik lagi
                    kolom_kosong = ", ".join(empty_fields)
                    st.warning(f"⚠️ Mohon lengkapi kolom: **{kolom_kosong}**")
  
# --- MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Menu Rekam Medis")
    with st.expander("👨‍⚕️ Atur Dokter Jaga Hari Ini", expanded=False):
        # SEMUA baris di bawah ini harus menjorok ke kanan (tambah 1 TAB / 4 SPASI)
        opts_dr_raw = get_master("Dokter")['nama'].tolist()
        opts_dr = sorted(list(set(opts_dr_raw)))
        
        with get_connection() as conn:
            try:
                dr_aktif_db = pd.read_sql("SELECT nama_dokter FROM dokter_jaga_harian", conn)['nama_dokter'].tolist()
            except:
                dr_aktif_db = []

        pilihan = st.multiselect(
            "Pilih Dokter yang Bertugas", 
            opts_dr, 
            default=dr_aktif_db,
            placeholder="Pilih dokter..."
        )

        if st.button("Simpan Jadwal Dokter"):
            with get_connection() as conn:
                conn.execute("DELETE FROM dokter_jaga_harian")
                for dr in pilihan:
                    conn.execute("INSERT INTO dokter_jaga_harian (nama_dokter) VALUES (?)", (dr,))
                conn.commit()
            st.success("Jadwal Berhasil Disimpan!")
            st.rerun()

    with get_connection() as conn:
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
        dokter AS 'Dokter',
        gender AS 'Gender',
        tgl_lahir AS 'TTL',
        alergi AS 'Alergi',
        gol_darah AS 'Gol Darah',
        blok_mes AS 'Blok/Kamar',
        lokasi_kerja AS 'Area Kerja',
        lokasi_mcu AS 'Lokasi Mcu Pertama Kali',
        status_antrian
    FROM pasien
    """
    df = pd.read_sql(query, conn)
    
    if not df.empty:
        # --- TAMBAHAN: FITUR PENCARIAN (Ubah di sini) ---
        search_term = st.text_input("🔍 Cari Nama Pasien / 查找病人姓名", "", key="search_rekam_medis")

        # Proses Filtering: Tabel akan menyusut sesuai ketikan Anda
        if search_term:
            df = df[df['Nama Lengkap'].str.contains(search_term, case=False, na=False)]

        # --- 1. LOGIKA WARNA (STYLING) ---
        def color_row(row):
            status = row['status_antrian']
            if status == "Menunggu Konsul Dokter":
                return ['background-color: #ffff00; color: black'] * len(row) # Kuning
            elif status == "Menunggu Hasil Lab & Radiologi":
                return ['background-color: #00b0f0; color: white'] * len(row) # Biru
            elif status == "Batas Download SKD":
                return ['background-color: #ff9900; color: white'] * len(row) # Orange
            return [''] * len(row)

        styled_df = df.style.apply(color_row, axis=1)

        # Menampilkan tabel yang sudah terfilter dan berwarna
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "id": None, # Sembunyikan kolom ID agar tidak berantakan
                "WhatsApp": st.column_config.TextColumn("WhatsApp"),
                "Tgl Daftar": st.column_config.DateColumn("Tanggal"),
                "Nama Lengkap": st.column_config.TextColumn("Nama Lengkap", width="large"),
                "status_antrian": None 
            }
        )
        
        # --- 2. KOTAK KETERANGAN WARNA (LEGEND) ---
        st.markdown("### 📋 Keterangan Status")
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1:
            st.info("🟡 **Kuning**: Menunggu Konsul Dokter")
        with col_k2:
            st.info("🔵 **Biru**: Menunggu Hasil Lab & Radiologi")
        with col_k3:
            st.warning("🟠 **Orange**: Batas Download SKD")
        with col_k4:
            st.success("🟢 **Hijau**: Batas Operan & Daftar Pasien")

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
                    "Batas Operan & Daftar Pasien"
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

        # --- 6. FORM HAPUS SEMUA DATA (HANYA ADMIN) ---
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
    with st.expander("🗑️ Zona Bahaya: Hapus Semua PDF Bulan Ini"):
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



