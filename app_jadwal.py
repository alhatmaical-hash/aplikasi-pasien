import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- KONFIGURASI HALAMAN (Mobile Friendly) ---
st.set_page_config(
    page_title="Sistem Jadwal Karyawan",
    page_icon="📅",
    layout="centered" # Centered lebih rapi saat dibuka di HP
)

# --- KONEKSI DATABASE ---
def init_db():
    conn = sqlite3.connect("office_schedule.db")
    cursor = conn.cursor()
    # Tabel Karyawan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS karyawan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            jabatan TEXT NOT NULL,
            perusahaan TEXT NOT NULL
        )
    """)
    # Tabel Jadwal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jadwal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            karyawan_id INTEGER,
            tanggal TEXT,
            shift TEXT,
            FOREIGN KEY (karyawan_id) REFERENCES karyawan (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("office_schedule.db")

# --- CSS CUSTOM UNTUK MOBILE & UI ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; }
    .card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        border-left: 5px solid #ff4b4b;
    }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGASI MENU ---
menu = ["🏠 Dasbor Hari Ini", "📅 Atur Jadwal", "👥 Manajemen Karyawan"]
choice = st.sidebar.radio("Navigasi Menu", menu)

# ==========================================
# 1. HALAMAN DASBOR HARI INI
# ==========================================
if choice == "🏠 Dasbor Hari Ini":
    st.title("🏠 Dasbor Jadwal")
    hari_ini = datetime.now().strftime("%Y-%m-%d")
    st.subheader(f"Petugas Aktif - {datetime.now().strftime('%d %B %Y')}")
    
    conn = get_db_connection()
    query = """
        SELECT k.nama, k.jabatan, k.perusahaan, j.shift 
        FROM jadwal j
        JOIN karyawan k ON j.karyawan_id = k.id
        WHERE j.tanggal = ?
    """
    df_hari_ini = pd.read_sql_query(query, conn, params=(hari_ini,))
    conn.close()
    
    if not df_hari_ini.empty:
        # Pilihan Filter untuk memudahkan pencarian di HP
        search_filter = st.text_input("🔍 Cari Nama / Jabatan / Perusahaan")
        if search_filter:
            df_hari_ini = df_hari_ini[
                df_hari_ini['nama'].str.contains(search_filter, case=False) |
                df_hari_ini['jabatan'].str.contains(search_filter, case=False) |
                df_hari_ini['perusahaan'].str.contains(search_filter, case=False)
            ]
            
        # Tampilan List Card (Lebih responsif di HP dibanding tabel lebar)
        for idx, row in df_hari_ini.iterrows():
            st.markdown(f"""
                <div class="card">
                    <strong style="font-size: 1.1rem;">{row['nama']}</strong> ({row['jabatan']})<br>
                    <span style="color: #555;">Perusahaan: {row['perusahaan']}</span><br>
                    <span class="badge" style="background-color: #e1e4e8; padding: 2px 8px; border-radius: 5px; font-weight: bold;">⏱️ {row['shift']}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Belum ada jadwal yang diatur untuk hari ini.")

# ==========================================
# 2. HALAMAN ATUR JADWAL
# ==========================================
elif choice == "📅 Atur Jadwal":
    st.title("📅 Pengaturan Jadwal")
    
    conn = get_db_connection()
    karyawan_df = pd.read_sql_query("SELECT id, nama, jabatan FROM karyawan", conn)
    conn.close()
    
    if karyawan_df.empty:
        st.warning("Silakan tambahkan karyawan terlebih dahulu di menu 'Manajemen Karyawan'.")
    else:
        # Form Input Jadwal
        with st.form("form_jadwal", clear_on_submit=True):
            # Membuat opsi kombinasi Nama + Jabatan untuk selectbox
            karyawan_options = {f"{row['nama']} ({row['jabatan']})": row['id'] for idx, row in karyawan_df.iterrows()}
            pilih_karyawan = st.selectbox("Pilih Karyawan", options=list(karyawan_options.keys()), index=None, placeholder="-- Pilih Karyawan --")
            
            pilih_tanggal = st.date_input("Pilih Tanggal", value=datetime.now())
            pilih_shift = st.selectbox("Pilih Shift Kerja", ["Shift Pagi (08:00 - 16:00)", "Shift Malam (16:00 - 24:00)", "Full Day / On-Call", "Off / Libur"])
            
            simpan_jadwal = st.form_submit_button("Simpan Jadwal ➕")
            
            if simpan_jadwal:
                if pilih_karyawan is None:
                    st.error("Mohon pilih karyawan terlebih dahulu.")
                else:
                    karyawan_id = karyawan_options[pilih_karyawan]
                    tgl_str = pilih_tanggal.strftime("%Y-%m-%d")
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    # Cek apakah jadwal di tanggal tersebut sudah ada untuk karyawan yg sama
                    cursor.execute("SELECT id FROM jadwal WHERE karyawan_id = ? AND tanggal = ?", (karyawan_id, tgl_str))
                    exist = cursor.fetchone()
                    
                    if exist:
                        # Jika sudah ada, lakukan update
                        cursor.execute("UPDATE jadwal SET shift = ? WHERE karyawan_id = ? AND tanggal = ?", (pilih_shift, karyawan_id, tgl_str))
                        st.success(f"Jadwal untuk {pilih_karyawan} pada {tgl_str} berhasil diperbarui!")
                    else:
                        # Jika belum ada, insert baru
                        cursor.execute("INSERT INTO jadwal (karyawan_id, tanggal, shift) VALUES (?, ?, ?)", (karyawan_id, tgl_str, pilih_shift))
                        st.success(f"Jadwal baru berhasil disimpan!")
                        
                    conn.commit()
                    conn.close()
                    
    # Tampilkan Rekap Jadwal Keseluruhan
    st.write("---")
    st.subheader("🗓️ Semua Rekap Jadwal")
    conn = get_db_connection()
    query_all = """
        SELECT j.id, j.tanggal, k.nama, k.jabatan, j.shift 
        FROM jadwal j
        JOIN karyawan k ON j.karyawan_id = k.id
        ORDER BY j.tanggal DESC
    """
    df_all = pd.read_sql_query(query_all, conn)
    conn.close()
    
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True, hide_index=True)
    else:
        st.caption("Belum ada data jadwal tersimpan.")

# ==========================================
# 3. HALAMAN MANAJEMEN KARYAWAN
# ==========================================
elif choice == "👥 Manajemen Karyawan":
    st.title("👥 Manajemen Karyawan")
    
    # Form Tambah Karyawan Baru
    with st.form("form_karyawan", clear_on_submit=True):
        st.subheader("Tambah Karyawan Baru")
        nama_karyawan = st.text_input("Nama Lengkap")
        jabatan_karyawan = st.text_input("Jabatan / Posisi (cth: Dokter Jaga, Admin, Perawat)")
        perusahaan_induk = st.text_input("Perusahaan / Site Unit")
        
        submit_karyawan = st.form_submit_button("Tambah Karyawan")
        
        if submit_karyawan:
            if nama_karyawan.strip() == "" or jabatan_karyawan.strip() == "":
                st.error("Nama dan Jabatan wajib diisi!")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO karyawan (nama, jabatan, perusahaan) VALUES (?, ?, ?)", 
                               (nama_karyawan, jabatan_karyawan, perusahaan_induk))
                conn.commit()
                conn.close()
                st.success(f"Karyawan {nama_karyawan} berhasil didaftarkan!")

    # Tampilkan Daftar Karyawan Saat Ini
    st.write("---")
    st.subheader("Daftar Karyawan Terdaftar")
    conn = get_db_connection()
    df_karyawan = pd.read_sql_query("SELECT id AS 'ID', nama AS 'Nama', jabatan AS 'Jabatan', perusahaan AS 'Perusahaan' FROM karyawan", conn)
    conn.close()
    
    if not df_karyawan.empty:
        st.dataframe(df_karyawan, use_container_width=True, hide_index=True)
    else:
        st.caption("Belum ada karyawan yang terdaftar.")
