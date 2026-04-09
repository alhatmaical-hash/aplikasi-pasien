from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

# Definisi Warna
WARNA_HITAM = (0, 0, 0)
WARNA_PUTIH = (255, 255, 255)

def buat_formulir_otomatis(data, petugas):
    # --- LANGKAH 1: Buat Kertas Putih Ukuran A4 ---
    # Ukuran A4 standar 300 DPI adalah 2480x3508 pixel
    width, height = 2480, 3508
    template = Image.new('RGB', (width, height), color=WARNA_PUTIH)
    draw = ImageDraw.Draw(template)
    
    # --- LANGKAH 2: Atur Font Times New Roman ---
    try:
        # Mencoba memanggil font sistem. Jika error, gunakan font default
        # Pastikan file arial.ttf/times.ttf ada di sistem server (biasanya ada)
        path_font_bold = "timesbd.ttf"  # Times New Roman Bold
        path_font_reg = "times.ttf"   # Times New Roman Regular
        
        # Peringatan: Streamlit Cloud terkadang tidak memiliki Times New Roman default.
        # Jika error, kode akan menggunakan Arial Bold yang ukurannya mirip.
        if not os.path.exists(path_font_bold): path_font_bold = "arialbd.ttf"
        if not os.path.exists(path_font_reg): path_font_reg = "arial.ttf"

        # Ukuran 18pt Bold untuk Kop, Ukuran 12pt Regular untuk Isi
        font_kop = ImageFont.truetype(path_font_bold, 18 * 4) # Perlu dikali 4 agar ukuran px pas
        font_isi = ImageFont.truetype(path_font_reg, 12 * 4) 
    except:
        font_kop = font_isi = ImageFont.load_default()

    # --- LANGKAH 3: Membuat Kop Formulir ---
    margin_kop = 80
    tinggi_kop = 400
    kotak_kop = [margin_kop, 80, width - margin_kop, tinggi_kop]
    draw.rectangle(kotak_kop, outline=WARNA_HITAM, width=4)
    
    # Teks Kop (Center Aligned)
    text_kop1 = "FORMULIR PENDAFTARAN PASIEN"
    text_kop2 = "KLINIK HARITA FERONICKEL OBI"
    
    # Hitung posisi X agar center
    w1 = draw.textlength(text_kop1, font=font_kop)
    w2 = draw.textlength(text_kop2, font=font_kop)
    
    draw.text(((width - w1)/2, tinggi_kop/2 - 50), text_kop1, fill=WARNA_HITAM, font=font_kop)
    draw.text(((width - w2)/2, tinggi_kop/2 + 30), text_kop2, fill=WARNA_HITAM, font=font_kop)

    # --- LANGKAH 4: Menempel Ketiga Logo ---
    y_logo = tinggi_kop/2 - 60
    
    # Logo 1: Harita Group (Kiri)
    if os.path.exists("image_8.png"):
        logo8 = Image.open("image_8.png").convert("RGBA")
        logo8 = logo8.resize((220, 160))
        template.paste(logo8, (margin_kop + 50, int(y_logo)), logo8)

    # Logo 2: HJF (Center Kiri)
    if os.path.exists("image_6.png"):
        logo6 = Image.open("image_6.png").convert("RGBA")
        logo6 = logo6.resize((200, 160))
        template.paste(logo6, (margin_kop + 320, int(y_logo)), logo6)

    # Logo 3: SMK3 (Kanan - Sesuai Instruksi Baru)
    if os.path.exists("image_7.png"):
        logo7 = Image.open("image_7.png").convert("RGBA")
        logo7 = logo7.resize((220, 160))
        template.paste(logo7, (width - margin_kop - 270, int(y_logo)), logo7)

    # --- LANGKAH 5: Membuat Tabel Data Pasien (14 Kolom) ---
    y_start_table = tinggi_kop + 100
    tinggi_baris = 120
    x_split_label = 20 # Jarak label dari garis kiri
    x_split_data = 800  # Posisi Titik Dua dan Isi Data
    
    headers = [
        "NAMA LENGKAP",
        "TEMPAT LAHIR",
        "TANGGAL LAHIR (DD/MM/YYYY)",
        "JENIS KELAMIN",
        "AGAMA",
        "NO HP (WHATSAPP)",
        "NIK / ID CARD",
        "PERUSAHAAN / COMPANY",
        "DEPARTEMEN",
        "JABATAN",
        "MES DAN NO KAMAR",
        "RIWAYAT ALERGI",
        "AREA LOKASI BEKERJA SPESIFIK",
        "GOLONGAN DARAH"
    ]
    
    # Mapping Data Pasien dari database ke Formulir
    isi_data = [
        data.get('nama', '-'),
        data.get('tempat_lahir', '-'),
        data.get('tgl_lahir', '-'),
        data.get('gender', '-'),
        data.get('agama', '-'),
        data.get('no_hp', '-'),
        data.get('nik', '-'),
        data.get('perusahaan', '-'),
        data.get('departemen', '-'),
        data.get('jabatan', '-'),
        data.get('blok_mes', '-'),
        data.get('alergi', '-'),
        data.get('lokasi_kerja', '-'),
        data.get('gol_darah', '-')
    ]

    for i, label in enumerate(headers):
        y_pos = y_start_table + (i * tinggi_baris)
        
        # Gambar Kotak Baris
        draw.rectangle([margin_kop, y_pos, width - margin_kop, y_pos + tinggi_baris], outline=WARNA_HITAM, width=2)
        
        # Tulis Label (X+20)
        draw.text((margin_kop + x_split_label, y_pos + tinggi_baris/2 - 30), label, fill=WARNA_HITAM, font=font_isi)
        
        # Tulis Titik Dua dan Isi Data (X+800)
        draw.text((margin_kop + x_split_data, y_pos + tinggi_baris/2 - 30), f":  {isi_data[i]}", fill=WARNA_HITAM, font=font_isi)

    # --- LANGKAH 6: Membuat Surat Pernyataan ---
    y_pernyataan = y_pos + tinggi_baris + 150
    header_pernyataan = "SURAT PERNYATAAN"
    w_per = draw.textlength(header_pernyataan, font=font_isi)
    # Gunakan text_header = font_isi agar ukuran sama, tapi tambahkan manual bold di header
    draw.text(((width - w_per)/2, y_pernyataan), header_pernyataan, fill=WARNA_HITAM, font=font_kop)
    
    pernyataan_isi = ("Dengan ini saya menyatakan setuju untuk di lakukan pemeriksaan dan tindakan yang diperlukan "
                    "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    
    # Gunakan fungsi text_wrap jika kalimat terlalu panjang (optional)
    draw.text((margin_kop + 50, y_pernyataan + 120), pernyataan_isi, fill=WARNA_HITAM, font=font_isi)

    # --- LANGKAH 7: Bagian Tanda Tangan ---
    y_ttd = y_pernyataan + 350
    tgl_skrg = datetime.now().strftime("%d %B %Y")
    
    # Tanggal Otomatis di Kanan
    text_tgl = f"Kawasi, {tgl_skrg}"
    w_tgl = draw.textlength(text_tgl, font=font_isi)
    draw.text((width - margin_kop - w_tgl - 100, y_ttd), text_tgl, fill=WARNA_HITAM, font=font_isi)
    
    # Header Petugas/Pasien
    draw.text((margin_kop + 150, y_ttd + 80), "Petugas Penerimaan Pasien", fill=WARNA_HITAM, font=font_isi)
    draw.text((width - margin_kop - w_tgl - 200, y_ttd + 80), "Pasien/Penanggung Jawab", fill=WARNA_HITAM, font=font_isi)

    # --- LANGKAH 8: Tempel Tanda Tangan Petugas secara Otomatis ---
    petugas_low = petugas.lower()
    if petugas_low == "deli": petugas_low = "ladeli"
    path_ttd = f"sig_{petugas_low}.png" # Menggunakan file yang sudah Anda upload

    if os.path.exists(path_ttd):
        sig_img = Image.open(path_ttd).convert("RGBA")
        sig_img = sig_img.resize((250, 160)) # Ukuran disesuaikan A4
        template.paste(sig_img, (margin_kop + 180, y_ttd + 160), sig_img)
    
    # Nama Petugas/Pasien
    draw.text((margin_kop + 150, y_ttd + 350), f"( {petugas} )", fill=WARNA_HITAM, font=font_isi)
    draw.text((width - margin_kop - w_tgl - 200, y_ttd + 350), "( .................................... )", fill=WARNA_HITAM, font=font_isi)

    # --- LANGKAH 9: Simpan File ---
    nama_bersih = data.get('nama', 'Pasien').replace(' ', '_')
    nama_file_hasil = f"Form_Pendaftaran_{nama_bersih}.png"
    template.save(nama_file_hasil)
    return nama_file_hasil
