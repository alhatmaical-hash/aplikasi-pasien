import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io 
try:
    from fpdf import FPDF
    import xlsxwriter
    EXPORT_AVAILABLE = True
except ImportError:
    EXPORT_AVAILABLE = False

st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
                  tgl_kunjungan TEXT, 
                  nama_pasien TEXT, 
                  diagnosa TEXT, 
                  poli TEXT,
                  departemen TEXT,
                  perusahaan TEXT)''')
    
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
    
    /* Style Tombol agar Bold & Putih */
    div.stButton > button {
        font-weight: bold !important;
        color: white !important;
        text-transform: uppercase;
        border-radius: 8px;
        height: 3em;
    }
    /* Warna Tombol Hapus Terpilih */
    div[data-testid="stHorizontalBlock"] div:nth-child(2) button {
        background-color: #D2691E !important;
    }
    /* Warna Tombol Delete All */
    div[data-testid="stHorizontalBlock"] div:nth-child(3) button {
        background-color: #FF0000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 APLIKASI REKAM MEDIS KHFO")
menu = st.sidebar.radio("MENU UTAMA", 
    ["Upload Data CSV", "Laporan 10 Penyakit", "Analisis Dept & Perusahaan", "Lihat Semua Data"])

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
    
    # Ambil tanggal otomatis dari CSV
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
    
    if not df_top.empty:
        # --- PROSES PENOMORAN & CHECKBOX ---
        # 1. Tambahkan kolom No. urut 1, 2, 3...
        df_top.insert(0, 'No.', range(1, len(df_top) + 1))
        # 2. Tambahkan kolom Pilih untuk fitur hapus
        df_top.insert(0, 'Pilih', False)
        
        col_t, col_g = st.columns([1.2, 2])
        
        with col_t:
            st.markdown("### Daftar Peringkat")
            # Tampilkan tabel dengan nomor urut
            edited_df = st.data_editor(
                df_top, 
                hide_index=True, 
                use_container_width=True,
                disabled=["No.", "Diagnosa Penyakit", "Jumlah Kasus"] # Agar data tidak bisa diedit asal
            )
            
            # Tombol Hapus Spesifik Diagnosa
            if st.button("🗑️ HAPUS TERPILIH", key="btn_hapus_diag"):
                selected_diag = edited_df[edited_df['Pilih'] == True]['Diagnosa Penyakit'].tolist()
                if selected_diag:
                    cur = conn.cursor()
                    for d in selected_diag:
                        cur.execute("DELETE FROM rekap_penyakit WHERE diagnosa = ? AND tgl_kunjungan BETWEEN ? AND ?", (d, t1, t2))
                    conn.commit()
                    st.success(f"✅ Berhasil menghapus diagnosa terpilih!")
                    st.rerun()
                else:
                    st.warning("Centang penyakit yang ingin dihapus.")

        with col_g:
            st.markdown("### Grafik Batang")
            st.bar_chart(df_top.set_index('Diagnosa Penyakit')['Jumlah Kasus'])
    else:
        st.warning("Data tidak ditemukan pada rentang tanggal tersebut.")
    if EXPORT_AVAILABLE:
            st.markdown("### 📥 Unduh Laporan")
            col_ex, col_pdf = st.columns(2)

            with col_ex:
                output_excel = io.BytesIO()
                # Pastikan xlsxwriter sudah terinstal
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    df_report.to_excel(writer, index=False, sheet_name='Laporan')
                
                st.download_button(
                    label="📁 Download Excel",
                    data=output_excel.getvalue(),
                    file_name=f"Laporan_{t1}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col_pdf:
                # Logika PDF Sederhana
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, "LAPORAN 10 PENYAKIT", ln=True, align='C')
                pdf.set_font("Arial", size=12)
                for i, row in df_report.iterrows():
                    pdf.cell(190, 10, f"{row['No']}. {row['Diagnosa Penyakit']}: {row['Jumlah Kasus']}", ln=True)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_output,
                    file_name=f"Laporan_{t1}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            # Jika library fpdf/xlsxwriter belum ada, munculkan pesan ini:
            st.warning("⚠️ Fitur download belum siap. Silakan instal 'fpdf2' dan 'xlsxwriter' di terminal atau requirements.txt.")
    
    else:
        st.warning("Data tidak ditemukan.")
    conn.close()

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
        # Tambahkan Nomor Urut untuk tampilan
        df_report = df_top.copy()
        df_report.insert(0, 'No.', range(1, len(df_report) + 1))
        
        st.bar_chart(df_report.set_index('Diagnosa Penyakit')['Jumlah Kasus'])
        st.dataframe(df_report, use_container_width=True, hide_index=True)

        st.markdown("### 📥 Unduh Laporan")
        col_ex, col_pdf = st.columns(2)

        # --- LOGIKA DOWNLOAD EXCEL ---
        with col_ex:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_report.to_excel(writer, index=False, sheet_name='Laporan_10_Penyakit')
            
            st.download_button(
                label="📁 Download Excel (.xlsx)",
                data=output_excel.getvalue(),
                file_name=f"Laporan_10_Penyakit_{t1}_ke_{t2}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # --- LOGIKA DOWNLOAD PDF ---
        with col_pdf:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "LAPORAN 10 PENYAKIT TERBESAR", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.cell(190, 10, f"Periode: {t1} s/d {t2}", ln=True, align='C')
            pdf.ln(10)
            
            # Header Tabel PDF
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(15, 10, "No", 1)
            pdf.cell(130, 10, "Diagnosa Penyakit", 1)
            pdf.cell(40, 10, "Jumlah", 1)
            pdf.ln()
            
            # Isi Tabel PDF
            pdf.set_font("Arial", size=12)
            for i, row in df_report.iterrows():
                pdf.cell(15, 10, str(row['No.']), 1)
                pdf.cell(130, 10, str(row['Diagnosa Penyakit']), 1)
                pdf.cell(40, 10, str(row['Jumlah Kasus']), 1)
                pdf.ln()

            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="📄 Download PDF (.pdf)",
                data=pdf_output,
                file_name=f"Laporan_10_Penyakit_{t1}_ke_{t2}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
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
