from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # Fungsi untuk membersihkan teks dari karakter non-latin agar tidak error
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- KOP SURAT ---
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(190, 7, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(190, 5, "Klinik Pratama - PT. Jaya Feronikel", ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, 25, 200, 25)

    # --- TABEL DATA PASIEN ---
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 7, "DATA PRIBADI PASIEN", ln=True)
    
    pdf.set_font("helvetica", "", 10)
    items = [
        ("NAMA LENGKAP", data.get('nama')),
        ("NIK / ID CARD", data.get('nik')),
        ("TEMPAT LAHIR", data.get('tempat_lahir')),
        ("TANGGAL LAHIR", data.get('tgl_lahir')),
        ("JENIS KELAMIN", data.get('gender')),
        ("AGAMA", data.get('agama')),
        ("NO HP (WA)", data.get('no_hp')),
        ("PERUSAHAAN", data.get('perusahaan')),
        ("DEPARTEMEN", data.get('departemen')),
        ("JABATAN", data.get('jabatan')),
        ("MES / NO KAMAR", data.get('blok_mes')),
        ("RIWAYAT ALERGI", data.get('alergi')),
        ("GOL. DARAH", data.get('gol_darah'))
    ]

    for label, value in items:
        pdf.cell(55, 7, f" {label}", border=1)
        pdf.cell(135, 7, f": {clean(value)}", border=1, ln=True)

    # --- PERNYATAAN ---
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 7, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 9)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan "
                  "yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    pdf.multi_cell(190, 5, pernyataan, border=1)

    # --- AREA TANDA TANGAN (TTD) ---
    pdf.ln(10)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(186, 5, f"Kawasi, {datetime.now().strftime('%d %B %Y')}", ln=True, align="R")
    
    # Simpan posisi Y agar gambar TTD presisi di bawah teks label
    y_posisi_ttd = pdf.get_y() 
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95
