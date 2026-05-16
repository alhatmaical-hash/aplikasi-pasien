import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Manajemen & Roster Karyawan",
    page_icon="📅",
    layout="centered"
)

# --- KONEKSI DATABASE ---
def init_db():
    conn = sqlite3.connect("office_schedule_v2.db")
    cursor = conn.cursor()
    # Tabel Karyawan (Ditambah kolom tipe untuk membedakan Staff/Crew)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS karyawan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            jabatan TEXT NOT NULL,
            perusahaan TEXT NOT NULL,
            tipe TEXT NOT NULL DEFAULT 'Crew'
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
    return sqlite3.connect("office_schedule_v2.db")

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; }
    .card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        border-left: 5px solid #007bff;
    }
    .highlight-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #90caf9;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGASI MENU ---
menu = ["🏠 Dasbor Hari Ini", "📅 Atur Jadwal & Shift", "✈️ Kalkulator Roster & Cuti", "👥 Manajemen Karyawan"]
choice = st.sidebar.radio("Navigasi Menu", menu)

# ==========================================
# 1. HALAMAN DASBOR HARI INI
# ==========================================
if choice == "🏠 Dasbor Hari Ini":
    st.title("🏠 Dasbor Jadwal Karyawan")
    hari_ini = datetime.now().strftime("%Y-%m-%d")
    st.subheader(f"Jadwal Aktif - {datetime.now().strftime('%d %B %Y')}")
    
    conn = get_db_connection()
    query = """
        SELECT k.nama, k.jabatan, k.tipe, k.perusahaan, j.shift 
        FROM jadwal j
        JOIN karyawan k ON j.karyawan_id = k.id
        WHERE j.tanggal = ?
    """
    df_hari_ini = pd.read_sql_query(query, conn, params=(hari_ini,))
    conn.close()
    
    if not df_hari_ini.empty:
        search_filter = st.text_input("🔍 Filter Nama / Jabatan / Perusahaan / Tipe")
        if search_filter:
            df_hari_ini = df_hari_ini[
                df_hari_ini['nama'].str.contains(search_filter, case=False) |
                df_hari_ini['jabatan'].str.contains(search_filter, case=False) |
                df_hari_ini['perusahaan'].str.contains(search_filter, case=False) |
                df_hari_ini['tipe'].str.contains(search_filter, case=False)
            ]
            
        for idx, row in df_hari_ini.iterrows():
            st.markdown(f"""
                <div class="card">
                    <strong style="font-size: 1.1rem;">{row['nama']}</strong> <span style="color:#777;">[{row['tipe']}]</span> - ({row['jabatan']})<br>
                    <span style="color: #555;">Unit/Perusahaan: {row['perusahaan']}</span><br>
                    <span style="background-color: #d1ecf1; color: #0c5460; padding: 3px 8px; border-radius: 5px; font-weight: bold; font-size: 0.9rem;">🕒 {row['shift']}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Belum ada jadwal yang diinput untuk hari ini.")

# ==========================================
# 2. HALAMAN ATUR JADWAL & SHIFT
# ==========================================
elif choice == "📅 Atur Jadwal & Shift":
    st.title("📅 Pengaturan Jadwal Harian")
    st.caption("Aturan Roster Pendek: Kerja 13 Hari $\\rightarrow$ Off 1 Hari")
    
    conn = get_db_connection()
    karyawan_df = pd.read_sql_query("SELECT id, nama, jabatan, tipe FROM karyawan", conn)
    conn.close()
    
    if karyawan_df.empty:
        st.warning("Silakan daftarkan karyawan terlebih dahulu di menu 'Manajemen Karyawan'.")
    else:
        with st.form("form_jadwal", clear_on_submit=True):
            karyawan_options = {f"{row['nama']} ({row['jabatan']} - {row['tipe']})": row['id'] for idx, row in karyawan_df.iterrows()}
            pilih_karyawan = st.selectbox("Pilih Karyawan", options=list(karyawan_options.keys()), index=None, placeholder="-- Pilih Karyawan --")
            
            pilih_tanggal = st.date_input("Pilih Tanggal", value=datetime.now())
            
            # Update Pilihan Shift sesuai instruksi baru Anda
            pilih_shift = st.selectbox("Pilih Shift Kerja", [
                "Shift Pagi (07:00 - 18:00)", 
                "Shift Malam (19:00 - 07:00)", 
                "Off / Hari Libur (Roster 13-1)"
            ])
            
            simpan_jadwal = st.form_submit_button("Simpan Jadwal")
            
            if simpan_jadwal:
                if pilih_karyawan is None:
                    st.error("Mohon tentukan karyawan terlebih dahulu.")
                else:
                    karyawan_id = karyawan_options[pilih_karyawan]
                    tgl_str = pilih_tanggal.strftime("%Y-%m-%d")
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM jadwal WHERE karyawan_id = ? AND tanggal = ?", (karyawan_id, tgl_str))
                    exist = cursor.fetchone()
                    
                    if exist:
                        cursor.execute("UPDATE jadwal SET shift = ? WHERE karyawan_id = ? AND tanggal = ?", (pilih_shift, karyawan_id, tgl_str))
                        st.success(f"Jadwal {pilih_karyawan} pada {tgl_str} berhasil diupdate!")
                    else:
                        cursor.execute("INSERT INTO jadwal (karyawan_id, tanggal, shift) VALUES (?, ?, ?)", (karyawan_id, tgl_str, pilih_shift))
                        st.success(f"Jadwal berhasil ditambahkan!")
                        
                    conn.commit()
                    conn.close()
                    
    st.write("---")
    st.subheader("🗓️ Log Semua Jadwal Terdaftar")
    conn = get_db_connection()
    df_all = pd.read_sql_query("""
        SELECT j.tanggal AS 'Tanggal', k.nama AS 'Nama', k.tipe AS 'Tipe', k.jabatan AS 'Jabatan', j.shift AS 'Shift' 
        FROM jadwal j JOIN karyawan k ON j.karyawan_id = k.id ORDER BY j.tanggal DESC
    """, conn)
    conn.close()
    
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True, hide_index=True)

# ==========================================
# 3. HALAMAN KALKULATOR ROSTER & CUTI (LOGIKA 70 HARI)
# ==========================================
elif choice == "✈️ Kalkulator Roster & Cuti":
    st.title("✈️ Analisis Siklus Roster & Cuti Panjang")
    st.subheader("Simulasi Jadwal Istirahat (70 Hari Kerja)")
    
    conn = get_db_connection()
    karyawan_df = pd.read_sql_query("SELECT id, nama, tipe FROM karyawan", conn)
    conn.close()
    
    if karyawan_df.empty:
        st.warning("Tambahkan data karyawan terlebih dahulu.")
    else:
        karyawan_options = {f"{row['nama']} ({row['tipe']})": (row['id'], row['tipe']) for idx, row in karyawan_df.iterrows()}
        pilih = st.selectbox("Pilih Karyawan untuk Hitung Roster", options=list(karyawan_options.keys()))
        
        if pilih:
            karyawan_id, tipe_karyawan = karyawan_options[pilih]
            
            # Input parameter tanggal mulai roster
            tgl_mulai_kerja = st.date_input("Tanggal Mulai Masuk On-Site (Hari ke-1)", value=datetime.now())
            
            st.markdown("---")
            st.write("### 📌 Penyesuaian Jadwal Lapangan")
            # Fitur input jika karyawan mundur tanggal cutinya
            hari_mundur = st.number_input("Jumlah Hari Menunda Pulang / Mundur Cuti (Jika ada)", min_value=0, step=1, value=0)
            
            # Logika Perhitungan dasar
            total_hari_kerja_standar = 70
            total_hari_kerja_aktual = total_hari_kerja_standar + hari_mundur
            
            # Jatah cuti & perjalanan dasar berdasarkan Staff/Crew
            cuti_dasar = 14
            hari_perjalanan = 4 if tipe_karyawan == "Staff" else 2
            
            # Logika Extra Cuti: Mundur 5 hari = +1 hari cuti
            extra_cuti = hari_mundur // 5
            total_cuti_aktual = cuti_dasar + extra_cuti
            
            # Kalkulasi Tanggal Otomatis
            # 1. Tanggal Mulai Cuti (Setelah selesai hari kerja aktual)
            tgl_mulai_cuti = tgl_mulai_kerja + timedelta(days=total_hari_kerja_aktual)
            # 2. Total durasi di luar site (Cuti + Perjalanan)
            total_hari_off_site = total_cuti_aktual + hari_perjalanan
            # 3. Tanggal kembali masuk site
            tgl_kembali_site = tgl_mulai_cuti + timedelta(days=total_hari_off_site)
            
            # Tampilan Output Analisis
            st.markdown(f"""
            <div class="highlight-box">
                <h4>📊 Hasil Kalkulasi Roster ({tipe_karyawan}):</h4>
                <ul>
                    <li><b>Total Hari Kerja di Site:</b> {total_hari_kerja_aktual} Hari (Standar 70 hari + Mundur {hari_mundur} hari)</li>
                    <li><b>Jatah Cuti Utama:</b> {cuti_dasar} Hari</li>
                    <li><b>Bonus Cuti Ekstra (Mundur):</b> <span style="color:green; font-weight:bold;">+{extra_cuti} Hari</span></li>
                    <li><b>Total Cuti Bersih:</b> {total_cuti_aktual} Hari</li>
                    <li><b>Waktu Perjalanan PP:</b> {hari_perjalanan} Hari</li>
                </ul>
                <hr>
                <p>📅 <b>Tanggal Mulai Cuti (Off-Site):</b> {tgl_mulai_cuti.strftime('%d %B %Y')}</p>
                <p>🛫 <b>Tanggal Wajib Kembali ke Site:</b> <span style="color:#d39e00; font-weight:bold;">{tgl_kembali_site.strftime('%d %B %Y')}</span></p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# 4. HALAMAN MANAJEMEN KARYAWAN
# ==========================================
elif choice == "👥 Manajemen Karyawan":
    st.title("👥 Manajemen Data Karyawan")
    
    with st.form("form_karyawan", clear_on_submit=True):
        st.subheader("Tambah Karyawan Baru")
        nama_karyawan = st.text_input("Nama Lengkap")
        jabatan_karyawan = st.text_input("Jabatan / Posisi")
        perusahaan_induk = st.text_input("Perusahaan / Site Unit")
        # Penambahan pilihan tipe Staff atau Crew
        tipe_karyawan = st.selectbox("Tipe Karyawan", ["Crew", "Staff"])
        
        submit_karyawan = st.form_submit_button("Daftarkan Karyawan")
        
        if submit_karyawan:
            if nama_karyawan.strip() == "" or jabatan_karyawan.strip() == "":
                st.error("Nama dan Jabatan tidak boleh kosong!")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO karyawan (nama, jabatan, perusahaan, tipe) VALUES (?, ?, ?, ?)", 
                               (nama_karyawan, jabatan_karyawan, perusahaan_induk, tipe_karyawan))
                conn.commit()
                conn.close()
                st.success(f"Karyawan {nama_karyawan} ({tipe_karyawan}) berhasil disimpan!")

    st.write("---")
    st.subheader("Daftar Karyawan Terdaftar")
    conn = get_db_connection()
    df_karyawan = pd.read_sql_query("SELECT id AS 'ID', nama AS 'Nama', tipe AS 'Tipe', jabatan AS 'Jabatan', perusahaan AS 'Perusahaan' FROM karyawan", conn)
    conn.close()
    
    if not df_karyawan.empty:
        st.dataframe(df_karyawan, use_container_width=True, hide_index=True)
