import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Audit ICD-10", layout="wide")

# --- 2. DATABASE ENGINE ---
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

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🔍 Menu Audit MIK")
    menu = st.radio("Pilih Modul:", 
                    ["Dashboard Mutu", 
                     "Instrumen Audit", 
                     "Riwayat & Laporan", 
                     "Decision Support"])
    st.markdown("---")
    st.caption("Aplikasi Kendali Mutu Coding")

# --- 4. MODUL: INSTRUMEN AUDIT ---
if menu == "Instrumen Audit":
    st.header("📝 Form Audit Akurasi Koding")
    
    with st.form("audit_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Data Pasien")
            tgl = st.date_input("Tanggal Audit", datetime.now())
            no_rm = st.text_input("Nomor Rekam Medis")
            nama = st.text_input("Nama Pasien")
            unit = st.selectbox("Unit Layanan", ["Rawat Jalan", "Rawat Inap", "UGD"])
            diag_dr = st.text_area("Diagnosa dalam Resume Medis")
        
        with c2:
            st.subheader("Analisis Koding")
            k_rs = st.text_input("Kode ICD-10 Coder (SIMRS)").upper()
            k_audit = st.text_input("Kode ICD-10 Auditor (Gold Standard)").upper()
            dokumen = st.radio("Kelengkapan Dokumen", ["Lengkap", "Tidak Lengkap"])
            error_type = st.selectbox("Kategori Kesalahan", 
                                    ["Tidak Ada", "Salah Kode Karakter ke-3", "Salah Kode Karakter ke-4", "Beda Bab ICD-10", "Dokumen Tidak Terbaca"])
            
        auditor = st.text_input("Nama Auditor")
        
        # Logika Otomatis Akurasi
        is_akurat = "AKURAT" if k_rs == k_audit else "TIDAK AKURAT"
        rekomendasi = f"Verifikasi ulang Kode {k_audit}" if is_akurat == "TIDAK AKURAT" else "Koding sudah sesuai standar."
        
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
                st.success(f"Audit RM {no_rm} berhasil disimpan!")
            else:
                st.error("Mohon isi No RM dan Kode RS!")

# --- 5. MODUL: DASHBOARD MUTU ---
elif menu == "Dashboard Mutu":
    st.header("📈 Dashboard Kualitas Data Rekam Medis")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM audit_klinik", conn)
    conn.close()
    
    if not df.empty:
        total = len(df)
        akurat = len(df[df['akurasi_kode'] == 'AKURAT'])
        persen_akurat = (akurat/total) * 100
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Sampel", f"{total} RM")
        col_m2.metric("Coding Akurat", f"{akurat}")
        col_m3.metric("Persentase Akurasi", f"{persen_akurat:.1f}%")
        
        st.markdown("---")
        st.subheader("Sebaran Kategori Kesalahan")
        error_counts = df['kategori_error'].value_counts()
        st.bar_chart(error_counts)
        
    else:
        st.info("Belum ada data audit yang masuk.")

# --- 6. MODUL: RIWAYAT ---
elif menu == "Riwayat & Laporan":
    st.header("📋 Riwayat Audit Dokumen")
    conn = sqlite3.connect(DB_NAME)
    df_history = pd.read_sql_query("SELECT * FROM audit_klinik ORDER BY id DESC", conn)
    conn.close()
    
    if not df_history.empty:
        st.dataframe(df_history, use_container_width=True)
        csv = df_history.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Ekspor Laporan (CSV)", data=csv, file_name="laporan_audit.csv", mime='text/csv')
    else:
        st.info("Riwayat masih kosong.")

# --- 7. MODUL: DECISION SUPPORT ---
elif menu == "Decision Support":
    st.header("💡 Rekomendasi Perbaikan Mutu")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT kategori_error FROM audit_klinik", conn)
    conn.close()
    
    if not df.empty:
        top_error = df['kategori_error'].mode()[0]
        st.warning(f"Temuan Masalah Utama: **{top_error}**")
        
        with st.expander("Lihat Saran Tindakan"):
            if top_error == "Salah Kode Karakter ke-4":
                st.write("✅ Disarankan melakukan pelatihan ulang spesifikasi digit ke-4 ICD-10.")
            elif top_error == "Dokumen Tidak Terbaca":
                st.write("✅ Disarankan koordinasi dengan DPJP terkait kejelasan penulisan diagnosa.")
            else:
                st.write("✅ Pertahankan kualitas koding dan lakukan sampling audit secara berkala.")
    else:
        st.info("Data belum tersedia untuk analisis keputusan.")
