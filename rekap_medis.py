import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

# --- 1. SET LOKASI DATABASE TETAP ---
# Ini memastikan database selalu ada di folder yang sama dengan skrip
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'klinik_data.db')

# --- 2. TEMA HANGAT & TIMES NEW ROMAN ---
st.set_page_config(page_title="Rekap Klinik v3", layout="wide")

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
    label, p { color: #3D2B1F !important; font-weight: bold; }
    .stButton>button { background-color: #8B4513 !important; color: white !important; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tgl_kunjungan TEXT, 
                  nama_pasien TEXT, 
                  diagnosa TEXT, 
                  poli TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. NAVIGASI ---
menu = st.sidebar.radio("MENU", ["Upload Data", "Laporan 10 Penyakit", "Cek Semua Data"])

# --- MODUL 1: UPLOAD DATA ---
if menu == "Upload Data":
    st.markdown("<h1>📝 UPLOAD & SIMPAN DATA</h1>", unsafe_allow_html=True)
    
    with st.expander("Klik untuk petunjuk format CSV", expanded=True):
        st.write("Kolom harus: **tgl_kunjungan**, **nama_pasien**, **diagnosa**, **poli**")
    
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        # Bersihkan nama kolom (kecilkan huruf & hapus spasi)
        df.columns = [c.lower().strip() for c in df.columns]
        
        st.write("Pratinjau Data:")
        st.dataframe(df.head())

        if st.button("PROSES & SIMPAN KE DATABASE"):
            try:
                # Perbaikan Tanggal Otomatis (Mengubah berbagai format ke YYYY-MM-DD)
                df['tgl_kunjungan'] = pd.to_datetime(df['tgl_kunjungan']).dt.strftime('%Y-%m-%d')
                
                # Bersihkan Teks
                df['diagnosa'] = df['diagnosa'].astype(str).str.upper().str.strip()
                df['nama_pasien'] = df['nama_pasien'].astype(str).str.strip()
                
                conn = sqlite3.connect(DB_PATH)
                df.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
                conn.close()
                
                st.success(f"✅ BERHASIL! {len(df)} data masuk ke: {DB_PATH}")
                st.balloons()
            except Exception as e:
                st.error(f"Eror: {e}. Pastikan kolom 'tgl_kunjungan' ada di file Anda.")

# --- MODUL 2: LAPORAN 10 PENYAKIT ---
elif menu == "Laporan 10 Penyakit":
    st.markdown("<h1>📊 TOP 10 PENYAKIT TERBESAR</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    tgl_a = c1.date_input("Dari Tanggal", date(2024,1,1))
    tgl_b = c2.date_input("Sampai Tanggal", date.today())

    conn = sqlite3.connect(DB_PATH)
    # Query menggunakan filter tanggal
    query = f"""
        SELECT diagnosa, COUNT(*) as jumlah 
        FROM rekap_penyakit 
        WHERE tgl_kunjungan BETWEEN '{tgl_a}' AND '{tgl_b}'
        GROUP BY diagnosa 
        ORDER BY jumlah DESC 
        LIMIT 10
    """
    df_top = pd.read_sql_query(query, conn)
    conn.close()

    if not df_top.empty:
        col_t, col_g = st.columns([1, 2])
        with col_t:
            st.table(df_top)
        with col_g:
            st.bar_chart(df_top.set_index('diagnosa'))
    else:
        st.warning("Data tidak muncul? Coba cek menu 'Cek Semua Data' untuk melihat apakah data benar-benar tersimpan.")

# --- MODUL 3: CEK SEMUA DATA (DEBUGGING) ---
elif menu == "Cek Semua Data":
    st.markdown("<h1>📂 ISI DATABASE KESELURUHAN</h1>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_PATH)
    df_all = pd.read_sql_query("SELECT * FROM rekap_penyakit", conn)
    conn.close()
    
    if not df_all.empty:
        st.write(f"Total data tersimpan: {len(df_all)}")
        st.dataframe(df_all)
        if st.button("Hapus Semua Data (Reset)"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM rekap_penyakit")
            conn.commit()
            conn.close()
            st.rerun()
    else:
        st.info("Database kosong.")
