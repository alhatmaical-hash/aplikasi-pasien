from fpdf import FPDF
import os
from datetime import datetime

class UnicodePDF(FPDF):
    def header(self):
        pass # Bisa diisi jika ingin header otomatis di tiap halaman

def buat_formulir_otomatis(data, petugas):
    # Inisialisasi PDF dengan dukungan Unicode
    pdf = UnicodePDF(orientation='P', unit='mm', format='A4')
    
    # --- PENTING: MENAMBAHKAN FONT UNICODE ---
    # Pastikan file font DejaVuSans.ttf ada di folder yang sama dengan kode ini.
    # Jika Anda tidak punya filenya, font Helvetica akan digunakan tapi karakter Mandarin di-skip.
    try:
        # Gunakan font DejaVuSans (Font gratis yang mendukung Unicode)
        # Anda bisa mendownloadnya atau menggunakan font .ttf lain yang ada di sistem
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
        font_utama = 'DejaVu'
    except:
        # Fallback jika font tidak ditemukan (karakter Mandarin akan hilang)
        font_utama = 'Helvetica'

    pdf.add_page()
    
    def clean(text):
        if not text: return "-"
        return str(text)

    # --- BAGIAN KOP SURAT ---
    pdf.set_font(font_utama, 'B', 14)
    pdf.cell(190, 7, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font(font_utama, '', 10)
    pdf.cell(190, 5, "Klinik Pratama - PT. Jaya Feronikel", ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, 25, 200, 25)

    # --- TABEL IDENTITAS PASIEN ---
    pdf.set_font(font_utama, 'B', 10)
    pdf.cell(190, 7, "DATA PRIBADI / 个人资料", ln=True) # Karakter Mandarin aman di sini
    
    pdf.set_font(font_utama, '', 10)
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
        pdf.cell(50, 7, label, border=1)
        pdf.cell(140, 7, f": {clean(value)}", border=1, ln=True)

    # --- SURAT PERNYATAAN ---
    pdf.ln(5)
    pdf.set_font(font_utama, 'B', 10)
    pdf.cell(190, 7, "SURAT PERNYATAAN / 声明书", ln=True)
    pdf.set_font(font_utama, '', 9)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan "
                  "yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    pdf.multi_cell(190, 5, pernyataan, border=1)

    # --- AREA TANDA TANGAN ---
    pdf.ln(10)
    pdf.set_font(font_utama, '', 10)
    pdf.cell(186, 5, f"Kawasi, {datetime.now().strftime('%d %B %Y')}", ln=True, align="R")
    
    y_ttd_label = pdf.get_y() 
    pdf.set_font(font_utama, 'B', 10)
    pdf.cell(95, 5, "Petugas Penerimaan", align="C")
    pdf.cell(95, 5, "Pasien / Keluarga", align="C", ln=True)

    # Logika TTD Petugas
    file_petugas = f"{str(petugas).lower()}.png" 
    if os.path.exists(file_petugas):
        pdf.image(file_petugas, x=40, y=y_ttd_label + 7, h=15)
    
    pdf.ln(20) 
    pdf.set_font(font_utama, 'B', 10)
    pdf.cell(95, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(95, 5, f"( {clean(data.get('nama')).upper()} )", align="C", ln=True)

    return bytes(pdf.output())
