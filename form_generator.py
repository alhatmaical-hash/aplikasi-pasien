from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- BAGIAN KOP ATAS (Informasi Dokumen) ---
    pdf.set_line_width(0.3)
    
    # Area Logo dan Alamat (Sisi Kiri)
    pdf.rect(10, 10, 90, 32) 
    
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # Logo Harita & HJF
    if path_harita: pdf.image(path_harita, x=12, y=12, h=10)
    if path_hjf:    pdf.image(path_hjf, x=28, y=12, h=10)
    
    # Teks Alamat & Email Klinik
    pdf.set_font("helvetica", "B", 11)
    pdf.set_xy(40, 12)
    pdf.cell(60, 5, "KLINIK HARITA FERONICKEL OBI", ln=True)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_x(40)
    pdf.cell(60, 4, "SITE KAWASI - PULAU OBI - HALSEL - MALUT", ln=True)
    pdf.set_font("helvetica", "", 8)
    pdf.set_x(40)
    pdf.cell(60, 4, "Email: admin.klinik@hjferronickel.com", ln=True)

    # Logo SMK3
    if path_smk3: pdf.image(path_smk3, x=85, y=12, h=12)

    # Tabel Detail Dokumen (Sisi Kanan)
    pdf.set_xy(100, 10)
    pdf.set_font("helvetica", "", 8)
    dok_info = [
        ["No. Dok", "HJF-FR-OHS-113"],
        ["Tgl Terbit", "12-10-2023"],
        ["No. Rev", "03"],
        ["Hal", "3"]
    ]
    for row in dok_info:
        pdf.set_x(100)
        pdf.cell(25, 8, row[0], border=1)
        pdf.cell(75, 8, row[1], border=1, ln=True, align="C")

    # --- JUDUL & NOMOR RM ---
    pdf.ln(2)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 8, "FORMULIR PENDAFTARAN PASIEN", border="T", ln=True, align="C")

    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 6, "No. Rekam Medis", ln=True, align="R")
    pdf.set_font("helvetica", "B", 36) # Font Raksasa
    no_rm = data.get('no_rm', 'KHFO-000000')
    pdf.cell(190, 15, no_rm, ln=True, align="R")

    # --- IDENTITAS PASIEN ---
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 8, " IDENTITAS PASIEN ( bagian ini harus lengkap dan mohon diisi pasien )", border=1, ln=True)

    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # Tabel Data Pasien
    labels = ["NAMA", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", "GOLONGAN DARAH"]
    val = [clean(data.get('nama')), clean(data.get('tempat_lahir')), clean(data.get('tgl_lahir')), clean(data.get('gender')), clean(data.get('agama')), clean(data.get('no_hp')), clean(data.get('nik')), clean(data.get('perusahaan')), clean(data.get('departemen')), clean(data.get('jabatan')), clean(data.get('blok_mes')), clean(data.get('alergi')), clean(data.get('gol_darah'))]

    pdf.set_font("helvetica", "", 10)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 7.5, labels[i], border=1) 
        pdf.set_font("helvetica", "", 10)
        pdf.cell(130, 7.5, f": {val[i]}", border=1, ln=True)

    # --- PERNYATAAN & TTD ---
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 6, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 9)
    pernyataan = "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut."
    pdf.multi_cell(190, 5, pernyataan, border=0)

    pdf.ln(5)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.cell(190, 5, tgl_skrg, ln=True, align="R")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 5, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 5, "Pasien / Keluarga,", align="C", ln=True)

    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        pdf.image(path_ttd, x=35, y=pdf.get_y() + 2, h=12)

    pdf.ln(18) 
    pdf.cell(95, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(95, 5, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
