from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- PENGATURAN KOP FORMULIR (Satu Halaman) ---
    pdf.set_line_width(0.8)
    margin_x = 10
    kop_y = 10
    lebar_kop = 190
    tinggi_kop = 35 # Sedikit dikurangi agar proporsional
    pdf.rect(margin_x, kop_y, lebar_kop, tinggi_kop) 

    # --- PENYUSUAN LOGO (Diperkecil & Disesuaikan Kop) ---
    # Fungsi pencari gambar agar logo pasti muncul meskipun format beda
    def cari_logo(nama_dasar):
        for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG']:
            path = nama_dasar + ext
            if os.path.exists(path):
                return path
        return None

    path_harita = cari_logo("harita")
    path_hjf = cari_logo("hjf")
    path_smk3 = cari_logo("smk3")

    # Posisi Logo Y diatur agar sejajar dengan teks kop (Posisi Y=13mm)
    # Ukuran Logo Y (Tinggi/h) diperkecil dari 33mm ke 25mm agar proporsional
    if path_harita: pdf.image(path_harita, x=12, y=13, h=25)
    if path_hjf: pdf.image(path_hjf, x=45, y=13, h=25)
    if path_smk3: pdf.image(path_smk3, x=165, y=13, h=25)

    # --- TEKS KOP FORMULIR ---
    pdf.set_font("helvetica", "B", 18)
    pdf.set_xy(margin_x, kop_y + 8)
    pdf.cell(lebar_kop, 10, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(lebar_kop, 10, "KLINIK HARITA FERONICKEL OBI", ln=True, align="C")

    # --- PEMBERSIH UNICODE (Anti-Error Karakter Mandarin) ---
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # --- TABEL DATA PASIEN (1 Halaman - 14 Kolom) ---
    pdf.ln(12) # Jarak dari kop ke tabel
    
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

    # Font Helvetica ukuran 12pt (Tajam & Jelas)
    pdf.set_font("helvetica", "", 12)
    # Pengaturan Tinggi Baris Tabel agar muat 14 kolom di satu halaman (Tinggi 8.5mm - Pas & Jelas)
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(65, 8.5, labels[i], border=1) # Kolom Label (Bold)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(125, 8.5, f": {val[i]}", border=1, ln=True) # Kolom Isi (Regular)

    # --- SURAT PERNYATAAN ---
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 8, "SURAT PERNYATAAN", ln=True, align="L")
    pdf.set_font("helvetica", "", 11)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan "
                  "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    # Multi_cell untuk menangani teks panjang
    pdf.multi_cell(190, 6, pernyataan)

    # --- TANDA TANGAN ---
    pdf.ln(15) # Jarak ke tanda tangan
    tgl_skrg = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    
    # Tanggal Otomatis di Kanan
    pdf.cell(95, 8, "", ln=False)
    pdf.cell(95, 8, tgl_skrg, ln=True, align="C")
    
    # Judul Petugas/Pasien
    pdf.cell(95, 8, "Petugas Penerimaan,", align="C")
    pdf.cell(95, 8, "Pasien / Keluarga,", align="C", ln=True)

    # --- PENEMPATAN TTD PETUGAS PRESISI ---
    # Kita kunci koordinat Y saat ini agar TTD tidak bergeser jika teks di atasnya berubah
    y_sign = pdf.get_y()
    
    # Mencari Tanda Tangan Digital Petugas (Jika ada file sig_petugas.png di GitHub)
    path_ttd = cari_logo(f"sig_{petugas.lower()}")
    if path_ttd:
        # Penyesuaian Posisi TTD agar pas di atas nama
        # X disesuaikan dengan posisi nama petugas di kiri (37mm)
        # Y diturunkan sedikit agar tidak menempel pada judul (Y=y_sign + 2mm)
        # Ukuran TTD juga diperkecil sedikit agar tidak menumpuk (Tinggi/h=18mm)
        pdf.image(path_ttd, x=37, y=y_sign + 2, h=18)

    pdf.ln(25) # Jarak tanda tangan manual
    
    # Nama Petugas & Pasien
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(95, 8, f"( {clean(petugas)} )", align="C")
    pdf.cell(95, 8, "( ............................ )", align="C", ln=True)

    # --- OUTPUT SEBAGAI BYTES UNTUK STREAMLIT ---
    # Mengembalikan data PDF dalam bentuk bytes agar bisa dibaca download_button
    return bytes(pdf.output())
