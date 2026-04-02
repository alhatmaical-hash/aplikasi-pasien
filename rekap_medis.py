import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io
import hashlib

# --- 0. KONFIGURASI HALAMAN ---
DB_PATH = 'klinik_data.db'
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. LOGIKA LOGIN (USER & PASSWORD DATABASE) ---

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def init_user_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Membuat tabel untuk menyimpan banyak user
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT PRIMARY KEY, password TEXT)')
    
    # Cek apakah sudah ada user 'admin' default
    c.execute('SELECT * FROM userstable WHERE username = "admin"')
    if not c.fetchone():
        # Username default: admin | Password default: admin123
        c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', ('admin', make_hashes('admin123')))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password FROM userstable WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        return check_hashes(password, data[0])
    return False

def add_userdata(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# Jalankan inisialisasi tabel user
init_user_db()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# Tampilan Form Login
if not st.session_state["authenticated"]:
    st.title("🏥 Akses Terbatas - Klinik Apps")
    
    # Menghapus sistem Tab di depan agar tidak bisa registrasi bebas
    with st.container(border=True):
        u_input = st.text_input("Username:", key="login_user")
        p_input = st.text_input("Password:", type="password", key="login_pwd")
        
        if st.button("🚀 MASUK KE SISTEM", use_container_width=True, type="primary"):
            if login_user(u_input, p_input):
                st.session_state["authenticated"] = True
                st.session_state["username"] = u_input
                st.rerun()
            else:
                st.error("❌ Username atau Password Salah!")
    st.stop()
# --- 2. SETTING DATABASE & FUNGSI ---


def get_date_range():
    try:
        conn = sqlite3.connect(DB_PATH)
        df_range = pd.read_sql_query("SELECT MIN(visit_time) as awal, MAX(visit_time) as akhir FROM rekap_penyakit", conn)
        conn.close()
        if df_range['awal'].iloc[0] is None:
            return date.today(), date.today()
        awal = pd.to_datetime(df_range['awal'].iloc[0]).date()
        akhir = pd.to_datetime(df_range['akhir'].iloc[0]).date()
        return awal, akhir
    except:
        return date.today(), date.today()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  visit_time TEXT, patient_name TEXT, diagnosa TEXT, 
                  clinic TEXT, department TEXT, company TEXT,
                  rest_status TEXT, rest_type TEXT, rest_duration INTEGER)''')
    
    # Pastikan kolom baru ada (untuk migrasi database)
    kolom_baru = [
        ('visit_time', 'TEXT'), ('patient_name', 'TEXT'), ('diagnosa', 'TEXT'),
        ('clinic', 'TEXT'), ('department', 'TEXT'), ('company', 'TEXT'),
        ('rest_status', 'TEXT'), ('rest_type', 'TEXT'), ('rest_duration', 'INTEGER')
    ]
    for kolom, tipe in kolom_baru:
        try:
            c.execute(f"ALTER TABLE rekap_penyakit ADD COLUMN {kolom} {tipe}")
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- 3. STYLE CSS ---
st.markdown("""
<style>
    div.stButton > button { font-weight: bold !important; color: black !important; border-radius: 8px; }
    button[kind="primary"] { background-color: #FF4B4B !important; }
    h1 { color: #2e7d32; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR NAVIGASI ---
st.sidebar.title("🏥 MENU KLINIK")
menu = st.sidebar.radio("NAVIGASI", 
    ["Upload Data CSV", "Laporan 10 Penyakit", "Analisis Dept & Perusahaan", "Keterangan Istirahat", "Lihat Semua Data", "Analisis Istirahat", "Manajemen User"])

if st.sidebar.button("🔴 KELUAR APLIKASI", type="primary", use_container_width=True):
    st.session_state["authenticated"] = False
    st.rerun()

# --- 5. MODUL 1: UPLOAD DATA (VERSI PERBAIKAN TOTAL) ---
if menu == "Upload Data CSV":
    st.markdown("<h1>📤 UPLOAD DATA PASIEN</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # Normalisasi nama kolom: huruf kecil dan ganti spasi dengan underscore
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            
            # --- LOGIKA PENYELARASAN KOLOM ---
            # Jika di CSV namanya 'department' (Inggris), ubah ke 'departemen' (Indo)
            if 'department' in df.columns and 'departemen' not in df.columns:
                df = df.rename(columns={'department': 'departemen'})
            
            st.write("### 🔍 Pratinjau Data:")
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("💾 SIMPAN KE DATABASE", use_container_width=True, type="primary"):
                conn = sqlite3.connect(DB_PATH)
                
                # Pembersihan Baris Kosong
                df = df.dropna(subset=['patient_name'])
                df['p_name_check'] = df['patient_name'].astype(str).str.strip().str.lower()
                df = df[~df['p_name_check'].isin(['none', 'nan', '', 'null'])].copy()

                if not df.empty:
                    # Pastikan format tanggal aman
                    df['visit_time'] = pd.to_datetime(df['visit_time']).dt.strftime('%Y-%m-%d')
                    
                    # Tambahkan kolom yang kurang secara otomatis agar tidak error
                    kolom_wajib = ['visit_time', 'patient_name', 'diagnosa', 'clinic', 'departemen', 'company', 'rest_status', 'rest_type', 'rest_duration']
                    for col in kolom_wajib:
                        if col not in df.columns:
                            df[col] = 0 if col == 'rest_duration' else "-"
                    
                    # Simpan hanya kolom yang dibutuhkan
                    df_to_save = df[kolom_wajib]
                    df_to_save.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Berhasil menyimpan {len(df_to_save)} data pasien.")
                    st.balloons()
                else:
                    st.warning("⚠️ File CSV tidak berisi data valid.")
                    conn.close()

        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {str(e)}")
            if 'conn' in locals(): conn.close()

# --- 6. MODUL 2: LAPORAN 10 PENYAKIT ---
elif menu == "Laporan 10 Penyakit":
    st.markdown("<h1>📊 10 PENYAKIT TERBESAR</h1>", unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    start = t1.date_input("Mulai", value=get_date_range()[0])
    end = t2.date_input("Sampai", value=get_date_range()[1])
    
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT diagnosa, COUNT(*) as jumlah FROM rekap_penyakit WHERE visit_time BETWEEN '{start}' AND '{end}' GROUP BY diagnosa ORDER BY jumlah DESC LIMIT 10"
    df_top = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_top.empty:
        st.dataframe(df_top, use_container_width=True)
        st.bar_chart(df_top.set_index('diagnosa'))
    else:
        st.warning("Data tidak tersedia.")

# --- 7. MODUL 3: ANALISIS DEPT & PERUSAHAAN ---
elif menu == "Analisis Dept & Perusahaan":
    st.markdown("<h1>🏢 ANALISIS KUNJUNGAN</h1>", unsafe_allow_html=True)
    start, end = st.columns(2)
    t1 = start.date_input("Mulai", value=get_date_range()[0], key="a1")
    t2 = end.date_input("Sampai", value=get_date_range()[1], key="a2")
    conn = sqlite3.connect(DB_PATH)
    df_data = pd.read_sql_query(f"SELECT department, company FROM rekap_penyakit WHERE visit_time BETWEEN '{t1}' AND '{t2}'", conn)
    conn.close()
    
    if not df_data.empty:
        tab1, tab2 = st.tabs(["📊 Departemen", "🏢 Perusahaan"])
        with tab1:
            st.bar_chart(df_data['department'].value_counts())
        with tab2:
            st.bar_chart(df_data['company'].value_counts())
    else:
        st.warning("Data kosong.")

# --- 8. MODUL 4: KETERANGAN ISTIRAHAT (MODUL BARU) ---
elif menu == "Keterangan Istirahat":
    st.markdown("<h1>🛌 ANALISIS ISTIRAHAT PASIEN</h1>", unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    start = t1.date_input("Mulai", value=get_date_range()[0], key="r1")
    end = t2.date_input("Sampai", value=get_date_range()[1], key="r2")

    conn = sqlite3.connect(DB_PATH)
    df_rest = pd.read_sql_query(f"SELECT rest_status, rest_type, rest_duration FROM rekap_penyakit WHERE visit_time BETWEEN '{start}' AND '{end}'", conn)
    conn.close()

    if not df_rest.empty:
        # Statistik Utama
        total = len(df_rest)
        ya_rest = len(df_rest[df_rest['rest_status'].str.lower() == 'ya'])
        tidak_rest = total - ya_rest

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pasien", f"{total}")
        m2.metric("✅ Istirahat (Ya)", f"{ya_rest}")
        m3.metric("❌ Tidak Istirahat", f"{tidak_rest}")

        if ya_rest > 0:
            st.write("### 📊 Detail Istirahat (Tipe: Hari vs Jam)")
            df_ya = df_rest[df_rest['rest_status'].str.lower() == 'ya']
            
            # Distribusi Tipe (Hari vs Jam)
            col1, col2 = st.columns(2)
            with col1:
                tipe_counts = df_ya['rest_type'].value_counts().reset_index()
                tipe_counts.columns = ['Tipe', 'Jumlah']
                st.dataframe(tipe_counts, hide_index=True, use_container_width=True)
            with col2:
                st.bar_chart(tipe_counts.set_index('Tipe'))

            st.write("### ⏱️ Detail Durasi Istirahat")
            detail = df_ya.groupby(['rest_type', 'rest_duration']).size().reset_index(name='Jumlah Orang')
            st.table(detail) # Tabel sederhana untuk durasi
    else:
        st.info("Belum ada data istirahat.")

# --- 9. MODUL: LIHAT SEMUA DATA (DENGAN DURASI, DEPT, & PERUSAHAAN) ---
elif menu == "Lihat Semua Data":
    st.markdown("<h1>📂 DATABASE REKAP MEDIS</h1>", unsafe_allow_html=True)
    
    t_awal, t_akhir = get_date_range()
    
    with st.expander("🔍 Filter & Statistik", expanded=True):
        c1, c2, c3 = st.columns([1,1,2])
        f1 = c1.date_input("Mulai Tanggal", t_awal)
        f2 = c2.date_input("Sampai Tanggal", t_akhir)
        st_filter = c3.selectbox("Filter Tampilan Status Istirahat:", ["Semua", "Ya", "Tidak"])

    conn = sqlite3.connect(DB_PATH)
    df_raw = pd.read_sql_query("SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", conn, params=[f1, f2])
    
    if not df_raw.empty:
        # Pembersihan data
        df_raw = df_raw.dropna(subset=['patient_name'])
        df_raw['p_name_check'] = df_raw['patient_name'].astype(str).str.strip().str.lower()
        df_raw = df_raw[~df_raw['p_name_check'].isin(['none', 'nan', '', 'null'])].copy()

        if not df_raw.empty:
            # Normalisasi Status & Durasi untuk tampilan
            df_raw['status_clean'] = df_raw['rest_status'].fillna('Tidak').astype(str).str.strip().str.lower()
            df_raw['dur_num'] = pd.to_numeric(df_raw['rest_duration'], errors='coerce').fillna(0)
            
            # Eksekusi Filter
            if st_filter == "Ya":
                df_tampil = df_raw[df_raw['status_clean'].isin(['ya', 'yes', 'y'])].copy()
            elif st_filter == "Tidak":
                df_tampil = df_raw[~df_raw['status_clean'].isin(['ya', 'yes', 'y'])].copy()
            else:
                df_tampil = df_raw.copy()

            st.metric(f"Data Terfilter ({st_filter})", f"{len(df_tampil)} Orang")
            st.markdown("---")

            # --- PENYUSUNAN TABEL (KOLOM LENGKAP) ---
            df_display = pd.DataFrame()
            df_display['No.'] = range(1, len(df_tampil) + 1)
            df_display['Pilih'] = False
            df_display['Tanggal'] = df_tampil['visit_time']
            df_display['Nama Pasien'] = df_tampil['patient_name']
            df_display['Diagnosa'] = df_tampil['diagnosa']
            
            # Menampilkan Clinic DAN Departemen
            df_display['Clinic'] = df_tampil['clinic']
            
            # Sesuaikan 'departemen' dengan nama kolom asli di database/CSV Anda
            if 'departemen' in df_tampil.columns:
                df_display['Departemen'] = df_tampil['departemen']
            elif 'department' in df_tampil.columns:
                df_display['Departemen'] = df_tampil['department']
            else:
                df_display['Departemen'] = "-"
            
            df_display['Perusahaan'] = df_tampil['company']
            
            # Kolom Istirahat (Hari/Jam)
            df_display['Istirahat'] = df_tampil['dur_num'].apply(
                lambda x: f"{int(x)} Hari" if 1 <= x <= 7 else (f"{int(x)} Jam" if x > 7 else "-")
            )
            
            df_display['Status'] = df_tampil['rest_status'].str.upper()
            df_display['db_id'] = df_tampil['id']

            # Render Tabel
            edited_df = st.data_editor(
                df_display, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "db_id": None, 
                    "Pilih": st.column_config.CheckboxColumn("Hapus?")
                },
                disabled=[c for c in df_display.columns if c != "Pilih"]
            )

            # Tombol Aksi
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🗑️ HAPUS DATA TERPILIH", use_container_width=True):
                    ids = edited_df[edited_df['Pilih'] == True]['db_id'].tolist()
                    if ids:
                        conn.cursor().execute(f"DELETE FROM rekap_penyakit WHERE id IN ({','.join(['?']*len(ids))})", ids)
                        conn.commit()
                        st.success(f"✅ Berhasil menghapus {len(ids)} data.")
                        st.rerun()
            
            with col_btn2:
                with st.expander("⚠️ Hapus Semua"):
                    if st.button("🔥 YA, HAPUS SEMUA DATA INI", use_container_width=True, type="primary"):
                        all_ids = df_display['db_id'].tolist()
                        if all_ids:
                            conn.cursor().execute(f"DELETE FROM rekap_penyakit WHERE id IN ({','.join(['?']*len(all_ids))})", all_ids)
                            conn.commit()
                            st.success("💥 Database untuk filter ini telah dibersihkan.")
                            st.rerun()
    else:
        st.info("Database kosong pada periode ini.")
    conn.close()
# --- 10. MODUL: ANALISIS ISTIRAHAT (VERSI AKURASI TINGGI) ---
elif menu == "Analisis Istirahat":
    st.markdown("<h1>📊 ANALISIS DETAIL ISTIRAHAT</h1>", unsafe_allow_html=True)
    
    t_awal, t_akhir = get_date_range()
    
    with st.expander("📅 Pengaturan Periode & Filter Utama", expanded=True):
        c1, c2 = st.columns(2)
        f1 = c1.date_input("Dari Tanggal", t_awal, key="ana_date_1")
        f2 = c2.date_input("Sampai Tanggal", t_akhir, key="ana_date_2")
        
        tipe_filter = st.radio(
            "Tampilan Tabel di Bawah:",
            ["Semua Data", "Hanya Istirahat Hari", "Hanya Istirahat Jam", "Tidak Istirahat"],
            horizontal=True
        )

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", conn, params=[f1, f2])
    conn.close()

    if not df.empty:
        # 1. Pembersihan Data (Wajib agar jumlah baris sinkron dengan CSV)
        df = df.dropna(subset=['patient_name'])
        df['p_check'] = df['patient_name'].astype(str).str.strip().str.lower()
        df = df[~df['p_check'].isin(['none', 'nan', '', 'null'])].copy()
        
        # 2. Normalisasi Status & Durasi
        df['status_clean'] = df['rest_status'].fillna('Tidak').astype(str).str.strip().str.lower()
        df['dur_clean'] = pd.to_numeric(df['rest_duration'], errors='coerce').fillna(0)
        
        # 3. Pengelompokan Data
        df_istirahat = df[df['status_clean'].isin(['ya', 'y', 'yes'])].copy()
        df_tidak = df[~df['status_clean'].isin(['ya', 'y', 'yes'])].copy()
        
        # Pemisahan Hari (1-7) dan Jam (>7) sesuai hitungan manual Anda
        df_hari = df_istirahat[(df_istirahat['dur_clean'] >= 1) & (df_istirahat['dur_clean'] <= 7)]
        df_jam = df_istirahat[df_istirahat['dur_clean'] > 7]

        # --- 4. TAMPILAN RINGKASAN SESUAI DATA CSV ---
        st.subheader("📌 Validasi Data Istirahat")
        
        # Baris Pertama: Total Utama
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Data (Clean)", f"{len(df)} Orang")
        m2.metric("✅ Total Istirahat", f"{len(df_istirahat)} Orang")
        m3.metric("❌ Tidak Istirahat", f"{len(df_tidak)} Orang")
        
        # Baris Kedua: Detail Pembagian Istirahat
        st.markdown("---")
        st.write("### 📂 Detail Pembagian Istirahat")
        s1, s2 = st.columns(2)
        s1.metric("🛌 Istirahat Kategori HARI", f"{len(df_hari)} Orang", help="Durasi 1 - 7")
        s2.metric("⏱️ Istirahat Kategori JAM", f"{len(df_jam)} Orang", help="Durasi > 7")

        # --- 5. LOGIKA FILTER TABEL ---
        if tipe_filter == "Hanya Istirahat Hari":
            df_final = df_hari
        elif tipe_filter == "Hanya Istirahat Jam":
            df_final = df_jam
        elif tipe_filter == "Tidak Istirahat":
            df_final = df_tidak
        else:
            df_final = df

        if not df_final.empty:
            df_view = pd.DataFrame()
            df_view['No.'] = range(1, len(df_final) + 1)
            df_view['Nama Pasien'] = df_final['patient_name']
            df_view['Diagnosa'] = df_final['diagnosa']
            df_view['Status'] = df_final['status_clean'].str.upper()
            df_view['Durasi'] = df_final['dur_clean'].apply(lambda x: f"{int(x)} Hari" if x <= 7 and x > 0 else (f"{int(x)} Jam" if x > 7 else "-"))
            
            st.dataframe(df_view, hide_index=True, use_container_width=True)
        else:
            st.warning("Data tidak ditemukan untuk filter ini.")
    else:
        st.info("Database kosong pada periode ini.")

# --- 11. MODUL: MANAJEMEN USER (REGISTRASI DI DALAM) ---
elif menu == "Manajemen User":
    st.markdown("<h1>👤 MANAJEMEN PENGGUNA</h1>", unsafe_allow_html=True)
    
    # Hanya izinkan user 'admin' yang bisa buka menu ini (Opsional)
    if st.session_state["username"] == "admin":
        with st.expander("🆕 Tambah Pengguna Baru", expanded=True):
            new_u = st.text_input("Username Baru", key="reg_user")
            new_p = st.text_input("Password Baru", type="password", key="reg_pwd")
            confirm_p = st.text_input("Konfirmasi Password", type="password", key="reg_confirm")
            
            if st.button("✅ DAFTARKAN USER", use_container_width=True):
                if new_u and new_p == confirm_p:
                    if add_userdata(new_u, new_p):
                        st.success(f"Berhasil! Akun '{new_u}' sekarang sudah bisa digunakan.")
                    else:
                        st.error("❌ Username sudah ada.")
                else:
                    st.warning("⚠️ Cek kembali input password Anda.")
                    
        # Tampilkan daftar user yang ada (Opsional)
        st.markdown("---")
        st.subheader("📋 Daftar Pengguna Sistem")
        conn = sqlite3.connect(DB_PATH)
        df_user = pd.read_sql_query("SELECT username FROM userstable", conn)
        conn.close()
        st.table(df_user)
    else:
        st.error("🚫 Maaf, hanya akun 'admin' yang boleh menambah user baru.")
