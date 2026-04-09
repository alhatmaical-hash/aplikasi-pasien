from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # 2. Fungsi Pembersih Teks (PENTING: Menghapus karakter Mandarin agar tidak error)
    def bersihkan_unicode(text):
        if not text:
            return "-"
        # Menghapus karakter yang tidak didukung oleh font standar
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # 3. Kop Formulir
    pdf.set_line_width(0.8)
    pdf.rect(10, 10, 190, 40) 

    # Pasang Logo (Pastikan file ada di GitHub)
    if os.path.exists("harita.jpg"): pdf.image("harita.jpg", x=12, y=13, h=33)
    if os.path.exists("hjf.jpg"): pdf.image("hjf.jpg", x=47, y=13, h=33)
    if os.path.exists("smk3.jpg"): pdf.image("smk3.jpg", x=163, y=13, h=33)

    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(10, 18)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(190, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # 4. Tabel Data (Semua data dibersihkan dengan fungsi bersihkan_unicode)
    pdf.ln(10)
    
    labels = [
        "NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", 
        "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", 
        "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", 
        "LOKASI KERJA", "GOLONGAN DARAH"
    ]
    
    val = [
        bersihkan_unicode(data.get('nama')), bersihkan_unicode(data.get('tempat_lahir')), 
        bersihkan_unicode(data.get('tgl_lahir')), bersihkan_unicode(data.get('gender')),
        bersihkan_unicode(data.get('agama')), bersihkan_unicode(data.get('no_hp')),
        bersihkan_unicode(data.get('nik')), bersihkan_unicode(data.get('perusahaan')),
        bersihkan_unicode(data.get('departemen')), bersihkan_unicode(data.get('jabatan')),
        bersihkan_unicode(data.get('blok_mes')), bersihkan_unicode(data.get('alergi')),
        bersihkan_unicode(data.get('lokasi_kerja')), bersihkan_unicode(data.get('gol_darah'))
    ]

    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(65, 8.5, labels[i], border=1)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(125, 8.5, f": {val[i]}", border=1, ln=True)

    # 5. Surat Pernyataan
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 8, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 11)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan "
                  "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    pdf.multi_cell(190, 6, pernyataan)

    # 6. Tanda Tangan
    pdf.ln(10)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.cell(95, 8, "", ln=False)
    pdf.cell(95, 8, tgl_skrg, ln=True, align="C")
    
    pdf.cell(95, 8, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 8, "Pasien / Keluarga,", align="C", ln=True)

    # Cek Tanda Tangan Digital
    path_ttd = f"sig_{petugas.lower()}.png"
    if os.path.exists(path_ttd):
        pdf.image(path_ttd, x=35, y=pdf.get_y(), h=18)

    pdf.ln(20)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(95, 8, f"( {bersihkan_unicode(petugas)} )", align="C")
    pdf.cell(95, 8, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
