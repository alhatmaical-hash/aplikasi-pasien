import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Smart Audit ICD-10 MIK", layout="wide")

# --- DATABASE ENGINE ---
DB_NAME = "audit_mik_pro.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
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
    st.title("🗂️ QC Rekam Medis")
    menu = st.radio("Navigasi Sistem:", 
                    ["Dashboard Mutu", 
                     "Instrumen Audit", 
                     "Riwayat & Laporan", 
                     "Decision Support"])
    st.markdown("---")
    st.caption("Proyek D4 MIK - Wihdatul Ummah Medical Center")

# --- MODUL 1: INSTRUMEN AUDIT ---
if menu == "Instrumen Audit":
    st.header("📋 Form Audit Koding Diagnosis")
    
    with st.form("audit_form"):
        c1, c2 = st.columns(2)
        with c1:
            tgl = st.date_input("Tanggal Audit", datetime.now())
            no_rm = st.text_input("Nomor Rekam Medis")
            nama = st.text_input("Nama Pasien")
            unit = st.selectbox("Unit Layanan", ["Rawat Jalan", "Rawat Inap", "UGD"])
            diag_dr = st.text_area("Diagnosa dalam Resume Medis")
        
        with c2:
            k_rs = st.text_input("Kode ICD-10 Coder (SIMRS)").upper()
            k_audit = st.text_input("Kode ICD-10 Auditor").upper()
            dokumen = st.radio("Kelengkapan Dokumen", ["Lengkap", "Tidak Lengkap"])
            error_type = st.selectbox("Kategori Kesalahan", 
                                    ["Tidak Ada", "Salah Kode Karakter ke-3", "Salah Kode Karakter ke-4", "Beda Bab ICD-10", "Dokumen Tidak Terbaca"])
            
        auditor = st.text_input("Nama Auditor")
        
        # Logic otomatis
        is_akurat = "AKURAT" if k_rs == k_audit else "TIDAK AKURAT"
        rekomendasi = f"Verifikasi ulang Kode {k_audit}" if is_akurat == "TIDAK AKURAT" else "Sudah sesuai standar."
        
        btn_simpan = st.form_submit_button("Simpan Hasil Audit")
        
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
                st.success(f"Data Berhasil Disimpan!")
            else:
                st.error("Isi data yang wajib (No RM & Kode RS)!")

# --- MODUL 2: DASHBOARD MONITORING (VERSI AMAN TANPA PLOTLY) ---
elif menu == "Dashboard Mutu":
    st.header("📊 Dashboard Kualitas Data (QC)")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM audit_klinik", conn)
    conn.close()
    
    if not df.empty:
        total = len(df)
        akurat = len(df[df['akurasi_kode'] == 'AKURAT'])
        persen_akurat = (akurat/total) * 100
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sampel", f"{total} RM")
        m2.metric("Akurat", f"{akurat}")
        m3.metric("Tingkat Akurasi", f"{persen_akurat:.1f}%")
        
        st.markdown("---")
        # Menggunakan grafik bawaan Streamlit (pasti jalan di komputer mana saja)
        st.subheader("Grafik Kategori Kesalahan")
        error_counts = df['kategori_error'].value_counts()
        st.bar_chart(error_counts)
        
    else:
        st.info("Belum ada data untuk ditampilkan di Dashboard.")

# --- MODUL 3: RIWAYAT ---
elif menu == "Riwayat & Laporan":
    st.header("📄 Riwayat Audit")
    conn = sqlite3.connect(DB_NAME)
    df_history = pd.read_sql_query("SELECT * FROM audit_klinik", conn)
    conn.close()
    st.dataframe(df_history, use_container_width=True)

# --- MODUL 4: DECISION SUPPORT ---
elif menu == "Decision Support":
    st.header("💡 Rekomendasi Tindakan Mutu")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT kategori_error FROM audit_klinik", conn)
    conn.close()
    
    if not df.empty:
        top_error = df['kategori_error'].mode()[0]
        st.warning(f"Masalah Dominan: **{top_error}**")
        if top_error != "Tidak Ada":
            st.write("👉 **Saran:** Lakukan refreshment training coding ICD-10 khususnya pada Bab terkait.")
        else:
            st.write("👉 **Saran:** Kualitas coding sangat baik, pertahankan!")
    else:
        st.info("Data belum cukup.")
