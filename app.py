import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time
import base64

# --- 1. FUNGSI UNTUK BACKGROUND GAMBAR LOKAL ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    page_bg_img = f'''
    <style>
    * {{
        font-family: "Times New Roman", Times, serif !important;
    }}
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_digital.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS master_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antrean_harian 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status TEXT, tgl_antre DATE)''')
    conn.commit()
    conn.close()

def get_next_number(poli_nama):
    conn = sqlite3.connect('klinik_digital.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM antrean_harian WHERE tgl_antre = ? AND poli = ?", (date.today(), poli_nama))
    count = c.fetchone()[0]
    conn.close()
    return (count % 200) + 1

# Inisialisasi
init_db()

# PASTIKAN FILE GAMBAR ANDA BERNAMA 'download.jpg' DAN SATU FOLDER DENGAN FILE INI
try:
    set_png_as_page_bg('download.jpg')
except:
    st.sidebar.error("Gambar 'download.jpg' tidak ditemukan di folder!")

# --- 3. UI APLIKASI ---
st.title("🏥 SISTEM PENDAFTARAN KLINIK TERPADU")

menu = st.sidebar.radio("MENU UTAMA", ["Pendaftaran", "Panggilan Perawat", "Monitor TV"])

if menu == "Pendaftaran":
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    status = st.radio("Pilih Status Pasien:", ["Pasien Lama (Cari NIK/Nama)", "Pasien Baru"], horizontal=True)
    
    nik_final, nama_final, valid = "", "", False

    if status == "Pasien Lama (Cari NIK/Nama)":
        search = st.text_input("MASUKKAN NIK ATAU NAMA PASIEN:")
        if search:
            conn = sqlite3.connect('klinik_digital.db')
            c = conn.cursor()
            c.execute("SELECT nik, nama FROM master_pasien WHERE nik = ? OR nama LIKE ?", (search, f'%{search}%'))
            res = c.fetchone()
            conn.close()
            if res:
                st.success(f"Ditemukan: {res[1]} (NIK: {res[0]})")
                nik_final, nama_final, valid = res[0], res[1], True
            else:
                st.error("Data tidak ditemukan! Mohon daftar sebagai Pasien Baru.")
    
    else:
        st.subheader("📝 REGISTRASI IDENTITAS BARU")
        c1, c2 = st.columns(2)
        with c1:
            nama_n = st.text_input("Nama Lengkap")
            nik_n = st.text_input("NIK / ID Card")
            t_lahir = st.text_input("Tempat Lahir")
            tg_lahir = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
            gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            no_wa = st.text_input("Nomor WhatsApp")
        with c2:
            pt = st.text_input("Perusahaan")
            dep = st.text_input("Departemen")
            jab = st.text_input("Jabatan")
            mes = st.text_input("Blok Mes")
            kmr = st.text_input("Nomor Kamar")
            gol = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
        
        riwayat_p = st.text_area("Riwayat Penyakit")
        riwayat_a = st.text_area("Riwayat Alergi")
        area = st.text_input("Area Lokasi Kerja")
        
        if nama_n and nik_n:
            nik_final, nama_final, valid = nik_n, nama_n, True

    if valid:
        st.markdown("---")
        poli = st.selectbox("PILIH POLI TUJUAN:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"])
        if st.button("KONFIRMASI & AMBIL ANTREAN"):
            conn = sqlite3.connect('klinik_digital.db')
            c = conn.cursor()
            try:
                if status == "Pasien Baru":
                    c.execute("INSERT INTO master_pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (nik_n, nama_n, t_lahir, str(tg_lahir), gender, "Agama", no_wa, pt, dep, jab, mes, kmr, riwayat_p, riwayat_a, area, gol))
                
                # Antrean berkelanjutan
                map_k = {"Poli Umum":"U", "Poli Gigi":"G", "MCU":"M", "UGD":"ER", "Rawat Inap":"RI"}
                no_urut = get_next_number(poli)
                antrean = f"{map_k[poli]}-{no_urut:02d}"
                
                c.execute("INSERT INTO antrean_harian (nik, no_urut, poli, status, tgl_antre) VALUES (?,?,?,?,?)",
                          (nik_final, antrean, poli, "Menunggu", date.today()))
                conn.commit()
                
                st.markdown(f"""
                <div style="background:white; color:black; padding:20px; border-radius:15px; text-align:center;">
                    <h2 style="color:black !important; text-shadow:none;">NOMOR ANTREAN</h2>
                    <h1 style="font-size:80px; color:red !important; text-shadow:none;">{antrean}</h1>
                    <p style="color:black !important; text-shadow:none;">Pasien: {nama_final} | Poli: {poli}</p>
                </div>
                """, unsafe_allow_html=True)
            except sqlite3.IntegrityError:
                st.error("NIK sudah terdaftar!")
            finally:
                conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# --- MODUL PERAWAT & MONITOR (Logika Sama) ---
elif menu == "Panggilan Perawat":
    st.title("👨‍⚕️ RUANG PANGGILAN PERAWAT")
    # Tambahkan logika tabel panggilan di sini

elif menu == "Monitor TV":
    st.title("📺 MONITOR ANTREAN")
    # Tambahkan logika layar TV di sini

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
