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
    # Membuat tabel dengan kolom terpisah sesuai gambar
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  visit_time TEXT, patient_name TEXT, diagnosa TEXT, 
                  clinic TEXT, departemen TEXT, company TEXT,
                  rest_status TEXT, istirahat_hari INTEGER, istirahat_jam INTEGER)''')
    
    # Pastikan migrasi kolom baru masuk ke DB yang sudah ada
    kolom_baru = [('istirahat_hari', 'INTEGER'), ('istirahat_jam', 'INTEGER')]
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

# --- 5. MODUL 1: UPLOAD DATA (VERSI PERBAIKAN SPASI & KOLOM) ---
if menu == "Upload Data CSV":
    st.markdown("<h1>📤 UPLOAD DATA PASIEN</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # Normalisasi nama kolom agar spasi jadi underscore
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            
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
                    
                    # Kolom wajib sesuai gambar (istirahat_hari & istirahat_jam terpisah)
                    kolom_wajib = ['visit_time', 'patient_name', 'diagnosa', 'clinic', 'departemen', 'company', 'rest_status', 'istirahat_hari', 'istirahat_jam']
                    
                    # Tambahkan kolom jika tidak ada di CSV
                    for col in kolom_wajib:
                        if col not in df.columns:
                            df[col] = 0 if 'istirahat' in col else "-"
                    
                    # Ambil data aktual tanpa merubah angka (sesuai permintaan)
                    df_to_save = df[kolom_wajib].copy()
                    df_to_save['istirahat_hari'] = pd.to_numeric(df_to_save['istirahat_hari'], errors='coerce').fillna(0).astype(int)
                    df_to_save['istirahat_jam'] = pd.to_numeric(df_to_save['istirahat_jam'], errors='coerce').fillna(0).astype(int)

                    # Simpan ke tabel rekap_penyakit
                    df_to_save.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Berhasil menyimpan {len(df_to_save)} data pasien.")
                    st.balloons()
                else:
                    st.warning("⚠️ File CSV tidak berisi data valid.")
                    if 'conn' in locals(): conn.close()

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
        # --- PERBAIKAN NOMOR URUT (MULAI DARI 1) ---
        df_top.index = range(1, len(df_top) + 1) # Mengubah index agar mulai dari 1
        df_top.index.name = 'No' # Memberi nama kolom index menjadi 'No'
        
        # Menampilkan tabel (gunakan reset_index agar kolom 'No' muncul di tabel)
        st.dataframe(df_top.reset_index(), use_container_width=True, hide_index=True)
        
        st.bar_chart(df_top.set_index('diagnosa')['jumlah'])
    else:
        st.warning("Data tidak tersedia.")

# --- 7. MODUL 3: ANALISIS DEPT & PERUSAHAAN (VERSI TABEL & GRAFIK) ---
elif menu == "Analisis Dept & Perusahaan":
    st.markdown("<h1>🏢 ANALISIS KUNJUNGAN</h1>", unsafe_allow_html=True)
    start, end = st.columns(2)
    t1 = start.date_input("Mulai", value=get_date_range()[0], key="a1")
    t2 = end.date_input("Sampai", value=get_date_range()[1], key="a2")
    
    conn = sqlite3.connect(DB_PATH)
    # Gunakan nama kolom 'departemen' agar sinkron dengan modul lainnya
    query = f"SELECT departemen, company FROM rekap_penyakit WHERE visit_time BETWEEN '{t1}' AND '{t2}'"
    df_data = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_data.empty:
        tab1, tab2 = st.tabs(["📊 Departemen", "🏢 Perusahaan"])
        
        with tab1:
            st.write("### Rekapitulasi Kunjungan Per Departemen")
            # Membuat tabel perhitungan
            dept_counts = df_data['departemen'].value_counts().reset_index()
            dept_counts.columns = ['Nama Departemen', 'Total Kunjungan']
            
            c1, c2 = st.columns([1, 2])
            with c1:
                # Menampilkan Tabel
                st.dataframe(dept_counts, hide_index=True, use_container_width=True)
            with c2:
                # Menampilkan Grafik
                st.bar_chart(dept_counts.set_index('Nama Departemen'))

        with tab2:
            st.write("### Rekapitulasi Kunjungan Per Perusahaan")
            # Membuat tabel perhitungan
            comp_counts = df_data['company'].value_counts().reset_index()
            comp_counts.columns = ['Nama Perusahaan', 'Total Kunjungan']
            
            c1, c2 = st.columns([1, 2])
            with c1:
                # Menampilkan Tabel
                st.dataframe(comp_counts, hide_index=True, use_container_width=True)
            with c2:
                # Menampilkan Grafik
                st.bar_chart(comp_counts.set_index('Nama Perusahaan'))
    else:
        st.warning("Data tidak ditemukan pada periode ini.")

# --- 8. MODUL 4: ANALISIS ISTIRAHAT (VERSI PERBAIKAN RUMUS) ---
elif menu == "Keterangan Istirahat":
    st.markdown("<h1>📋 REKAPITULASI TOTAL DATA SICK</h1>", unsafe_allow_html=True)
    
    # 1. Filter Tanggal
    t_awal, t_akhir = get_date_range()
    t1, t2 = st.columns(2)
    start = t1.date_input("Mulai", value=t_awal, key="r1")
    end = t2.date_input("Sampai", value=t_akhir, key="r2")

    conn = sqlite3.connect(DB_PATH)
    # AMBIL SEMUA KOLOM TERKAIT (Termasuk istirahat_hari dan istirahat_jam)
    query = "SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?"
    df_raw = pd.read_sql_query(query, conn, params=[start, end])
    conn.close()

    if not df_raw.empty:
        # --- PRE-PROCESSING DATA (PEMBERSIHAN) ---
        df_raw['company'] = df_raw['company'].fillna('UNKNOWN').str.upper().str.strip()
        df_raw['status_lower'] = df_raw['rest_status'].fillna('tidak').str.lower().str.strip()
        
        # Konversi kolom durasi ke angka agar bisa dihitung
        df_raw['h_num'] = pd.to_numeric(df_raw['istirahat_hari'], errors='coerce').fillna(0)
        df_raw['j_num'] = pd.to_numeric(df_raw['istirahat_jam'], errors='coerce').fillna(0)
        
        selisih_hari = (end - start).days + 1
        bulan_nama = start.strftime("%B").upper()

        # --- RUMUS BARU: MENGHITUNG BERDASARKAN KOLOM SPESIFIK ---
        def get_summary_table(df_filtered):
            if df_filtered.empty:
                return None
            
            total_pasien = len(df_filtered)
            
            # Hitung baris yang memiliki nilai > 0 di masing-masing kolom
            # Syarat: Status harus 'Ya' DAN angkanya bukan 0
            ist_hari = len(df_filtered[(df_filtered['status_lower'].isin(['ya', 'yes', 'y'])) & (df_filtered['h_num'] > 0)])
            ist_jam = len(df_filtered[(df_filtered['status_lower'].isin(['ya', 'yes', 'y'])) & (df_filtered['j_num'] > 0)])
            
            summary = pd.DataFrame({
                "TAHUN": [start.year],
                "BULAN": [bulan_nama],
                "TANGGAL": [f"{start.day} SAMPAI {end.day}"],
                "ANGKA KUNJUNGAN SAKIT": [f"{total_pasien} PASIEN"],
                "REKOMENDASI PER-HARI": [f"{ist_hari} PASIEN"],
                "REKOMENDASI PER-JAM": [f"{ist_jam} PASIEN"],
                "HARI KERJA": [f"{selisih_hari} HARI"]
            })
            return summary

        # --- DAFTAR LIST KONTRAKTOR ---
        list_hjf = ["PT INDO FUDONG (HJF)", "PT IMJ ( INOVASI MAJU JAYA) HJF", "PT BTG-ZJYC (ONC)", "PT. ZJYC ONC", "PT. GDSK (HJF)", "PT GLOBEL DARMA SARANA KARYA GDSK (HJF)", "PT GOBEL DHARMA SARANA KARYA GDSK (HJF)", "PT GEOSERVICES MAKASSAR", "PT. RENTOKIL INDONESIA", "PT.MATAHARI PUTRA PRIMA (HYPERMART) HJF"]
        list_kps = ["PT MCC BAOYE (KPS)", "PT MCC6 (KPS)", "PT. JINRUI KPS", "PT YAOHUA (KPS)", "PT CREC (KPS)", "PT. CISDI (KPS)", "PT CISDI-KPS", "PT JME-KPS", "PT. ETGH-KPS", "PT. BTG ZJYC (KPS)"]
        list_ost = ["PT. MCCBY DCM", "PT LONGI & CENTER OST", "PT CREC (OST)", "PT STHB (OST)", "PT ZTPI -OST", "PT ZTPI-(OST)", "ZTPI (OST)", "PT. ZTPI/ OST", "PT ZTPI (OST)", "PT JIANGXI (OST)", "PT. CCEPC OST", "PT INDO FUDONG (OST)", "PT CSCEC (OST)"]
        list_ckm = ["PT. MCC BAOYE (CKM)"]

        # --- TAMPILAN SISTEM TAB ---
        st.write("### 🏢 Pilih Ringkasan Perusahaan")
        tab1, tab2, tab3, tab4 = st.tabs(["HJF GROUP", "KPS GROUP", "OST GROUP", "CKM GROUP"])

        with tab1:
            st.subheader("PT. HALMAHERA JAYA FERONIKEL (HJF)")
            induk = df_raw[df_raw['company'].str.contains("HALMAHERA", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            else: st.info("Data Induk HJF Tidak Ditemukan")
            
            st.subheader("KONTRAKTOR HJF")
            kon = df_raw[df_raw['company'].isin(list_hjf)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)
            else: st.info("Data Kontraktor HJF Tidak Ditemukan")

        with tab2:
            st.subheader("PT. KARUNIA PERMAI SENTOSA (KPS)")
            induk = df_raw[df_raw['company'].str.contains("KARUNIA", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            else: st.info("Data Induk KPS Tidak Ditemukan")
            
            st.subheader("KONTRAKTOR KPS")
            kon = df_raw[df_raw['company'].isin(list_kps)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)
            else: st.info("Data Kontraktor KPS Tidak Ditemukan")

        with tab3:
            st.subheader("PT. OBI SINAR TIMUR (OST)")
            induk = df_raw[df_raw['company'].str.contains("OBI SINAR", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            else: st.info("Data Induk OST Tidak Ditemukan")
            
            st.subheader("KONTRAKTOR OST")
            kon = df_raw[df_raw['company'].isin(list_ost)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)
            else: st.info("Data Kontraktor OST Tidak Ditemukan")

        with tab4:
            st.subheader("PT. CIPTA KEMAKMURAN MITRA (CKM)")
            induk = df_raw[df_raw['company'].str.contains("CIPTA KEMAKMURAN", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            else: st.info("Data Induk CKM Tidak Ditemukan")
            
            st.subheader("KONTRAKTOR CKM")
            kon = df_raw[df_raw['company'].isin(list_ckm)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)
            else: st.info("Data Kontraktor CKM Tidak Ditemukan")

        # --- CATATAN KAKI ---
        st.markdown("---")
        st.markdown("<p style='color:red; font-weight:bold; text-align:center;'>NOTE : DAFTAR KUNJUNGAN DAN JUMLAH REKOMENDASI ISTIRAHAT GABUNG DENGAN 3 DEVISI (RANAP, RAJAL, UGD).</p>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ Belum ada data untuk periode tanggal ini.")
# --- 9. MODUL: LIHAT SEMUA DATA (DENGAN DURASI, DEPT, & PERUSAHAAN) ---
elif menu == "Lihat Semua Data":
    st.markdown("<h1>📂 DATABASE REKAM MEDIS</h1>", unsafe_allow_html=True)
    
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

          # --- PERBAIKAN PENYUSUNAN TABEL (AGAR HARI & JAM TAMPIL) ---
            df_display = pd.DataFrame()
            df_display['No.'] = range(1, len(df_tampil) + 1)
            df_display['Pilih'] = False
            df_display['Tanggal'] = df_tampil['visit_time']
            df_display['Nama Pasien'] = df_tampil['patient_name']
            df_display['Diagnosa'] = df_tampil['diagnosa']
            df_display['Clinic'] = df_tampil['clinic']
            df_display['Departemen'] = df_tampil['departemen']
            df_display['Perusahaan'] = df_tampil['company']
            df_display['Status'] = df_tampil['rest_status'].astype(str).str.upper()
            
            # 1. Pastikan data None/NaN diubah jadi 0 dulu agar bisa diproses
            # 2. Kemudian ubah angka 0 menjadi '-' agar tampilan di tabel rapi
            df_display['Istirahat Hari'] = pd.to_numeric(df_tampil['istirahat_hari'], errors='coerce').fillna(0).replace(0, '-')
            df_display['Istirahat Jam'] = pd.to_numeric(df_tampil['istirahat_jam'], errors='coerce').fillna(0).replace(0, '-')
            
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
# --- 10. MODUL: ANALISIS ISTIRAHAT (TAMPILKAN SEMUA DATA & HITUNG) ---
elif menu == "Analisis Istirahat":
    st.markdown("<h1>📊 ANALISIS DETAIL ISTIRAHAT</h1>", unsafe_allow_html=True)
    
    t_awal, t_akhir = get_date_range()
    
    with st.expander("📅 Pengaturan Periode", expanded=True):
        c1, c2 = st.columns(2)
        f1 = c1.date_input("Dari Tanggal", t_awal, key="ana_date_1")
        f2 = c2.date_input("Sampai Tanggal", t_akhir, key="ana_date_2")

    conn = sqlite3.connect(DB_PATH)
    # Mengambil semua data tanpa filter DISTINCT agar data double tetap muncul
    df = pd.read_sql_query("SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", conn, params=[f1, f2])
    conn.close()

    if not df.empty:
        # 1. Normalisasi tampilan agar TIDAK ADA "NONE"
        # Semua sel kosong diisi "-" agar tabel terlihat bersih
        df = df.fillna("-")
        
        # Konversi kolom istirahat ke angka hanya untuk keperluan perhitungan statistik
        df['istirahat_hari_num'] = pd.to_numeric(df['istirahat_hari'], errors='coerce').fillna(0)
        df['istirahat_jam_num'] = pd.to_numeric(df['istirahat_jam'], errors='coerce').fillna(0)
        df['status_clean'] = df['rest_status'].astype(str).str.strip().str.lower()
        
        # 2. Perhitungan Statistik (Hanya Menghitung)
        df_istirahat = df[df['status_clean'].isin(['ya', 'yes', 'y'])].copy()
        df_tidak = df[~df['status_clean'].isin(['ya', 'yes', 'y'])].copy()
        
        df_hari_only = df_istirahat[df_istirahat['istirahat_hari_num'] > 0]
        df_jam_only = df_istirahat[df_istirahat['istirahat_jam_num'] > 0]
        
        # 3. Tampilan Ringkasan (Metric)
        st.subheader("📌 Ringkasan Status Pasien")
        
        if 'filter_pilihan' not in st.session_state:
            st.session_state.filter_pilihan = "Semua"

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Data", f"{len(df)} Orang")
        if m1.button("Lihat Semua Data", use_container_width=True):
            st.session_state.filter_pilihan = "Semua"
            
        m2.metric("Total Istirahat", f"{len(df_istirahat)} Orang")
        if m2.button("Lihat Daftar Istirahat", use_container_width=True):
            st.session_state.filter_pilihan = "Istirahat"
            
        m3.metric("Kembali Bekerja", f"{len(df_tidak)} Orang")
        if m3.button("Lihat Daftar Kembali Kerja", use_container_width=True):
            st.session_state.filter_pilihan = "Tidak"

        # 4. Statistik Durasi
        st.markdown("---")
        s1, s2 = st.columns(2)
        s1.metric("🛌 Kategori HARI", f"{len(df_hari_only)} Orang")
        s2.metric("⏱️ Kategori JAM", f"{len(df_jam_only)} Orang")
        
        if s1.button("Filter Kategori HARI", use_container_width=True):
            st.session_state.filter_pilihan = "Hari"
        if s2.button("Filter Kategori JAM", use_container_width=True):
            st.session_state.filter_pilihan = "Jam"

        # 5. Penentuan Data yang Ditampilkan Tabel
        if st.session_state.filter_pilihan == "Istirahat":
            df_final = df_istirahat
        elif st.session_state.filter_pilihan == "Tidak":
            df_final = df_tidak
        elif st.session_state.filter_pilihan == "Hari":
            df_final = df_hari_only
        elif st.session_state.filter_pilihan == "Jam":
            df_final = df_jam_only
        else:
            df_final = df

        # 6. Tampilkan Tabel Apa Adanya (Sesuai Data Mentah)
        st.write(f"### 📋 Menampilkan: {st.session_state.filter_pilihan}")
        
        if not df_final.empty:
            df_view = pd.DataFrame()
            df_view['No.'] = range(1, len(df_final) + 1)
            df_view['Tanggal'] = df_final['visit_time']
            df_view['Nama Pasien'] = df_final['patient_name']
            df_view['Diagnosa'] = df_final['diagnosa']
            df_view['Clinic'] = df_final['clinic']
            df_view['Departemen'] = df_final['departemen']
            df_view['Perusahaan'] = df_final['company']
            df_view['Status'] = df_final['rest_status'].astype(str).str.upper()
            
            # Tampilkan angka asli dari database, ganti 0 dengan "-" untuk kerapian
            df_view['Istirahat Hari'] = df_final['istirahat_hari'].replace(0, '-')
            df_view['Istirahat Jam'] = df_final['istirahat_jam'].replace(0, '-')
            
            st.dataframe(df_view, hide_index=True, use_container_width=True)
        else:
            st.warning("Data tidak ditemukan untuk kategori ini.")
            
    else:
        st.info("ℹ️ Database kosong untuk periode tanggal ini.")
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
