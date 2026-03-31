import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time

# --- 1. KONFIGURASI TAMPILAN (UI) ---
st.set_page_config(page_title="Sistem Klinik Digital", layout="wide")

def apply_custom_design():
    st.markdown("""
    <style>
    /* Mengatur Background Abu-abu Gelap */
    .stApp {
        background-color: #2F2F2F;
    }

    /* Font Global ke Times New Roman */
    * {
        font-family: 'Times New Roman', Times, serif !important;
    }

    /* Container Form (Glassmorphism) */
    div[data-testid="stForm"], .main-box {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #00D4FF; 
    }

    /* Teks Putih Terang & Jelas */
    h1, h2, h3, label, p, .stMarkdown {
        color: #FFFFFF !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
    }

    /* Warna Label Input */
    .stTextInput label, .stSelectbox label, .stTextArea label, .stDateInput label {
        color: #00D4FF !important; 
        font-size: 18px !important;
        font-weight: bold !important;
    }

    /* Kotak Input Putih agar tulisan hitam kontras */
    input, select, textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* Tombol Pendaftaran */
    .stButton>button {
        background: linear-gradient(90deg, #00D4FF, #00509D) !important;
        color: white !important;
        border: none;
        height: 3.5em;
        width: 100%;
        font-weight: bold !important;
    }
    
    /* ======================================================= */
    /* PERUBAHAN DISINI: Box Nomor Antrean Dibuat Warna Gelap */
    /* ======================================================= */
    .ticket {
        background: #1A1A1A !important; /* Warna Hitam Pekat */
        color: #FFFFFF !important;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        border: 2px solid #00D4FF;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4); /* Efek Menyala Biru */
        margin-top: 20px;
    }
    
    /* Angka Nomor Antrean dibuat Menyala Kuning Emas */
    .ticket h1 {
        font-size: 90px !important;
        color: #F1C40F !important;
        text-shadow: 0 0 15px rgba(241, 196, 15, 0.6) !important;
        margin: 5px 0 !important;
    }
    
    /* Teks detail di dalam tiket */
    .ticket h2 {
        color: #00D4FF !important;
        margin: 0 !important;
    }
    
    .ticket p {
        color: #E0E0E0 !important;
        font-size: 18px !important;
    }
    /* ======================================================= */
    
    </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('klinik_admin.db')
    c = conn.cursor()
    # Master Data Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS master_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    # Transaksi Antrean
    c.execute('''CREATE TABLE IF NOT EXISTS antrean_harian 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status TEXT, tgl DATE)''')
    conn.commit()
    conn.close()

def get_next_no(poli):
    conn = sqlite3.connect('klinik_admin.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM antrean_harian WHERE tgl = ? AND poli = ?", (date.today(), poli))
    count = c.fetchone()[0]
    conn.close()
    return (count % 300) + 1

init_db()

# --- 3. LOGIKA NAVIGASI ---
menu = st.sidebar.radio("MENU ADMIN", ["Pendaftaran Pasien", "Panggilan Admin (PC)", "Monitor Antrean"])

if menu == "Pendaftaran Pasien":
    st.title("🏥 PENDAFTARAN PASIEN KLINIK HARITA FERONIKEL OBI")
    
    status = st.radio("Tipe Kedatangan:", ["Pasien Lama", "Pasien Baru"], horizontal=True)
    
    final_nik, final_nama, is_ready = "", "", False

    if status == "Pasien Lama":
        search = st.text_input("MASUKKAN NIK / NAMA PASIEN:")
        if search:
            conn = sqlite3.connect('klinik_admin.db')
            c = conn.cursor()
            c.execute("SELECT nik, nama FROM master_pasien WHERE nik = ? OR nama LIKE ?", (search, f'%{search}%'))
            res = c.fetchone()
            conn.close()
            if res:
                st.success(f"Ditemukan: {res[1]} ({res[0]})")
                final_nik, final_nama, is_ready = res[0], res[1], True
            else:
                st.error("Data tidak ditemukan! Silakan pilih 'Pasien Baru'.")
    
    else:
        with st.form("reg_baru"):
            st.subheader("📝 IDENTITAS WAJIB (WAJIB DIISI SEMUA)")
            c1, c2 = st.columns(2)
            with c1:
                nama = st.text_input("Nama Pasien")
                nik = st.text_input("NIK / ID Card")
                tmpt = st.text_input("Tempat Lahir")
                tgl = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
                gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
                agama = st.selectbox("Agama", ["Islam", "Kristen", "Katolik", "Hindu", "Budha"])
                hp = st.text_input("No HP / WhatsApp")
                gol = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
            with c2:
                pt = st.text_input("Perusahaan")
                dept = st.text_input("Departemen")
                jbt = st.text_input("Jabatan")
                mes = st.text_input("Blok Mes")
                kmr = st.text_input("Nomor Kamar")
                area = st.text_input("Area Lokasi Kerja")
                r_sakit = st.text_area("Riwayat Penyakit")
                r_alergi = st.text_area("Riwayat Alergi")
            
            submitted = st.form_submit_button("VALIDASI DATA")
            
            if submitted:
                inputs = [nama, nik, tmpt, hp, pt, dept, jbt, mes, kmr, area, r_sakit, r_alergi]
                if all(inputs):
                    conn = sqlite3.connect('klinik_admin.db')
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO master_pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                  (nik, nama, tmpt, str(tgl), gender, agama, hp, pt, dept, jbt, mes, kmr, r_sakit, r_alergi, area, gol))
                        conn.commit()
                        st.success("Registrasi Berhasil!")
                        final_nik, final_nama, is_ready = nik, nama, True
                    except:
                        st.error("Gagal: NIK sudah terdaftar.")
                    conn.close()
                else:
                    st.warning("⚠️ Semua kolom identitas wajib diisi!")

    if is_ready:
        st.markdown("---")
        poli_tuju = st.selectbox("PILIH POLI TUJUAN:", ["Poli Umum", "Poli Gigi", "MCU", "Unit Gawat Darurat", "Rawat Inap"])
        
        if st.button("CETAK NOMOR ANTREAN"):
            kode_map = {"Poli Umum":"U", "Poli Gigi":"G", "MCU":"M", "Unit Gawat Darurat":"ER", "Rawat Inap":"RI"}
            no_urut = get_next_no(poli_tuju)
            label = f"{kode_map[poli_tuju]}-{no_urut:02d}"
            
            conn = sqlite3.connect('klinik_admin.db')
            c = conn.cursor()
            c.execute("INSERT INTO antrean_harian (nik, no_urut, poli, status, tgl) VALUES (?,?,?,?,?)",
                      (final_nik, label, poli_tuju, "Menunggu", date.today()))
            conn.commit()
            conn.close()
            
            st.markdown(f"""
            <div class="ticket">
                <h2 style='color:black !important; margin:0;'>NOMOR ANTREAN</h2>
                <h1 style='font-size:80px; color:#c0392b !important; margin:0;'>{label}</h1>
                <p style='color:black !important;'>Pasien: <b>{final_nama}</b><br>Tujuan: <b>{poli_tuju}</b></p>
                <p style='color:grey; font-size:12px;'>Silakan menunggu panggilan Admin</p>
            </div>
            """, unsafe_allow_html=True)

elif menu == "Panggilan Admin (PC)":
    st.title("💻 PANEL ADMIN / PERAWAT")
    sel_poli = st.selectbox("Monitor Poli:", ["Poli Umum", "Poli Gigi", "MCU", "Unit Gawat Darurat", "Rawat Inap"])
    
    conn = sqlite3.connect('klinik_admin.db')
    df = pd.read_sql_query(f"SELECT a.id, a.no_urut, p.nama FROM antrean_harian a JOIN master_pasien p ON a.nik = p.nik WHERE a.poli = '{sel_poli}' AND a.status = 'Menunggu' AND a.tgl = '{date.today()}'", conn)
    
    if not df.empty:
        st.table(df[['no_urut', 'nama']])
        if st.button("PANGGIL BERIKUTNYA"):
            c = conn.cursor()
            c.execute("UPDATE antrean_harian SET status = 'Dipanggil' WHERE id = ?", (int(df.iloc[0]['id']),))
            conn.commit()
            st.success(f"Memanggil {df.iloc[0]['no_urut']}...")
            time.sleep(1)
            st.rerun()
    else:
        st.info("Antrean kosong.")
    conn.close()

elif menu == "Monitor Antrean":
    st.title("📺 MONITOR LAYAR TUNGGU")
    conn = sqlite3.connect('klinik_admin.db')
    cols = st.columns(5)
    list_poli = ["Poli Umum", "Poli Gigi", "MCU", "Unit Gawat Darurat", "Rawat Inap"]
    
    for i, p in enumerate(list_poli):
        with cols[i]:
            st.markdown(f"<div style='background:white; color:black; padding:15px; border-radius:10px; text-align:center;'><h4>{p}</h4>", unsafe_allow_html=True)
            res = pd.read_sql_query(f"SELECT no_urut FROM antrean_harian WHERE poli='{p}' AND status='Dipanggil' AND tgl='{date.today()}' ORDER BY id DESC LIMIT 1", conn)
            val = res['no_urut'][0] if not res.empty else "--"
            st.markdown(f"<h1 style='color:#00D4FF;'>{val}</h1></div>", unsafe_allow_html=True)
    conn.close()
    time.sleep(5)
    st.rerun()
