from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # 1. Buat Kertas Putih Ukuran A4 (sekitar 2480x3508 px untuk 300 DPI atau lebih kecil untuk web)
    # Kita gunakan ukuran 800x1100 px agar ringan di Streamlit
    canvas = Image.new('RGB', (800, 1100), color='white')
    draw = ImageDraw.Draw(canvas)
    
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
        font_regular = ImageFont.truetype("arial.ttf", 16)
    except:
        font_bold = font_regular = ImageFont.load_default()

    # 2. Membuat Header (Garis dan Judul)
    draw.rectangle([20, 20, 780, 120], outline="black", width=2) # Kotak Logo/Header
    draw.text((300, 40), "FORMULIR PENDAFTARAN PASIEN", fill="black", font=font_bold)
    draw.text((330, 70), "KLINIK HARITA FERONICKEL OBI", fill="black", font=font_regular)
    
    # 3. Membuat Tabel Identitas Pasien
    y_start = 150
    headers = [
        ("NAMA", data.get('nama', '-')),
        ("TEMPAT LAHIR", data.get('tempat_lahir', '-')),
        ("PERUSAHAAN", data.get('perusahaan', '-')),
        ("NIK/ID", data.get('nik', '-')),
        ("DEPARTEMEN", data.get('departemen', '-')),
        ("JABATAN", data.get('jabatan', '-')),
        ("LOKASI KERJA", data.get('lokasi_kerja', '-'))
    ]

    for i, (label, value) in enumerate(headers):
        y_pos = y_start + (i * 40)
        # Gambar Kotak Baris
        draw.rectangle([20, y_pos, 780, y_pos + 40], outline="black", width=1)
        # Tulis Label
        draw.text((30, y_pos + 10), label, fill="black", font=font_bold)
        # Tulis Titik Dua dan Isi Data (Ambil dari Rekam Medis)
        draw.text((250, y_pos + 10), f":  {value}", fill="black", font=font_regular)

    # 4. Bagian Tanda Tangan
    y_ttd = y_pos + 100
    tgl_skrg = datetime.now().strftime("%d %B %Y")
    draw.text((550, y_ttd), f"Kawasi, {tgl_skrg}", fill="black", font=font_regular)
    
    draw.text((50, y_ttd + 40), "Petugas Penerimaan Pasien", fill="black", font=font_regular)
    draw.text((550, y_ttd + 40), "Pasien/Penanggung Jawab", fill="black", font=font_regular)

    # 5. Tempel Tanda Tangan Petugas secara Otomatis
    petugas_low = petugas.lower()
    if petugas_low == "deli": petugas_low = "ladeli"
    path_ttd = f"sig_{petugas_low}.png" # Menggunakan file yang sudah Anda upload

    if os.path.exists(path_ttd):
        sig_img = Image.open(path_ttd).convert("RGBA")
        sig_img = sig_img.resize((150, 80))
        canvas.paste(sig_img, (50, y_ttd + 70), sig_img)
    
    draw.text((50, y_ttd + 160), f"( {petugas} )", fill="black", font=font_bold)
    draw.text((550, y_ttd + 160), "( .................................... )", fill="black", font=font_regular)

    # 6. Simpan File
    filename = f"Form_{data.get('nama', 'Pasien')}.png"
    canvas.save(filename)
    return filename
