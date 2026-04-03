import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Smart Audit ICD-10 MIK", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE (MAHASISWA 2: BACKEND/DATABASE) ---
DB_NAME = "audit_mik_pro.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabel Utama Hasil Audit dengan Indikator Mutu
    c.execute('''CREATE TABLE IF NOT EXISTS audit_klinik (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_audit TEXT,
                    no_rm TEXT,
                    nama_pasien TEXT,
                    unit_layanan TEXT,
                    diagnosa_dokter TEXT,
                    kode_rs TEXT,
                    kode_auditor TEXT,
                    akurasi_kode TEXT,
                    kelengkapan_dokumen TEXT,
                    kategori_error TEXT,
                    rekomendasi TEXT,
                    auditor_name TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=80)
    st.title("🗂️ QC Rekam Medis")
    menu = st.radio("Navigasi Sistem:", 
                    ["Dashboard Mutu (Mhs 3)", 
                     "Instrumen Audit (Mhs 1)", 
                     "Riwayat & Laporan", 
                     "Decision Support"])
    st.markdown("---")
    st.caption("📍 Lokasi: Wihdatul Ummah Medical Center")

# --- MODUL 1: INSTRUMEN AUDIT (MAHASISWA 1: DESAIN & INDIKATOR) ---
if menu == "Instrumen Audit (Mhs 1)":
    st.header("📋 Form Audit Koding Diagnosis (Quality Control)")
    
    with st.form("audit_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Data Pasien")
            tgl = st.date_input("Tanggal Audit", datetime.now())
            no_rm = st.text_input("Nomor Rekam Medis (WUMC-xxxx)")
            nama = st.text_input("Nama Pasien")
            unit = st.selectbox("Unit Layanan", ["Rawat Jalan", "Rawat Inap", "UGD"])
            diag_dr = st.text_area("Diagnosa Utama (Resume Medis)")
        
        with c2:
            st.subheader("Penilaian Coder")
            k_rs = st.text_input("Kode ICD-10 SIMRS (Coder)").upper()
            k_audit = st.text_input("Kode ICD-10 Seharusnya (Auditor)").upper()
            
            # Indikator Penilaian (Mhs 1)
            dokumen = st.radio("Kelengkapan Dokumen Penunjang", ["Lengkap", "Tidak Lengkap"])
            error_type = st.selectbox("Kategori Kesalahan (Jika Ada)", 
                                    ["Tidak Ada", "Salah Kode Karakter ke-3", "Salah Kode Karakter ke-4", "Beda Bab ICD-10", "Dokumen Tidak Terbaca"])
            
        auditor = st.text_input("Nama Mahasiswa Auditor")
        
        # Decision Logic (Mhs 1 & 2)
        is_akurat = "AKURAT" if k_rs == k_audit else "TIDAK AKURAT"
        rekomendasi = f"Perlu verifikasi ulang pada Kode {k_audit}" if is_akurat == "TIDAK AKURAT" else "Coding sudah sesuai standar."
        
        btn_simpan = st.form_submit_button("Submit Hasil Audit")
        
        if btn_simpan:
            if no_rm and k_rs:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("""INSERT INTO audit_klinik (tgl_audit, no_rm, nama_pasien, unit_layanan, diagnosa_dokter, 
                             kode_rs, kode_auditor, akurasi_kode, kelengkapan_dokumen, kategori_error, rekomendasi, auditor_name) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (tgl.strftime("%Y-%m-%d"), no_rm, nama, unit, diag_dr, k_rs, k_audit, is_akurat, dokumen, error_type, rekomendasi, auditor))
                conn.commit()
                conn.close()
                st.success(f"Audit RM {no_rm} Berhasil Disimpan sebagai {is_akurat}")
            else:
                st.warning("Mohon lengkapi data No RM dan Kode RS!")

# --- MODUL 2: DASHBOARD MONITORING (MAHASISWA 3: ANALISIS DATA) ---
elif menu == "Dashboard Mutu (Mhs 3)":
    st.header("📊 Dashboard Monitoring Kualitas Data (QC)")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM audit_klinik", conn)
    conn.close()
    
    if not df.empty:
        # Metrik Utama
        total = len(df)
        akurat = len(df[df['akurasi_kode'] == 'AKURAT'])
        persen_akurat = (akurat/total) * 100
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Sampel Audit", f"{total} RM")
        col_m2.metric("Coding Akurat", f"{akurat}")
        col_m3.metric("Persentase Akurasi", f"{persen_akurat:.1f}%")
        
        # Grafik Analisis (Plotly)
        st.markdown("---")
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("Tren Kesalahan Coding")
            fig_error = px.pie(df, names='kategori_error', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_error, use_container_width=True)
            
        with g2:
            st.subheader("Akurasi per Unit Layanan")
            fig_unit = px.bar(df, x='unit_layanan', color='akurasi_kode', barmode='group')
            st.plotly_chart(fig_unit, use_container_width=True)
    else:
        st.info("Dashboard akan muncul setelah ada data audit yang diinput.")

# --- MODUL 3: RIWAYAT & LAPORAN OTOMATIS ---
elif menu == "Riwayat & Laporan":
    st.header("📄 Laporan Audit Berkala")
    conn = sqlite3.connect(DB_NAME)
    df_history = pd.read_sql_query("SELECT * FROM audit_klinik ORDER BY id DESC", conn)
    conn.close()
    
    if not df_history.empty:
        # Fitur Download (Laporan Otomatis)
        csv = df_history.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Laporan Audit (CSV)", data=csv, file_name="laporan_audit_icd10.csv", mime='text/csv')
        
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("Belum ada riwayat audit.")

# --- MODUL 4: DECISION SUPPORT (REKOMENDASI) ---
elif menu == "Decision Support":
    st.header("💡 Alat Bantu Pengambilan Keputusan")
    st.write("Sistem memberikan rekomendasi tindakan berdasarkan kategori kesalahan terbanyak.")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT kategori_error FROM audit_klinik", conn)
    conn.close()
    
    if not df.empty:
        top_error = df['kategori_error'].mode()[0]
        st.error(f"Penyebab utama ketidakakuratan saat ini: **{top_error}**")
        
        with st.expander("Klik untuk Rekomendasi Tindakan Mutu"):
            if top_error == "Salah Kode Karakter ke-4":
                st.write("✅ **Rekomendasi:** Sosialisasi penggunaan ICD-10 Volume 1 & 3 untuk pengecekan spesifikasi digit ke-4.")
            elif top_error == "Dokumen Tidak Lengkap":
                st.write("✅ **Rekomendasi:** Audit kepatuhan penulisan resume medis oleh Dokter (DPJP).")
            else:
                st.write("✅ **Rekomendasi:** Pertahankan performa coding dan lakukan audit rutin bulanan.")
    else:
        st.info("Data belum cukup untuk memberikan rekomendasi.")
