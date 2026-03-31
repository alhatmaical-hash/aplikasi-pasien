import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- 1. PENGATURAN DATABASE ---
def init_db():
    conn = sqlite3.connect('data_klinik.db')
    c = conn.cursor()
    # Membuat tabel jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS pasien 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  no_antrean TEXT, 
                  nama TEXT, 
                  tgl_lahir TEXT, 
                  gender TEXT, 
                  no_hp TEXT, 
                  poli TEXT, 
                  keluhan TEXT, 
                  tgl_daftar DATE)''')
    conn.commit()
    conn.close()

def simpan_ke_db(antrean, nama, tgl, gender, hp, poli, keluhan):
    conn = sqlite3.connect('data_klinik.db')
    c = conn.cursor()
    c.execute("INSERT INTO pasien (no_antrean, nama, tgl_lahir, gender, no_hp, poli, keluhan, tgl_daftar) VALUES (?,?,?,?,?,?,?,?)",
              (antrean, nama, tgl, gender, hp, poli, keluhan, date.today()))
    conn.commit()
    conn.close()

# Jalankan fungsi database
init_db()

# --- 2. TAMPILAN ANTARMUKA (UI) ---
st.set_page_config(page_title="Sistem Pendaftaran Klinik", page_icon=" ", layout="wide")

# Sidebar untuk Navigasi
st.sidebar.title("Menu Klinik")
pilihan = st.sidebar.radio("Navigasi:", ["Pendaftaran Pasien", "Data Admin (Rekap)"])

# --- HALAMAN PENDAFTARAN ---
if pilihan == "Pendaftaran Pasien":
    st.title(" Pendaftaran Pasien Baru")
    st.write("Silakan isi data diri Anda dengan benar.")
    
    with st.form("form_pasien", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nama = st.text_input("Nama Lengkap Pasien")
            tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1940, 1, 1))
            gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            
        with col2:
            poli = st.selectbox("Pilih Poli", ["Umum", "Gigi", "Anak", "Mata", "Kandungan"])
            whatsapp = st.text_input("Nomor WhatsApp (Aktif)")
            
        keluhan = st.text_area("Keluhan Utama")
        
        submit = st.form_submit_button("Daftar Sekarang")

    if submit:
        if nama and whatsapp:
            # Membuat Nomor Antrean (Contoh: G-123)
            kode_p = poli[0].upper() # Ambil huruf depan poli
            detik = int(time.time()) % 1000 # Ambil 3 angka unik dari waktu
            antrean_final = f"{kode_p}-{detik:03d}"
            
            # Simpan ke Database
            simpan_ke_db(antrean_final, nama, str(tgl_lahir), gender, whatsapp, poli, keluhan)
            
            # Tampilan Sukses
            st.success("✅ Pendaftaran Berhasil!")
            st.balloons()
            
            # "Kertas" Antrean
            st.markdown(f"""
            <div style="border: 2px dashed #4CAF50; padding: 20px; border-radius: 10px; background-color: #f9f9f9;">
                <h3 style="text-align: center; color: #4CAF50;">TIKET ANTREAN</h3>
                <h1 style="text-align: center; font-size: 50px;">{antrean_final}</h1>
                <p style="text-align: center;"><b>Nama:</b> {nama} | <b>Poli:</b> {poli}</p>
                <p style="text-align: center; font-size: 12px;">Pendaftaran pada: {date.today()}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Link WhatsApp Otomatis ke Admin
            nomor_admin = "082347353762" # Ganti dengan nomor Anda
            pesan = f"Halo Admin, saya {nama} baru saja mendaftar online untuk Poli {poli} dengan No. Antrean {antrean_final}."
            st.markdown(f"[📲 Klik di sini untuk Konfirmasi via WhatsApp](https://wa.me/{nomor_admin}?text={pesan.replace(' ', '%20')})")
        else:
            st.error("Gagal: Nama dan Nomor WhatsApp tidak boleh kosong!")

# --- HALAMAN ADMIN ---
else:
    st.title("📂 Data & Laporan Pasien")
    
    conn = sqlite3.connect('data_klinik.db')
    df = pd.read_sql_query("SELECT * FROM pasien ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        st.subheader("Daftar Seluruh Pasien Terdaftar")
        st.dataframe(df, use_container_width=True)
        
        # Tombol Download Excel/CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Unduh Data Pasien (CSV)",
            data=csv,
            file_name=f'rekap_pasien_{date.today()}.csv',
            mime='text/csv',
        )
        
        st.divider()
        st.write(f"Total Pasien Terdaftar: **{len(df)} Orang**")
    else:
        st.info("Belum ada data pasien yang masuk hari ini.")
