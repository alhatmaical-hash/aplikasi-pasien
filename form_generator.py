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
    tinggi_kop = 30 
    pdf.rect(margin_x, kop_y, lebar_kop, tinggi_kop) 

    # Fungsi pencari gambar
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # POSISI LOGO: HJF digeser lebih ke kiri (x=33) agar teks tengah sangat luas
    if path_harita: pdf.image(path_harita, x=12, y=13, h=18)
    if path_hjf:    pdf.image(path_hjf, x=33, y=13, h=18) 
    if path_smk3:   pdf.image(path_smk3, x=172, y=13, h=18)

    # TEKS KOP
    pdf.set_font("helvetica", "B", 16)
    pdf.set_xy(margin_x, kop_y + 6)
    pdf.cell(lebar_kop, 8, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(lebar_kop, 8, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # --- KOLOM NO REKAM MEDIS (Diperbesar & Melebar) ---
    pdf.ln(4)
    # Font diperbesar ke 14pt dan tabel lebar penuh 190mm
    pdf.set_font("helvetica", "B", 14) 
    no_rm = data.get('no_rm', '-') 
    pdf.cell(190, 12, f"  No Rekam Medis : {no_rm}", border=1, ln=True)

    # Fungsi pembersih karakter
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii
