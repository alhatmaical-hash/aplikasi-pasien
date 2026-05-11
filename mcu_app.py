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
                    id INTEGER PRIMARY KEY AUTOINCREMENT, id_karyawan TEXT, jenis_mcu TEXT, mcu_ke INTEGER,
                    antropometri TEXT, visus TEXT, buta_warna TEXT, 
                    lab_summary TEXT, non_lab_summary TEXT, fisik_umum TEXT,
                    kesimpulan TEXT, follow_up TEXT, saran TEXT, tgl_periksa TEXT)''')
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

    # --- MENU MASTER DATA ---
    if choice == "Master Data":
        st.header("⚙️ Manajemen Data Master")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_pt = st.text_input("Tambah Perusahaan")
            if st.button("Simpan PT"):
                conn = sqlite3.connect('mcu_complex.db'); conn.execute('INSERT INTO master_perusahaan VALUES (?)', (new_pt,)); conn.commit()
        with col2:
            new_dept = st.text_input("Tambah Departemen")
            if st.button("Simpan Dept"):
                conn = sqlite3.connect('mcu_complex.db'); conn.execute('INSERT INTO master_dept VALUES (?)', (new_dept,)); conn.commit()
        with col3:
            new_jab = st.text_input("Tambah Jabatan")
            if st.button("Simpan Jabatan"):
                conn = sqlite3.connect('mcu_complex.db'); conn.execute('INSERT INTO master_jabatan VALUES (?)', (new_jab,)); conn.commit()

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
            c2.info(f"Usia Terhitung: {usia} Tahun")
            
            gender = c3.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            doh = c1.date_input("Date of Hire (Masa Kerja)")
            
            # Ambil data dari master
            conn = sqlite3.connect('mcu_complex.db')
            list_pt = [x[0] for x in conn.execute('SELECT * FROM master_perusahaan').fetchall()]
            list_dept = [x[0] for x in conn.execute('SELECT * FROM master_dept').fetchall()]
            list_jab = [x[0] for x in conn.execute('SELECT * FROM master_jabatan').fetchall()]
            
            pt = c2.selectbox("Perusahaan", list_pt if list_pt else ["-"])
            dept = c3.selectbox("Departemen", list_dept if list_dept else ["-"])
            jab = c1.selectbox("Jabatan", list_jab if list_jab else ["-"])
            
            lokasi = c2.text_input("Lokasi Kerja")
            hp = c3.text_input("No HP")
            
            status_m = c1.selectbox("Status Pernikahan", ["Lajang", "Menikah", "Cerai"])
            jml_anak = c2.number_input("Jumlah Anak", 0, 20)
            tinggal = c3.selectbox("Tempat Tinggal", ["Mes", "Kawasi", "Lainnya"])
            air = c1.selectbox("Sumber Air Minum", ["RO", "Galon Isi Ulang", "Sumur", "PDAM"])
            
            if st.form_submit_button("Daftarkan Karyawan"):
                conn = sqlite3.connect('mcu_complex.db')
                conn.execute('INSERT OR REPLACE INTO pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                             (id_kar, nik, nama, "Tempat", str(tgl_lhr), usia, gender, str(doh), pt, dept, jab, lokasi, hp, status_m, jml_anak, tinggal, air))
                conn.commit()
                st.success("Data Karyawan Berhasil Disimpan!")

    # --- MENU 2: PEMERIKSAAN & UPLOAD ---
    elif choice == "2. Pemeriksaan & Upload":
        st.header("🩺 Input Pemeriksaan & Upload Lampiran")
        id_cari = st.text_input("Masukkan ID Karyawan untuk Mulai Pemeriksaan")
        
        if id_cari:
            with st.expander("Input Fisik & Antropometri", expanded=True):
                col1, col2 = st.columns(2)
                antropometri = col1.text_area("Antropometri (TB, BB, BMI, Lingkar Perut)")
                visus = col2.text_area("Visus (Mata Kanan/Kiri)")
                buta_warna = col1.selectbox("Buta Warna", ["Tidak Buta Warna", "Buta Warna Parsial", "Buta Warna Total"])

            with st.expander("Upload Hasil Penunjang (PDF/Image)"):
                up_lab = st.file_uploader("Upload Hasil Lab (PDF)", type=['pdf', 'jpg', 'png'])
                up_rad = st.file_uploader("Upload Hasil Radiologi (PDF)", type=['pdf', 'jpg', 'png'])
                up_ekg = st.file_uploader("Upload Hasil EKG (PDF)", type=['pdf', 'jpg', 'png'])
                if up_lab: st.success("Lab terupload!")

            if st.button("Simpan Tahap Awal"):
                st.toast("Data pemeriksaan awal tersimpan.")

    # --- MENU 3: HASIL & KESIMPULAN (DOKTER) ---
    elif choice == "3. Hasil & Kesimpulan (Dokter)":
        st.header("👨‍⚕️ Resume Medis & Penentuan Kelayakan")
        id_dr = st.text_input("ID Karyawan")
        
        if id_dr:
            st.subheader("Rangkuman Hasil")
            tab1, tab2, tab3 = st.tabs(["Laboratorium", "Non-Laboratorium", "Fisik & Kesimpulan"])
            
            with tab1:
                hematologi = st.text_area("Hematologi Lengkap")
                kimia = st.text_area("Kimia Klinik")
                urine = st.text_area("Urine Lengkap")
                serologi = st.multiselect("Serologi Positif", ["HBsAg", "Anti HCV", "Anti HAV", "Anti HIV"])
            
            with tab2:
                ekg_res = st.text_input("Hasil EKG")
                rad_res = st.text_input("Hasil Rontgen Thorax PA")
                audio = st.text_input("Audiometri")
                spiro = st.text_input("Spirometri")
            
            with tab3:
                st.write("### Kesimpulan Kelayakan")
                kesimpulan = st.radio("Status Kelayakan", 
                    ["Fit for Work", "Fit with Note", "Fit with Restriction", "Unfit Temporary", "Unfit"], horizontal=True)
                
                st.write("### Follow Up")
                fu_klinik = st.checkbox("Memerlukan pengobatan ke klinik")
                fu_spesialis = st.checkbox("Memerlukan pengobatan ke dokter spesialis")
                
                saran = st.text_area("Catatan atau Saran Medis")
                
                if st.button("Finalisasi & Generate Report"):
                    st.success("Data Final MCU Berhasil Disimpan!")
                    st.download_button("Download PDF (Simulasi)", b"PDF_CONTENT", "Hasil_MCU.pdf")

if __name__ == "__main__":
    main()
