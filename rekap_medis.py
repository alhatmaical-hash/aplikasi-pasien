import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

# --- 1. SET LOKASI DATABASE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'klinik_data.db')

# --- 2. TEMA HANGAT ---
st.set_page_config(page_title="Rekap Klinik v5", layout="wide")

st.markdown("""
<style>
    * { font-family: "Times New Roman", Times, serif !important; }
    .stApp { background-color: #F5F5DC; }
    h1, h2, h3 { color: #4A2C2A !important; text-align: center; font-weight: bold; }
    .report-card {
        background-color: #EADDCA;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #C19A6B;
        margin-bottom: 20px;
    }
    .stTable, .stDataFrame { background-color: #FFFFFF !important; border-radius: 10px; }
    label, p { color: #3D2B1F !important; font-weight: bold; }
    .stButton>button { background-color: #8B4513 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. INISIALISASI DATABASE (UPDATE KOLOM) ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Menambahkan kolom departemen dan perusahaan
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tgl_kunjungan TEXT, 
                  nama_pasien TEXT, 
                  diagnosa TEXT, 
                  poli TEXT,
                  departemen TEXT,
                  perusahaan TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. NAVIGASI ---
menu = st.sidebar.radio("MENU UTAMA", ["Upload Data CSV", "Laporan 10 Penyakit", "Analisis Dept & Perusahaan", "Lihat Semua Data"])

# --- MODUL 1: UPLOAD DATA ---
if menu == "Upload Data CSV":
    st.markdown("<h1>📝 UPLOAD & SIMPAN DATA</h1>", unsafe_allow_html=True)
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.info("Pastikan CSV memiliki kolom: tgl_kunjungan, nama_pasien, diagnosa, poli, departemen, perusahaan")
    uploaded_file = st.file_uploader("Pilih File CSV", type=["csv"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.lower().strip() for c in df.columns]
        
        st.write("Pratinjau Data:")
        preview_df = df.head().copy()
        preview_df.index = preview_df.index + 1
        st.dataframe(preview_df)

        if st.button("SIMPAN KE DATABASE"):
            try:
                df['tgl_kunjungan'] = pd.to_datetime(df['tgl_kunjungan']).dt.strftime('%Y-%m-%d')
                # Standarisasi teks jadi UPPERCASE agar grouping konsisten
                for col in ['diagnosa', 'departemen', 'perusahaan']:
                    if col in df.columns:
                        df[col] = df[col].astype(str).str.upper().str.strip()
                
                conn = sqlite3.connect(DB_PATH)
                df.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
                conn.close()
                st.success(f"✅ Berhasil menyimpan {len(df)} data!")
                st.balloons()
            except Exception as e:
                st.error(f"Gagal Simpan: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- MODUL 2: LAPORAN 10 PENYAKIT ---
elif menu == "Laporan 10 Penyakit":
    st.markdown("<h1>📊 10 PENYAKIT TERBESAR</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    t1 = c1.date_input("Mulai", date(2024, 1, 1))
    t2 = c2.date_input("Sampai", date.today())

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
        df_top.insert(0, 'No.', range(1, len(df_top) + 1))
        col_t, col_g = st.columns([1, 2])
        with col_t:
            st.dataframe(df_top, hide_index=True, use_container_width=True)
        with col_g:
            st.bar_chart(df_top.set_index('Diagnosa Penyakit')['Jumlah Kasus'])
    else:
        st.warning("Data tidak ditemukan.")

# --- MODUL BARU: ANALISIS DEPT & PERUSAHAAN ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 1. Pastikan tabel utama ada
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tgl_kunjungan TEXT, 
                  nama_pasien TEXT, 
                  diagnosa TEXT, 
                  poli TEXT)''')
    
    # 2. Tambahkan kolom departemen jika belum ada
    try:
        c.execute("ALTER TABLE rekap_penyakit ADD COLUMN departemen TEXT")
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada
        
    # 3. Tambahkan kolom perusahaan jika belum ada
    try:
        c.execute("ALTER TABLE rekap_penyakit ADD COLUMN perusahaan TEXT")
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada
        
    conn.commit()
    conn.close()
