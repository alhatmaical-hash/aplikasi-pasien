import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import io

# --- 1. KONFIGURASI TAMPILAN (WARNA HANGAT & TIMES NEW ROMAN) ---
st.set_page_config(page_title="Rekap 10 Penyakit Terbesar", layout="wide")

def apply_custom_style():
    st.markdown("""
    <style>
    /* Mengatur Font Global */
    * { 
        font-family: "Times New Roman", Times, serif !important; 
    }

    /* Background Warna Hangat (Beige) */
    .stApp { 
        background-color: #F5F5DC; 
    }
    
    /* Judul Utama - Cokelat Tua */
    h1, h2, h3 { 
        color: #4A2C2A !important; 
        font-weight: bold;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }

    /* Card/Blok Konten */
    .report-card {
        background-color: #EADDCA;
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #C19A6B;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* Teks Label */
    label, p, .stMarkdown { 
        color: #3D2B1F !important; 
        font-size: 18px !important;
        font-weight: bold;
    }

    /* Kotak Input & Upload */
    input, select, textarea, .stFileUploader {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #A67B5B !important;
    }

    /* Tombol Cokelat Hangat */
    .stButton>button {
        background-color: #8B4513 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px;
        width: 100%;
        height: 3.5em;
    }
    
    /* Styling Tabel */
    .dataframe {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #C19A6B;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_data.db')
    c = conn.cursor()
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
menu = st.sidebar.radio("MENU UTAMA", ["Upload & Input Data", "Laporan 10 Penyakit", "Filter Kunjungan"])

# --- MODUL 1: UPLOAD & INPUT ---
if menu == "Upload & Input Data":
    st.markdown("<h1>📝 INPUT DATA DIAGNOSA</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📁 Upload Excel/CSV", "✍️ Input Manual"])
    
    with tab1:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("Upload File Rekap Kunjungan")
        st.info("Pastikan file memiliki kolom: **tgl_kunjungan**, **nama_pasien**, **diagnosa**, **poli**")
        
        uploaded_file = st.file_uploader("Pilih file (XLSX atau CSV)", type=["xlsx", "csv"])
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file, engine='openpyxl')
                
                st.write("Pratinjau Data:")
                st.dataframe(df_upload.head(5), use_container_width=True)
                
                if st.button("PROSES & SIMPAN KE DATABASE"):
                    # Normalisasi data
                    df_upload['diagnosa'] = df_upload['diagnosa'].str.upper().str.strip()
                    
                    conn = sqlite3.connect('klinik_data.db')
                    df_upload.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
                    conn.close()
                    
                    st.success(f"✅ Berhasil mengimpor {len(df_upload)} data penyakit!")
                    st.balloons()
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        with st.form("manual_entry"):
            st.subheader("Form Input Manual")
            c1, c2 = st.columns(2)
            tgl = c1.date_input("Tanggal", date.today())
            nama = c1.text_input("Nama Pasien")
