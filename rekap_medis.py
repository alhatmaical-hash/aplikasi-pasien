import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io

# --- 0. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. LOGIKA PASSWORD ---
if "admin_password" not in st.session_state:
    st.session_state["admin_password"] = "admin123"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🏥 Akses Terbatas - Klinik Apps")
    tab_login, tab_buat = st.tabs(["🔑 Masuk Sistem", "🆕 Buat/Ganti Password"])
    
    with tab_login:
        pwd_input = st.text_input("Masukkan Password Admin:", type="password", key="login_pwd")
        if st.button("🚀 MASUK KE SISTEM KLINIK", use_container_width=True, type="primary"):
            if pwd_input == st.session_state["admin_password"]:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Password Salah!")
    
    with tab_buat:
        old_p = st.text_input("Password Lama", type="password", key="old_p")
        new_p = st.text_input("Password Baru", type="password", key="new_p")
        if st.button("SIMPAN & UPDATE PASSWORD"):
            if old_p == st.session_state["admin_password"]:
                if new_p:
                    st.session_state["admin_password"] = new_p
                    st.success("✅ Berhasil! Silakan kembali ke tab Masuk.")
                else:
                    st.warning("⚠️ Password baru kosong.")
            else:
                st.error("❌ Password lama salah.")
    st.stop()

# --- 2. SETTING DATABASE & FUNGSI ---
DB_PATH = 'klinik_data.db'

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
    ["Upload Data CSV", "Laporan 10 Penyakit", "Analisis Dept & Perusahaan", "Keterangan Istirahat", "Lihat Semua Data"])

if st.sidebar.button("🔴 KELUAR APLIKASI", type="primary", use_container_width=True):
    st.session_state["authenticated"] = False
    st.rerun()

# --- 5. MODUL 1: UPLOAD DATA ---
if menu == "Upload Data CSV":
    st.markdown("<h1>📤 UPLOAD DATA PASIEN</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        st.write("### 🔍 Pratinjau Data:")
        st.dataframe(df.head(), use_container_width=True)
        
        if st.button("💾 SIMPAN KE DATABASE SEKARANG", use_container_width=True, type="primary"):
            try:
                conn = sqlite3.connect(DB_PATH)
                df['visit_time'] = pd.to_datetime(df['visit_time']).dt.strftime('%Y-%m-%d')
                
                # --- KODE PENGAMAN: Tambahkan kolom jika tidak ada di CSV ---
                for col in ['rest_status', 'rest_type', 'rest_duration']:
                    if col not in df.columns:
                        if col == 'rest_duration':
                            df[col] = 0 # Default angka 0
                        else:
                            df[col] = "Tidak" # Default status Tidak
                
                kolom_target = ['visit_time', 'patient_name', 'diagnosa', 'clinic', 'department', 'company', 'rest_status', 'rest_type', 'rest_duration']
                
                df_to_save = df[kolom_target]
                df_to_save.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                st.success("✅ Berhasil Disimpan!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

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

# --- 9. MODUL: LIHAT & HAPUS DATA (SESUAI TABEL UPLOAD) ---
elif menu == "Lihat Semua Data":
    st.markdown("<h1>📂 DATABASE REKAP MEDIS</h1>", unsafe_allow_html=True)
    
    # Ambil rentang tanggal dari database untuk default filter
    awal_db, akhir_db = get_date_range()
    
    # --- AREA FILTER & PENCARIAN ---
    with st.expander("🔍 Filter Pencarian Data", expanded=True):
        c1, c2, c3 = st.columns([1, 1, 2])
        f1 = c1.date_input("Dari Tanggal", value=awal_db, key="filter_tgl1")
        f2 = c2.date_input("Sampai Tanggal", value=akhir_db, key="filter_tgl2")
        cari = c3.text_input("Cari Nama Pasien", placeholder="Ketik nama pasien di sini...")

    # Koneksi ke Database
    conn = sqlite3.connect(DB_PATH)
    
    # Query dengan Filter Tanggal dan Nama
    query = "SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?"
    params = [f1, f2]
    if cari:
        query += " AND patient_name LIKE ?"
        params.append(f'%{cari}%')
    
    df_raw = pd.read_sql_query(query, conn, params=params)
    
    if not df_raw.empty:
        # --- MENYUSUN TAMPILAN TABEL (SESUAI URUTAN UPLOAD) ---
        df_display = pd.DataFrame()
        
        # 1. Nomor Urut & Checkbox Hapus
        df_display['No.'] = range(1, len(df_raw) + 1)
        df_display['Pilih'] = False
        
        # 2. Kolom Utama (Urutan sesuai Gambar Upload Anda)
        df_display['Visit Time'] = df_raw['visit_time']
        df_display['Patient Name'] = df_raw['patient_name']
        df_display['Diagnosa'] = df_raw['diagnosa']
        df_display['Clinic'] = df_raw['clinic']
        df_display['Company'] = df_raw['company']
        df_display['Department'] = df_raw['department']
        
        # 3. Kolom Keterangan Istirahat (Custom Request)
        df_display['Istirahat (Y/T)'] = df_raw['rest_status']
        
        # Logika memisahkan durasi Hari dan Jam
        df_display['Istirahat Hari'] = df_raw.apply(
            lambda x: x['rest_duration'] if str(x['rest_type']).lower() == 'hari' else "-", axis=1
        )
        df_display['Istirahat Jam'] = df_raw.apply(
            lambda x: x['rest_duration'] if str(x['rest_type']).lower() == 'jam' else "-", axis=1
        )
        
        # Simpan ID asli (Hidden) untuk keperluan hapus data
        df_display['db_id'] = df_raw['id']

        # --- MENAMPILKAN TABEL INTERAKTIF ---
        st.write(f"Menampilkan **{len(df_display)}** data ditemukan:")
        
        edited_df = st.data_editor(
            df_display, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "db_id": None, # Sembunyikan ID Database asli dari user
                "Pilih": st.column_config.CheckboxColumn("Hapus?", default=False),
                "No.": st.column_config.Column(width="small"),
                "Visit Time": st.column_config.Column(width="medium"),
                "Patient Name": st.column_config.Column(width="large"),
                "Istirahat (Y/T)": st.column_config.Column(width="small"),
            },
            disabled=[c for c in df_display.columns if c != "Pilih"] # Hanya kolom 'Pilih' yang bisa diklik
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- TOMBOL AKSI (HAPUS) ---
        col_btn1, col_btn2 = st.columns([1, 4])
        
        with col_btn1:
            if st.button("🗑️ HAPUS TERPILIH", use_container_width=True):
                ids_to_delete = edited_df[edited_df['Pilih'] == True]['db_id'].tolist()
                if ids_to_delete:
                    cur = conn.cursor()
                    placeholder = ','.join(['?'] * len(ids_to_delete))
                    cur.execute(f"DELETE FROM rekap_penyakit WHERE id IN ({placeholder})", ids_to_delete)
                    conn.commit()
                    st.success(f"✅ {len(ids_to_delete)} data berhasil dihapus!")
                    st.rerun()
                else:
                    st.warning("Silakan centang kolom 'Hapus' pada data yang ingin dibuang.")

        with col_btn2:
            # Fitur pengaman untuk mengosongkan database
            if st.checkbox("⚠️ Aktifkan Tombol Kosongkan Seluruh Database"):
                if st.button("🔥 DELETE ALL DATA PERMANENTLY", type="primary"):
                    cur = conn.cursor()
                    cur.execute("DELETE FROM rekap_penyakit")
                    cur.execute("DELETE FROM sqlite_sequence WHERE name='rekap_penyakit'")
                    conn.commit()
                    st.success("✅ Database telah dikosongkan secara total!")
                    st.rerun()

    else:
        st.info("Tidak ada data ditemukan. Pastikan rentang tanggal sudah benar atau coba upload data baru di menu Upload.")
    
    conn.close()
