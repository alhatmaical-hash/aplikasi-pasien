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
    ["Upload Data CSV", "Laporan 10 Penyakit", "Analisis Dept & Perusahaan", "Keterangan Istirahat", "Lihat Semua Data", "Analisis Istirahat"])

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

# --- 9. MODUL: LIHAT DATA (DENGAN TOTAL YA/TIDAK) ---
elif menu == "Lihat Semua Data":
    st.markdown("<h1>📂 DATABASE REKAP MEDIS</h1>", unsafe_allow_html=True)
    
    t_awal, t_akhir = get_date_range()
    
    with st.expander("🔍 Filter & Statistik", expanded=True):
        c1, c2, c3 = st.columns([1,1,2])
        f1 = c1.date_input("Mulai", t_awal)
        f2 = c2.date_input("Sampai", t_akhir)
        st_filter = c3.selectbox("Filter Tampilan Tabel:", ["Semua", "Ya", "Tidak"])

    conn = sqlite3.connect(DB_PATH)
    df_raw = pd.read_sql_query("SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", conn, params=[f1, f2])
    
    if not df_raw.empty:
        # --- 1. PEMBERSIHAN BARIS NONE (WAJIB) ---
        df_raw = df_raw.dropna(subset=['patient_name'])
        df_raw['p_name_check'] = df_raw['patient_name'].astype(str).str.strip().str.lower()
        df_raw = df_raw[~df_raw['p_name_check'].isin(['none', 'nan', '', 'null'])].copy()

        if not df_raw.empty:
            # --- 2. LOGIKA PEMBERSIHAN STATUS ---
            df_raw['status_clean'] = df_raw['rest_status'].fillna('Tidak').astype(str).str.strip().str.lower()
            df_raw['dur_clean'] = pd.to_numeric(df_raw['rest_duration'], errors='coerce').fillna(0)

            # --- 3. HITUNG TOTAL YA vs TIDAK (STATISTIK UTAMA) ---
            # Menghitung berdasarkan status_clean yang sudah diseragamkan
            total_ya = len(df_raw[df_raw['status_clean'].isin(['ya', 'y', 'yes'])])
            total_tidak = len(df_raw[df_raw['status_clean'].isin(['tidak', 't', 'no', ''])])
            total_semua = len(df_raw)

            # Tampilkan Metrik Statistik di bagian atas
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Data Pasien", f"{total_semua} Orang")
            m2.metric("Total Istirahat (YA)", f"{total_ya} Orang", delta="Perlu Istirahat", delta_color="normal")
            m3.metric("Total Tidak Istirahat", f"{total_tidak} Orang", delta="Langsung Kerja", delta_color="inverse")
            
            st.markdown("---")

            # --- 4. FILTER TAMPILAN TABEL ---
            if st_filter == "Ya":
                df_tampil = df_raw[df_raw['status_clean'].isin(['ya', 'yes', 'y'])].copy()
            elif st_filter == "Tidak":
                df_tampil = df_raw[df_raw['status_clean'].isin(['tidak', 'no', 't', 'n', ''])].copy()
            else:
                df_tampil = df_raw.copy()

            if not df_tampil.empty:
                # Susun Tabel Tampilan
                df_display = pd.DataFrame()
                df_display['No.'] = range(1, len(df_tampil) + 1)
                df_display['Pilih'] = False
                df_display['Visit Time'] = df_tampil['visit_time']
                df_display['Patient Name'] = df_tampil['patient_name']
                df_display['Diagnosa'] = df_tampil['diagnosa']
                df_display['Clinic'] = df_tampil['clinic']
                df_display['Company'] = df_tampil['company']
                df_display['Department'] = df_tampil['department']
                df_display['Istirahat (Y/T)'] = df_tampil['rest_status']
                
                # Logika Hari vs Jam
                df_display['Istirahat Hari'] = df_tampil.apply(
                    lambda x: f"{int(float(x['dur_clean']))}" if (x['status_clean'] in ['ya','y'] and 1 <= float(x['dur_clean']) <= 7) else "-", axis=1
                )
                df_display['Istirahat Jam'] = df_tampil.apply(
                    lambda x: f"{int(float(x['dur_clean']))}" if (x['status_clean'] in ['ya','y'] and float(x['dur_clean']) > 7) else "-", axis=1
                )
                df_display['db_id'] = df_tampil['id']

                # Render Tabel
                edited_df = st.data_editor(
                    df_display, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={"db_id": None, "Pilih": st.column_config.CheckboxColumn("Hapus?")},
                    disabled=[c for c in df_display.columns if c != "Pilih"]
                )

                # Tombol Aksi Hapus
                if st.button("🗑️ HAPUS DATA TERPILIH", use_container_width=True):
                    ids = edited_df[edited_df['Pilih'] == True]['db_id'].tolist()
                    if ids:
                        conn.cursor().execute(f"DELETE FROM rekap_penyakit WHERE id IN ({','.join(['?']*len(ids))})", ids)
                        conn.commit()
                        st.success(f"Berhasil menghapus {len(ids)} data.")
                        st.rerun()
            else:
                st.warning(f"Tidak ada data dengan filter '{st_filter}' pada periode ini.")
        else:
            st.warning("Data bersih tidak ditemukan (semua baris kosong).")
    else:
        st.info("Database kosong pada rentang tanggal ini.")
    
    conn.close()

# --- 10. MODUL: ANALISIS ISTIRAHAT PASIEN (DENGAN FILTER DETAIL) ---
elif menu == "Analisis Istirahat":
    st.markdown("<h1>📊 ANALISIS DETAIL ISTIRAHAT</h1>", unsafe_allow_html=True)
    
    t_awal, t_akhir = get_date_range()
    
    with st.expander("📅 Pengaturan Periode & Filter Utama", expanded=True):
        c1, c2 = st.columns(2)
        f1 = c1.date_input("Dari Tanggal", t_awal, key="ana_date_1")
        f2 = c2.date_input("Sampai Tanggal", t_akhir, key="ana_date_2")
        
        # Tombol Filter Spesifik
        tipe_filter = st.radio(
            "Pilih Kategori Analisis:",
            ["Semua Istirahat", "Hanya Istirahat Hari (1-7)", "Hanya Istirahat Jam (> 7)"],
            horizontal=True
        )

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", conn, params=[f1, f2])
    conn.close()

    if not df.empty:
        # --- PEMBERSIHAN DATA ---
        df = df.dropna(subset=['patient_name'])
        df['status_clean'] = df['rest_status'].fillna('Tidak').astype(str).str.strip().str.lower()
        df['dur_clean'] = pd.to_numeric(df['rest_duration'], errors='coerce').fillna(0)
        
        # Hanya ambil yang statusnya 'Ya' untuk analisis ini
        df_ya = df[df['status_clean'].isin(['ya', 'y', 'yes'])].copy()

        # Logika Pemisahan Data
        df_hari = df_ya[(df_ya['dur_clean'] >= 1) & (df_ya['dur_clean'] <= 7)]
        df_jam = df_ya[df_ya['dur_clean'] > 7]

        # --- LOGIKA TOMBOL FILTER ---
        if tipe_filter == "Hanya Istirahat Hari (1-7)":
            df_final = df_hari
            label_stat = "Istirahat Hari"
            warna = "blue"
        elif tipe_filter == "Hanya Istirahat Jam (> 7)":
            df_final = df_jam
            label_stat = "Istirahat Jam"
            warna = "orange"
        else:
            df_final = df_ya
            label_stat = "Total Istirahat (Ya)"
            warna = "green"

        # --- TAMPILAN STATISTIK RINGKAS ---
        st.subheader(f"📈 Statistik: {tipe_filter}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Jumlah Pasien", f"{len(df_final)} Orang")
        col2.metric("Rata-rata Durasi", f"{round(df_final['dur_clean'].mean(), 1) if not df_final.empty else 0}")
        col3.metric("Total Kunjungan Umum", f"{len(df)} Orang")

        st.markdown("---")

        if not df_final.empty:
            # Tampilkan Tabel Hasil Filter
            st.write(f"**Daftar Pasien ({label_stat}):**")
            
            # Susun Tabel Tampilan
            df_view = pd.DataFrame()
            df_view['No.'] = range(1, len(df_final) + 1)
            df_view['Visit Time'] = df_final['visit_time']
            df_view['Patient Name'] = df_final['patient_name']
            df_view['Diagnosa'] = df_final['diagnosa']
            df_view['Company'] = df_final['company']
            df_view['Durasi'] = df_final['dur_clean'].apply(lambda x: f"{int(x)} {'Hari' if x <= 7 else 'Jam'}")
            
            st.dataframe(df_view, hide_index=True, use_container_width=True)
            
            # Tombol Download Data Terfilter
            csv = df_view.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download Data {label_stat}",
                data=csv,
                file_name=f'analisis_{label_stat.lower().replace(" ", "_")}.csv',
                mime='text/csv',
            )
        else:
            st.warning(f"Tidak ada data ditemukan untuk kategori {tipe_filter}")
