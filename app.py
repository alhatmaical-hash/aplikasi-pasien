import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

# --- 1. CONFIG & STYLING (DARK BLOCKS) ---
st.set_page_config(page_title="Klinik Digital - Dark Mode", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_dark_theme(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    st.markdown(f'''
    <style>
    /* Font Global */
    * {{ font-family: "Times New Roman", Times, serif !important; }}

    /* Background Utama */
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.8)), 
                          url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* BLOK INPUT & FORM - DIBUAT GELAP */
    div[data-testid="stForm"], .glass-card, .stTabs {{
        background: rgba(0, 20, 40, 0.85) !important; /* Biru Gelap Transparan */
        backdrop-filter: blur(10px);
        border: 1px solid #00d4ff;
        border-radius: 15px;
        padding: 25px;
        color: white !important;
    }}

    /* TIKET ANTREAN - DIBUAT GELAP AGAR NO ANTREAN MENYALA */
    .dark-ticket {{
        background: rgba(10, 10, 10, 0.9);
        color: #00d4ff !important;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #00d4ff;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        margin-top: 20px;
    }}

    /* Font No Antrean dibuat sangat besar dan terang */
    .queue-number {{
        font-size: 100px !important;
        color: #00ffcc !important;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 255, 204, 0.8);
        margin: 10px 0;
    }}

    /* Label Text */
    label, p, h1, h2, h3 {{
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }}

    /* Input Fields (Tetap Putih agar mudah diketik, namun border gelap) */
    input, select, textarea {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: black !important;
        font-weight: bold !important;
    }}
    </style>
    ''', unsafe_allow_html=True)
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
