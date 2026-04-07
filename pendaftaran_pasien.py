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
                    status_antrian TEXT,
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
        ("dokter", "TEXT"),
        ("gender", "TEXT"),
        ("blok_mes", "TEXT"),
        ("tgl_lahir", "TEXT"),
        ("alergi", "TEXT"),
        ("gol_darah", "TEXT"),
        ("lokasi_kerja", "TEXT"),
        ("lokasi_mcu", "TEXT"),
        ("status_antrian", "TEXT")
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
    with get_connection() as conn:
        return pd.read_sql(f"SELECT id, nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)

# --- 4. MANAJEMEN LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    # Tampilan Halaman Login & Pendaftaran Publik
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
else:
    # Sidebar untuk Admin & Staff
    role_user = st.session_state.get('role')
    st.sidebar.success(f"🔓 {role_user}: {st.session_state['username']}")
    
    # PERBAIKAN: Pastikan nama menu konsisten
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
    
    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()
    custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

    # Pastikan teks di sini SAMA PERSIS dengan yang di dalam IF nanti
    pernah = st.radio("PERNAH BEROBAT DISINI? / 您以前在这里看过病吗？", ["Iya Sudah / 是的", "Belum Pernah / 从未"], horizontal=True)

    with st.form("form_reg", clear_on_submit=True):
        # PERBAIKAN: Menggunakan pengecekan teks yang tepat
        if pernah == "Iya Sudah / 是的":
            st.subheader("📌 Form Pasien Lama (Ringkas)")
            col1, col2 = st.columns(2)
            with col1:
                jenis_kunjungan = st.selectbox("Jenis Kunjungan / 就诊类型", ["Berobat / 治病", "Kontrol MCU / 体检复查", "Masuk UGD / 急诊", "Kontrol Post Rujuk / 转院后复查", "Kontrol Rawat Luka / 伤口护理复查"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名")
                nik = st.text_input("NIK / ID Card / 身份证号")
            with col2:
                perusahaan = st.selectbox("Perusahaan / 公司", opts_perusahaan)
                dept = st.selectbox("Departemen / 部门", opts_dept)
                jabatan = st.selectbox("Jabatan / 职位", opts_jabatan)
            
            # Data otomatis untuk pasien lama
            no_hp, agama, gender, blok_mes, tgl_lahir, alergi, gol_darah, lokasi_kerja, lokasi_mcu = "-", "Lama", "Lama", "-", "-", "-", "-", "-", "-"
            responses = {}

        else:
            st.subheader("📑 Form Pasien Baru (Lengkap)")
            col1, col2 = st.columns(2)
            with col1:
                jenis_kunjungan = st.selectbox("Jenis Kunjungan / 就诊类型", ["Berobat / 治病", "Kontrol MCU / 体检复查", "Masuk UGD / 急诊", "Kontrol Post Rujuk / 转院后复查", "Kontrol Rawat Luka / 伤口护理复查"])
                nama_lengkap = st.text_input("Nama Lengkap / 全名")
                no_hp = st.text_input("No HP Aktif (WhatsApp) / 手机号码")
                nik = st.text_input("NIK / ID Card / 身份证号")
                agama = st.selectbox("Agama / 宗教", ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"])
                gender = st.radio("Jenis Kelamin / 性别", ["Laki-laki / 男", "Perempuan / 女"], horizontal=True)

            with col2:
                blok_mes = st.text_input("Blok Mes dan No Kamar / 宿舍楼和房间号")
                tgl_lahir = st.text_input("Tempat & Tanggal Lahir / 出生地点和日期 (Contoh: Obi, 01-01-1990)")
                perusahaan = st.selectbox("Perusahaan / 公司", opts_perusahaan)
                dept = st.selectbox("Departemen / 部门", opts_dept)
                jabatan = st.selectbox("Jabatan / 职位", opts_jabatan)

            st.divider()
            col3, col4 = st.columns(2)
            with col3:
                alergi = st.multiselect("Jenis Alergi / 过敏类型", ["Makanan / 食物", "Obat / 药物", "Cuaca / 天气", "Tidak Ada / 无"])
                gol_darah = st.selectbox("Golongan Darah / 血型", ["A", "B", "AB", "O", "-"])
            with col4:
                lokasi_mcu = st.selectbox("Lokasi MCU Pertama Kali", ["Klinik HJF", "Klinik HPAL", "Klinik Luar Obi"])
                lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik / 具体工作地点")
            
            st.subheader("📋 Informasi Tambahan / 附加信息")
            responses = {field: st.text_input(f"{field.upper()}") for field in custom_fields}
        
        submit_btn = st.form_submit_button("KIRIM PENDAFTARAN / 提交登记")
        
        if submit_btn:
            # 1. Tentukan field mana saja yang wajib dicek
            if pernah == "Iya Sudah / 是的":
                # Untuk Pasien Lama
                required_fields = [nama_lengkap, nik, perusahaan, dept, jabatan]
            else:
                # Untuk Pasien Baru
                required_fields = [
                    nama_lengkap, nik, no_hp, blok_mes, tgl_lahir, 
                    perusahaan, dept, jabatan, lokasi_kerja, str(alergi)
                ]

            # 2. Logika pengecekan: Tidak boleh kosong, tidak boleh cuma spasi, dan list tidak boleh []
            is_valid = all(str(f).strip() != "" and str(f) != "[]" for f in required_fields)

            if is_valid:
                try:
                    with get_connection() as conn:
                        cur = conn.cursor()
                        cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan, no_hp, agama, gender, blok_mes, tgl_lahir, alergi, gol_darah, lokasi_kerja, lokasi_mcu, status_antrian) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                     (datetime.now().strftime("%Y-%m-%d"), nama_lengkap, nik, pernah, perusahaan, dept, jabatan, no_hp, agama, gender, blok_mes, tgl_lahir, str(alergi), gol_darah, lokasi_kerja, lokasi_mcu, "Normal"))
                        
                        last_id = cur.lastrowid
                        for f_name, f_val in responses.items():
                            cur.execute("INSERT INTO pasien_custom_data (pasien_id, field_name, field_value) VALUES (?,?,?)", (last_id, f_name, f_val))
                        conn.commit()
                    
                    st.success("Berhasil Terdaftar! / 登记成功！")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")
            else:
                # Muncul jika ada salah satu field di atas yang kosong
                st.warning("⚠️ Mohon lengkapi SEMUA kolom yang bertanda bintang! / 请填写所有必填项！")
  
# --- MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Menu Rekam Medis")
    
    conn = get_connection()
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
                "WhatsApp": st.column_config.TextColumn("WhatsApp"),
                "Tgl Daftar": st.column_config.DateColumn("Tanggal"),
                "status_antrian": None 
            }
        )
        
        # --- 2. KOTAK KETERANGAN WARNA (LEGEND) ---
        st.markdown("### 📋 Keterangan Status")
        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            st.info("🟡 **Kuning**: Menunggu Konsul Dokter")
        with col_k2:
            st.info("🔵 **Biru**: Menunggu Hasil Lab & Radiologi")
        with col_k3:
            st.warning("🟠 **Orange**: Batas Download SKD")

        # --- 3. FITUR UNDUH (CSV) ---
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv,
            file_name='data_rekam_medis.csv',
            mime='text/csv',
        )

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
                    "Batas Download SKD"
                ])
                btn_update = st.form_submit_button("Simpan Perubahan")
                
                if btn_update:
                    cur = conn.cursor()
                    cur.execute("UPDATE pasien SET status_antrian = ? WHERE nama_lengkap = ?", (status_baru, nama_p))
                    conn.commit()
                    st.success(f"Status {nama_p} berhasil diubah ke {status_baru}!")
                    st.rerun()

        # --- 5. FORM HAPUS DATA (Sudah termasuk pencarian) ---
        st.divider()
        with st.expander("🗑️ Hapus Data Pasien"):
            with st.form("hapus_pasien_form"):
                st.warning("Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
                
                # Nama yang muncul di sini sekarang hanya yang ada di hasil pencarian di atas
                nama_hapus = st.selectbox("Pilih Nama Pasien yang akan dihapus", df['Nama Lengkap'].tolist())
                konfirmasi = st.checkbox(f"Saya yakin ingin menghapus data tersebut")
                
                btn_hapus = st.form_submit_button("Hapus Data Pasien")
                
                if btn_hapus:
                    if konfirmasi:
                        try:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM pasien WHERE nama_lengkap = ?", (nama_hapus,))
                            conn.commit()
                            st.success(f"Data pasien '{nama_hapus}' telah berhasil dihapus.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menghapus data: {e}")
                    else:
                        st.error("Silakan centang kotak konfirmasi sebelum menghapus.")

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
            # --- TAMBAHAN: Pilih Role ---
            role_pilihan = st.selectbox("Pilih Role / 权限", ["Admin", "User"])
            
            if st.form_submit_button("Buat Akun"):
                if un and up:
                    conn = get_connection()
                    try:
                        # Masukkan role sesuai pilihan (Admin atau User)
                        conn.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", 
                                     (un, up, role_pilihan))
                        conn.commit()
                        conn.close()
                        st.success(f"Akun {role_pilihan} Berhasil Dibuat")
                        st.rerun()
                    except Exception as e: 
                        st.error(f"Gagal: Username sudah ada!")
        
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



