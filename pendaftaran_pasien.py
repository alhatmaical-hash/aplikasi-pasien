import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Konfigurasi Halaman
st.set_page_config(page_title="Pendaftaran Mandiri Klinik", layout="centered")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('klinik_data.db')
    c = conn.cursor()
    # Tabel Master untuk dropdown dinamis
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    # Tabel Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS pendaftaran (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar TEXT,
                    jenis_kunjungan TEXT, nama_lengkap TEXT, no_hp TEXT,
                    blok_mes TEXT, agama TEXT, nik TEXT, gender TEXT,
                    pernah_berobat TEXT, tempat_tgl_lahir TEXT,
                    perusahaan TEXT, departemen TEXT, jabatan TEXT,
                    alergi TEXT, gol_darah TEXT, lokasi_kerja TEXT,
                    file_skd_path TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def get_master(kategori):
    conn = sqlite3.connect('klinik_data.db')
    df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}'", conn)
    conn.close()
    return df['nama'].tolist()

def add_master(kategori, nama):
    conn = sqlite3.connect('klinik_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kategori, nama))
    conn.commit()
    conn.close()

def delete_master(kategori, nama):
    conn = sqlite3.connect('klinik_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM master_data WHERE kategori=? AND nama=?", (kategori, nama))
    conn.commit()
    conn.close()

# --- UI LOGIC ---
menu = ["Pendaftaran Pasien", "Upload SKD (Admin)", "Pengaturan Master Data"]
choice = st.sidebar.selectbox("Menu Utama", menu)

# --- 1. PENDAFTARAN PASIEN ---
if choice == "Pendaftaran Pasien":
    st.header("📝 Form Pendaftaran Pasien")
    st.info("Silakan isi data Anda dengan benar.")

    with st.form("form_daftar"):
        col1, col2 = st.columns(2)
        
        with col1:
            jenis_kunjungan = st.selectbox("Jenis Kunjungan", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk", "Kontrol Rawat Luka"])
            nama_lengkap = st.text_input("Nama Lengkap")
            no_hp = st.text_input("No HP Aktif (WhatsApp)")
            agama = st.selectbox("Agama", ["Islam", "Kristen", "Hindu", "Buddha", "Katolik", "Tidak Diketahui"])
            nik = st.text_input("NIK / ID Card")
            gender = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"], horizontal=True)

        with col2:
            blok_mes = st.text_input("Blok Mes dan No Kamar")
            pernah_berobat = st.radio("Pernah Berobat Disini?", ["Iya Sudah", "Belum Pernah"], horizontal=True)
            tgl_lahir = st.text_input("Tempat & Tanggal Lahir (Contoh: Obi, 01-01-1990)")
            perusahaan = st.selectbox("Perusahaan", get_master("Perusahaan"))
            dept = st.selectbox("Departemen", get_master("Departemen"))
            jabatan = st.selectbox("Jabatan", get_master("Jabatan"))

        alergi = st.multiselect("Jenis Alergi", ["Makanan", "Obat", "Cuaca", "Tidak Ada"])
        gol_darah = st.selectbox("Golongan Darah", ["A", "B", "AB", "O", "-"])
        lokasi_kerja = st.text_area("Lokasi Area Bekerja Spesifik")
        
        submit = st.form_submit_button("Daftar Sekarang")

    if submit:
        if nama_lengkap and no_hp:
            conn = sqlite3.connect('klinik_data.db')
            c = conn.cursor()
            c.execute('''INSERT INTO pendaftaran (tgl_daftar, jenis_kunjungan, nama_lengkap, no_hp, blok_mes, agama, nik, gender, pernah_berobat, tempat_tgl_lahir, perusahaan, departemen, jabatan, alergi, gol_darah, lokasi_kerja) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (date.today(), jenis_kunjungan, nama_lengkap, no_hp, blok_mes, agama, nik, gender, pernah_berobat, tgl_lahir, perusahaan, dept, jabatan, str(alergi), gol_darah, lokasi_kerja))
            conn.commit()
            conn.close()
            
            st.success(f"Pendaftaran Berhasil! Halo {nama_lengkap}, silakan menunggu untuk dilayani. Semoga lekas sembuh.")
            # Simulasi pengiriman pesan (Bisa diintegrasikan dengan API WhatsApp seperti Fonnte/Twilio)
            st.write(f"📲 *Pesan otomatis dikirim ke {no_hp}...*")
        else:
            st.error("Mohon lengkapi Nama dan No HP!")

# --- 2. UPLOAD SKD (ADMIN) ---
elif choice == "Upload SKD (Admin)":
    st.header("📄 Upload Surat Keterangan Dokter")
    
    conn = sqlite3.connect('klinik_data.db')
    df_pasien = pd.read_sql("SELECT id, nama_lengkap, no_hp FROM pendaftaran WHERE file_skd_path IS NULL", conn)
    conn.close()

    if not df_pasien.empty:
        pasien_opt = df_pasien.apply(lambda x: f"{x['id']} - {x['nama_lengkap']}", axis=1).tolist()
        pilih_pasien = st.selectbox("Pilih Pasien", pasien_opt)
        pasien_id = pilih_pasien.split(" - ")[0]
        
        uploaded_file = st.file_uploader("Pilih file PDF SKD", type=['pdf'])
        
        if st.button("Simpan & Bagikan Link"):
            if uploaded_file:
                # Logika simpan file (Contoh simpan lokal, idealnya ke Cloud Storage untuk link publik)
                file_path = f"skd_{pasien_id}.pdf"
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                conn = sqlite3.connect('klinik_data.db')
                c = conn.cursor()
                c.execute("UPDATE pendaftaran SET file_skd_path=? WHERE id=?", (file_path, pasien_id))
                conn.commit()
                conn.close()
                st.success("File berhasil diupload!")
                st.info(f"Link Akses: https://klinik-anda.streamlit.app/view?id={pasien_id}")
    else:
        st.write("Tidak ada data pasien baru.")

# --- 3. PENGATURAN MASTER DATA ---
elif choice == "Pengaturan Master Data":
    st.header("⚙️ Manajemen Perusahaan, Dept & Jabatan")
    
    kat = st.radio("Kategori Master", ["Perusahaan", "Departemen", "Jabatan"], horizontal=True)
    
    col_add, col_del = st.columns(2)
    
    with col_add:
        st.subheader(f"Tambah {kat}")
        new_val = st.text_input(f"Nama {kat} Baru")
        if st.button("Simpan"):
            add_master(kat, new_val)
            st.rerun()

    with col_del:
        st.subheader(f"Hapus {kat}")
        existing_vals = get_master(kat)
        to_del = st.selectbox(f"Pilih {kat} yang dihapus", existing_vals)
        if st.button("Hapus Data"):
            delete_master(kat, to_del)
            st.rerun()
    
    st.divider()
    st.write(f"Daftar {kat} Saat Ini:", get_master(kat))
