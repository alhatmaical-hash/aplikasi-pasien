from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # Fungsi clean untuk menghindari error karakter non-latin pada font helvetica
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- KOP FORMULIR ---
    pdf.set_line_width(0.3)
    margin_x, kop_y = 10, 10
    pdf.rect(margin_x, kop_y, 90, 32) 
    
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    path_harita, path_hjf, path_smk3 = cari_logo("harita"), cari_logo("hjf"), cari_logo("smk3")
    if path_harita: pdf.image(path_harita, x=12, y=13, h=10)
    if path_hjf:    pdf.image(path_hjf, x=21, y=13, h=10) 
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_xy(33, 13)
    pdf.cell(60, 4, clean("KLINIK HARITA FERONICKEL OBI"), ln=True)
    pdf.set_font("helvetica", "B", 7)
    pdf.set_x(33)
    pdf.cell(60, 4, clean("SITE KAWASI - PULAU OBI - HALSEL - MALUT"), ln=True)
    pdf.set_font("helvetica", "", 7)
    pdf.set_x(33)
    pdf.cell(60, 4, clean("Email: admin.klinik@hjferronickel.com"), ln=True)
    if path_smk3: pdf.image(path_smk3, x=85, y=13, h=12)

    # Tabel Informasi Dokumen (Kanan Atas)
    pdf.set_xy(100, kop_y)
    pdf.set_font("helvetica", "", 8)
    dok_info = [["No. Dok", "HJF-FR-OHS-113"], ["Tgl Terbit", "12-10-2023"], ["No. Rev", "03"], ["Hal", "3"]]
    for h in dok_info:
        pdf.set_x(100)
        pdf.cell(25, 8, h[0], border=1)
        pdf.cell(75, 8, h[1], border=1, ln=True, align="C")

    # --- JUDUL & NO REKAM MEDIS ---
    pdf.ln(2)
    pdf.set_line_width(0.5)
    
    # Baris Judul
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN  ", border=1, ln=True, align="C")
    
    # Baris No Rekam Medis - SEKARANG ALIGN LEFT
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, " No. Rekam Medis  :", border=1, ln=True, align="L")

    # --- IDENTITAS PASIEN ---
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, " IDENTITAS PASIEN / ( bagian ini harus lengkap / )", border=1, ln=True)

    labels = [
        "NAMA LENGKAP ", "TEMPAT LAHIR  ", "TANGGAL LAHIR  ", 
        "JENIS KELAMIN  ", "AGAMA  ", "NO HP (WA)  ", 
        "NIK  ID CARD  ", "PERUSAHAAN  ", "DEPARTEMEN  ", 
        "JABATAN  ", "MES  NO KAMAR  ", "RIWAYAT ALERGI  ", "GOL. DARAH  "
    ]
    
    val_keys = ['nama', 'tempat_lahir', 'tgl_lahir', 'gender', 'agama', 'no_hp', 'nik', 'perusahaan', 'departemen', 'jabatan', 'blok_mes', 'alergi', 'gol_darah']

    pdf.set_font("helvetica", "", 9)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(70, 7.5, clean(labels[i]), border=1) 
        pdf.set_font("helvetica", "", 10)
        pdf.cell(120, 7.5, f": {clean(data.get(val_keys[i]))}", border=1, ln=True)

    # --- AREA SURAT PERNYATAAN ---
    pdf.ln(4)
    y_pernyataan = pdf.get_y()
    pdf.rect(10, y_pernyataan, 190, 85) 

    pdf.set_xy(12, y_pernyataan + 3)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(186, 6, "SURAT PERNYATAAN / ", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")

 # --- AREA TANDA TANGAN ---
    pdf.ln(10)
    pdf.cell(186, 5, f"Kawasi, {datetime.now().strftime('%d %B %Y')}", ln=True, align="R")
    
    # Simpan posisi Y saat ini
    posisi_y_ttd = pdf.get_y()
    
    pdf.set_x(12)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(93, 5, "Petugas Penerimaan / ", align="C")
    pdf.cell(93, 5, "Pasien / Keluarga / ", align="C", ln=True)

    # --- LOGIKA TANDA TANGAN PETUGAS ---
    # Mencari file tanda tangan petugas berdasarkan nama (huruf kecil)
    file_ttd_petugas = f"{str(petugas).lower()}.png"
    if os.path.exists(file_ttd_petugas):
        # x=40 adalah posisi di bawah teks 'Petugas Penerimaan'
        pdf.image(file_ttd_petugas, x=40, y=posisi_y_ttd + 8, h=18)
    
    # Render TTD Pasien jika filenya ada
    file_ttd_pasien = data.get('ttd_pasien') 
    if file_ttd_pasien and os.path.exists(file_ttd_pasien):
        pdf.image(file_ttd_pasien, x=135, y=posisi_y_ttd + 8, h=18)

    # Beri jarak agar nama tidak menimpa gambar TTD
    pdf.ln(25) 
    
    pdf.set_x(12)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(93, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(93, 5, f"( {clean(data.get('nama')).upper()} )", align="C", ln=True)

    # Garis penutup bawah
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)

    return bytes(pdf.output())
