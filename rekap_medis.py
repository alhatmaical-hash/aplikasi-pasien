import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

# --- 1. KONFIGURASI TAMPILAN ---
st.set_page_config(page_title="Rekap 10 Penyakit Terbesar", layout="wide")

def apply_custom_style():
    st.markdown("""
    <style>
    * { font-family: "Times New Roman", Times, serif !important; }
    .stApp { background-color: #1e1e1e; color: white; }
    
    /* Card Style untuk Input & Tabel */
    .report-card {
        background: rgba(40, 40, 40, 0.9);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #00d4ff;
        margin-bottom: 20px;
    }
    
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 2px 2px 4px black; }
    
    /* Styling Tabel Pandas agar kontras */
    .dataframe {
        background-color: #2b2b2b !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('rekam_medis.db')
    c = conn.cursor()
    # Tabel Kunjungan & Diagnosa
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tgl_kunjungan DATE, 
                  nama_pasien TEXT, 
                  diagnosa TEXT, 
                  poli TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. MENU NAVIGASI ---
menu = st.sidebar.selectbox("PILIH MENU", ["Input Diagnosa Pasien", "Laporan 10 Penyakit Terbesar", "Filter Kunjungan"])

# --- MODUL 1: INPUT DATA ---
if menu == "Input Diagnosa Pasien":
    st.title("📝 Input Diagnosa Harian")
    with st.form("form_diagnosa"):
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        tgl = st.date_input("Tanggal Kunjungan", date.today())
        nama = st.text_input("Nama Pasien")
        # Input Diagnosa (Bisa mengetik bebas atau drop-down)
        diag = st.selectbox("Diagnosa Penyakit", 
                            ["ISPA", "Hipertensi", "Diabetes Melitus", "Gastritis", "Cephalgia", 
                             "Dermatitis", "Myalgia", "Influenza", "Diare", "Asma", "Lain-lain"])
        if diag == "Lain-lain":
            diag = st.text_input("Sebutkan Nama Penyakit Lainnya")
            
        poli = st.selectbox("Poli Asal", ["Umum", "Gigi", "MCU", "UGD", "Rawat Inap"])
        
        submitted = st.form_submit_button("SIMPAN REKAP")
        if submitted:
            if nama and diag:
                conn = sqlite3.connect('rekam_medis.db')
                c = conn.cursor()
                c.execute("INSERT INTO rekap_penyakit (tgl_kunjungan, nama_pasien, diagnosa, poli) VALUES (?,?,?,?)",
                          (tgl, nama, diag.upper(), poli))
                conn.commit()
                conn.close()
                st.success(f"Data {nama} dengan diagnosa {diag} berhasil disimpan!")
            else:
                st.warning("Mohon isi Nama dan Diagnosa!")
        st.markdown('</div>', unsafe_allow_html=True)

# --- MODUL 2: 10 PENYAKIT TERBESAR ---
elif menu == "Laporan 10 Penyakit Terbesar":
    st.title("📊 Top 10 Penyakit Terbesar")
    
    conn = sqlite3.connect('rekam_medis.db')
    df = pd.read_sql_query("SELECT diagnosa, COUNT(*) as jumlah FROM rekap_penyakit GROUP BY diagnosa ORDER BY jumlah DESC LIMIT 10", conn)
    conn.close()

    if not df.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Tabel Frekuensi")
            st.dataframe(df, use_container_width=True)
        
        with col2:
            st.subheader("Grafik Batang")
            st.bar_chart(df.set_index('diagnosa'))
    else:
        st.info("Belum ada data untuk dianalisis.")

# --- MODUL 3: FILTER KUNJUNGAN ---
elif menu == "Filter Kunjungan":
    st.title("🔍 Filter & Cari Data Kunjungan")
    
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Dari Tanggal", date.today())
    with c2:
        end_date = st.date_input("Sampai Tanggal", date.today())
    
    filter_diag = st.text_input("Cari Diagnosa Spesifik (Kosongkan jika ingin semua)")
    st.markdown('</div>', unsafe_allow_html=True)

    conn = sqlite3.connect('rekam_medis.db')
    query = f"SELECT * FROM rekap_penyakit WHERE tgl_kunjungan BETWEEN '{start_date}' AND '{end_date}'"
    if filter_diag:
        query += f" AND diagnosa LIKE '%{filter_diag.upper()}%'"
    
    df_filter = pd.read_sql_query(query, conn)
    conn.close()

    if not df_filter.empty:
        st.write(f"Ditemukan {len(df_filter)} kunjungan.")
        st.dataframe(df_filter, use_container_width=True)
        
        # Tombol Download Excel/CSV
        csv = df_filter.to_csv(index=False).encode('utf-8')
        st.download_button("Export ke CSV", csv, "rekap_kunjungan.csv", "text/csv")
    else:
        st.warning("Tidak ada data pada rentang tanggal tersebut.")