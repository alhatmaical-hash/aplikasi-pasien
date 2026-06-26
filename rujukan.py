import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# 1. Konfigurasi Halaman (Menggunakan Zona Waktu WIT / Asia/Jayapura Friendly)
st.set_page_config(
    page_title="Klinik Apps - Rujukan & Triase",
    page_icon="🏥",
    layout="wide"
)

# 2. Inisialisasi Database SQLite
def init_db():
    conn = sqlite3.connect('rujukan_klinik.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rujukan_pasien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no_rujukan TEXT UNIQUE,
            tanggal_rujukan TEXT,
            no_rm TEXT,
            nama_pasien TEXT,
            nik TEXT,
            tanggal_lahir TEXT,
            jenis_kelamin TEXT,
            triase TEXT,
            diagnosis_awal TEXT,
            alasan_dirujuk TEXT,
            faskes_tujuan TEXT,
            dokter_merujuk TEXT,
            status_rujukan TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

# Jalankan inisialisasi database di awal
init_db()

# Fungsi helper koneksi database
def get_db_connection():
    return sqlite3.connect('rujukan_klinik.db')

# Fungsi generate Nomor Rujukan Otomatis
def generate_no_rujukan():
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y%m%d") # Format YYYYMMDD
    
    # Hitung jumlah rujukan yang dibuat hari ini
    cursor.execute("SELECT COUNT(*) FROM rujukan_pasien WHERE tanggal_rujukan LIKE ?", (f"{datetime.now().strftime('%Y-%m-%d')}%",))
    count = cursor.fetchone()[0] + 1
    conn.close()
    
    # Format penomoran menggunakan penulisan string Python yang aman dari SyntaxError oktal
    return f"RJK/{today_str}/{count:04d}"

# 3. Navigasi Menu Samping (Sidebar)
menu = st.sidebar.radio("Navigasi Menu Rujukan", ["Form Rujukan Baru", "Data & Status Rujukan"])

st.title("🏥 Sistem Rujukan Pasien & Triase")
st.markdown("---")

if menu == "Form Rujukan Baru":
    st.subheader("📝 Input Formulir Rujukan Pasien")
    
    # Form dibungkus agar submit dilakukan tersentralisasi
    with st.form("form_rujukan", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### **Data Identitas Pasien**")
            no_rm = st.text_input("Nomor Rekam Medis (No. RM)", placeholder="Misal: RM-00123")
            nama_pasien = st.text_input("Nama Lengkap Pasien", placeholder="Masukkan nama pasien")
            nik = st.text_input("NIK (KTP)", max_chars=16, placeholder="16 digit nomor induk kependudukan")
            
            # Nilai awal diset kosong agar pengguna dipaksa memilih secara manual
            tanggal_lahir = st.date_input("Tanggal Lahir", value=None, min_value=datetime(1900, 1, 1), max_value=datetime.now())
            jenis_kelamin = st.selectbox("Jenis Kelamin", options=["", "Laki-laki", "Perempuan"], index=0)

        with col2:
            st.markdown("##### **Kondisi Klinis & Triase**")
            
            # Pilihan Tingkat Kegawatan/Triase Rujukan
            triase = st.radio(
                "Kategori Triase Rujukan",
                options=[
                    "🔴 P1 (Emergency / Gawat Darurat)", 
                    "🟡 P2 (Urgent / Darurat Tidak Gawat)", 
                    "🟢 P3 (Non-Urgent / Tidak Gawat Tidak Darurat)", 
                    "⚪ P0 (Death on Arrival)"
                ],
                index=0,
                help="Pilih tingkat keparahan klinis pasien untuk menentukan prioritas penanganan di faskes tujuan."
            )
            
            diagnosis_awal = st.text_area("Diagnosis Sementara / Keluhan Utama", placeholder="Tuliskan gejala klinis dan diagnosis awal...")
            alasan_dirujuk = st.text_area("Alasan Dirujuk", placeholder="Misal: Keterbatasan alat bedah, memerlukan ICU, dll.")
            
            st.markdown("##### **Fasilitas Tujuan**")
            faskes_tujuan = st.selectbox(
                "Fasilitas Kesehatan (Faskes) Tujuan",
                options=["", "RSUD Labuha", "RSUD Dr. H. Chasan Boesoirie Ternate"],
                index=0
            )
            dokter_merujuk = st.text_input("Dokter yang Merujuk", placeholder="Nama Dokter DPJP")

        st.markdown("---")
        # Perbaikan baris tombol submit di sini
        submit_btn = st.form_submit_button("Simpan & Buat Surat Rujukan")
        
        if submit_btn:
            # Validasi form kosong
            if not no_rm or not nama_pasien or not jenis_kelamin or not faskes_tujuan or tanggal_lahir is None:
                st.error("❌ Mohon lengkapi semua data pasien, jenis kelamin, tanggal lahir, dan faskes tujuan!")
            else:
                no_rujukan = generate_no_rujukan()
                waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO rujukan_pasien (
                            no_rujukan, tanggal_rujukan, no_rm, nama_pasien, nik, 
                            tanggal_lahir, jenis_kelamin, triase, diagnosis_awal, 
                            alasan_dirujuk, faskes_tujuan, dokter_merujuk
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        no_rujukan, waktu_sekarang, no_rm, nama_pasien, nik, 
                        str(tanggal_lahir), jenis_kelamin, triase, diagnosis_awal, 
                        alasan_dirujuk, faskes_tujuan, dokter_merujuk
                    ))
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Rujukan berhasil dibuat dengan Nomor: {no_rujukan}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Gagal menyimpan data ke database: {e}")

elif menu == "Data & Status Rujukan":
    st.subheader("📋 Daftar dan Monitoring Status Rujukan")
    
    conn = get_db_connection()
    query = "SELECT id, no_rujukan, tanggal_rujukan, no_rm, nama_pasien, triase, faskes_tujuan, status_rujukan FROM rujukan_pasien ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.info("Belum ada data rujukan yang tersimpan.")
    else:
        # Pencarian data dinamis
        search_query = st.text_input("🔍 Cari berdasarkan Nama Pasien atau No. RM", "")
        if search_query:
            df = df[df['nama_pasien'].str.contains(search_query, case=False, na=False) | df['no_rm'].str.contains(search_query, case=False, na=False)]
        
        st.markdown("### Manajemen Status Rujukan")
        st.caption("Klik dua kali pada kolom 'Status Rujukan' untuk mengubah status respons faskes, lalu tekan tombol simpan perubahan di bawah.")
        
        # Penggunaan st.data_editor untuk manajemen data tabular yang fleksibel
        edited_df = st.data_editor(
            df,
            column_config={
                "id": None, # Menyembunyikan kolom ID internal database
                "no_rujukan": "No. Rujukan",
                "tanggal_rujukan": "Waktu Input",
                "no_rm": "No. RM",
                "nama_pasien": "Nama Pasien",
                "triase": "Triase",
                "faskes_tujuan": "Faskes Tujuan",
                "status_rujukan": st.column_config.SelectboxColumn(
                    "Status Rujukan",
                    help="Ubah status respons dari faskes tujuan",
                    width="medium",
                    options=["Pending", "Diterima", "Ditolak", "Selesai"],
                    required=True,
                )
            },
            disabled=["no_rujukan", "tanggal_rujukan", "no_rm", "nama_pasien", "triase", "faskes_tujuan"],
            key="data_rujukan_editor",
            use_container_width=True
        )
        
        if st.button("💾 Simpan Perubahan Status"):
            conn = get_db_connection()
            cursor = conn.cursor()
            changes_saved = 0
            
            for index, row in edited_df.iterrows():
                original_status = df.loc[df['id'] == row['id'], 'status_rujukan'].values[0]
                if row['status_rujukan'] != original_status:
                    cursor.execute(
                        "UPDATE rujukan_pasien SET status_rujukan = ? WHERE id = ?",
                        (row['status_rujukan'], int(row['id']))
                    )
                    changes_saved += 1
            
            conn.commit()
            conn.close()
            
            if changes_saved > 0:
                st.success(f"✅ Berhasil memperbarui {changes_saved} status rujukan!")
                st.rerun()
            else:
                st.info("Tidak ada perubahan status yang dideteksi.")
