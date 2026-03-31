import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

# --- 1. KONFIGURASI TAMPILAN & BACKGROUND (UI) ---
st.set_page_config(page_title="Sistem Klinik APD Digital", layout="wide", page_icon="🏥")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_custom_ui(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    st.markdown(f'''
    <style>
    /* Font Global */
    * {{
        font-family: 'Times New Roman', Times, serif !important;
    }}

    /* Background Utama dengan Overlay Gelap */
    .stApp {{
        background-image: linear-gradient(rgba(0, 20, 40, 0.7), rgba(0, 10, 20, 0.9)), 
                          url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Judul Utama */
    .stApp h1 {{
        color: white !important;
        font-weight: bold;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
        text-transform: uppercase;
        margin-bottom: 5px;
    }}

    /* Kotak Form (Glassmorphism): Transparan, Terang, & Jelas */
    div[data-testid="stForm"], .glass-container, .stApp [data-testid="stMarkdownContainer"] p {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        padding: 30px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #e0f7fa !important; /* Biru Cyan Terang */
        font-size: 18px !important;
        font-weight: bold;
    }}

    /* Input Fields */
    input, select, textarea {{
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: black !important;
        font-weight: bold !important;
    }}

    /* Tombol Cari & Daftar */
    .stButton>button {{
        background: linear-gradient(90deg, #00d4ff, #00509d) !important;
        color: white !important;
        border-radius: 10px;
        font-weight: bold;
        height: 3.5em;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        box-shadow: 0 0 15px #00d4ff;
        transform: scale(1.02);
    }}
    </style>
    ''', unsafe_allow_html=True)

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_pro.db')
    c = conn.cursor()
    # Tabel Master Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS master_pasien 
                 (nik TEXT PRIMARY KEY, nama TEXT, tempat_lahir TEXT, tgl_lahir TEXT, 
                  gender TEXT, agama TEXT, no_hp TEXT, perusahaan TEXT, 
                  departemen TEXT, jabatan TEXT, blok_mes TEXT, no_kamar TEXT, 
                  riwayat_penyakit TEXT, riwayat_alergi TEXT, area_kerja TEXT, 
                  golongan_darah TEXT)''')
    # Tabel Transaksi Antrean (Berkelanjutan & Harian)
    c.execute('''CREATE TABLE IF NOT EXISTS antrean_harian 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nik TEXT, no_urut TEXT, 
                  poli TEXT, status_antre TEXT, tgl DATE)''')
    conn.commit()
    conn.close()

def get_next_number(poli_nama):
    conn = sqlite3.connect('klinik_pro.db')
    c = conn.cursor()
    # Menghitung total antrean di poli tersebut hari ini (maks 300)
    c.execute("SELECT COUNT(*) FROM antrean_harian WHERE tgl = ? AND poli = ?", (date.today(), poli_nama))
    count = c.fetchone()[0]
    conn.close()
    if count >= 300: return 1
    return count + 1

# Inisialisasi Database
init_db()

# Terapkan UI Custom (Gunakan nama file gambar Anda)
try:
    apply_custom_ui('download.jpg')
except:
    st.error("Gambar 'download.jpg' tidak ditemukan! Pastikan file ada di folder aplikasi.")

# --- 3. LOGIKA APLIKASI KLINIK ---
menu = st.sidebar.radio("MENU KLINIK PRO", ["Pendaftaran", "Panggilan Perawat", "Monitor TV"])

if menu == "Pendaftaran":
    st.title("🏥 PENDAFTARAN PASIEN - KLINIK UTAMA")
    st.info("Sistem Antrean Berlanjut (U001 - U300)")
    
    status = st.radio("Pilih Status Pasien:", ["Pasien Lama (Pencarian NIK)", "Pasien Baru"], horizontal=True)
    
    nik_pencarian, nama_ketemu, data_valid = "", "", False

    if status == "Pasien Lama (Pencarian NIK)":
        search_nik = st.text_input("MASUKKAN NIK PASIEN LAMA:")
        btn_cari = st.button("🔍 CARI DATA")
        
        if btn_cari and search_nik:
            conn = sqlite3.connect('klinik_pro.db')
            c = conn.cursor()
            c.execute("SELECT nama FROM master_pasien WHERE nik = ?", (search_nik,))
            res = c.fetchone()
            conn.close()
            if res:
                st.success(f"Ditemukan: {res[0]}")
                nik_pencarian, nama_ketemu, data_valid = search_nik, res[0], True
            else:
                st.error("NIK tidak ditemukan! Silakan daftar sebagai Pasien Baru.")
    else:
        st.subheader("📝 REGISTRASI IDENTITAS BARU (WAJIB ISI)")
        c1, c2 = st.columns(2)
        with c1:
            nama_b = st.text_input("Nama Lengkap Pasien")
            nik_b = st.text_input("NIK / ID Card")
            t_lahir_b = st.text_input("Tempat Lahir")
            tg_lahir_b = st.date_input("Tanggal Lahir", min_value=date(1950, 1, 1))
            gender_b = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            agama_b = st.selectbox("Agama", ["Islam", "Kristen", "Katolik", "Hindu", "Budha"])
            no_wa_b = st.text_input("Nomor WhatsApp")
            pt_b = st.text_input("Perusahaan")
        with c2:
            dept_b = st.text_input("Departemen")
            jab_b = st.text_input("Jabatan")
            mes_b = st.text_input("Blok Mes")
            kmr_b = st.text_input("Nomor Kamar")
            area_b = st.text_input("Area Lokasi Kerja")
            gol_b = st.selectbox("Golongan Darah", ["A", "B", "AB", "O"])
            penyakit_b = st.text_area("Riwayat Penyakit")
            alergi_b = st.text_area("Riwayat Alergi")
        
        if nama_b and nik_b and tg_lahir_b andpt_b and no_wa_b and penyakit_b and alergi_b and area_b:
            nik_pencarian, nama_ketemu, data_valid = nik_b, nama_b, True

    # FORM PILIH POLI
    if data_valid:
        st.markdown("---")
        poli_tujuan = st.selectbox("PILIH POLI TUJUAN BEROBAT:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"])
        
        if st.button("KONFIRMASI & AMBIL NO ANTREAN"):
            conn = sqlite3.connect('klinik_pro.db')
            c = conn.cursor()
            
            try:
                # 1. Jika Pasien Baru, simpan data identitas
                if status == "Pasien Baru":
                    c.execute("INSERT INTO master_pasien VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (nik_b, nama_b, t_lahir_b, str(tg_lahir_b), gender_b, agama_b, no_wa_b, pt_b, 
                               dept_b, jab_b, mes_b, kmr_b, penyakit_b, alergi_b, area_b, gol_b))
                
                # 2. Proses Antrean (Berkelanjutan)
                kode_poli = {"Poli Umum":"U", "Poli Gigi":"G", "MCU":"M", "UGD":"ER", "Rawat Inap":"RI"}
                no_urut = get_next_number(poli_tujuan)
                label_antrean = f"{kode_poli[poli_tujuan]}-{no_urut:03d}"
                
                c.execute("INSERT INTO antrean_harian (nik, no_urut, poli, status_antre, tgl) VALUES (?,?,?,?,?)",
                          (nik_pencarian, label_antrean, poli_tujuan, "Menunggu", date.today()))
                conn.commit()
                
                # Tampilan Berhasil & Tiket
                st.balloons()
                st.markdown(f"""
                <div style="background:#e3f2fd; padding:30px; border-radius:15px; text-align:center; border:3px dashed #00509d">
                    <h2 style='color:#00509d;'>PENDAFTARAN BERHASIL</h2>
                    <p style='color:black;'>Silakan tunjukkan nomor antrean ini</p>
                    <h1 style='font-size:80px; color:#c0392b; margin:10px 0;'>{label_antrean}</h1>
                    <p style='color:black;'>Pasien: {nama_ketemu} | Poli: {poli_tujuan}</p>
                </div>
                """, unsafe_allow_html=True)
            except sqlite3.IntegrityError:
                st.error("NIK SUDAH TERDAFTAR!")
            finally:
                conn.close()

elif menu == "Panggilan Perawat":
    st.title("👩‍⚕️ PANEL PANGGILAN PASIEN")
    p_poli = st.selectbox("Poli Ruangan Anda:", ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"])
    
    conn = sqlite3.connect('klinik_pro.db')
    df = pd.read_sql_query(f"SELECT a.id, a.no_urut, p.nama, p.nik FROM antrean_harian a JOIN master_pasien p ON a.nik = p.nik WHERE a.poli = '{p_poli}' AND a.tgl = '{date.today()}' AND a.status_antre = 'Menunggu'", conn)
    
    if not df.empty:
        st.write(f"Pasien Menunggu: {len(df)}")
        st.table(df[['no_urut', 'nama', 'nik']])
        if st.button("PANGGIL BERIKUTNYA"):
            c = conn.cursor()
            c.execute("UPDATE antrean_harian SET status_antre = 'Dipanggil' WHERE id = ?", (int(df.iloc[0]['id']),))
            conn.commit()
            st.rerun()
    else: st.info(f"Tidak ada antrean menunggu di {p_poli}.")
    conn.close()

elif menu == "Monitor TV":
    st.title("📺 MONITOR ANTREAN KLINIK")
    conn = sqlite3.connect('klinik_pro.db')
    
    col_kiri, col_kanan = st.columns(2)
    polis = ["Poli Umum", "Poli Gigi", "MCU", "UGD", "Rawat Inap"]
    
    for i, p in enumerate(polis):
        with col_kiri if i % 2 == 0 else col_kanan:
            st.markdown(f"<div style='background:#2c3e50; color:white; padding:20px; border-radius:10px; text-align:center; margin-bottom:15px;'><h4>{p}</h4>", unsafe_allow_html=True)
            res = pd.read_sql_query(f"SELECT no_urut FROM antrean_harian WHERE poli='{p}' AND status_antre='Dipanggil' AND tgl='{date.today()}' ORDER BY id DESC LIMIT 1", conn)
            val = res['no_urut'][0] if not res.empty else "--"
            st.markdown(f"<h1 style='color:#f1c40f;'>{val}</h1></div>", unsafe_allow_html=True)
    conn.close()
    st.info("Halaman ini akan otomatis memperbarui data jika perawat memanggil pasien.")
    # Auto-refresh halaman setiap 10 detik
    time_to_refresh = st.empty()
