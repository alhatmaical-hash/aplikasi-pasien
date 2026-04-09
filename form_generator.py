from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- KOP FORMULIR ---
    pdf.set_line_width(0.3)
    margin_x, kop_y = 10, 10
    lebar_kop_kiri, tinggi_kop = 90, 32
    pdf.rect(margin_x, kop_y, lebar_kop_kiri, tinggi_kop) 
    
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    # Logo HJF dirapatkan ke kiri (x=21) ke arah logo Harita
    path_harita, path_hjf, path_smk3 = cari_logo("harita"), cari_logo("hjf"), cari_logo("smk3")
    if path_harita: pdf.image(path_harita, x=12, y=13, h=10)
    if path_hjf:    pdf.image(path_hjf, x=21, y=13, h=10) 
    
    # Teks Kop digeser mengikuti posisi logo
    pdf.set_font("helvetica", "B", 10)
    pdf.set_xy(33, 13)
    pdf.cell(lebar_kop_kiri - 30, 4, clean("KLINIK HARITA FERONICKEL OBI"), ln=True)
    pdf.set_font("helvetica", "B", 7)
    pdf.set_x(33)
    pdf.cell(lebar_kop_kiri - 30, 4, clean("SITE KAWASI - PULAU OBI - HALSEL - MALUT"), ln=True)
    pdf.set_font("helvetica", "", 7)
    pdf.set_x(33)
    pdf.cell(lebar_kop_kiri - 30, 4, clean("Email: admin.klinik@hjferronickel.com"), ln=True)
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
    pdf.set_line_width(0.8)
    y_judul = pdf.get_y()
    pdf.rect(10, y_judul, 190, 22) 
    
    # Judul Tengah
    pdf.set_xy(10, y_judul + 2)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 8, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    
    # No Rekam Medis - TOP ALIGN
    pdf.set_xy(10, y_judul + 1) # Koordinat Y dinaikkan agar Top Align
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(188, 6, "No. Rekam Medis", ln=True, align="R")
    
    # KHFO-000000 (Besar)
    pdf.set_xy(10, y_judul + 6)
    pdf.set_font("helvetica", "B", 36)
    no_rm = data.get('no_rm', 'KHFO-000000') 
    pdf.cell(188, 15, clean(no_rm), ln=True, align="R")

    # --- IDENTITAS PASIEN ---
    pdf.set_xy(10, y_judul + 22)
    pdf.set_line_width(0.3)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 8, " IDENTITAS PASIEN ( bagian ini harus lengkap dan mohon diisi pasien )", border=1, ln=True)

    labels = ["NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", "GOLONGAN DARAH"]
    val = [clean(data.get('nama')), clean(data.get('tempat_lahir')), clean(data.get('tgl_lahir')), clean(data.get('gender')), clean(data.get('agama')), clean(data.get('no_hp')), clean(data.get('nik')), clean(data.get('perusahaan')), clean(data.get('departemen')), clean(data.get('jabatan')), clean(data.get('blok_mes')), clean(data.get('alergi')), clean(data.get('gol_darah'))]

    pdf.set_font("helvetica", "", 10)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 7.2, labels[i], border=1) 
        pdf.set_font("helvetica", "", 10)
        pdf.cell(130, 7.2, f": {val[i]}", border=1, ln=True)

    # --- SURAT PERNYATAAN & TTD (DIPERLEBAR KE BAWAH) ---
    pdf.ln(4)
    y_bawah = pdf.get_y()
    # Tinggi kotak ditingkatkan menjadi 75mm untuk memaksimalkan kertas A4
    pdf.rect(10, y_bawah, 190, 75) 

    pdf.set_xy(12, y_bawah + 3)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(186, 6, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")

    pdf.ln(15) # Spasi lebih luas agar tidak kosong di bawah
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.set_font("helvetica", "", 10)
    pdf.cell(186, 5, tgl_skrg, ln=True, align="R")
    
    pdf.set_x(12)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(93, 5, "Petugas Penerimaan,", align="C")
    pdf.cell(93, 5, "Pasien / Keluarga,", align="C", ln=True)

    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        pdf.image(path_ttd, x=37, y=pdf.get_y() + 5, h=16)

    pdf.ln(30) # Ruang TTD diperlebar agar seimbang
    pdf.set_x(12)
    pdf.cell(93, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(93, 5, "( ............................ )", align="C", ln=True)

    return bytes(pdf.output())
