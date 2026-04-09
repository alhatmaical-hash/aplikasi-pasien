from PIL import Image, ImageDraw, ImageFont
import os

def buat_formulir_otomatis(data, petugas):
    # 1. Buka Template
    template = Image.open('template_form.png')
    draw = ImageDraw.Draw(template)
    
    # 2. Atur Font (Pastikan file arial.ttf tersedia atau gunakan default)
    try:
        font_data = ImageFont.truetype("arial.ttf", 22)  # Ukuran untuk isi data
        font_header = ImageFont.truetype("arial.ttf", 18) # Ukuran sedikit kecil jika perlu
    except:
        font_data = ImageFont.load_default()

    # 3. Masukkan Data Pasien ke Koordinat (X, Y)
    # Anda perlu mencoba (trial and error) angka ini agar pas di kotak
    draw.text((450, 265), data['nama'], fill="black", font=font_data)
    draw.text((450, 305), data['tempat_lahir'], fill="black", font=font_data)
    draw.text((450, 425), data['perusahaan'], fill="black", font=font_data)
    draw.text((450, 465), data['departemen'], fill="black", font=font_data)
    draw.text((450, 505), data['jabatan'], fill="black", font=font_data)
    draw.text((450, 545), data['blok_mes'], fill="black", font=font_data)
    draw.text((450, 625), data['lokasi_kerja'], fill="black", font=font_data)
    
    # 4. Tambahkan Tanggal Otomatis di bawah Surat Pernyataan
    from datetime import datetime
    tgl_sekarang = datetime.now().strftime("%d %B %Y")
    draw.text((800, 780), f"Kawasi, {tgl_sekarang}", fill="black", font=font_data)

    # 5. Tempel Tanda Tangan Petugas
    petugas_low = petugas.lower()
    if petugas_low == "deli": petugas_low = "ladeli"
    
    path_ttd = f"sig_{petugas_low}.png"
    if os.path.exists(path_ttd):
        signature = Image.open(path_ttd).convert("RGBA")
        # Perkecil ukuran tanda tangan agar muat di kotak (misal: 150x100)
        signature = signature.resize((150, 100)) 
        # Tempel di area Petugas Penerimaan Pasien (Koordinat X, Y)
        template.paste(signature, (180, 850), signature)

    # 6. Simpan Hasil
    nama_file_hasil = f"Form_Pendaftaran_{data['nama'].replace(' ', '_')}.png"
    template.save(nama_file_hasil)
    return nama_file_hasil
