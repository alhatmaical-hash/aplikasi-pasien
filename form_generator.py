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
    tinggi_kop = 35 
    pdf.rect(margin_x, kop_y, lebar_kop, tinggi_kop) 

    # Fungsi pencari gambar
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    # Mengambil Logo
    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # PERBAIKAN POSISI LOGO: HJF digeser ke kiri (x=38) agar tidak menutupi tulisan tengah
    if path_harita: pdf.image(path_harita, x=12, y=14, h=22)
    if path_hjf:    pdf.image(path_hjf, x=38, y=14, h=22) # Geser ke kiri samping Harita
    if path_smk3:   pdf.image(path_smk3, x=168, y=14, h=22)

    # TEKS KOP (Sekarang bersih tidak tertutup logo)
    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(margin_x, kop_y + 8)
    pdf.cell(lebar_kop, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(lebar_kop, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # Fungsi pembersih karakter
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # --- TABEL DATA PASIEN ---
    pdf.ln(15) 
    labels = ["NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", "LOKASI KERJA", "GOLONGAN DARAH"]
    val = [clean(data.get('nama')), clean(data.get('tempat_lahir')), clean(data.get('tgl_lahir')), clean(data.get('gender')), clean(data.get('agama')), clean(data.get('no_hp')), clean(data.get('nik')), clean(data.get('perusahaan')), clean(data.get('departemen')), clean(data.get('jabatan')), clean(data.get('blok_mes')), clean(data.get('alergi')), clean(data.get('lokasi_kerja')), clean(data.get('gol_darah'))]

    pdf.set_font("helvetica", "", 12)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(65, 8.5, labels[i], border=1) 
        pdf.set_font("helvetica", "", 12)
        pdf.cell(125, 8.5, f": {val[i]}", border=1, ln=True)

    # --- BAGIAN PERNYATAAN DENGAN KOTAK (KOLOM) ---
    pdf.ln(8)
    y_pernyataan = pdf.get_y()
    pdf.rect(10, y_pernyataan, 190, 25) # Membuat kotak untuk pernyataan
    
    pdf.set_xy(12, y_pernyataan + 2)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(180, 8, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 11)
    pernyataan = "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut."
    pdf.set_x(12)
    pdf.multi_cell(186, 6, pernyataan)

    # --- BAGIAN TANDA TANGAN DENGAN KOTAK (KOLOM) ---
    pdf.ln(5)
    y_ttd_box = pdf.get_y()
    pdf.rect(10, y_ttd_box, 190, 50) # Membuat kotak untuk area tanda tangan
    
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.set_xy(10, y_ttd_box + 2)
    pdf.cell(95, 8, "", ln=False)
    pdf.cell(95, 8, tgl_skrg, ln=True, align="C")
    
    pdf.set_x(10)
    pdf.cell(95, 8, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 8, "Pasien / Keluarga,", align="C", ln=True)

    # Tanda Tangan Digital Petugas
    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        pdf.image(path_ttd, x=35, y=pdf.get_y() + 2, h=18)

    pdf.ln(25) 
    pdf.set_font("helvetica", "B", 12)
    pdf.set_x(10)
    pdf.cell(95, 8, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(95, 8, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
