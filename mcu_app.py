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

        # 1. Row Statistik Utama
        col1, col2, col3 = st.columns(3)
        total_mcu = len(df_h)
        col1.metric("Total Pasien Terdaftar", f"{len(df_p)} Orang")
        col2.metric("Total MCU Selesai", f"{total_mcu} Pemeriksaan")
        
        # Hitung persentase penyelesaian (optional tapi keren)
        prosentase = (total_mcu / len(df_p) * 100) if len(df_p) > 0 else 0
        col3.metric("Penyelesaian MCU", f"{prosentase:.1f}%")

        st.divider()

        # 2. Row Statistik Detail (Fit, Unfit, Follow Up)
        st.subheader("📈 Statistik Kondisi Kesehatan")
        s1, s2, s3, s4 = st.columns(4)
        
        if not df_h.empty:
            # Hitung Status Fit
            # Kita hitung yang mengandung kata 'Fit' (Fit for Work, Fit with Note, Fit with Restriction)
            jml_fit = len(df_h[df_h['kesimpulan'].str.contains('Fit', na=False)])
            jml_unfit = len(df_h[df_h['kesimpulan'].str.contains('Unfit', na=False)])
            
            # Hitung Follow Up (Berdasarkan teks di kolom follow_up)
            # Catatan: Ini bergantung pada string yang disimpan saat finalisasi
            jml_klinik = len(df_h[df_h['follow_up'].str.contains('klinik', na=False, case=False)])
            jml_spesialis = len(df_h[df_h['follow_up'].str.contains('spesialis', na=False, case=False)])
            
            s1.success(f"✅ Total Fit\n### {jml_fit}")
            s2.error(f"❌ Total Unfit\n### {jml_unfit}")
            s3.warning(f"🏥 Kontrol Klinik\n### {jml_klinik}")
            s4.info(f"👨‍⚕️ Ke Spesialis\n### {jml_spesialis}")
        else:
            st.info("Statistik akan muncul setelah ada pemeriksaan yang diselesaikan oleh Dokter.")

        st.divider()

        # 3. Tabel Pasien & Fitur Manajemen
        st.subheader("📋 Manajemen Daftar Pasien")
        
        if not df_p.empty:
            # Tombol Download Excel
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_p.to_excel(writer, index=False, sheet_name='Daftar_Pasien')
                if not df_h.empty:
                    df_h.to_excel(writer, index=False, sheet_name='Hasil_MCU')
            
            st.download_button(
                label="📥 Download Data ke Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"Rekap_MCU_{date.today()}.xlsx",
                mime="application/vnd.ms-excel"
            )

            # Fitur Hapus Data
            with st.expander("🗑️ Zona Bahaya (Hapus Data Pasien)"):
                id_hapus = st.selectbox("Pilih ID Karyawan yang akan dihapus:", ["-- Pilih ID --"] + df_p['id_karyawan'].tolist())
                if st.button("Konfirmasi Hapus Pasien"):
                    if id_hapus != "-- Pilih ID --":
                        conn = sqlite3.connect('mcu_complex.db')
                        cur = conn.cursor()
                        # Hapus di tabel pasien dan hasil mcu
                        cur.execute("DELETE FROM pasien WHERE id_karyawan=?", (id_hapus,))
                        cur.execute("DELETE FROM hasil_mcu WHERE id_karyawan=?", (id_hapus,))
                        conn.commit()
                        conn.close()
                        st.error(f"Data {id_hapus} telah dihapus.")
                        st.rerun() # Refresh halaman

            st.dataframe(df_p, use_container_width=True, hide_index=True)
        else:
            st.write("Belum ada data pasien.")

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
        
        # Ambil data dari master untuk dropdown
        conn = sqlite3.connect('mcu_complex.db')
        list_pt = [x[0] for x in conn.execute('SELECT * FROM master_perusahaan').fetchall()]
        list_dept = [x[0] for x in conn.execute('SELECT * FROM master_dept').fetchall()]
        list_jab = [x[0] for x in conn.execute('SELECT * FROM master_jabatan').fetchall()]
        conn.close()

        with st.form("regis_form"):
            # Baris 1
            c1, c2, c3 = st.columns(3)
            # Dropdown Jenis MCU (Hijau) - Kosong di awal
            jenis_mcu = c1.selectbox("Jenis MCU", 
                                     ["MCU ANNUAL (MCU TAHUNAN)", "PRE EMPLOYMENT (MCU KARYAWAN BARU)"], 
                                     index=None, placeholder="Pilih Jenis MCU...")
            id_kar = c2.text_input("No ID Karyawan")
            nik = c3.text_input("NIK KTP")
            
            # Baris 2
            c4, c5, c6 = st.columns(3)
            nama = c4.text_input("Nama Lengkap")
            tgl_lhr = c5.date_input("Tanggal Lahir", min_value=date(1960,1,1))
            usia = hitung_usia(tgl_lhr)
            c6.info(f"Usia Terhitung: {usia} Tahun")
            
            # Baris 3
            c7, c8, c9 = st.columns(3)
            # Dropdown Jenis Kelamin (Hijau) - Kosong di awal
            gender = c7.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"], index=None, placeholder="Pilih...")
            doh_manual = c8.text_input("Masa Lama Kerja (Date of Hire)", placeholder="Contoh: 2 Tahun / 5 Bulan")
            # Dropdown Perusahaan (Hijau) - Kosong di awal
            pt = c9.selectbox("Perusahaan", list_pt, index=None, placeholder="Pilih Perusahaan...")

            # Baris 4
            c10, c11, c12 = st.columns(3)
            # Dropdown Departemen (Hijau) - Kosong di awal
            dept = c10.selectbox("Departemen", list_dept, index=None, placeholder="Pilih Departemen...")
            # Dropdown Jabatan (Hijau) - Kosong di awal
            jab = c11.selectbox("Jabatan", list_jab, index=None, placeholder="Pilih Jabatan...")
            lokasi = c12.text_input("Lokasi Kerja")

            # Baris 5
            c13, c14, c15 = st.columns(3)
            hp = c13.text_input("No HP")
            # Dropdown Status Pernikahan (Hijau) - Kosong di awal
            status_m = c14.selectbox("Status Pernikahan", ["Lajang", "Menikah", "Cerai"], index=None, placeholder="Pilih...")
            jml_anak = c15.number_input("Jumlah Anak", 0, 20)

            # Baris 6
            c16, c17, c18 = st.columns(3)
            # Dropdown Tempat Tinggal (Hijau) - Kosong di awal
            tinggal = c16.selectbox("Tempat Tinggal", ["Mes", "Kawasi", "Lainnya"], index=None, placeholder="Pilih...")
            # Dropdown Sumber Air (Hijau) - Kosong di awal
            air = c17.selectbox("Sumber Air Minum", ["RO", "Galon Isi Ulang", "Sumur", "PDAM"], index=None, placeholder="Pilih...")
            
            # Logika Kondisional untuk kolom MCU Annual Ke-
            mcu_ke = 0
            if jenis_mcu == "MCU ANNUAL (MCU TAHUNAN)":
                mcu_ke = c18.number_input("MCU Annual Ke-", min_value=1, step=1)
            else:
                # Menampilkan kolom kosong sebagai placeholder agar layout tetap rapi
                c18.write("") 
            
            submit_btn = st.form_submit_button("Simpan Registrasi")
            
            if submit_btn:
                if not jenis_mcu or not pt or not dept or not gender:
                    st.error("Silakan lengkapi semua pilihan yang bertanda dropdown!")
                else:
                    conn = sqlite3.connect('mcu_complex.db')
                    conn.execute('''INSERT OR REPLACE INTO pasien 
                                 (id_karyawan, nik, nama, tgl_lahir, usia, gender, doh, perusahaan, dept, jabatan, lokasi, no_hp, status_nikah, jml_anak, tempat_tinggal, sumber_air) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                 (id_kar, nik, nama, str(tgl_lhr), usia, gender, doh_manual, pt, dept, jab, lokasi, hp, status_m, jml_anak, tinggal, air))
                    conn.commit()
                    conn.close()
                    st.success(f"Berhasil! {nama} terdaftar untuk {jenis_mcu}")

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
