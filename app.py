import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('klinik_perusahaan.db')
    c = conn.cursor()
    # Tabel Data Induk Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS data_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    
    # Tabel Antrean Harian
    c.execute('''CREATE TABLE IF NOT EXISTS antrean 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nik TEXT, 
                  no_urut TEXT, 
                  poli TEXT, 
                  status TEXT, 
                  tgl_antre DATE)''')
    conn.commit()
    conn.close()

def get_next_antrean(poli_kode):
    conn = sqlite3.connect('klinik_perusahaan.db')
    c = conn.cursor()
    today = date.today()
    c.execute("SELECT COUNT(*) FROM antrean WHERE tgl_antre = ? AND poli LIKE ?", (today, f"{poli_kode}%"))
    count = c.fetchone()[0]
    conn.close()
    if count >= 200: return 1
    return count + 1

init_db()

# --- 2. TAMPILAN UTAMA ---
st.set_page_config(page_title="Sistem Klinik Terpadu", layout="wide")

menu = st.sidebar.selectbox("Pilih Akses:", ["Pendaftaran Pasien", "Layar Panggilan (Monitor)", "Ruang Perawat (Panggil Pasien)"])

# --- MODUL 1: PENDAFTARAN ---
if menu == "Pendaftaran Pasien":
    st.title("🏥 Pendaftaran Klinik")
    status_pasien = st.radio("Status Pasien:", ["Pasien Baru", "Pasien Lama"], horizontal=True)
    
    with st.form("form_pendaftaran"):
        st.subheader("Data Identitas")
        c1, c2 = st.columns(2)
        
        if status_pasien == "Pasien Baru":
            with c1:
                nama = st.text_input("Nama Lengkap")
                nik = st.text_input("NIK / ID Card")
                tempat_lahir = st.text_input("Tempat Lahir")
                tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
                gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
                agama = st.selectbox("Agama", ["Islam", "Kristen", "Katolik", "Hindu", "Budha", "Khonghucu"])
                gol_darah = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
                no_hp = st.text_input("Nomor HP")
            with c2:
                perusahaan = st.text_input("Perusahaan")
                departemen = st.text_input("Departemen")
                jabatan = st.text_input("Jabatan")
                blok_mes = st.text_input("Blok Mes")
                no_kamar = st.text_input("Nomor Kamar")
                area_kerja = st.text_input("Area Lokasi Kerja")
                riwayat_penyakit = st.text_area("Riwayat Penyakit")
                riwayat_alergi = st.text_area("Riwayat Alergi")
        else:
            nik = st.text_input("Masukkan NIK Pasien Lama")
            st.info("Sistem akan mengambil data Anda secara otomatis berdasarkan NIK.")

        st.divider()
        st.subheader("Tujuan Poli")
        poli_tujuan = st.selectbox("Pilih Poli:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"])
        
        submit = st.form_submit_button("Ambil Nomor Antrean")

    if submit:
        conn = sqlite3.connect('klinik_perusahaan.db')
        c = conn.cursor()
        
        # Logika Simpan Data Baru
        can_proceed = True
        if status_pasien == "Pasien Baru":
            fields = [nama, nik, tempat_lahir, no_hp, perusahaan, departemen, jabatan, blok_mes, no_kamar, area_kerja, riwayat_penyakit, riwayat_alergi]
            if all(fields):
                try:
                    c.execute("INSERT INTO data_pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (nik, nama, tempat_lahir, str(tgl_lahir), gender, agama, no_hp, perusahaan, 
                               departemen, jabatan, blok_mes, no_kamar, riwayat_penyakit, riwayat_alergi, area_kerja, gol_darah))
                except sqlite3.IntegrityError:
                    st.error("NIK sudah terdaftar!")
                    can_proceed = False
            else:
                st.error("Semua kolom wajib diisi!")
                can_proceed = False

        # Logika Antrean
        if can_proceed:
            kode_poli = {"Poli Umum": "U", "Poli Gigi": "G", "MCU": "M", "UGD": "ER", "Rawat Inap": "RI"}[poli_tujuan]
            no_urut = get_next_antrean(kode_poli)
            antrean_label = f"{kode_poli}-{no_urut:02d}"
            
            c.execute("INSERT INTO antrean (nik, no_urut, poli, status, tgl_antre) VALUES (?,?,?,?,?)",
                      (nik, antrean_label, poli_tujuan, "Menunggu", date.today()))
            conn.commit()
            
            st.success(f"Pendaftaran Berhasil! Nomor Antrean Anda: {antrean_label}")
            st.metric("NOMOR ANTREAN", antrean_label)
        conn.close()

# --- MODUL 2: RUANG PERAWAT (PEMANGGILAN) ---
elif menu == "Ruang Perawat (Panggil Pasien)":
    st.title("👩‍⚕️ Dashboard Perawat")
    poli_perawat = st.selectbox("Pilih Poli Anda:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"])
    
    conn = sqlite3.connect('klinik_perusahaan.db')
    # Ambil daftar yang menunggu di poli tersebut
    df = pd.read_sql_query(f"SELECT a.id, a.no_urut, p.nama, a.status FROM antrean a JOIN data_pasien p ON a.nik = p.nik WHERE a.poli = '{poli_perawat}' AND a.tgl_antre = '{date.today()}' AND a.status = 'Menunggu' ORDER BY a.id ASC", conn)
    
    if not df.empty:
        st.write(f"Pasien Menunggu di {poli_perawat}:")
        st.table(df[['no_urut', 'nama']])
        
        pasien_next = df.iloc[0]
        if st.button(f"Panggil Antrean {pasien_next['no_urut']}"):
            c = conn.cursor()
            # Update status jadi 'Dipanggil'
            c.execute("UPDATE antrean SET status = 'Dipanggil' WHERE id = ?", (int(pasien_next['id']),))
            conn.commit()
            st.rerun()
    else:
        st.info(f"Tidak ada pasien menunggu di {poli_perawat}.")
    conn.close()

# --- MODUL 3: LAYAR MONITOR (TV) ---
elif menu == "Layar Panggilan (Monitor)":
    st.title("📺 Layar Panggilan Antrean")
    conn = sqlite3.connect('klinik_perusahaan.db')
    
    cols = st.columns(3)
    polis = ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"]
    
    for i, p in enumerate(polis):
        with cols[i % 3]:
            st.subheader(p)
            res = pd.read_sql_query(f"SELECT no_urut, status FROM antrean WHERE poli = '{p}' AND tgl_antre = '{date.today()}' AND status = 'Dipanggil' ORDER BY id DESC LIMIT 1", conn)
            if not res.empty:
                st.markdown(f"<h1 style='text-align: center; color: green;'>{res['no_urut'][0]}</h1>", unsafe_allow_html=True)
            else:
                st.markdown("<h1 style='text-align: center; color: gray;'>--</h1>", unsafe_allow_html=True)
    conn.close()
    # Auto refresh setiap 10 detik
    time_to_refresh = st.empty()
    st.info("Halaman ini akan otomatis memperbarui data jika perawat memanggil pasien.")
