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

    # Fungsi pencari gambar (mencegah error jika file tidak ditemukan)
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path):
                return path
        return None

    # Mengambil Logo
    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # Logo diperkecil (h=20) agar tidak menutupi teks
    if path_harita: pdf.image(path_harita, x=12, y=15, h=20)
    if path_hjf: pdf.image(path_hjf, x=42, y=15, h=20)
    if path_smk3: pdf.image(path_smk3, x=170, y=15, h=20)

    # Teks Kop
    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(margin_x, kop_y + 8)
    pdf.cell(lebar_kop, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(lebar_kop, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # Fungsi pembersih karakter non-latin untuk mencegah crash
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # --- TABEL DATA PASIEN ---
    pdf.ln(15) 
    labels = [
        "NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", 
        "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", 
        "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", 
        "LOKASI KERJA", "GOLONGAN DARAH"
    ]
    
    val = [
        clean(data.get('nama')), clean(data.get('tempat_lahir')), 
        clean(data.get('tgl_lahir')), clean(data.get('gender')),
        clean(data.get('agama')), clean(data.get('no_hp')),
        clean(data.get('nik')), clean(data.get('perusahaan')),
        clean(data.get('departemen')), clean(data.get('jabatan')),
        clean(data.get('blok_mes')), clean(data.get('alergi')),
        clean(data.get('lokasi_kerja')), clean(data.get('gol_darah'))
    ]

    pdf.set_font("helvetica", "", 12)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(65, 8.5, labels[i], border=1) 
        pdf.set_font("helvetica", "", 12)
        pdf.cell(125, 8.5, f": {val[i]}", border=1, ln=True)

    # --- SURAT PERNYATAAN ---
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 8, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 11)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan "
                  "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    pdf.multi_cell(190, 6, pernyataan)

    # --- AREA TANDA TANGAN ---
    pdf.ln(10)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.cell(95, 8, "", ln=False)
    pdf.cell(95, 8, tgl_skrg, ln=True, align="C")
    
    pdf.cell(95, 8, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 8, "Pasien / Keluarga,", align="C", ln=True)

    # Tanda Tangan Digital Petugas
    y_ttd = pdf.get_y()
    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        pdf.image(path_ttd, x=35, y=y_ttd + 2, h=18)

    pdf.ln(25) 
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(95, 8, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(95, 8, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
