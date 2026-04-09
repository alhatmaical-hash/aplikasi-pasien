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
    tinggi_kop = 35 
    pdf.rect(margin_x, kop_y, lebar_kop, tinggi_kop) 

    # Fungsi pencari gambar (mencegah error jika file tidak ditemukan)
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path):
                return path
        return None

    # Mengambil Logo
    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # Logo diperkecil (h=20) agar tidak menutupi teks
    if path_harita: pdf.image(path_harita, x=12, y=15, h=20)
    if path_hjf: pdf.image(path_hjf, x=42, y=15, h=20)
    if path_smk3: pdf.image(path_smk3, x=170, y=15, h=20)

    # Teks Kop
    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(margin_x, kop_y + 8)
    pdf.cell(lebar_kop, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(lebar_kop, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # Fungsi pembersih karakter non-latin untuk mencegah crash
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # --- TABEL DATA PASIEN ---
    pdf.ln(15) 
    labels = [
        "NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", 
        "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", 
        "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RI
