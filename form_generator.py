from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- FUNGSI PENCARI LOGO (Mencegah Error Nama File) ---
    def cari_gambar(nama_dasar):
        # Mencoba berbagai ekstensi file yang mungkin Anda upload ke GitHub
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path):
                return path
        return None

    # --- KOP FORMULIR ---
    pdf.set_line_width(0.8)
    pdf.rect(10, 10, 190, 40) 

    # Mencari dan memasang logo
    path_harita = cari_gambar("harita")
    path_hjf = cari_gambar("hjf")
    path_smk3 = cari_gambar("smk3")

    # Posisi Y diatur agar logo terlihat besar dan rapi
    if path_harita: pdf.image(path_harita, x=12, y=13, h=33)
    if path_hjf: pdf.image(path_hjf, x=47, y=13, h=33)
    if path_smk3: pdf.image(path_smk3, x=163, y=13, h=33)

    # Teks Kop
    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(10, 18)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(190, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # --- PEMBERSIH TEKS (PENTING: Agar tidak error jika ada Mandarin) ---
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # --- TABEL DATA PASIEN (14 BARIS) ---
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
        pdf.cell(65, 8.5, labels[i], border=1)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(125, 8.5, f": {val[i]}", border=1, ln=True)

    # --- TANDA TANGAN ---
    pdf.ln(8)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.cell(95, 8, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 8, tgl_skrg, ln=True, align="C")
    
    # Mencari Tanda Tangan Digital Petugas
    path_ttd = cari_gambar(f"sig_{petugas.lower()}")
    if path_ttd:
        pdf.image(path_ttd, x=35, y=pdf.get_y(), h=18)

    pdf.ln(25)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(95, 8, f"( {clean(petugas)} )", align="C")
    pdf.cell(95, 8, "( ............................ )", align="C", ln=True)

    # Mengembalikan data bytes untuk download_button Streamlit
    return bytes(pdf.output())
