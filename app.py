import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- 1. CONFIG & UI STYLE ---
st.set_page_config(page_title="Klinik Digital Pro", layout="wide", page_icon="🏥")

def local_css():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #003366 0%, #00509d 50%, #f0f2f6 100%);
        background-attachment: fixed;
    }
    .main-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
    }
    .header-box {
        display: flex; align-items: center; justify-content: center;
        background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;
    }
    .ticket-box {
        background: #e3f2fd; padding: 25px; border-radius: 15px;
        text-align: center; border: 3px dashed #00509d; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_final.db')
    c = conn.cursor()
    # Tabel Master Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS master_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    # Tabel Transaksi Antrean (Berkelanjutan)
    c.execute('''CREATE TABLE IF NOT EXISTS antrean_harian 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status TEXT, tgl_antre DATE)''')
    conn.commit()
    conn.close()

def get_next_number(poli_nama):
    conn = sqlite3.connect('klinik_final.db')
    c = conn.cursor()
    # Menghitung total antrean di poli tersebut hari ini (tanpa membedakan lama/baru)
    c.execute("SELECT COUNT(*) FROM antrean_harian WHERE tgl_antre = ? AND poli = ?", (date.today(), poli_nama))
    count = c.fetchone()[0]
    conn.close()
    return (count % 200) + 1

init_db()

# --- 3. HEADER ---
st.markdown("""
<div class="header-box">
    <img src="https://cdn-icons-png.flaticon.com/512/3306/3306560.png" width="80">
    <div style="margin-left:20px; color:#003366;">
        <h1 style='margin:0;'>Sistem Antrean Klinik Terpadu</h1>
        <p style='margin:0;'>Pelayanan Cepat, Tepat, dan Akurat</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 4. LOGIKA PENDAFTARAN ---
menu = st.sidebar.radio("MENU", ["Pendaftaran", "Panggilan Perawat", "Monitor TV"])

if menu == "Pendaftaran":
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    status = st.radio("Status Kedatangan:", ["Pasien Baru (Pertama Kali)", "Pasien Lama (Sudah Pernah Daftar)"], horizontal=True)
    
    # Inisialisasi variabel untuk menghindari Error
    nik_input = ""
    nama_pasien = ""
    boleh_daftar = False

    if status == "Pasien Lama (Sudah Pernah Daftar)":
        st.subheader("🔍 Cari Data Pasien")
        search_nik = st.text_input("Masukkan NIK atau ID Card")
        
        if search_nik:
            conn = sqlite3.connect('klinik_final.db')
            c = conn.cursor()
            c.execute("SELECT nama, perusahaan, departemen FROM master_pasien WHERE nik = ?", (search_nik,))
            result = c.fetchone()
            conn.close()
            
            if result:
                st.success(f"Data Ditemukan: **{result[0]}** dari **{result[1]} - {result[2]}**")
                nik_input = search_nik
                nama_pasien = result[0]
                boleh_daftar = True
            else:
                st.error("NIK tidak ditemukan! Silakan pilih 'Pasien Baru' jika Anda belum pernah mendaftar.")
    
    else:
        st.subheader("📝 Registrasi Pasien Baru")
        c1, c2 = st.columns(2)
        with c1:
            nama_new = st.text_input("Nama Lengkap")
            nik_new = st.text_input("NIK / ID Card")
            tempat_l = st.text_input("Tempat Lahir")
            tgl_l = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
            gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            no_hp = st.text_input("No. WhatsApp")
        with c2:
            perusahaan = st.text_input("Perusahaan")
            dept = st.text_input("Departemen")
            jabatan = st.text_input("Jabatan")
            mes = st.text_input("Blok Mes")
            kamar = st.text_input("Nomor Kamar")
            gol_d = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
        
        riwayat_p = st.text_area("Riwayat Penyakit")
        riwayat_a = st.text_area("Riwayat Alergi")
        area_k = st.text_input("Area Lokasi Kerja")
        
        if nama_new and nik_new:
            nik_input = nik_new
            nama_pasien = nama_new
            boleh_daftar = True

    # FORM PILIH POLI (Muncul untuk keduanya jika data sudah valid)
    if boleh_daftar:
        st.divider()
        poli_tujuan = st.selectbox("Pilih Poli Tujuan Berobat:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"])
        btn_daftar = st.button("AMBIL NOMOR ANTREAN")

        if btn_daftar:
            conn = sqlite3.connect('klinik_final.db')
            c = conn.cursor()
            
            try:
                # Jika Pasien Baru, simpan dulu ke Master Data
                if status == "Pasien Baru (Pertama Kali)":
                    c.execute("INSERT INTO master_pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (nik_new, nama_new, tempat_l, str(tgl_l), gender, "Islam", no_hp, perusahaan, 
                               dept, jabatan, mes, kamar, riwayat_p, riwayat_a, area_k, gol_d))
                
                # Proses Antrean (Berkelanjutan)
                kode_map = {"Poli Umum":"U", "Poli Gigi":"G", "MCU":"M", "UGD":"ER", "Rawat Inap":"RI"}
                no_urut = get_next_number(poli_tujuan)
                label_antrean = f"{kode_map[poli_tujuan]}-{no_urut:02d}"
                
                c.execute("INSERT INTO antrean_harian (nik, no_urut, poli, status, tgl_antre) VALUES (?,?,?,?,?)",
                          (nik_input, label_antrean, poli_tujuan, "Menunggu", date.today()))
                conn.commit()
                
                st.markdown(f"""
                <div class="ticket-box">
                    <h2 style='color:#00509d; margin:0;'>NOMOR ANTREAN</h2>
                    <h1 style='font-size:100px; margin:10px 0;'>{label_antrean}</h1>
                    <h3>Pasien: {nama_pasien}</h3>
                    <p>Tujuan: <b>{poli_tujuan}</b></p>
                    <p style='font-size:12px;'>Mohon menunggu panggilan perawat di layar monitor</p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            except sqlite3.IntegrityError:
                st.error("Error: NIK ini sudah ada di sistem. Gunakan menu 'Pasien Lama'.")
            finally:
                conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MODUL PERAWAT & MONITOR (Sama seperti sebelumnya) ---
elif menu == "Panggilan Perawat":
    st.title("👩‍⚕️ Panel Perawat")
    p_poli = st.selectbox("Poli Anda:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"])
    conn = sqlite3.connect('klinik_final.db')
    df = pd.read_sql_query(f"SELECT a.id, a.no_urut, p.nama FROM antrean_harian a JOIN master_pasien p ON a.nik = p.nik WHERE a.poli = '{p_poli}' AND a.status = 'Menunggu' AND a.tgl_antre = '{date.today()}'", conn)
    if not df.empty:
        st.table(df[['no_urut', 'nama']])
        if st.button("PANGGIL PASIEN"):
            c = conn.cursor()
            c.execute("UPDATE antrean_harian SET status = 'Dipanggil' WHERE id = ?", (int(df.iloc[0]['id']),))
            conn.commit()
            st.rerun()
    else: st.info("Tidak ada antrean.")
    conn.close()

elif menu == "Monitor TV":
    st.title("📺 Antrean Sekarang")
    conn = sqlite3.connect('klinik_final.db')
    polis = ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"]
    cols = st.columns(len(polis))
    for i, p in enumerate(polis):
        with cols[i]:
            st.markdown(f"<div style='background:#003366; color:white; padding:15px; border-radius:10px; text-align:center;'><h4>{p}</h4>", unsafe_allow_html=True)
            res = pd.read_sql_query(f"SELECT no_urut FROM antrean_harian WHERE poli='{p}' AND status='Dipanggil' AND tgl_antre='{date.today()}' ORDER BY id DESC LIMIT 1", conn)
            val = res['no_urut'][0] if not res.empty else "--"
            st.markdown(f"<h1 style='color:#ffcc00;'>{val}</h1></div>", unsafe_allow_html=True)
    conn.close()
    time.sleep(5)
    st.rerun()
