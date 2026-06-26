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

init_db()

def get_db_connection():
    return sqlite3.connect('rujukan_klinik.db')

def generate_no_rujukan():
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y%m%d")
    cursor.execute("SELECT COUNT(*) FROM rujukan_pasien WHERE tanggal_rujukan LIKE ?", (f"{datetime.now().strftime('%Y-%m-%d')}%",))
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"RJK/{today_str}/{count:04d}"

# 3. Navigasi Menu Samping (Sidebar)
menu = st.sidebar.radio("Navigasi Menu Rujukan", ["Form Rujukan Baru", "Data & Status Rujukan"])

st.title("🏥 Sistem Rujukan Pasien & Triase")
st.markdown("---")

if menu == "Form Rujukan Baru":
    st.subheader("📝 Input Formulir Rujukan Pasien")
    
    with st.form("form_rujukan", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### **Data Identitas Pasien**")
            no_rm = st.text_input("Nomor Rekam Medis (No. RM)", placeholder="Misal: RM-00123")
            nama_pasien = st.text_input("Nama Lengkap Pasien", placeholder="Masukkan nama pasien")
            nik = st.text_input("NIK (KTP)", max_chars=16, placeholder="16 digit nomor induk kependudukan")
            tanggal_lahir = st.date_input("Tanggal Lahir", value=None, min_value=datetime(1900, 1, 1), max_value=datetime.now())
            jenis_kelamin = st.selectbox("Jenis Kelamin", options=["", "Laki-laki", "Perempuan"], index=0)

        with col2:
            st.markdown("##### **Kondisi Klinis & Triase**")
            triase = st.radio(
                "Kategori Triase Rujukan",
                options=[
                    "🔴 P1 (Emergency / Gawat Darurat)", 
                    "🟡 P2 (Urgent / Darurat Tidak Gawat)", 
                    "🟢 P3 (Non-Urgent / Tidak Gawat Tidak Darurat)", 
                    "⚪ P0 (Death on Arrival)"
                ],
                index=0
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
        submit_btn = st.form_submit_button("Simpan & Buat Surat Rujukan")
        
        if submit_btn:
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
    
    # Ambil semua data dari database untuk pemrosesan detail cetak/hapus
    conn = get_db_connection()
    query = "SELECT * FROM rujukan_pasien ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.info("Belum ada data rujukan yang tersimpan.")
    else:
        search_query = st.text_input("🔍 Cari berdasarkan Nama Pasien atau No. RM", "")
        if search_query:
            df = df[df['nama_pasien'].str.contains(search_query, case=False, na=False) | df['no_rm'].str.contains(search_query, case=False, na=False)]
        
        st.markdown("### Manajemen Status Rujukan")
        st.caption("Centang baris di sebelah kiri untuk **Mencetak PDF** atau **Menghapus Data**. Klik dua kali pada kolom Status Rujukan untuk mengubah status.")
        
        # Tambahkan kolom pilihan/checkbox di st.data_editor menggunakan num_rows="dynamic" atau custom column select
        df.insert(0, "Pilih", False)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False, width="small"),
                "id": None, 
                "no_rujukan": "No. Rujukan",
                "tanggal_rujukan": "Waktu Input",
                "no_rm": "No. RM",
                "nama_pasien": "Nama Pasien",
                "nik": None,          # Sembunyikan data detail di tabel utama
                "tanggal_lahir": None,
                "jenis_kelamin": None,
                "diagnosis_awal": None,
                "alasan_dirujuk": None,
                "dokter_merujuk": None,
                "triase": "Triase",
                "faskes_tujuan": "Faskes Tujuan",
                "status_rujukan": st.column_config.SelectboxColumn(
                    "Status Rujukan",
                    options=["Pending", "Diterima", "Ditolak", "Selesai"],
                    required=True,
                    width="medium"
                )
            },
            disabled=["no_rujukan", "tanggal_rujukan", "no_rm", "nama_pasien", "triase", "faskes_tujuan"],
            key="data_rujukan_editor",
            use_container_width=True
        )
        
        # Deteksi baris mana saja yang sedang dipilih/dicentang user
        selected_rows = edited_df[edited_df["Pilih"] == True]
        
        # Area Tombol Aksi Tambahan (Simpan, Cetak, Hapus)
        col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 5])
        
        with col_btn1:
            btn_save = st.button("💾 Simpan Status", use_container_width=True)
        
        # Memunculkan tombol Hapus & Cetak jika ada baris yang dipilih
        if not selected_rows.empty:
            with col_btn2:
                btn_print = st.button("🖨️ Cetak Surat Rujukan", type="primary", use_container_width=True)
            with col_btn3:
                btn_delete = st.button("🗑️ Hapus Rujukan", type="secondary")
                
            # PROSES 1: CETAK SURAT RUJUKAN (HTML PRINT MODE)
            if btn_print:
                for _, row in selected_rows.iterrows():
                    st.markdown("### 🖨️ Dokumen Siap Cetak")
                    st.info("💡 **Tips:** Tekan tombol **Ctrl + P** (Windows) atau **Cmd + P** (Mac) pada keyboard Anda lalu ubah tujuannya menjadi **'Save as PDF'**.")
                    
                    # Template Nota/Surat Rujukan Medis Standar
                    html_template = f"""
                    <div id="print-area" style="padding: 30px; border: 2px solid #333; font-family: Arial, sans-serif; background-color: #fff; color: #000; line-height: 1.6;">
                        <div style="text-align: center; border-bottom: 3px double #000; padding-bottom: 10px; margin-bottom: 20px;">
                            <h2 style="margin: 0; text-transform: uppercase;">SURAT RUJUKAN PASIEN</h2>
                            <h4 style="margin: 5px 0 0 0; font-weight: normal;">No. Rujukan: {row['no_rujukan']}</h4>
                        </div>
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                            <tr><td style="width: 30%; font-weight: bold; vertical-align: top;">Tanggal Rujukan</td><td>: {row['tanggal_rujukan']}</td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">Faskes Tujuan</td><td>: <strong>{row['faskes_tujuan']}</strong></td></tr>
                            <tr><td colspan="2"><hr style="border: 0; border-top: 1px solid #ccc; margin: 10px 0;"></td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">No. Rekam Medis</td><td>: {row['no_rm']}</td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">Nama Pasien</td><td>: {row['nama_pasien']}</td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">NIK</td><td>: {row['nik'] if row['nik'] else '-'}</td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">Tanggal Lahir</td><td>: {row['tanggal_lahir']}</td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">Jenis Kelamin</td><td>: {row['jenis_kelamin']}</td></tr>
                            <tr><td colspan="2"><hr style="border: 0; border-top: 1px solid #ccc; margin: 10px 0;"></td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">Kategori Triase</td><td>: {row['triase']}</td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">Diagnosis Awal</td><td>: {row['diagnosis_awal']}</td></tr>
                            <tr><td style="font-weight: bold; vertical-align: top;">Alasan Dirujuk</td><td>: {row['alasan_dirujuk']}</td></tr>
                        </table>
                        <div style="margin-top: 50px; text-align: right;">
                            <p style="margin-bottom: 60px;">Dokter yang Merujuk,</p>
                            <p style="font-weight: bold; text-decoration: underline;">( {row['dokter_merujuk'] if row['dokter_merujuk'] else '........................'} )</p>
                        </div>
                    </div>
                    <script>
                        // Otomatis memicu fungsi print bawaan browser
                        window.print();
                    </script>
                    <style>
                        /* Menyembunyikan seluruh elemen dashboard Streamlit saat cetak dipicu */
                        @media print {{
                            body * {{ visibility: hidden; }}
                            #print-area, #print-area * {{ visibility: visible; }}
                            #print-area {{ position: absolute; left: 0; top: 0; width: 100%; }}
                        }}
                    </style>
                    """
                    st.components.v1.html(html_template, height=650, scrolling=True)
            
            # PROSES 2: HAPUS RUJUKAN
            if btn_delete:
                conn = get_db_connection()
                cursor = conn.cursor()
                for _, row in selected_rows.iterrows():
                    cursor.execute("DELETE FROM rujukan_pasien WHERE id = ?", (int(row['id']),))
                conn.commit()
                conn.close()
                st.success("🗑️ Data rujukan berhasil dihapus!")
                st.rerun()

        # PROSES 3: SIMPAN PERUBAHAN STATUS EDIT
        if btn_save:
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
                st.info("Tidak ada perubahan status yang diubah.")
