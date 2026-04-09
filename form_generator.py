from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (A4 - Menggunakan 'fpdf2' untuk format bytes)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- PENGATURAN KOP FORMULIR (Satu Halaman & Logo Besar) ---
    pdf.set_line_width(0.8)
    margin_x = 10
    kop_y = 10
    lebar_kop = 190
    tinggi_kop = 40  # Ditinggikan untuk logo yang lebih besar
    pdf.rect(margin_x, kop_y, lebar_kop, tinggi_kop) 

    # Penempatan Logo (Diperbesar secara signifikan untuk kejelasan)
    # Sesuaikan nama file .jpg/png di GitHub Anda
    if os.path.exists("harita.jpg"): pdf.image("harita.jpg", x=12, y=kop_y + 3, h=33)
    if os.path.exists("hjf.jpg"): pdf.image("hjf.jpg", x=47, y=kop_y + 3, h=33)
    # Logo SMK3 diposisikan di sisi paling kanan sesuai instruksi sebelumnya
    if os.path.exists("smk3.jpg"): pdf.image("smk3.jpg", x=163, y=kop_y + 3, h=33)

    # Teks Kop (Gunakan Helvetica Bold ukuran besar: 18pt untuk cetakan tajam)
    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(margin_x, kop_y + 10)
    pdf.cell(lebar_kop, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(lebar_kop, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # --- PENGATURAN TABEL DATA PASIEN (14 KOLOM) ---
    pdf.ln(10) # Jarak dari kop ke tabel (dikurangi sedikit agar muat satu halaman)
    
    labels = [
        "NAMA LENGKAP", "TEMPAT LAHIR", "TANGGAL LAHIR", "JENIS KELAMIN", 
        "AGAMA", "NO HP (WHATSAPP)", "NIK / ID CARD", "PERUSAHAAN", 
        "DEPARTEMEN", "JABATAN", "MES / NO KAMAR", "RIWAYAT ALERGI", 
        "LOKASI KERJA", "GOLONGAN DARAH"
    ]
    
    val = [
        data.get('nama','-'), data.get('tempat_lahir','-'), data.get('tgl_lahir','-'),
        data.get('gender','-'), data.get('agama','-'), data.get('no_hp','-'),
        data.get('nik','-'), data.get('perusahaan','-'), data.get('departemen','-'),
        data.get('jabatan','-'), data.get('blok_mes','-'), data.get('alergi','-'),
        data.get('lokasi_kerja','-'), data.get('gol_darah','-')
    ]

    # Pengaturan Tinggi Baris Tabel agar muat 14 kolom di satu halaman (Tinggi 8.5mm - Pas & Jelas)
    pdf.set_font("helvetica", "", 12) # Font Times New Roman 12 untuk isi tabel
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(65, 8.5, labels[i], border=1) # Kolom Label
        pdf.set_font("helvetica", "", 12)
        pdf.cell(125, 8.5, f": {val[i]}", border=1, ln=True) # Kolom Isi

    # --- SURAT PERNYATAAN (Disingkat & Dirapikan agar muat satu halaman) ---
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 12) # Kop surat pernyataan Bold 12pt
    pdf.cell(190, 8, "SURAT PERNYATAAN", ln=True, align="L")
    pdf.set_font("helvetica", "", 11) # Isi surat pernyataan 11pt Regular
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan "
                  "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    # Multi_cell untuk menangani teks panjang
    pdf.multi_cell(190, 6, pernyataan)

    # --- BAGIAN TANDA TANGAN (Dikompensasi agar tidak tumpang tindih) ---
    pdf.ln(10) # Jarak ke tanda tangan dikurangi
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    
    # Tanggal Otomatis di Kanan
    pdf.cell(95, 8, "", ln=False)
    pdf.cell(95, 8, tgl_skrg, ln=True, align="C")
    
    # Judul Petugas/Pasien
    pdf.cell(95, 8, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 8, "Pasien / Keluarga,", align="C", ln=True)

    # Tempel Tanda Tangan Digital Petugas (Jika ada file sig_petugas.png di GitHub)
    current_y = pdf.get_y()
    path_ttd = f"sig_{petugas.lower()}.png"
    if os.path.exists(path_ttd):
        pdf.image(path_ttd, x=35, y=current_y, h=18)

    pdf.ln(20) # Jarak untuk tanda tangan manual
    
    # Nama Petugas & Pasien
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(95, 8, f"( {petugas} )", align="C")
    pdf.cell(95, 8, "( ............................ )", align="C", ln=True)

    # --- OUTPUT SEBAGAI BYTES UNTUK STREAMLIT ---
    return bytes(pdf.output())
