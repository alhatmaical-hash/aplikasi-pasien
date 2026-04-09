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
    pdf.set_
