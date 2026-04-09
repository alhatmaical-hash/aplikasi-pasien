from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- PENGATURAN KOP FORMULIR ---
    pdf.set_line_width(0.8)
    pdf.rect(10, 10, 190, 40) 

    # 2. Logika Pemanggilan Logo (Pastikan file harita.jpg, hjf.jpg, smk3.jpg ada di GitHub)
    # Posisi Y disesuaikan agar logo terlihat besar dan sejajar dengan teks
    y_logo = 13 
    
    if os.path.exists("harita.jpg"): 
        pdf.image("harita.jpg", x=12, y=y_logo, h=33)
    
    if os.path.exists("hjf.jpg"): 
        pdf.image("hjf.jpg", x=47, y=y_logo, h=33)
    
    if os.path.exists("smk3.jpg"): 
        pdf.image("smk3.jpg", x=163, y=y_logo, h=33)

    # Teks Kop (Helvetica Bold)
    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(10, 18)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(190, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # 3. Fungsi Pembersih Teks (Mencegah Error Karakter Mandarin)
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # 4. Tabel Data Pasien (Tinggi baris disesuaikan agar muat 1 halaman)
    pdf.ln(10)
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
        pdf.cell(65, 8.5, labels[i], border=1) # Tinggi baris 8.5mm
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
    pdf.ln(8)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.cell(95, 8, "", ln=False)
    pdf.cell(95, 8, tgl_skrg, ln=True, align="C")
    
    pdf.cell(95, 8, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 8, "Pasien / Keluarga,", align="C", ln=True)

    # Tanda Tangan Digital Petugas
    path_ttd = f"sig_{petugas.lower()}.png"
    if os.path.exists(path_ttd):
        pdf.image(path_ttd, x=35, y=pdf.get_y(), h=18)

    pdf.ln(22) # Ruang tanda tangan manual
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(95, 8, f"( {clean(petugas)} )", align="C")
    pdf.cell(95, 8, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
