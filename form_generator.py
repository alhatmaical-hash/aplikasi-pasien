from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Gunakan FPDF (Mendukung Unicode secara default di fpdf2)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    
    # 2. Tambahkan Font Unicode (Sangat Penting!)
    # Kita coba pakai font DejaVu atau Arial jika ada file .ttf di folder Anda.
    # Jika tidak ada, kita gunakan 'helvetica' tapi karakter Mandarin akan di-skip agar tidak error.
    try:
        # Jika Anda punya file font .ttf di github, masukkan di sini:
        # pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        # pdf.set_font('DejaVu', '', 12)
        pdf.set_fallback_fonts(["helvetica"]) # Pencegah error jika karakter tidak dikenal
    except:
        pass

    pdf.add_page()
    
    # 3. Kop Formulir
    pdf.set_line_width(1)
    pdf.rect(10, 10, 190, 40) 

    if os.path.exists("harita.jpg"): pdf.image("harita.jpg", x=12, y=12, h=25)
    if os.path.exists("hjf.jpg"): pdf.image("hjf.jpg", x=45, y=12, h=25)
    if os.path.exists("smk3.jpg"): pdf.image("smk3.jpg", x=165, y=12, h=25)

    pdf.set_font("helvetica", "B", 18) # Gunakan helvetica sebagai pengganti times agar lebih aman
    pdf.set_xy(10, 18)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(190, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # 4. Tabel Data (Bersihkan karakter non-latin agar tidak error)
    pdf.ln(15)
    
    labels = [
        "NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", 
        "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", 
        "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", 
        "LOKASI KERJA", "GOLONGAN DARAH"
    ]
    
    # Fungsi pembersih karakter Mandarin agar PDF tidak crash
    def clean_text(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    val = [
        clean_text(data.get('nama')), clean_text(data.get('tempat_lahir')), 
        clean_text(data.get('tgl_lahir')), clean_text(data.get('gender')),
        clean_text(data.get('agama')), clean_text(data.get('no_hp')),
        clean_text(data.get('nik')), clean_text(data.get('perusahaan')),
        clean_text(data.get('departemen')), clean_text(data.get('jabatan')),
        clean_text(data.get('blok_mes')), clean_text(data.get('alergi')),
        clean_text(data.get('lokasi_kerja')), clean_text(data.get('gol_darah'))
    ]

    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(60, 10, labels[i], border=1)
        pdf.set_font("helvetica", "", 11)
        pdf.cell(130, 10, f": {val[i]}", border=1, ln=True)

    # 5. Surat Pernyataan
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 10, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 10)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan "
                  "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    pdf.multi_cell(190, 7, pernyataan)

    # 6. Tanda Tangan
    pdf.ln(10)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.cell(95, 10, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 10, tgl_skrg, ln=True, align="C")
    
    pdf.ln(2)
    y_ttd = pdf.get_y()
    path_ttd = f"sig_{petugas.lower()}.png"
    if os.path.exists(path_ttd):
        pdf.image(path_ttd, x=35, y=y_ttd, h=20)

    pdf.ln(20)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(95, 10, f"( {clean_text(petugas)} )", align="C")
    pdf.cell(95, 10, "( ............................ )", align="C", ln=True)

    return pdf.output()
