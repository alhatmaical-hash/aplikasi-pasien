from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- PENGATURAN KOP ATAS (Tabel Informasi Dokumen) ---
    pdf.set_line_width(0.3)
    margin_x = 10
    kop_y = 10
    lebar_kop_kiri = 90
    tinggi_kop = 32 # Tinggi area kop (Kuning) agar logo tidak mnutupi teks
    
    # Kotak untuk area Logo dan Alamat di Kiri
    pdf.rect(margin_x, kop_y, lebar_kop_kiri, tinggi_kop) 
    
    # Fungsi pencari gambar agar logo pasti muncul
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path): return path
        return None

    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # PERBAIKAN LOGO: HJF digeser sedikit ke kiri (x=26) agar tidak mnutupi teks tengah
    if path_harita: pdf.image(path_harita, x=12, y=13, h=10)
    if path_hjf:    pdf.image(path_hjf, x=26, y=13, h=10)
    
    # TEKS KOP (Dipastikan BERSIH dan TERBACA, tidak tertutup logo)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_xy(38, 13)
    pdf.cell(lebar_kop_kiri - 30, 4, clean(data.get('kop_klinik', 'KLINIK HARITA FERONI')), ln=True)
    pdf.set_font("helvetica", "B", 7)
    pdf.set_x(38)
    pdf.cell(lebar_kop_kiri - 30, 4, clean(data.get('kop_site', 'SITE KAWASI - PULAU OBI - HAI')), ln=True)
    pdf.set_font("helvetica", "", 7)
    pdf.set_x(38)
    pdf.cell(lebar_kop_kiri - 30, 4, clean(data.get('kop_email', 'Email: admin.klinik@hjferronickel.o')), ln=True)

    # Logo SMK3 di kanan area alamat
    if path_smk3: pdf.image(path_smk3, x=85, y=13, h=12)

    # --- TABEL INFORMASI DOKUMEN (Sisi Kanan) ---
    # Posisi X diletakkan di 100mm (lebar_kop_kiri + 10mm margin)
    pdf.set_xy(100, kop_y)
    headers = [["No. Dok", "HJF-FR-OHS-113"], ["Tgl Terbit", "12-10-2023"], ["No. Rev", "03"], ["Hal", "3"]]
    pdf.set_font("helvetica", "", 8)
    for h in headers:
        pdf.set_x(100)
        pdf.cell(25, 8, h[0], border=1) # Kolom Label (Regular, 8pt)
        pdf.cell(75, 8, h[1], border=1, ln=True, align="C") # Kolom Isi (Bold, 8pt, Tengah)

    # --- PEMBERSIH UNICODE (Anti-Error Karakter Mandarin) ---
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # --- JUDUL & NO REKAM MEDIS DENGAN KOTAK ---
    pdf.ln(2)
    pdf.set_line_width(0.8) # Garis kotak judul lebih tebal
    pdf.rect(10, pdf.get_y(), 190, 22) # Bingkai kotak untuk judul dan No RM
    
    pdf.set_xy(10, pdf.get_y() + 2)
    pdf.set_font("helvetica", "B", 12)
    # Teks "FORMULIR PENDAFTARAN PASIEN" (Bold, 12pt, Tengah)
    pdf.cell(190, 8, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    
    # Teks "No. Rekam Medis" di pojok kanan (Regular, 10pt)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 6, "No. Rekam Medis ", ln=True, align="R")
    
    # Teks "KHFO-XXXXXX" (Bold, 36pt, Kanan) - Teks manual sesuai gambar
    pdf.set_font("helvetica", "B", 36)
    pdf.cell(190, 15, "KHFO-000000", ln=True, align="R")

    # --- SUB-JUDUL IDENTITAS PASIEN ---
    pdf.set_line_width(0.3)
    pdf.set_font("helvetica", "B", 11)
    # Membuat kotak sub-judul (Lebar 190mm, Tinggi 8mm)
    pdf.cell(190, 8, " IDENTITAS PASIEN ( bagian ini harus lengkap dan mohon diisi pasien )", border=1, ln=True)

    # --- TABEL DATA PASIEN (14 Baris) ---
    pdf.ln(0)
    labels = ["NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", "GOLONGAN DARAH"]
    val = [clean(data.get('nama')), clean(data.get('tempat_lahir')), clean(data.get('tgl_lahir')), clean(data.get('gender')), clean(data.get('agama')), clean(data.get('no_hp')), clean(data.get('nik')), clean(data.get('perusahaan')), clean(data.get('departemen')), clean(data.get('jabatan')), clean(data.get('blok_mes')), clean(data.get('alergi')), clean(data.get('gol_darah'))]

    # Jarak baris 7.5mm agar muat 14 kolom dalam satu halaman A4 tanpa dempet
    pdf.set_font("helvetica", "", 10)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 7.5, labels[i], border=1) 
        pdf.set_font("helvetica", "", 10)
        pdf.cell(130, 7.5, f": {val[i]}", border=1, ln=True)

    # --- PERBAIKAN BAWAH A4: KOTAK SURAT PERNYATAAN & TTD AGAR LEGA (SISI MERAH) ---
    pdf.ln(5)
    y_pernyataan_box = pdf.get_y()
    
    # Kotak bawah diperpanjang tingginya agar terlihat lega sesuai referensi
    # Sesuai yang Anda tandai merah
    pdf.rect(10, y_pernyataan_box, 190, 58) 

    # Area Teks Pernyataan (Koordinat X/Y di dalam kotak)
    pdf.set_xy(12, y_pernyataan_box + 2)
    pdf.set_font("helvetica", "B", 11)
    # Teks "SURAT PERNYATAAN" (Bold, 11pt, Kiri)
    pdf.cell(186, 6, "SURAT PERNYATAAN", ln=True)
    pdf.set_font("helvetica", "", 10)
    pernyataan = "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut."
    pdf.set_x(12)
    pdf.multi_cell(186, 5, pernyataan) # Multi_cell untuk menangani teks panjang

    # Area Tanda Tangan (di pojok kanan kotak diperpanjang)
    pdf.ln(5)
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    pdf.set_font("helvetica", "", 10)
    # Tanggal Otomatis di Kanan
    pdf.cell(186, 5, tgl_skrg, ln=True, align="R")
    
    # Judul Petugas/Pasien
    pdf.set_x(12)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(93, 5, "Petugas Penerimaan,", align="C")
    pdf.cell(93, 5, "Pasien / Keluarga,", align="C", ln=True)

    # Menempelkan TTD Digital Petugas (sig_alhatma.png) jika file ada
    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        # Penyesuaian Posisi TTD agar pas di atas nama
        pdf.image(path_ttd, x=37, y=pdf.get_y() + 2, h=14)

    pdf.ln(22) # Jarak diperlebar ke bawah agar tidak dempet saat diprint
    
    # Nama Petugas & Pasien
    pdf.set_x(12)
    pdf.set_font("helvetica", "B", 10)
    # Nama petugas dalam kurung dan Bold (contoh: ( ALHATMA ))
    pdf.cell(93, 5, f"( {clean(petugas).upper()} )", align="C")
    # Area TTD Pasien kosong
    pdf.cell(93, 5, "( ............................ )", align="C", ln=True)

    # --- OUTPUT SEBAGAI BYTES UNTUK STREAMLIT ---
    return bytes(pdf.output())
