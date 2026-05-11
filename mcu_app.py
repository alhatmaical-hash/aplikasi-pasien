import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from io import BytesIO

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('mcu_complex.db')
    c = conn.cursor()
    # Tabel Master
    c.execute('CREATE TABLE IF NOT EXISTS master_perusahaan (nama TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS master_dept (nama TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS master_jabatan (nama TEXT)')
    
    # Tabel Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id_karyawan TEXT PRIMARY KEY, nik TEXT, nama TEXT, tempat_lahir TEXT, 
                    tgl_lahir TEXT, usia INTEGER, gender TEXT, doh TEXT, perusahaan TEXT, 
                    dept TEXT, jabatan TEXT, lokasi TEXT, no_hp TEXT, status_nikah TEXT, 
                    jml_anak INTEGER, tempat_tinggal TEXT, sumber_air TEXT)''')
    
    # Tabel Pemeriksaan & Hasil
    c.execute('''CREATE TABLE IF NOT EXISTS hasil_mcu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, id_karyawan TEXT, jenis_mcu TEXT, 
                    lab_summary TEXT, non_lab_summary TEXT, kesimpulan TEXT, 
                    follow_up TEXT, saran TEXT, tgl_periksa TEXT)''')
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def hitung_usia(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

# --- UI APP ---
def main():
    st.set_page_config(page_title="Sistem Manajemen MCU Klinik", layout="wide")
    init_db()

    st.sidebar.title("🏥 Klinik MCU")
    menu = ["Dashboard", "Master Data", "1. Registrasi Pasien", "2. Pemeriksaan & Upload", "3. Hasil & Kesimpulan (Dokter)"]
    choice = st.sidebar.radio("Navigasi", menu)

    # --- MENU: DASHBOARD ---
    if choice == "Dashboard":
        st.title("📊 Dashboard Pelayanan MCU")
        conn = sqlite3.connect('mcu_complex.db')
        df_p = pd.read_sql_query("SELECT * FROM pasien", conn)
        df_h = pd.read_sql_query("SELECT * FROM hasil_mcu", conn)
        conn.close()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registrasi", len(df_p))
        col2.metric("MCU Selesai", len(df_h))
        col3.metric("Fit for Work", len(df_h[df_h['kesimpulan'] == "Fit for Work"]) if not df_h.empty else 0)

        st.divider()
        st.subheader("📋 Daftar Pasien Terregistrasi")
        st.dataframe(df_p, use_container_width=True, hide_index=True)

    # --- MENU: MASTER DATA ---
    elif choice == "Master Data":
        st.header("⚙️ Manajemen Data Master")
        col1, col2, col3 = st.columns(3)
        conn = sqlite3.connect('mcu_complex.db')
        with col1:
            new_pt = st.text_input("Tambah Perusahaan")
            if st.button("Simpan PT"):
                conn.execute('INSERT INTO master_perusahaan VALUES (?)', (new_pt,))
                conn.commit()
                st.success("PT Tersimpan")
        with col2:
            new_dept = st.text_input("Tambah Departemen")
            if st.button("Simpan Dept"):
                conn.execute('INSERT INTO master_dept VALUES (?)', (new_dept,))
                conn.commit()
                st.success("Dept Tersimpan")
        with col3:
            new_jab = st.text_input("Tambah Jabatan")
            if st.button("Simpan Jabatan"):
                conn.execute('INSERT INTO master_jabatan VALUES (?)', (new_jab,))
                conn.commit()
                st.success("Jabatan Tersimpan")
        conn.close()

    # --- MENU 1: REGISTRASI ---
    elif choice == "1. Registrasi Pasien":
        st.header("📝 Form Registrasi Karyawan")
        with st.form("regis_form"):
            c1, c2, c3 = st.columns(3)
            id_kar = c1.text_input("No ID Karyawan")
            nik = c2.text_input("NIK KTP")
            nama = c3.text_input("Nama Lengkap")
            tgl_lhr = c1.date_input("Tanggal Lahir", min_value=date(1960,1,1))
            usia = hitung_usia(tgl_lhr)
            c2.info(f"Usia: {usia} Tahun")
            gender = c3.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            doh = c1.date_input("Date of Hire")
            
            conn = sqlite3.connect('mcu_complex.db')
            pts = [x[0] for x in conn.execute('SELECT * FROM master_perusahaan').fetchall()]
            depts = [x[0] for x in conn.execute('SELECT * FROM master_dept').fetchall()]
            jabs = [x[0] for x in conn.execute('SELECT * FROM master_jabatan').fetchall()]
            conn.close()
            
            pt = c2.selectbox("Perusahaan", pts if pts else ["-"])
            dept = c3.selectbox("Departemen", depts if depts else ["-"])
            jab = c1.selectbox("Jabatan", jabs if jabs else ["-"])
            lokasi = c2.text_input("Lokasi Kerja")
            hp = c3.text_input("No HP")
            status_m = c1.selectbox("Status Pernikahan", ["Lajang", "Menikah", "Cerai"])
            jml_anak = c2.number_input("Jumlah Anak", 0, 10)
            tinggal = c3.selectbox("Tempat Tinggal", ["Mes", "Kawasi", "Lainnya"])
            air = c1.selectbox("Sumber Air", ["RO", "Galon", "Sumur"])
            
            if st.form_submit_button("Simpan Registrasi"):
                conn = sqlite3.connect('mcu_complex.db')
                conn.execute('INSERT OR REPLACE INTO pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                             (id_kar, nik, nama, "Tempat", str(tgl_lhr), usia, gender, str(doh), pt, dept, jab, lokasi, hp, status_m, jml_anak, tinggal, air))
                conn.commit()
                conn.close()
                st.success("Registrasi Berhasil!")

    # --- MENU 2: PEMERIKSAAN & UPLOAD ---
    elif choice == "2. Pemeriksaan & Upload":
        st.header("🩺 Input Pemeriksaan & Upload Lampiran")
        id_cari = st.text_input("Masukkan ID Karyawan")
        if id_cari:
            with st.expander("Fisik & Upload", expanded=True):
                antropometri = st.text_area("Antropometri (TB, BB, BMI)")
                up_lab = st.file_uploader("Upload Hasil Lab/Rad/EKG", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
                if st.button("Simpan Progres"):
                    st.success("Data pemeriksaan awal tersimpan.")

    # --- MENU 3: HASIL & KESIMPULAN (DOKTER) ---
    elif choice == "3. Hasil & Kesimpulan (Dokter)":
        st.header("👨‍⚕️ Resume Medis & Penentuan Kelayakan")
        id_dr = st.text_input("ID Karyawan untuk Resume")
        if id_dr:
            tab1, tab2, tab3 = st.tabs(["Laboratorium", "Non-Laboratorium", "Kesimpulan"])
            with tab1:
                hem = st.text_area("Hematologi")
                kim = st.text_area("Kimia Klinik")
                ser = st.multiselect("Serologi", ["HBsAg", "Anti HIV", "Anti HCV"])
            with tab2:
                ekg = st.text_input("Hasil EKG")
                rad = st.text_input("Hasil Rontgen")
            with tab3:
                kes = st.radio("Status", ["Fit for Work", "Fit with Note", "Fit with Restriction", "Unfit Temporary", "Unfit"], horizontal=True)
                fu1 = st.checkbox("Ke Klinik")
                fu2 = st.checkbox("Ke Spesialis")
                saran = st.text_area("Saran")
                
                if st.button("Finalisasi & Simpan"):
                    conn = sqlite3.connect('mcu_complex.db')
                    conn.execute('INSERT INTO hasil_mcu (id_karyawan, lab_summary, non_lab_summary, kesimpulan, saran, tgl_periksa) VALUES (?,?,?,?,?,?)',
                                 (id_dr, f"Hem: {hem}, Ser: {ser}", f"EKG: {ekg}, Rad: {rad}", kes, saran, str(date.today())))
                    conn.commit()
                    conn.close()
                    st.success("Data MCU Final Tersimpan!")

if __name__ == "__main__":
    main()
