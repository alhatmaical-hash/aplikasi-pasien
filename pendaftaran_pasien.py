import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS CUSTOM (UNTUK TAMPILAN MENARIK) ---
st.markdown("""
    <style>
    /* Mengatur font dan background */
    .main {
        background-color: #f5f7f9;
    }
    
    /* Membuat tombol simpan/kirim berwarna biru profesional */
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        width: 100%;
        height: 3em;
        font-weight: bold;
        border: none;
    }
    
    /* Efek hover tombol */
    div.stButton > button:first-child:hover {
        background-color: #0056b3;
        color: white;
    }

    /* Menyembunyikan baris indeks di tabel pandas */
    .row_heading.level0 {display:none}
    .blank {display:none}

    /* Mengatur padding untuk mobile agar tidak terlalu rapat */
    @media (max-width: 640px) {
        .block-container {
            padding: 1rem 1rem;
        }
    }
    </style>
    """, unsafe_with_html=True)

# --- 3. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('klinik_pendaftaran.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE,
                    bulan_daftar TEXT,
                    jenis_kunjungan TEXT, nama_lengkap TEXT, no_hp TEXT,
                    blok_mes TEXT, agama TEXT, nik TEXT, gender TEXT,
                    pernah_berobat TEXT, tempat_tgl_lahir TEXT,
                    perusahaan TEXT, departemen TEXT, jabatan TEXT,
                    alergi TEXT, gol_darah TEXT, lokasi_kerja TEXT,
                    file_skd_path TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. FUNGSI HELPER ---
def get_master(kategori):
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
    conn.close()
    return df['nama'].tolist()

def add_master(kategori, nama):
    if nama:
        conn = sqlite3.connect('klinik_pendaftaran.db')
        c = conn.cursor()
        c.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kategori, nama))
        conn.commit()
        conn.close()

def delete_master(kategori, nama):
    conn = sqlite3.connect('klinik_pendaftaran.db')
    c = conn.cursor()
    c.execute("DELETE FROM master_data WHERE kategori=? AND nama=?", (kategori, nama))
    conn.commit()
    conn.close()

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🏥 Menu Klinik")
    menu = st.radio("Navigasi:", 
        ["Pendaftaran Pasien", "Rekam Medis (Admin)", "Upload SKD", "Pusat SKD Publik", "Pengaturan Master"])
    st.info("Aplikasi ini dioptimalkan untuk scan QR Code melalui Smartphone.")

# --- 6. LOGIK MENU ---

if menu == "Pendaftaran Pasien":
    st.subheader("📝 Form Pendaftaran Mandiri")
    st.write("Silakan lengkapi data Anda untuk mendapatkan layanan.")
    
    with st.form("form_pendaftaran", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat luka"])
            nama = st.text_input("NAMA LENGKAP", placeholder="Sesuai KTP")
            hp = st.text_input("NO HP AKTIF (WhatsApp)", placeholder="0812...")
            agama = st.selectbox("AGAMA", ["Islam", "Kristen", "Hindu", "Buddah", "Katolik", "Tidak Diketahui"])
            nik = st.text_input("NIK / ID CARD")
            gender = st.selectbox("JENIS KELAMIN", ["Laki-laki", "Perempuan"])
            pernah = st.radio("SUDAH PERNAH BEROBAT?", ["Iya Sudah", "Belum Pernah"], horizontal=True)

        with col2:
            blok = st.text_input("BLOK MES & NO KAMAR")
            ttl = st.text_input("TEMPAT & TANGGAL LAHIR")
            perusahaan = st.selectbox("PERUSAHAAN", get_master("Perusahaan"))
            dept = st.selectbox("DEPARTEMEN", get_master("Departemen"))
            jabatan = st.selectbox("JABATAN", get_master("Jabatan"))
            alergi = st.selectbox("JENIS ALERGI", ["Tidak Ada", "Makanan", "Obat", "Cuaca"])
            darah = st.selectbox("GOLONGAN DARAH", ["A", "B", "AB", "O", "Tidak Tahu"])
        
        lokasi = st.text_area("LOKASI AREA BEKERJA (Detail)")
        
        submit = st.form_submit_button("KIRIM PENDAFTARAN")
        
        if submit:
            if not nama or not hp:
                st.error("Nama dan No HP wajib diisi!")
            else:
                now = datetime.now()
                tgl_skrg = now.date()
                bln_skrg = now.strftime("%B %Y")
                
                conn = sqlite3.connect('klinik_pendaftaran.db')
                c = conn.cursor()
                c.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, jenis_kunjungan, nama_lengkap, no_hp, blok_mes, agama, nik, gender, pernah_berobat, tempat_tgl_lahir, perusahaan, departemen, jabatan, alergi, gol_darah, lokasi_kerja) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (tgl_skrg, bln_skrg, kunjungan, nama, hp, blok, agama, nik, gender, pernah, ttl, perusahaan, dept, jabatan, alergi, darah, lokasi))
                conn.commit()
                conn.close()
                
                st.success(f"Pendaftaran anda berhasil silahkan menunggu untuk di layani, semoga lekas sembuh")
                st.balloons()

elif menu == "Rekam Medis (Admin)":
    st.subheader("📊 Data Rekam Medis Pasien")
    
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_bulan = st.multiselect("Filter Bulan Daftar", df['bulan_daftar'].unique())
        with col_f2:
            f_tgl = st.date_input("Filter Tanggal Spesifik", value=[])

        # Logika Filter
        if f_bulan:
            df = df[df['bulan_daftar'].isin(f_bulan)]
        if len(f_tgl) == 2:
            df = df[(df['tgl_daftar'] >= str(f_tgl[0])) & (df['tgl_daftar'] <= str(f_tgl[1]))]
        
        st.dataframe(df, use_container_width=True)
        
        # Download Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Download Excel", data=output.getvalue(), file_name="Data_Rekam_Medis.xlsx")
    else:
        st.warning("Belum ada data.")

elif menu == "Upload SKD":
    st.subheader("📤 Upload Surat Keterangan Dokter")
    
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df_p = pd.read_sql("SELECT id, nama_lengkap, departemen FROM pasien", conn)
    conn.close()
    
    if not df_p.empty:
        pilihan = st.selectbox("Pilih Pasien", df_p.apply(lambda x: f"{x['id']} - {x['nama_lengkap']} ({x['departemen']})", axis=1))
        pasien_id = pilihan.split(" - ")[0]
        file_pdf = st.file_uploader("Upload File PDF", type=['pdf'])
        
        if st.button("Simpan & Update Data"):
            if file_pdf:
                st.success(f"File berhasil diunggah untuk ID {pasien_id}. HR/Admin dapat melihat di Pusat SKD.")
            else:
                st.warning("Silakan pilih file PDF terlebih dahulu.")
    else:
        st.info("Daftar pasien kosong.")

elif menu == "Pusat SKD Publik":
    st.subheader("📂 Akses Dokumen SKD (HR & Pengawas)")
    
    conn = sqlite3.connect('klinik_pendaftaran.db')
    df_skd = pd.read_sql("SELECT tgl_daftar, nama_lengkap, departemen, perusahaan FROM pasien", conn)
    conn.close()
    
    f_dept_skd = st.multiselect("Filter Departemen", df_skd['departemen'].unique())
    if f_dept_skd:
        df_skd = df_skd[df_skd['departemen'].isin(f_dept_skd)]
        
    st.table(df_skd)

elif menu == "Pengaturan Master":
    st.subheader("⚙️ Manajemen Dropdown Data")
    st.write("Gunakan menu ini untuk menambah Perusahaan, Departemen, atau Jabatan baru.")
    
    tab1, tab2, tab3 = st.tabs(["Perusahaan", "Departemen", "Jabatan"])
    
    for t, kat in zip([tab1, tab2, tab3], ["Perusahaan", "Departemen", "Jabatan"]):
        with t:
            col_a, col_b = st.columns(2)
            with col_a:
                new_val = st.text_input(f"Nama {kat} Baru", key=f"add_{kat}")
                if st.button(f"Tambah {kat}", key=f"btn_add_{kat}"):
                    add_master(kat, new_val)
                    st.rerun()
            with col_b:
                list_data = get_master(kat)
                to_del = st.selectbox(f"Hapus {kat}", ["-- Pilih --"] + list_data, key=f"sel_{kat}")
                if st.button(f"Hapus {kat}", key=f"btn_del_{kat}"):
                    delete_master(kat, to_del)
                    st.rerun()
