import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io 

st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# --- LOGIKA PASSWORD DENGAN FITUR BUAT/GANTI PASSWORD ---
if "admin_password" not in st.session_state:
    st.session_state["admin_password"] = "admin123"  # Password awal

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🏥 Akses Terbatas - Klinik Apps")
    
    # Membuat dua tab: Satu untuk Masuk, satu untuk Atur Password
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
        st.info("Gunakan menu ini untuk membuat password baru jika Anda tahu password lama.")
        old_p = st.text_input("Password Lama (Default: admin123)", type="password", key="old_p")
        new_p = st.text_input("Password Baru yang Diinginkan", type="password", key="new_p")
        
        if st.button("SIMPAN & UPDATE PASSWORD"):
            if old_p == st.session_state["admin_password"]:
                if new_p:
                    st.session_state["admin_password"] = new_p
                    st.success("✅ Password berhasil diperbarui! Silakan kembali ke tab 'Masuk Sistem'.")
                else:
                    st.warning("⚠️ Password baru tidak boleh kosong.")
            else:
                st.error("❌ Password lama salah. Tidak bisa mengganti password.")
                
    st.stop() # Tetap mengunci bagian bawah aplikasi
# --- 1. SETTING DASAR ---
DB_PATH = 'klinik_data.db'

# --- 2. FUNGSI PENDUKUNG (WAJIB DI ATAS AGAR TIDAK NAMEERROR) ---
def get_date_range():
    try:
        conn = sqlite3.connect(DB_PATH)
        # Mengambil tanggal awal dan akhir dari database
        df_range = pd.read_sql_query("SELECT MIN(tgl_kunjungan) as awal, MAX(tgl_kunjungan) as akhir FROM rekap_penyakit", conn)
        conn.close()
        
        # Jika database masih kosong
        if df_range['awal'].iloc[0] is None:
            return date.today(), date.today()
        
        # Konversi hasil database ke format tanggal Python
        awal = pd.to_datetime(df_range['awal'].iloc[0]).date()
        akhir = pd.to_datetime(df_range['akhir'].iloc[0]).date()
        return awal, akhir
    except:
        # Jika terjadi error (misal tabel belum dibuat), gunakan tanggal hari ini
        return date.today(), date.today()

# --- 3. INISIALISASI DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  Visit Time TEXT, 
                  Patient Name TEXT, 
                  Diagnosa TEXT, 
                  Clinic TEXT,
                  Department TEXT,
                  Company TEXT)''')
    
    # Cek kolom tambahan jika belum ada (antisipasi versi lama)
    try:
        c.execute("ALTER TABLE rekap_penyakit ADD COLUMN departemen TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE rekap_penyakit ADD COLUMN perusahaan TEXT")
    except: pass
    
    conn.commit()
    conn.close()

init_db()

# --- 4. STYLE CSS (TOMBOL & TAMPILAN) ---
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    h1 { color: #2e7d32; text-align: center; font-weight: bold; }
    
    /* Style Tombol agar Bold & TULISAN HITAM */
    div.stButton > button {
        font-weight: bold !important;
        color: black !important; /* Diubah menjadi hitam */
        text-transform: uppercase;
        border-radius: 8px;
        height: 3em;
    }

    /* Memastikan teks di dalam tombol primary (merah) juga hitam */
    button[kind="primary"] p {
        color: black !important;
    }
    
    /* Warna Tombol Hapus Terpilih */
    div[data-testid="stHorizontalBlock"] div:nth-child(2) button {
        background-color: #D2691E !important;
    }
    
    /* Warna Tombol Delete All (Merah) */
    div[data-testid="stHorizontalBlock"] div:nth-child(3) button {
        background-color: #FF0000 !important;
    }

    /* Warna Tombol Keluar di Sidebar (Merah Terang) */
    button[kind="primary"] {
        background-color: #FF4B4B !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 APLIKASI REKAM MEDIS KHFO")
menu = st.sidebar.radio("MENU UTAMA", 
    ["Upload Data CSV", "Laporan 10 Penyakit", "Analisis Dept & Perusahaan", "Lihat Semua Data"])
# --- COPY & PASTE KODE INI DI BAWAH MENU RADIO ---
st.sidebar.write("---") # Garis pembatas agar rapi

with st.sidebar.expander("⚙️ PENGATURAN AKUN"):
    st.subheader("Ganti Password")
    pwd_lama = st.text_input("Password Saat Ini", type="password")
    pwd_baru = st.text_input("Password Baru", type="password")
    
    if st.button("SIMPAN PASSWORD BARU"):
        if pwd_lama == st.session_state["admin_password"]:
            if pwd_baru:
                st.session_state["admin_password"] = pwd_baru
                st.success("✅ Password berhasil diganti!")
            else:
                st.warning("⚠️ Password baru tidak boleh kosong.")
        else:
            st.error("❌ Password lama salah.")

    st.write("---")
    st.write("---")
        
    if st.button("🔴 KELUAR DARI APLIKASI", use_container_width=True, type="primary"):
       st.session_state["authenticated"] = False
       st.rerun()
# -----------------------------------------------
# --- 6. MODUL: UPLOAD DATA ---
if menu == "Upload Data CSV":
    st.markdown("<h1>📤 UPLOAD DATA PASIEN</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Pratinjau Data:", df.head())
        
        if st.button("SIMPAN KE DATABASE"):
            conn = sqlite3.connect(DB_PATH)
            df.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
            conn.close()
            st.success("✅ Data berhasil disimpan!")

# --- 7. MODUL: LAPORAN 10 PENYAKIT ---
elif menu == "Laporan 10 Penyakit":
    st.markdown("<h1>📊 10 PENYAKIT TERBESAR</h1>", unsafe_allow_html=True)
    
    tgl_awal_db, tgl_akhir_db = get_date_range()
    
    c1, c2 = st.columns(2)
    t1 = c1.date_input("Mulai", value=tgl_awal_db, key="l1")
    t2 = c2.date_input("Sampai", value=tgl_akhir_db, key="l2")

    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT diagnosa AS 'Diagnosa Penyakit', COUNT(*) AS 'Jumlah Kasus' 
        FROM rekap_penyakit 
        WHERE tgl_kunjungan BETWEEN '{t1}' AND '{t2}' 
        GROUP BY diagnosa 
        ORDER BY [Jumlah Kasus] DESC 
        LIMIT 10
    """
    df_top = pd.read_sql_query(query, conn)
    conn.close()

    if not df_top.empty:
        # Tambahkan Nomor Urut
        df_report = df_top.copy()
        df_report.insert(0, 'No.', range(1, len(df_report) + 1))
        
        # --- 1. TABEL DATA (DI ATAS) ---
        st.markdown("### 📋 Tabel Peringkat")
        st.dataframe(df_report, use_container_width=True, hide_index=True)

        # --- 2. GRAFIK (DI TENGAH) ---
        st.markdown("### 📈 Visualisasi")
        # Menggunakan kolom agar grafik tidak terlalu lebar (proporsional)
        col_kiri, col_tengah, col_kanan = st.columns([1, 4, 1])
        with col_tengah:
            st.bar_chart(df_report.set_index('Diagnosa Penyakit')['Jumlah Kasus'])

        # --- 3. TOMBOL DOWNLOAD (SEKARANG DI PALING BAWAH) ---
        st.markdown("---") # Garis pemisah tipis
        st.markdown("### 📥 Simpan Laporan")
        
        csv_data = df_report.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 DOWNLOAD LAPORAN (CSV)",
            data=csv_data,
            file_name=f"Laporan_10_Penyakit_{t1}.csv",
            mime='text/csv',
            use_container_width=True
        )

    else:
        st.warning("Data tidak ditemukan pada rentang tanggal tersebut.")
# --- 8. MODUL: ANALISIS DEPT & PERUSAHAAN ---
elif menu == "Analisis Dept & Perusahaan":
    st.markdown("<h1>🏢 ANALISIS KUNJUNGAN</h1>", unsafe_allow_html=True)
    
    tgl_awal_db, tgl_akhir_db = get_date_range()
    
    c1, c2 = st.columns(2)
    t1 = c1.date_input("Mulai", value=tgl_awal_db, key="d1")
    t2 = c2.date_input("Sampai", value=tgl_akhir_db, key="d2")

    conn = sqlite3.connect(DB_PATH)
    # Kita ambil semua data dulu untuk dicek kolomnya
    df_data = pd.read_sql_query(f"SELECT * FROM rekap_penyakit WHERE tgl_kunjungan BETWEEN '{t1}' AND '{t2}'", conn)
    conn.close()

    if not df_data.empty:
        # Kecilkan semua nama kolom agar tidak bentrok (Case Insensitive)
        df_data.columns = [c.lower() for c in df_data.columns]
        
        tab1, tab2 = st.tabs(["📊 Per Departemen", "🏢 Per Perusahaan"])
        
        with tab1:
            if 'departemen' in df_data.columns:
                res_dept = df_data['departemen'].value_counts().reset_index()
                res_dept.columns = ['Nama Departemen', 'Jumlah Kunjungan']
                # Tambahkan nomor urut
                res_dept.insert(0, 'No.', range(1, len(res_dept) + 1))
                st.dataframe(res_dept, use_container_width=True, hide_index=True)
                st.bar_chart(res_dept.set_index('Nama Departemen')['Jumlah Kunjungan'])
            else:
                st.error("❌ Kolom 'departemen' tidak ditemukan di database. Pastikan CSV Anda memiliki kolom tersebut.")

        with tab2:
            if 'perusahaan' in df_data.columns:
                res_corp = df_data['perusahaan'].value_counts().reset_index()
                res_corp.columns = ['Nama Perusahaan', 'Jumlah Kunjungan']
                # Tambahkan nomor urut
                res_corp.insert(0, 'No.', range(1, len(res_corp) + 1))
                st.dataframe(res_corp, use_container_width=True, hide_index=True)
                st.bar_chart(res_corp.set_index('Nama Perusahaan')['Jumlah Kunjungan'])
            else:
                st.error("❌ Kolom 'perusahaan' tidak ditemukan di database. Pastikan CSV Anda memiliki kolom tersebut.")
    else:
        st.warning("Data tidak ditemukan pada rentang tanggal tersebut.")
# --- 9. MODUL: LIHAT & HAPUS DATA ---
elif menu == "Lihat Semua Data":
    st.markdown("<h1>📂 DATABASE KESELURUHAN</h1>", unsafe_allow_html=True)
    
    # --- 1. AREA FILTER (DI ATAS TABEL) ---
    tgl_awal_db, tgl_akhir_db = get_date_range()
    
    with st.expander("🔍 Filter & Pencarian Data", expanded=True):
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            f1 = st.date_input("Dari Tanggal", value=tgl_awal_db, key="f_tgl1")
        with c2:
            f2 = st.date_input("Sampai Tanggal", value=tgl_akhir_db, key="f_tgl2")
        with c3:
            cari_nama = st.text_input("Cari Nama Pasien", placeholder="Masukkan nama pasien...")

    conn = sqlite3.connect(DB_PATH)
    
    # --- 2. QUERY DENGAN FILTER ---
    # Menggunakan parameter query untuk keamanan dan fleksibilitas
    query = """
        SELECT id, tgl_kunjungan, nama_pasien, diagnosa, poli, departemen, perusahaan 
        FROM rekap_penyakit 
        WHERE (tgl_kunjungan BETWEEN ? AND ?)
    """
    params = [f1, f2]

    # Tambahkan filter nama jika kotak pencarian diisi
    if cari_nama:
        query += " AND nama_pasien LIKE ?"
        params.append(f'%{cari_nama}%')
    
    df_all = pd.read_sql_query(query, conn, params=params)
    
    if not df_all.empty:
        # --- 3. PERSIAPAN TAMPILAN TABEL ---
        df_display = df_all.copy()
        df_display.insert(0, 'No.', range(1, len(df_display) + 1))
        df_display.insert(0, 'Pilih', False)
        
        # Tabel Interaktif
        edited_df = st.data_editor(
            df_display, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "id": None, 
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                "No.": st.column_config.Column(width="small"),
                "tgl_kunjungan": "Tanggal",
                "nama_pasien": "Nama Pasien"
            },
            disabled=[c for c in df_display.columns if c != "Pilih"] 
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 4. TOMBOL AKSI SEJAJAR (DI BAWAH TABEL) ---
        col_check, col_btn1, col_btn2 = st.columns([1.5, 1, 1])
        
        with col_check:
            konfirmasi_semua = st.checkbox("⚠️ AKTIFKAN FITUR HAPUS SEMUA")
            
        with col_btn1:
            btn_hapus_terpilih = st.button("🗑️ HAPUS TERPILIH")
            
        with col_btn2:
            btn_hapus_semua = st.button("🔥 DELETE ALL DATA", type="primary", disabled=not konfirmasi_semua)

        # --- 5. LOGIKA PENGHAPUSAN ---
        if btn_hapus_terpilih:
            ids_to_delete = edited_df[edited_df['Pilih'] == True]['id'].tolist()
            if ids_to_delete:
                cur = conn.cursor()
                query_del = f"DELETE FROM rekap_penyakit WHERE id IN ({','.join(map(str, ids_to_delete))})"
                cur.execute(query_del)
                conn.commit()
                st.success(f"✅ {len(ids_to_delete)} baris berhasil dihapus!")
                st.rerun()
            else:
                st.warning("Pilih baris yang ingin dihapus terlebih dahulu.")

        if btn_hapus_semua:
            cur = conn.cursor()
            cur.execute("DELETE FROM rekap_penyakit")
            cur.execute("DELETE FROM sqlite_sequence WHERE name='rekap_penyakit'")
            conn.commit()
            st.success("✅ Database bersih total!")
            st.rerun()

    else:
        st.info("Data tidak ditemukan untuk kriteria pencarian tersebut.")
    
    conn.close()
