import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('mcu_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mcu_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_periksa TEXT,
                    nama TEXT,
                    nik TEXT,
                    perusahaan TEXT,
                    jenis_mcu TEXT,
                    tinggi REAL,
                    berat REAL,
                    bmi REAL,
                    sistolik INTEGER,
                    diastolik INTEGER,
                    gds REAL,
                    hb REAL,
                    kesimpulan TEXT,
                    catatan TEXT)''')
    conn.commit()
    conn.close()

# --- LOGIKA MEDIS ---
def hitung_mcu_logic(sistolik, gds, bmi):
    # Penentuan Status Kelayakan
    if sistolik >= 160 or gds >= 200:
        return "TEMPORARY UNFIT", "Hipertensi/Gula Darah tinggi. Perlu stabilisasi."
    elif 140 <= sistolik < 160 or 25 <= bmi < 30:
        return "FIT WITH NOTE", "Kondisi terkontrol, perlu observasi rutin."
    elif sistolik < 140 and gds < 140:
        return "FIT TO WORK", "Kondisi sehat sesuai standar."
    else:
        return "PENDING", "Memerlukan pemeriksaan penunjang lanjutan."

# --- UI APP ---
def main():
    st.set_page_config(page_title="Sistem MCU Profesional", layout="wide")
    init_db()

    # Sidebar Navigasi
    st.sidebar.image("harita.jpg", width=150) # Menggunakan logo yang ada di repo Anda
    menu = ["🏠 Dashboard", "📝 Registrasi & Pemeriksaan", "📊 Data & Rekapitulasi"]
    choice = st.sidebar.selectbox("Menu Utama", menu)

    if choice == "🏠 Dashboard":
        st.title("Pusat Layanan Medical Check-Up")
        st.info("Selamat datang di modul integrasi MCU Klinik Harita.")
        
        # Statistik Singkat
        conn = sqlite3.connect('mcu_database.db')
        df = pd.read_sql_query("SELECT * FROM mcu_records", conn)
        conn.close()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pemeriksaan", len(df))
        col2.metric("Fit to Work", len(df[df['kesimpulan'] == "FIT TO WORK"]))
        col3.metric("Unfit/Temporary", len(df[df['kesimpulan'] == "TEMPORARY UNFIT"]))

    elif choice == "📝 Registrasi & Pemeriksaan":
        st.header("Form Pemeriksaan MCU Lengkap")
        
        with st.form("form_mcu"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Data Peserta")
                nama = st.text_input("Nama Lengkap / 姓名")
                nik = st.text_input("NIK / 身份证号码")
                perusahaan = st.selectbox("Perusahaan", ["PT. HJF", "PT. KPS", "PT. OST", "PT. CKM"])
                jenis = st.radio("Jenis MCU", ["Pre-Employment", "Annual MCU"])
            
            with col2:
                st.subheader("Vital Sign & Fisik")
                tb = st.number_input("Tinggi Badan (cm)", value=165)
                bb = st.number_input("Berat Badan (kg)", value=60)
                td_s = st.number_input("Sistolik (mmHg)", value=120)
                td_d = st.number_input("Diastolik (mmHg)", value=80)
            
            st.divider()
            st.subheader("Hasil Laboratorium")
            c3, c4 = st.columns(2)
            with c3:
                hb = st.number_input("Hemoglobin (g/dL)", value=14.0)
            with c4:
                gds = st.number_input("Gula Darah (mg/dL)", value=100)

            catatan_dokter = st.text_area("Catatan Tambahan Dokter")
            
            submit = st.form_submit_button("Simpan & Proses Hasil")
            
            if submit:
                # Kalkulasi otomatis
                bmi_val = round(bb / ((tb/100)**2), 2)
                status, saran = hitung_mcu_logic(td_s, gds, bmi_val)
                tgl_skrg = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # Simpan ke DB
                conn = sqlite3.connect('mcu_database.db')
                c = conn.cursor()
                c.execute('''INSERT INTO mcu_records (tgl_periksa, nama, nik, perusahaan, jenis_mcu, tinggi, berat, bmi, sistolik, diastolik, gds, hb, kesimpulan, catatan)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                            (tgl_skrg, nama, nik, perusahaan, jenis, tb, bb, bmi_val, td_s, td_d, gds, hb, status, catatan_dokter))
                conn.commit()
                conn.close()
                
                st.success(f"Data Berhasil Disimpan! Status: {status}")
                st.info(f"Saran Medis: {saran}")

    elif choice == "📊 Data & Rekapitulasi":
        st.header("Laporan Hasil MCU")
        conn = sqlite3.connect('mcu_database.db')
        df = pd.read_sql_query("SELECT * FROM mcu_records ORDER BY id DESC", conn)
        conn.close()
        
        # Fitur Pencarian
        search = st.text_input("Cari Nama atau NIK")
        if search:
            df = df[df['nama'].str.contains(search, case=False) | df['nik'].contains(search)]
        
        st.dataframe(df, use_container_width=True)
        
        # Tombol Download CSV untuk HR
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Rekap Excel/CSV", data=csv, file_name="rekap_mcu.csv", mime="text/csv")

if __name__ == "__main__":
    main()
