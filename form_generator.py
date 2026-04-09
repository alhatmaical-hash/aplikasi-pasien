from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Posisikan Fungsi Clean di Paling Atas agar bisa diakses semua bagian
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # 2. Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- PENGATURAN KOP FORMULIR ---
    pdf.set_line_width(0.3)
    margin_x = 10
    kop_y = 10
    lebar_kop_kiri = 90
    tinggi_kop = 32 
    
    # Kotak Logo & Alamat (Sisi Kiri)
    pdf.rect(margin_x, kop_y, lebar_kop_kiri, tinggi_kop) 
    
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # Penempatan Logo (Diatur agar tidak mnutupi teks)
    if path_harita: pdf.image(path_harita, x=12, y=13, h=10)
    if path_hjf:    pdf.image(path_hjf, x=26, y=13, h=10)
    
    # Teks Kop Klinik (Sekarang aman menggunakan clean)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_xy(38, 13)
    pdf.cell(lebar_kop_kiri - 30, 4, clean("KLINIK HARITA FERONICKEL OBI"), ln=True)
    pdf.set_font("helvetica", "B", 7)
    pdf.set_x(38)
    pdf.cell(lebar_kop_kiri - 30, 4, clean("SITE KAWASI - PULAU OBI - HALSEL - MALUT"), ln=True)
    pdf.set_font("helvetica", "", 7)
    pdf.set_x(38)
    pdf.cell(lebar_kop_kiri - 30, 4, clean("Email: admin.klinik@hjferronickel.com"), ln=True)

    if path_smk3: pdf.image(path_smk3, x=85, y=13, h=12)

    # --- TABEL INFORMASI DOKUMEN (Sisi Kanan) ---
    pdf.set_xy(100, kop_y)
    pdf.set_font("helvetica", "", 8)
    headers = [["No. Dok", "HJF-FR-OHS-113"], ["Tgl Terbit", "12-10-2023"], ["No. Rev", "03"], ["Hal", "3"]]
    for h in headers:
        pdf.set_x(100)
        pdf.cell(25, 8, h[0], border=1)
        pdf.cell(75, 8, h[1], border=1, ln=True, align="C")

    # --- JUDUL & NO REKAM MEDIS ---
    pdf.ln(2)
    pdf.set_line_width(0.8)
    pdf.rect(10, pdf.get_y(), 190, 22) # Kotak judul & No RM
    
    pdf.set_xy(10, pdf.get_y() + 2)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 8, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 6, "No. Rekam Medis ", ln=True, align="R")
    
    # KHFO-000000 dihilangkan teksnya, hanya area besar
    pdf.set_font("helvetica", "B", 36)
    no_rm = data.get('no_rm', '') 
    pdf.cell(190, 15, clean(no_rm), ln=True, align="R")

    # --- IDENTITAS PASIEN ---
    pdf.set_line_width(0.3)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 8, " IDENTITAS PASIEN ( bagian ini harus lengkap dan mohon diisi pasien )", border=1, ln=True)

    # --- TABEL DATA PASIEN ---
    labels = ["NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", "GOLONGAN DARAH"]
    val = [clean(data.get('nama')), clean(data.get('tempat_lahir')), clean(data.get('tgl_lahir')), clean(data.get('gender')), clean(data.get('agama')), clean(data.get('no_hp')), clean(data.get('nik')), clean(data.get('perusahaan')), clean(data.get('departemen')), clean(data.get('jabatan')), clean(data.get('blok_mes')), clean(data.get('alergi')), clean(data.get('gol_darah'))]

    pdf.set_font("helvetica", "", 10)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 7.5, labels[i], border=1) 
        pdf.set_font("helvetica", "", 10)
        pdf.cell(130, 7.5, f": {val[i]}", border=1, ln=True)

    # --- AREA SURAT PERNYATAAN & TTD (BINGKAI KOTAK) ---
    pdf.ln(5)
    y_box = pdf.get_y()
    pdf.rect(10, y_box, 190, 55) # Kotak bawah sesuai gambar

    pdf.set_xy(12, y_box + 2)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(186, 6, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")

    pdf.ln(5)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.set_font("helvetica", "", 10)
    pdf.cell(186, 5, tgl_skrg, ln=True, align="R")
    
    pdf.set_x(12)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(93, 5, "Petugas Penerimaan,", align="C")
    pdf.cell(93, 5, "Pasien / Keluarga,", align="C", ln=True)

    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        pdf.image(path_ttd, x=37, y=pdf.get_y() + 2, h=14)

    pdf.ln(18) 
    pdf.set_x(12)
    pdf.cell(93, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(93, 5, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
