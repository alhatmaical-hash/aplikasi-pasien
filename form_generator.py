from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- PENGATURAN KOP FORMULIR ---
    pdf.set_line_width(0.8)
    margin_x = 10
    kop_y = 10
    lebar_kop = 190
    tinggi_kop = 30 # Ukuran kop yang lebih ramping
    pdf.rect(margin_x, kop_y, lebar_kop, tinggi_kop) 

    # Fungsi pencari gambar (jpg/png)
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # LOGO DIPERKECIL (Tinggi h=18) agar teks di tengah aman
    if path_harita: pdf.image(path_harita, x=12, y=13, h=18)
    if path_hjf:    pdf.image(path_hjf, x=35, y=13, h=18)
    if path_smk3:   pdf.image(path_smk3, x(172), y=13, h=18)

    # TEKS KOP (Dipastikan tidak tertutup logo)
    pdf.set_font("helvetica", "B", 16)
    pdf.set_xy(margin_x, kop_y + 6)
    pdf.cell(lebar_kop, 8, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(lebar_kop, 8, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # --- KOLOM NO REKAM MEDIS (Area Merah Anda) ---
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 12)
    # Membuat kotak khusus No Rekam Medis tepat di bawah kop
    pdf.cell(190, 10, f" No Rekam Medis : {data.get('no_rm', '')}", border=1, ln=True)

    # Fungsi pembersih karakter
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # --- TABEL DATA PASIEN ---
    pdf.ln(2) 
    labels = ["NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", "LOKASI KERJA", "GOLONGAN DARAH"]
    val = [clean(data.get('nama')), clean(data.get('tempat_lahir')), clean(data.get('tgl_lahir')), clean(data.get('gender')), clean(data.get('agama')), clean(data.get('no_hp')), clean(data.get('nik')), clean(data.get('perusahaan')), clean(data.get('departemen')), clean(data.get('jabatan')), clean(data.get('blok_mes')), clean(data.get('alergi')), clean(data.get('lokasi_kerja')), clean(data.get('gol_darah'))]

    pdf.set_font("helvetica", "", 11)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(60, 8, labels[i], border=1) 
        pdf.set_font("helvetica", "", 11)
        pdf.cell(130, 8, f": {val[i]}", border=1, ln=True)

    # --- KOTAK SURAT PERNYATAAN ---
    pdf.ln(5)
    y_pernyataan = pdf.get_y()
    pdf.rect(10, y_pernyataan, 190, 22)
    pdf.set_xy(12, y_pernyataan + 2)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(180, 6, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 10)
    pernyataan = "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut."
    pdf.set_x(12)
    pdf.multi_cell(186, 5, pernyataan)

    # --- KOTAK AREA TANDA TANGAN ---
    pdf.ln(5)
    y_ttd_box = pdf.get_y()
    pdf.rect(10, y_ttd_box, 190, 45)
    
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.set_xy(10, y_ttd_box + 2)
    pdf.cell(190, 6, tgl_skrg, ln=True, align="R") # Tanggal di kanan atas kotak
    
    pdf.set_x(10)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(95, 6, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 6, "Pasien / Keluarga,", align="C", ln=True)

    # Tanda Tangan Digital Petugas
    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        pdf.image(path_ttd, x=35, y=pdf.get_y() + 2, h=16)

    pdf.ln(22) 
    pdf.set_x(10)
    pdf.cell(95, 6, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(95, 6, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
