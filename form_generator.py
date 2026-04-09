from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (Ukuran A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 2. Membuat Kop Formulir (Garis Luar)
    pdf.set_line_width(1)
    pdf.rect(10, 10, 190, 40) # Kotak Kop

    # 3. Memasukkan Logo (Pastikan file .jpg ada di folder utama)
    if os.path.exists("harita.jpg"):
        pdf.image("harita.jpg", x=12, y=12, h=25)
    if os.path.exists("hjf.jpg"):
        pdf.image("hjf.jpg", x=45, y=12, h=25)
    if os.path.exists("smk3.jpg"):
        pdf.image("smk3.jpg", x=165, y=12, h=25)

    # 4. Judul Kop (Besar & Bold)
    pdf.set_font("Times", "B", 18)
    pdf.set_xy(10, 18)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("Times", "B", 16)
    pdf.cell(190, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # 5. Tabel Data Pasien (Tulisan Ukuran 12 - Sangat Jelas)
    pdf.ln(15) # Jarak ke tabel
    
    labels = [
        "NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", 
        "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", 
        "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", 
        "LOKASI KERJA", "GOLONGAN DARAH"
    ]
    
    val = [
        data.get('nama','-'), data.get('tempat_lahir','-'), data.get('tgl_lahir','-'),
        data.get('gender','-'), data.get('agama','-'), data.get('no_hp','-'),
        data.get('nik','-'), data.get('perusahaan','-'), data.get('departemen','-'),
        data.get('jabatan','-'), data.get('blok_mes','-'), data.get('alergi','-'),
        data.get('lokasi_kerja','-'), data.get('gol_darah','-')
    ]

    pdf.set_font("Times", "", 12)
    for i in range(len(labels)):
        pdf.set_font("Times", "B", 12)
        pdf.cell(60, 10, labels[i], border=1) # Kolom Label
        pdf.set_font("Times", "", 12)
        pdf.cell(130, 10, f": {val[i]}", border=1, ln=True) # Kolom Isi

    # 6. Surat Pernyataan
    pdf.ln(10)
    pdf.set_font("Times", "B", 12)
    pdf.cell(190, 10, "SURAT PERNYATAAN", ln=True, align="L")
    pdf.set_font("Times", "", 11)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan "
                  "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    pdf.multi_cell(190, 7, pernyataan)

    # 7. Tanda Tangan
    pdf.ln(15)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.cell(100, 10, "", ln=False)
    pdf.cell(90, 10, tgl_skrg, ln=True, align="C")
    
    pdf.cell(95, 10, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 10, "Pasien / Keluarga,", align="C", ln=True)

    # Tempel Tanda Tangan Digital (Jika ada)
    y_ttd = pdf.get_y()
    path_ttd = f"sig_{petugas.lower()}.png"
    if os.path.exists(path_ttd):
        pdf.image(path_ttd, x=35, y=y_ttd, h=20)

    pdf.ln(25)
    pdf.set_font("Times", "B", 12)
    pdf.cell(95, 10, f"( {petugas} )", align="C")
    pdf.cell(95, 10, "( ............................ )", align="C", ln=True)

    # 8. Output sebagai Byte (Bisa langsung diprint di browser)
    return pdf.output(dest='S').encode('latin-1')
