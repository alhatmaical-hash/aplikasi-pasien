
Percakapan dengan Gemini
sy mau buat aplikasi

Halo! Wah, proyek seru nih. Saya siap bantu dari awal sampai aplikasinya jadi.

Biar kita bisa langsung terarah, boleh cerita sedikit tentang rencana aplikasinya? Misalnya:

Aplikasi untuk apa? (Apakah ini kelanjutan dari sistem manajemen klinik/pendaftaran pasien yang pakai Streamlit, atau mau bikin ide baru lagi?)

Target penggunanya siapa? (Untuk staf internal, pasien/masyarakat umum, atau lainnya?)

Fitur utama apa saja yang harus ada di tahap awal ini?

Kalau Anda sudah ada potongan kode awal atau struktur database yang ingin digunakan, silakan dibagikan saja di sini. Yuk, kita rancang aplikasinya!

saya mau buat aplikasi rujukan pasien

Menarik! Aplikasi rujukan pasien akan sangat membantu mempercepat proses administrasi dan memastikan data pasien aman serta akurat saat berpindah fasilitas kesehatan.

Karena aplikasi ini berurusan dengan data medis yang sensitif, kita perlu merancangnya dengan struktur yang rapi dan alur yang jelas.

Berikut adalah rancangan awal (arsitektur dasar) yang bisa kita gunakan, terutama jika Anda ingin membangunnya menggunakan kombinasi Python (Streamlit) dan SQLite:

1. Alur Utama Aplikasi (User Flow)
Secara umum, proses rujukan biasanya melibatkan 3 tahapan utama:

Pembuatan Rujukan (Faskes Asal): Dokter atau staf menginput data pasien, diagnosis, alasan dirujuk, dan faskes tujuan.

Validasi & Pemantauan (Dashboard): Riwayat rujukan yang bisa dipantau statusnya (misal: Pending, Diterima, atau Selesai).

Cetak/Unduh Surat Rujukan: Sistem otomatis membuat dokumen rujukan (bisa berupa PDF atau tampilan siap cetak) yang dilengkapi nomor rujukan unik.

2. Rancangan Struktur Database (SQLite)
Untuk tahap awal, kita bisa membuat satu tabel utama bernama rujukan_pasien. Berikut adalah draf struktur kolomnya:

SQL
CREATE TABLE rujukan_pasien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    no_rujukan TEXT UNIQUE,         -- Format otomatis, misal: RJK/2026/06/0001
    tanggal_rujukan TEXT,           -- Timestamp otomatis (WIT)
    nama_pasien TEXT,
    no_rm TEXT,                     -- Nomor Rekam Medis
    nik TEXT,
    tanggal_lahir TEXT,
    jenis_kelamin TEXT,
    diagnosis_awal TEXT,            -- Keluhan / Diagnosis Sementara
    alasan_dirujuk TEXT,            -- Alasan medis/fasilitas kurang
    faskes_tujuan TEXT,             -- Rumah Sakit / Faskes rujukan
    dokter_merujuk TEXT,            -- Nama dokter yang menangani
    status_rujukan TEXT DEFAULT 'Pending' -- Pending / Diterima / Ditolak
);
3. Fitur Utama yang Bisa Kita Buat
Agar aplikasi ini fungsional dan mudah digunakan, kita bisa bagi menjadi beberapa modul/menu di Streamlit:

Form Input Rujukan: Input data pasien dengan validasi (misal: pilihan jenis kelamin pakai selectbox, pilihan tanggal pakai date_input).

Daftar & Riwayat Rujukan: Menggunakan st.data_editor atau st.dataframe agar staf bisa melihat, mencari berdasarkan No. RM/Nama, atau mengubah status rujukan jika faskes tujuan sudah merespons.

Cetak Surat Rujukan (Format PDF/Preview): Tombol khusus untuk memunculkan dokumen rujukan yang rapi, siap dicetak atau disimpan.

Langkah Selanjutnya
Bagaimana menurut Anda mengenai rancangan awal ini? Apakah aplikasi rujukan ini mau diintegrasikan langsung sebagai modul baru di dalam sistem klinik yang sudah ada, atau Anda ingin kita bangun ini sebagai aplikasi mandiri (standalone) terlebih dahulu?

oke boleh di buatkan kodenya dan kalau bisa mnculkan pilihan triase rujukannya

Tentu, ini adalah kode lengkap untuk modul atau aplikasi mandiri rujukan pasien menggunakan Streamlit dan SQLite.

Di sini saya sudah menambahkan fitur pilihan Triase rujukan dengan kode warna standar medis (P1 sampai P0) agar memudahkan petugas dalam mengkategorikan tingkat kegawatan pasien saat dirujuk. Selain itu, sesuai dengan standar input form yang baik, pilihan dropdown seperti jenis kelamin, faskes, dan tanggal lahir dikosongkan terlebih dahulu agar memaksa user memilih secara manual.

Saya telah membuatkan file kodenya dengan nama app_rujukan.py. Silakan klik tag file di bawah untuk melihat/mengunduh kodenya:
Ikon PY
app_rujukan
 PY 
Buka

Cara Menjalankan Aplikasi Ini:
Pastikan Anda sudah menginstal library yang dibutuhkan (streamlit dan pandas):

Bash
pip install streamlit pandas
Jalankan aplikasi menggunakan perintah berikut di terminal/command prompt Anda:

Bash
streamlit run app_rujukan.py
Fitur Utama yang Ada di Dalam Kode:
Triase Rujukan Berbasis Prioritas:

🔴 P1 (Emergency): Gawat Darurat.

🟡 P2 (Urgent): Darurat Tidak Gawat.

🟢 P3 (Non-Urgent): Tidak Gawat Tidak Darurat.

⚪ P0: Death on Arrival.

Generasi Otomatis No Rujukan: Kode otomatis membuat format penomoran unik berbasis tanggal hari ini (contoh: RJK/20260626/0001).

Pemberlakuan Input Kosong: Komponen dropdown dan tanggal diset ke kosong (None / "") di awal agar meminimalkan kesalahan data karena terlewat diisi oleh staf penanggung jawab.

Data Editor Dinamis: Di menu Data & Status Rujukan, Anda bisa memantau pasien dan mengubah status respons rujukan (dari Pending menjadi Diterima / Ditolak / Selesai) langsung dari baris tabel menggunakan fitur st.data_editor.




Gemini adalah AI dan dapat melakukan kesalahan.

import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# 1. Konfigurasi Halaman (WIT Timezone / Asia/Jayapura Friendly)
st.set_page_config(
    page_title="Klinik Apps - Rujukan & Triase",
    page_icon="🏥",
    layout="wide"
)

# 2. Inisialisasi Database
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

init_db()

# Fungsi helper untuk database
def get_db_connection():
    return sqlite3.connect('rujukan_klinik.db')

def generate_no_rujukan():
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y%m%d") # Format YYYYMMDD
    cursor.execute("SELECT COUNT(*) FROM rujukan_pasien WHERE tanggal_rujukan LIKE ?", (f"{datetime.now().strftime('%Y-%m-%d')}%",))
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"RJK/{today_str}/{count:04d}"

# 3. Navigasi Menu
menu = st.sidebar.radio("Navigasi Menu rujukan", ["Form Rujukan Baru", "Data & Status Rujukan"])

st.title("🏥 Sistem Rujukan Pasien & Triase")
st.markdown("---")

if menu == "Form Rujukan Baru":
    st.subheader("📝 Input Formulir Rujukan Pasien")
    
    # Menggunakan form agar submit tersentralisasi
    with st.form("form_rujukan", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### **Data Identitas Pasien**")
            no_rm = st.text_input("Nomor Rekam Medis (No. RM)", placeholder="Misal: RM-00123")
            nama_pasien = st.text_input("Nama Lengkap Pasien", placeholder="Masukkan nama pasien")
            nik = st.text_input("NIK (KTP)", max_chars=16, placeholder="16 digit nomor induk kependudukan")
            
            # Form kosong tanpa default pilihan agar user memilih manual
            tanggal_lahir = st.date_input("Tanggal Lahir", value=None, min_value=datetime(1900, 1, 1), max_value=datetime.now())
            jenis_kelamin = st.selectbox("Jenis Kelamin", options=["", "Laki-laki", "Perempuan"], index=0)

        with col2:
            st.markdown("##### **Kondisi Klinis & Triase**")
            
            # Fitur Pilihan Triase dengan Radio Button berwarna/berlabel jelas
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
                options=["", "RSUD Jayapura", "RS Dian Harapan", "RS Bhayangkara", "RS Marthen Indey"],
                index=0
            )
            dokter_merujuk = st.text_input("Dokter yang Merujuk", placeholder="Nama Dokter DPJP")

        st.markdown("---")
        submit_btn = st.form_submit_with_ui_button = st.form_submit_button("Simpan & Buat Surat Rujukan")
        
        if submit_btn:
            # Validasi input wajib kosong
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
                    st.error(f"Gagal menyimpan data: {e}")

elif menu == "Data & Status Rujukan":
    st.subheader("📋 Daftar dan Monitoring Status Rujukan")
    
    conn = get_db_connection()
    query = "SELECT id, no_rujukan, tanggal_rujukan, no_rm, nama_pasien, triase, faskes_tujuan, status_rujukan FROM rujukan_pasien ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.info("Belum ada data rujukan yang tersimpan.")
    else:
        # Fitur filter pencarian cepat
        search_query = st.text_input("🔍 Cari berdasarkan Nama Pasien atau No. RM", "")
        if search_query:
            df = df[df['nama_pasien'].str.contains(search_query, case=False, na=False) | df['no_rm'].str.contains(search_query, case=False, na=False)]
        
        st.markdown("### Managemen Status Rujukan")
        st.caption("Anda dapat mengubah status rujukan langsung pada tabel di bawah ini (klik dua kali pada kolom 'status_rujukan') lalu tekan tombol simpan.")
        
        # Menggunakan st.data_editor untuk mengubah status rujukan secara dinamis
        edited_df = st.data_editor(
            df,
            column_config={
                "id": None, # Sembunyikan ID
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
            
            # Cek baris mana saja yang berubah
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
                st.info("Tidak ada perubahan status yang diubah.")
app_rujukan.py
Menampilkan app_rujukan.py.
