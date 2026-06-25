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

# --- KONEKSI DATABASE & INISIALISASI ---
def init_db():
    conn = sqlite3.connect("office_schedule_v3.db")
    cursor = conn.cursor()
    
    # 1. Tabel Master Jabatan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_jabatan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_jabatan TEXT NOT NULL UNIQUE
        )
    """)
    
    # 2. Tabel Karyawan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS karyawan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            jabatan TEXT NOT NULL,
            perusahaan TEXT NOT NULL,
            tipe TEXT NOT NULL DEFAULT 'Crew'
        )
    """)
    
    # 3. Tabel Jadwal Kerja
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jadwal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            karyawan_id INTEGER,
            tanggal TEXT,
            shift TEXT,
            FOREIGN KEY (karyawan_id) REFERENCES karyawan (id)
        )
    """)
    
    # --- ISI DATA JABATAN STANDAR JIKA MASIH KOSONG ---
    cursor.execute("SELECT COUNT(*) FROM master_jabatan")
    if cursor.fetchone()[0] == 0:
        jabatan_default = [
            "Supervisor Klinik", "Supervisor Paramedic", "Supervisor Pharmacy", 
            "Formen", "Paramedic Staff", "Medical Record Staff", 
            "Pharmacy Staff", "Admin Klinik", "Translator Klinik", "Crew Klinik", "Driver Ambulance", "Driver LV Klinik", "Medical Docter"
        ]
        cursor.executemany("INSERT INTO master_jabatan (nama_jabatan) VALUES (?)", [(j,) for j in jabatan_default])
        
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("office_schedule_v3.db")

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
    st.title("📅 Pengaturan Jadwal & Roster Matriks")
    st.caption("Aturan Roster Pendek: Kerja 13 Hari → Off 1 Hari")
    
    conn = get_db_connection()
    karyawan_df = pd.read_sql_query("SELECT id, nama, jabatan, tipe FROM karyawan", conn)
    conn.close()
    
    if karyawan_df.empty:
        st.warning("Silakan daftarkan karyawan terlebih dahulu di menu 'Manajemen Karyawan'.")
    else:
        # --- FORM INPUT JADWAL ---
        with st.expander("➕ Tambah / Update Jadwal Harian", expanded=False):
            with st.form("form_jadwal", clear_on_submit=True):
                karyawan_options = {f"{row['nama']} ({row['jabatan']} - {row['tipe']})": row['id'] for idx, row in karyawan_df.iterrows()}
                pilih_karyawan = st.selectbox("Pilih Karyawan", options=list(karyawan_options.keys()), index=None, placeholder="-- Pilih Karyawan --")
                
                pilih_tanggal = st.date_input("Pilih Tanggal", value=datetime.now())
                pilih_shift = st.selectbox("Pilih Shift Kerja", [
                    "P",   # Pagi (Sesuai kode di gambar Anda)
                    "M",   # Malam
                    "OFF", # Libur
                    "CT",  # Cuti
                    "TRV"  # Travel / Perjalanan
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
                            st.success(f"Jadwal berhasil diupdate!")
                        else:
                            cursor.execute("INSERT INTO jadwal (karyawan_id, tanggal, shift) VALUES (?, ?, ?)", (karyawan_id, tgl_str, pilih_shift))
                            st.success(f"Jadwal berhasil ditambahkan!")
                            
                        conn.commit()
                        conn.close()
                        st.rerun()

        st.write("---")
        
        # --- FILTER BULAN & TAHUN UNTUK GRID VIEW ---
        st.subheader("🗓️ Matriks Jadwal Jaga Bulanan")
        col_bln, col_thn = st.columns(2)
        with col_bln:
            bulan_pilihan = st.selectbox("Pilih Bulan", list(range(1, 13)), index=datetime.now().month - 1, format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
        with col_thn:
            tahun_pilihan = st.selectbox("Pilih Tahun", [2025, 2026, 2027], index=1) # Default 2026 sesuai template Anda

        # Ambil data jadwal berdasarkan bulan dan tahun yang dipilih
        conn = get_db_connection()
        query_matriks = """
            SELECT k.nama AS Nama, j.tanggal, j.shift 
            FROM jadwal j 
            JOIN karyawan k ON j.karyawan_id = k.id
            WHERE strftime('%m', j.tanggal) = ? AND strftime('%Y', j.tanggal) = ?
        """
        # Format parameter agar sesuai dengan format database SQLite ('05' untuk Mei, '2026' untuk tahun)
        bln_str = f"{bulan_pilihan:02d}"
        thn_str = str(tahun_pilihan)
        
        df_log = pd.read_sql_query(query_matriks, conn, params=(bln_str, thn_str))
        conn.close()

        # --- LOGIKA GENERATE MATRIX TABLE ---
        if not df_log.empty:
            # Ekstrak angka tanggal saja (1-31) untuk dijadikan header kolom seperti di Excel Anda
            df_log['Hari'] = pd.to_datetime(df_log['tanggal']).dt.day
            
            # Proses Pivot: Mengubah baris log menjadi kolom horizontal (Matrix)
            df_pivot = df_log.pivot(index='Nama', columns='Hari', values='shift').fillna('-')
            
            # Pastikan semua tanggal (1 sampai jumlah hari di bulan tersebut) muncul sebagai kolom
            import calendar
            jumlah_hari = calendar.monthrange(tahun_pilihan, bulan_pilihan)[1]
            for hari in range(1, jumlah_hari + 1):
                if hari not in df_pivot.columns:
                    df_pivot[hari] = '-'
            
            # Urutkan kolom dari tanggal 1 sampai akhir
            df_pivot = df_pivot[sorted(df_pivot.columns)]
            df_pivot = df_pivot.reset_index()

            # --- HIGHLIGHT / WARNA GAYA MODEREN ---
            # Menggunakan pandas styler untuk mewarnai cell otomatis (P=Hijau, M=Biru, OFF/CT=Merah) seperti gambar Anda
            def beri_warna_shift(val):
                if val == 'P':
                    return 'background-color: #d4edda; color: #155724; font-weight: bold; text-align: center;'
                elif val == 'M':
                    return 'background-color: #cce5ff; color: #004085; font-weight: bold; text-align: center;'
                elif val in ['OFF', 'CT', 'CHT']:
                    return 'background-color: #f8d7da; color: #721c24; font-weight: bold; text-align: center;'
                elif val == 'TRV':
                    return 'background-color: #ffeeba; color: #856404; font-weight: bold; text-align: center;'
                return 'text-align: center; color: #ccc;'

            style_df = df_pivot.style.map(beri_warna_shift, subset=df_pivot.columns[1:])
            
            # Tampilkan ke Streamlit dengan container lebar penuh
            st.dataframe(style_df, use_container_width=True, hide_index=True)
            
            # --- LEGEND / KETERANGAN ---
            st.markdown("""
            <div style="display: flex; gap: 15px; margin-top: 15px; font-size: 0.85rem;">
                <div><span style="background-color: #d4edda; padding: 2px 8px; border-radius: 3px; font-weight:bold;">P</span> Pagi</div>
                <div><span style="background-color: #cce5ff; padding: 2px 8px; border-radius: 3px; font-weight:bold;">M</span> Malam</div>
                <div><span style="background-color: #f8d7da; padding: 2px 8px; border-radius: 3px; font-weight:bold;">OFF / CT</span> Libur / Cuti</div>
                <div><span style="background-color: #ffeeba; padding: 2px 8px; border-radius: 3px; font-weight:bold;">TRV</span> Travel</div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.info(f"Belum ada data jadwal yang diinput untuk bulan {datetime(2000, bulan_pilihan, 1).strftime('%B')} {tahun_pilihan}.")

# ==========================================
# 3. HALAMAN KALKULATOR ROSTER & CUTI
# ==========================================
elif choice == "✈️ Kalkulator Roster & Cuti":
    st.title("✈️ Analisis Siklus Roster & Cuti Panjang")
    
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
            tgl_mulai_kerja = st.date_input("Tanggal Mulai Masuk On-Site (Hari ke-1)", value=datetime.now())
            
            st.markdown("---")
            st.write("### 📌 Penyesuaian Jadwal Lapangan")
            hari_mundur = st.number_input("Jumlah Hari Menunda Pulang / Mundur Cuti (Jika ada)", min_value=0, step=1, value=0)
            
            # --- LOGIKA BARU UNTUK SUPERVISOR, STAFF, & CREW ---
            if tipe_karyawan == "Supervisor":
                total_hari_kerja_standar = 63
                hari_perjalanan = 4  # Setara staff, silakan ubah angka ini jika berbeda
            elif tipe_karyawan == "Staff":
                total_hari_kerja_standar = 70
                hari_perjalanan = 4
            else: # Crew
                total_hari_kerja_standar = 70
                hari_perjalanan = 2
                
            total_hari_kerja_aktual = total_hari_kerja_standar + hari_mundur
            cuti_dasar = 14
            
            # Rumus bonus cuti extra (Mundur 5 hari = +1 hari cuti)
            extra_cuti = hari_mundur // 5
            total_cuti_aktual = cuti_dasar + extra_cuti
            
            # Perhitungan Tanggal Otomatis
            tgl_mulai_cuti = tgl_mulai_kerja + timedelta(days=total_hari_kerja_aktual)
            total_hari_off_site = total_cuti_aktual + hari_perjalanan
            tgl_kembali_site = tgl_mulai_cuti + timedelta(days=total_hari_off_site)
            
            st.markdown(f"""
            <div class="highlight-box">
                <h4>📊 Hasil Kalkulasi Roster ({tipe_karyawan}):</h4>
                <ul>
                    <li><b>Siklus Kerja Standar:</b> {total_hari_kerja_standar} Hari Kerja</li>
                    <li><b>Total Hari Kerja di Site (Aktual):</b> {total_hari_kerja_aktual} Hari (Termasuk mundur {hari_mundur} hari)</li>
                    <li><b>Total Cuti Bersih:</b> {total_cuti_aktual} Hari (Jatah {cuti_dasar} hari + Bonus {extra_cuti} hari)</li>
                    <li><b>Waktu Perjalanan PP:</b> {hari_perjalanan} Hari</li>
                </ul>
                <hr>
                <p>📅 <b>Tanggal Mulai Cuti (Off-Site):</b> {tgl_mulai_cuti.strftime('%d %B %Y')}</p>
                <p>🛫 <b>Tanggal Wajib Kembali ke Site:</b> <span style="color:#d39e00; font-weight:bold;">{tgl_kembali_site.strftime('%d %B %Y')}</span></p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# ==========================================
# 4. HALAMAN MANAJEMEN KARYAWAN
# ==========================================
elif choice == "👥 Manajemen Karyawan":
    st.title("👥 Data Karyawan & Master Jabatan")
    
    # Ambil data list jabatan dari database secara dinamis
    conn = get_db_connection()
    list_jabatan_db = pd.read_sql_query("SELECT nama_jabatan FROM master_jabatan ORDER BY nama_jabatan ASC", conn)['nama_jabatan'].tolist()
    conn.close()
    
    # Buat daftar Perusahaan sesuai instruksi tetap Anda
    perusahaan_options = [
        "PT. HALMAHERA JAYA FERONIKEL", 
        "PT. KARUNIA PERMAI SENTOSA", 
        "PT. OBI SINAR TIMUR"
    ]
    
    # Kita bagi halaman menjadi dua bagian (Tab) agar rapi
    tab1, tab2 = st.tabs(["➕ Tambah Karyawan", "🛠️ Kelola Jabatan Baru"])
    
    with tab1:
        with st.form("form_karyawan", clear_on_submit=True):
            st.subheader("Pendaftaran Karyawan Baru")
            nama_karyawan = st.text_input("Nama Lengkap Karyawan")
            
            # Memakai index=None agar dropdown bawaan kosong sampai dipilih pengguna
            pilih_jabatan = st.selectbox("Pilih Jabatan / Posisi", options=list_jabatan_db, index=None, placeholder="-- Silakan Pilih Jabatan --")
            pilih_perusahaan = st.selectbox("Pilih Perusahaan Induk", options=perusahaan_options, index=None, placeholder="-- Silakan Pilih Perusahaan --")
            tipe_karyawan = st.selectbox("Tipe Karyawan", ["Crew", "Staff", "Superintendent", "Supervisor"])
            
            submit_karyawan = st.form_submit_button("Daftarkan Karyawan")
            
            if submit_karyawan:
                if not nama_karyawan.strip():
                    st.error("Nama karyawan tidak boleh kosong!")
                elif pilih_jabatan is None:
                    st.error("Mohon pilih jabatan terlebih dahulu!")
                elif pilih_perusahaan is None:
                    st.error("Mohon pilih perusahaan terlebih dahulu!")
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO karyawan (nama, jabatan, perusahaan, tipe) VALUES (?, ?, ?, ?)", 
                                   (nama_karyawan, pilih_jabatan, pilih_perusahaan, tipe_karyawan))
                    conn.commit()
                    conn.close()
                    st.success(f"Karyawan {nama_karyawan} berhasil disimpan!")
                    st.rerun() # Refresh halaman untuk update daftar bawah

    with tab2:
        st.subheader("🛠️ Tambah Kamus Jabatan Baru")
        st.caption("Gunakan formulir ini jika di kemudian hari terdapat divisi atau posisi jabatan baru di klinik.")
        
        with st.form("form_jabatan_baru", clear_on_submit=True):
            jabatan_baru = st.text_input("Ketik Nama Jabatan Baru (cth: HSE Officer, Driver)")
            submit_jabatan = st.form_submit_button("Simpan Jabatan Baru 💾")
            
            if submit_jabatan:
                if jabatan_baru.strip() == "":
                    st.error("Nama jabatan baru tidak boleh kosong.")
                else:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO master_jabatan (nama_jabatan) VALUES (?)", (jabatan_baru.strip(),))
                        conn.commit()
                        conn.close()
                        st.success(f"Jabatan '{jabatan_baru}' berhasil ditambahkan ke dalam sistem!")
                        st.rerun() # Refresh agar langsung muncul di dropdown tab sebelah
                    except sqlite3.IntegrityError:
                        st.error("Jabatan tersebut sudah terdaftar di sistem.")

    # --- BAGIAN BAWAH YANG DIPERBARUI (DAFTAR KARYAWAN + TOMBOL HAPUS) ---
    st.write("---")
    st.subheader("Daftar Karyawan Terdaftar")
    
    conn = get_db_connection()
    df_karyawan = pd.read_sql_query("SELECT id, nama, tipe, jabatan, perusahaan FROM karyawan ORDER BY id DESC", conn)
    conn.close()
    
    if not df_karyawan.empty:
        # Loop untuk menampilkan data baris demi baris beserta tombol hapusnya
        for idx, row in df_karyawan.iterrows():
            col_data, col_aksi = st.columns([4, 1])
            
            with col_data:
                st.markdown(f"""
                    <div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #6c757d;">
                        <b>{row['nama']}</b> ({row['tipe']})<br>
                        <span style="font-size: 0.85rem; color: #555;">{row['jabatan']} | {row['perusahaan']}</span>
                    </div>
                """, unsafe_allow_html=True)
                
            with col_aksi:
                # Tombol hapus dengan key unik berbasis ID karyawan
                hapus_klik = st.button("🗑️ Hapus", key=f"del_{row['id']}")
                
                if hapus_klik:
                    # Modal dialog konfirmasi pengaman
                    @st.dialog(f"Konfirmasi Hapus: {row['nama']}")
                    def konfirmasi_dialog(karyawan_id, nama_karyawan):
                        st.write(f"Apakah Anda yakin ingin menghapus data **{nama_karyawan}**? Semua riwayat jadwal miliknya juga akan terhapus.")
                        col_ya, col_tidak = st.columns(2)
                        
                        with col_ya:
                            if st.button("Ya, Hapus", type="primary"):
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                # Hapus jadwalnya dulu agar tidak melanggar foreign key constraint
                                cursor.execute("DELETE FROM jadwal WHERE karyawan_id = ?", (karyawan_id,))
                                # Baru hapus data karyawannya
                                cursor.execute("DELETE FROM karyawan WHERE id = ?", (karyawan_id,))
                                conn.commit()
                                conn.close()
                                st.success("Data berhasil dihapus!")
                                st.rerun()
                        with col_tidak:
                            if st.button("Batal"):
                                st.rerun()
                                
                    konfirmasi_dialog(row['id'], row['nama'])
    else:
        st.caption("Belum ada karyawan yang terdaftar.")
