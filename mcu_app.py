import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
from PIL import Image
import numpy as np
import os
import re



# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('mcu_complex.db')
    c = conn.cursor()
    # Tabel Master
    c.execute('CREATE TABLE IF NOT EXISTS master_perusahaan (nama TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS master_dept (nama TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS master_jabatan (nama TEXT)')
    
    # Tabel Pasien
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id_karyawan TEXT PRIMARY KEY, nik TEXT, nama TEXT, tempat_lahir TEXT, 
                    tgl_lahir TEXT, usia INTEGER, gender TEXT, doh TEXT, perusahaan TEXT, 
                    dept TEXT, jabatan TEXT, lokasi TEXT, no_hp TEXT, status_nikah TEXT, 
                    jml_anak INTEGER, tempat_tinggal TEXT, sumber_air TEXT)''')
    
    # Tabel Pemeriksaan & Hasil
    c.execute('''CREATE TABLE IF NOT EXISTS hasil_mcu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, id_karyawan TEXT, jenis_mcu TEXT, 
                    lab_summary TEXT, non_lab_summary TEXT, kesimpulan TEXT, 
                    follow_up TEXT, saran TEXT, tgl_periksa TEXT)''')
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def hitung_usia(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

from fpdf import FPDF

def generate_consent_pdf(data_pasien, tipe, img_ttd):
    pdf = FPDF()
    
    # --- PENGATURAN FONT (WAJIB ADA simhei.ttf) ---
    font_path = os.path.join(os.getcwd(), "simhei.ttf")
    can_use_unicode = False
    if os.path.exists(font_path):
        try:
            pdf.add_font('SimHei', '', font_path)
            font_main = 'SimHei'
            can_use_unicode = True
        except: font_main = 'Helvetica'
    else: font_main = 'Helvetica'

    def safe_t(text):
        return text if can_use_unicode else re.sub(r'[^\x00-\x7F]+', '', text)

    pdf.add_page()
    w = 190 # Lebar konten efektif

    # --- 1. HEADER (KOP SURAT) ---
    # Membuat tabel header agar rapi seperti di foto
    pdf.set_font(font_main, 'B', 11)
    pdf.cell(140, 7, "KLINIK HARITA NICKEL OBI", border='TL', align='C')
    pdf.set_font(font_main, '', 8)
    pdf.cell(20, 7, "No. Dok", border='TL')
    pdf.cell(30, 7, "HJF-FR-OHS-370", border='TLR', ln=True)
    
    pdf.set_font(font_main, 'B', 9)
    pdf.cell(140, 5, "FIRST-AID POST PT. HALMAHERA JAYA FERONIKEL", border='L', align='C')
    pdf.set_font(font_main, '', 8)
    pdf.cell(20, 5, "Tgl Terbit", border='L')
    pdf.cell(30, 5, "22/02/2024", border='LR', ln=True)
    
    pdf.cell(140, 5, "SITE KAWASI - PULAU OBI - HALSEL - MALUT", border='L', align='C')
    pdf.cell(20, 5, "No. Rev", border='L')
    pdf.cell(30, 5, "000", border='LR', ln=True)
    
    pdf.cell(140, 5, "Email: mcu.klinik@hjferonikel.com", border='LB', align='C')
    pdf.cell(20, 5, "Hal", border='LB')
    pdf.cell(30, 5, "Page | 1", border='LBR', ln=True)

    pdf.ln(5)

    # --- 2. JUDUL ---
    pdf.set_font(font_main, 'B', 10)
    judul = "PERSETUJUAN UMUM / GENERAL CONSENT  一般同意" if tipe == "General Consent" else "INFORMED CONSENT 知情同意书"
    pdf.cell(w, 7, safe_t(judul), ln=True, align='C')
    pdf.ln(2)

    # --- 3. DATA PASIEN (BAGIAN ATAS) ---
    pdf.set_font(font_main, '', 9)
    data_label = [
        ["No. RM/ID 医疗记录号", data_pasien[1]],
        ["Nama Pasien/姓名", data_pasien[0]],
        ["Perusahaan/公司", data_pasien[2]],
        ["Jenis Kelamin/性别", data_pasien[3]],
        ["Tanggal Lahir/出生日期", data_pasien[4]]
    ]
    
    # Geser ke kanan untuk bagian identitas
    for label, val in data_label:
        pdf.set_x(110) 
        pdf.cell(40, 5, safe_t(label), border=0)
        pdf.cell(40, 5, f": {val}", border=0, ln=True)

    pdf.ln(5)

    # --- 4. PERNYATAAN PEMBUKA ---
    pdf.set_font(font_main, 'B', 9)
    pdf.set_x(10)
    pdf.cell(w, 5, safe_t("PASIEN DAN / WALI HUKUM HARUS MEMBACA, MEMAHAMI"), ln=True, align='C')
    pdf.cell(w, 5, safe_t("DAN MENGISI INFORMASI TERSEBUT"), ln=True, align='C')
    pdf.cell(w, 5, safe_t("患者和/或法定监护人必须阅读、理解并填写该信息"), ln=True, align='C')
    pdf.ln(3)

    # --- 5. ISI POINT-POINT (SESUAI GAMBAR) ---
    pdf.set_font(font_main, '', 8)
    if tipe == "General Consent":
        points = [
            "1. Saya menyetujui dilakukan pemeriksaan dan/atau perawatan kepada saya (我同意对我进行检查和/或治疗)",
            "2. HAK DAN KEWAJIBAN SEBAGAI PASIEN:saya mengakui bahwa proses pendaftaran untuk mendaptkan perawatan di klinik harita nickel obi dan
                penandatanganan dokumen ini, saya telah mendapat informasi tentang hak-hak dan kewajiban saya sebagai pasien.",
            """3. PERSETUJUAN PELAYANAN KESEHATAN:saya menyetujui dan memberikan persetujuan untuk mendapatkan pelayanan kesehatan di Klinik Harita Nickel Obi
                dan dengan ini saya meminta dan meberikan kuasa kepada pihak Klinik Harita Nickel-Obi, Dokter Dan Perawat, Dan Tenaga Kesehatan Lainnya untuk
                memberikan asuhan keperawatan, pemeriksaan fisik yang di lakukan oleh dokter dan perawat, melakukan prosedur diagnostic, radiologi, dan atau terapi dan tata
                laksana sesuai pertimbangan dokter yang di perlukan atau di rasarankan pada perawat saya. Hal ini mencangkup seluruh pemeriksaan dan prosedur diagnostic rutin
                termasuk X-Ray, pemberian dan atau tindakan medis serta penyuntikan (Intra-muskular, intravena dan prosedur incasif lainnya), produk farmasi dan obat-obatan
                pemasangan alat kesehatan (kecuali yang membutuhkan persetujuan khusus/tertulis), dan pengambilandarah untuk pemeriksaan laboratorium atau pemeriksaan patologi
                yang dibutuhkan untuk pengobatan dan tindakan yang aman.",
            "4. PRIVASI:saya memberi kuasa kepada Klinik Harita Nickel-Obi untuk menjaga privasi dan kerahasiaan penyakit saya selama dalam pemeriksaan.",
            "5. RAHASIA KEDOKTERAN: Saya setuju Klinik Harita Nickel-Obi wajib menjamin rahasia kedokteran saya baik untuk kepentingan perawatan atau
                pengobatan, kecuali saya mengugkapkan sendiri atau orang lain yang saya beri kuasa kepada penjamin.",
            """6. MEMBUKA RAHASIA KEDOKTERAN:saya setuju untuk membuka rahasia kedokteran terkait dengan kondisi kesehatan asuhan dan pengobatan yang saya terima kepada
                a. Dokter dan tenaga kesehatanlain yang memberikan asuhan kepada saya
                b. Manajemen perusahaan untuk proses klaim asuransi dan/ atau administrasi perusahaan lainnya, seperti kesimpulan kelaikan memulai atau melanjutkan
                   pekerjaan serta hasil pemeriksaan lanjutan dari fasilitas kesehatan lanjut jika di lakukan rujukan
                c. kepada yang tersebut berikut ini",
            "7. BARANG PRIBADI:saya setuju untuk tidak membawah barang-barang berharga yang tidak di perlukan selama dalam perawatan di klinik harita nickel obi
                saya memahami dan menyetujuiklinik harita nickel obi tidak bertanggung jawab terhadap kehilangan, kerusakan, pencurian barang berharga.",
            "8. PENGAJUAN KELUHAN:saya menyatakan bahwa saya telah menerima informasi tentang adanya tata cara mengajukan dan mengatasi keluhan terhadap
                pelayanan medis yang diberikan terhadap saya. Saya setuju untuk mengikuti tata cara mengajukan keluhan sesuai prosedur yang ada.",

            """Melalui dokuemen ini saya menegaskan kembali bahwa saya mempercayakan kepada tenaga kesehatan klinik harita nickel obi untuk memberikan perawatan, diagnostic dan
            terapi kepada saya sebagai pasien rawat jalan, rawat inap, medical check up (MCU) atau unit gawat darurat, termasuk semua pemeriksaan penunjang yangdibutuhkan untuk
            pengobatan dan tindakan yang aman. SAYA TELAH MEMBACA DAN SEPENUHNYA SETUJU dengan setiap pernyataan yang terdapat pada formulir ini dan menandatangani tanpa paksaan
            dan dengan kesadaran penuh." 
                
        ]
    else:
        points = [
            "Saya menyatakan SETUJU (同意) / MENOLAK (拒绝) untuk dilakukan pemeriksaan darah yaitu:",
            "anti-HIV, HBsAg dan anti-HCV (人类免疫缺陷病毒、乙型肝炎和丙型肝炎)",
            "Demikian persetujuan ini saya buat tanpa ada paksaan dari pihak mana pun."
        ]

    for p in points:
        pdf.set_x(10)
        pdf.multi_cell(w, 4, safe_t(p))
        pdf.ln(1)

    # --- 6. TANDA TANGAN (BAGIAN BAWAH) ---
    pdf.ln(10)
    curr_y = pdf.get_y()
    
    # Lokasi Tanda Tangan
    pdf.set_font(font_main, '', 9)
    pdf.text(30, curr_y, safe_t("Petugas 护士"))
    pdf.text(140, curr_y, safe_t("Pasien / wali 病人"))
    
    # Gambar TTD
    temp_path = "sign_temp.png"
    img_ttd.save(temp_path)
    pdf.image(temp_path, x=135, y=curr_y + 2, w=35)
    
    # Nama Terang
    pdf.text(30, curr_y + 25, "( .................................... )")
    pdf.text(140, curr_y + 25, f"( {data_pasien[0]} )")
    pdf.set_font(font_main, '', 7)
    pdf.text(30, curr_y + 28, "Tanda tangan dan nama lengkap")

    return pdf.output()
    
def main():
    st.set_page_config(page_title="Sistem Manajemen MCU Klinik", layout="wide")
    init_db()

    st.sidebar.title("🏥 Klinik MCU")
    menu = [
        "Dashboard", 
        "Master Data", 
        "1. Registrasi Pasien", 
        "1.5 General & Informed Consent", # Menu baru
        "2. Pemeriksaan & Upload", 
        "3. Hasil & Kesimpulan (Dokter)"
    ]
    choice = st.sidebar.radio("Navigasi", menu)

    # --- MENU: DASHBOARD ---
    if choice == "Dashboard":
        st.title("📊 Dashboard Pelayanan MCU")
        conn = sqlite3.connect('mcu_complex.db')
        df_p = pd.read_sql_query("SELECT * FROM pasien", conn)
        df_h = pd.read_sql_query("SELECT * FROM hasil_mcu", conn)
        conn.close()

        col1, col2, col3 = st.columns(3)
        total_mcu = len(df_h)
        col1.metric("Total Pasien Terdaftar", f"{len(df_p)} Orang")
        col2.metric("Total MCU Selesai", f"{total_mcu} Pemeriksaan")
        prosentase = (total_mcu / len(df_p) * 100) if len(df_p) > 0 else 0
        col3.metric("Penyelesaian MCU", f"{prosentase:.1f}%")

        st.divider()
        st.subheader("📈 Statistik Kondisi Kesehatan")
        s1, s2, s3, s4 = st.columns(4)
        if not df_h.empty:
            jml_fit = len(df_h[df_h['kesimpulan'].str.contains('Fit', na=False)])
            jml_unfit = len(df_h[df_h['kesimpulan'].str.contains('Unfit', na=False)])
            jml_klinik = len(df_h[df_h['follow_up'].str.contains('klinik', na=False, case=False)])
            jml_spesialis = len(df_h[df_h['follow_up'].str.contains('spesialis', na=False, case=False)])
            s1.success(f"✅ Total Fit\n### {jml_fit}")
            s2.error(f"❌ Total Unfit\n### {jml_unfit}")
            s3.warning(f"🏥 Kontrol Klinik\n### {jml_klinik}")
            s4.info(f"👨‍⚕️ Ke Spesialis\n### {jml_spesialis}")
        else:
            st.info("Statistik akan muncul setelah ada pemeriksaan.")

        st.divider()
        if not df_p.empty:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_p.to_excel(writer, index=False, sheet_name='Daftar_Pasien')
            st.download_button(label="📥 Download Excel", data=buffer.getvalue(), file_name=f"Rekap_MCU_{date.today()}.xlsx")
            st.dataframe(df_p, use_container_width=True, hide_index=True)

    # --- MENU: MASTER DATA & AKUN ---
    elif choice == "Master Data":
        st.header("⚙️ Manajemen Data Master & Akun")
        
        tab_master, tab_akun = st.tabs(["📋 Data Master", "👤 Manajemen Akun"])
        
        with tab_master:
            conn = sqlite3.connect('mcu_complex.db')
            
            # Baris 1: Perusahaan
            st.subheader("🏢 Perusahaan")
            c1, c2 = st.columns([3, 1])
            new_pt = c1.text_input("Nama Perusahaan Baru", key="add_pt")
            if c2.button("Simpan PT", use_container_width=True):
                if new_pt:
                    conn.execute('INSERT INTO master_perusahaan VALUES (?)', (new_pt,))
                    conn.commit()
                    st.success(f"PT {new_pt} Berhasil Disimpan")
                    st.rerun()

            st.divider()

            # Baris 2: Departemen
            st.subheader("📁 Departemen")
            c3, c4 = st.columns([3, 1])
            new_dept = c3.text_input("Nama Departemen Baru", key="add_dept")
            if c4.button("Simpan Dept", use_container_width=True):
                if new_dept:
                    conn.execute('INSERT INTO master_dept VALUES (?)', (new_dept,))
                    conn.commit()
                    st.success(f"Dept {new_dept} Berhasil Disimpan")
                    st.rerun()

            st.divider()

            # Baris 3: Jabatan
            st.subheader("👔 Jabatan")
            c5, c6 = st.columns([3, 1])
            new_jab = c5.text_input("Nama Jabatan Baru", key="add_jab")
            if c6.button("Simpan Jabatan", use_container_width=True):
                if new_jab:
                    conn.execute('INSERT INTO master_jabatan VALUES (?)', (new_jab,))
                    conn.commit()
                    st.success(f"Jabatan {new_jab} Berhasil Disimpan")
                    st.rerun()
            
            conn.close()

        with tab_akun:
            st.subheader("🔐 Tambah Akun Pengguna (Petugas/Dokter)")
            # Inisialisasi tabel user jika belum ada
            conn = sqlite3.connect('mcu_complex.db')
            conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
            
            with st.form("form_akun"):
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type="password")
                new_role = st.selectbox("Role / Jabatan", ["Admin", "Dokter", "Perawat", "Registrasi"])
                if st.form_submit_button("Buat Akun"):
                    try:
                        conn.execute('INSERT INTO users VALUES (?,?,?)', (new_user, new_pass, new_role))
                        conn.commit()
                        st.success(f"Akun {new_user} sebagai {new_role} berhasil dibuat!")
                    except:
                        st.error("Username sudah ada.")
            
            # Tampilkan Daftar Akun
            st.divider()
            st.subheader("👥 Daftar Pengguna Sistem")
            df_users = pd.read_sql_query("SELECT username, role FROM users", conn)
            st.table(df_users)
            conn.close()

    # --- MENU 1: REGISTRASI ---
    elif choice == "1. Registrasi Pasien":
        st.header("📝 Form Registrasi Karyawan")
        conn = sqlite3.connect('mcu_complex.db')
        list_pt = [x[0] for x in conn.execute('SELECT * FROM master_perusahaan').fetchall()]
        list_dept = [x[0] for x in conn.execute('SELECT * FROM master_dept').fetchall()]
        list_jab = [x[0] for x in conn.execute('SELECT * FROM master_jabatan').fetchall()]
        conn.close()

        jenis_mcu = st.selectbox("Jenis MCU", ["MCU ANNUAL (MCU TAHUNAN)", "PRE EMPLOYMENT (MCU KARYAWAN BARU)"], index=None, placeholder="Pilih Jenis MCU...")

        with st.form("regis_form"):
            c1, c2, c3 = st.columns(3)
            id_kar = c1.text_input("No ID Karyawan")
            nik = c2.text_input("NIK KTP")
            nama = c3.text_input("Nama Lengkap")
            
            c4, c5, c6 = st.columns(3)
            tmp_lhr = c4.text_input("Tempat Lahir")
            tgl_lhr = c5.date_input("Tanggal Lahir", min_value=date(1960,1,1))
            usia = hitung_usia(tgl_lhr)
            c6.info(f"Usia Terhitung: {usia} Tahun")
            
            c7, c8, c9 = st.columns(3)
            gender = c7.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"], index=None)
            doh_manual = c8.text_input("Masa Lama Kerja (DOH)")
            pt = c9.selectbox("Perusahaan", list_pt, index=None)

            c10, c11, c12 = st.columns(3)
            dept = c10.selectbox("Departemen", list_dept, index=None)
            jab = c11.selectbox("Jabatan", list_jab, index=None)
            lokasi = c12.text_input("Lokasi Kerja")

            c13, c14, c15 = st.columns(3)
            hp = c13.text_input("No HP")
            status_m = c14.selectbox("Status Pernikahan", ["Lajang", "Menikah", "Cerai"], index=None)
            jml_anak = c15.number_input("Jumlah Anak", 0, 20)

            c16, c17, c18 = st.columns(3)
            tinggal = c16.selectbox("Tempat Tinggal", ["Mes", "Kawasi", "Lainnya"], index=None)
            air = c17.selectbox("Sumber Air Minum", ["RO", "Galon Isi Ulang", "Sumur", "PDAM"], index=None)
            
            mcu_ke = 0
            if jenis_mcu == "MCU ANNUAL (MCU TAHUNAN)":
                mcu_ke = c18.number_input("MCU Annual Ke-", min_value=1, step=1)
            
            if st.form_submit_button("Simpan Registrasi"):
                conn = sqlite3.connect('mcu_complex.db')
                conn.execute('''INSERT OR REPLACE INTO pasien 
                             (id_karyawan, nik, nama, tempat_lahir, tgl_lahir, usia, gender, doh, perusahaan, dept, jabatan, lokasi, no_hp, status_nikah, jml_anak, tempat_tinggal, sumber_air) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (id_kar, nik, nama, tmp_lhr, str(tgl_lhr), usia, gender, doh_manual, pt, dept, jab, lokasi, hp, status_m, jml_anak, tinggal, air))
                conn.commit()
                conn.close()
                st.success(f"Berhasil Terdaftar!")

   # --- DI DALAM MENU 1.5 ---
    elif choice == "1.5 General & Informed Consent":
        st.header("📑 Digital Consent Form")
        id_cari = st.text_input("Masukkan ID Karyawan")
        
        if id_cari:
            conn = sqlite3.connect('mcu_complex.db')
            # Ambil data lengkap untuk PDF
            p = conn.execute("SELECT nama, id_karyawan, perusahaan, gender, tgl_lahir FROM pasien WHERE id_karyawan=?", (id_cari,)).fetchone()
            conn.close()
            
            if p:
                st.success(f"Pasien: {p[0]} ({p[2]})")
                tipe = st.radio("Pilih Dokumen", ["General Consent", "Informed Consent"], horizontal=True)
                
                # Canvas TTD
                st.subheader("Tanda Tangan Pasien / 病人签名")
                canvas_res = st_canvas(
                    stroke_width=2, stroke_color="#000", background_color="#ffffff",
                    height=150, width=400, drawing_mode="freedraw", key="canvas_sig"
                )
    
                if st.button("Generate & Download PDF"):
                    if canvas_res.image_data is not None:
                        # Ambil gambar dari canvas
                        img = Image.fromarray(canvas_res.image_data.astype('uint8'), 'RGBA')
                        
                        # Buat PDF
                        pdf_raw = generate_consent_pdf(p, tipe, img)
                        
                        # KONVERSI KE BYTES (Solusi Error)
                        pdf_bytes = bytes(pdf_raw) 
                        
                        st.download_button(
                            label="📥 Download Dokumen PDF",
                            data=pdf_bytes, # Gunakan data yang sudah dikonversi
                            file_name=f"{tipe}_{id_cari}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("Data pasien tidak ditemukan. Silakan registrasi terlebih dahulu.")

    # --- MENU 2: PEMERIKSAAN & UPLOAD ---
    elif choice == "2. Pemeriksaan & Upload":
        st.header("🩺 Input Pemeriksaan & Upload Lampiran")
        id_cari = st.text_input("Masukkan ID Karyawan")
        if id_cari:
            with st.expander("Fisik & Upload", expanded=True):
                antropometri = st.text_area("Antropometri (TB, BB, BMI)")
                up_lab = st.file_uploader("Upload Hasil Lab/Rad/EKG", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
                if st.button("Simpan Progres"):
                    st.success("Data pemeriksaan awal tersimpan.")

    # --- MENU 3: HASIL & KESIMPULAN (DOKTER) ---
    elif choice == "3. Hasil & Kesimpulan (Dokter)":
        st.header("👨‍⚕️ Resume Medis & Penentuan Kelayakan")
        id_dr = st.text_input("ID Karyawan untuk Resume")
        if id_dr:
            tab1, tab2, tab3 = st.tabs(["Laboratorium", "Non-Laboratorium", "Kesimpulan"])
            with tab1:
                hem = st.text_area("Hematologi")
                kim = st.text_area("Kimia Klinik")
                ser = st.multiselect("Serologi", ["HBsAg", "Anti HIV", "Anti HCV"])
            with tab2:
                ekg = st.text_input("Hasil EKG")
                rad = st.text_input("Hasil Rontgen")
            with tab3:
                kes = st.radio("Status", ["Fit for Work", "Fit with Note", "Fit with Restriction", "Unfit Temporary", "Unfit"], horizontal=True)
                fu1 = st.checkbox("Ke Klinik")
                fu2 = st.checkbox("Ke Spesialis")
                saran = st.text_area("Saran")
                
                if st.button("Finalisasi & Simpan"):
                    conn = sqlite3.connect('mcu_complex.db')
                    conn.execute('INSERT INTO hasil_mcu (id_karyawan, lab_summary, non_lab_summary, kesimpulan, saran, tgl_periksa) VALUES (?,?,?,?,?,?)',
                                 (id_dr, f"Hem: {hem}, Ser: {ser}", f"EKG: {ekg}, Rad: {rad}", kes, saran, str(date.today())))
                    conn.commit()
                    conn.close()
                    st.success("Data MCU Final Tersimpan!")

if __name__ == "__main__":
    main()
