from PIL import Image, ImageDraw, ImageFont

def buat_formulir_otomatis(data_pasien, nama_petugas):
    try:
        # 1. Buka template (pastikan file ini ada di GitHub kamu)
        img = Image.open("template_form.png")
        draw = ImageDraw.Draw(img)
        
        # Sumbu X (jarak dari kiri) biasanya sama untuk semua titik dua (:)
        x_titik = 530 
        
        # 2. Tulis data ke formulir (Sumbu Y/Tinggi diatur agar pas di kotak)
        draw.text((x_titik, 255), f": {data_pasien['nama']}", fill="black")
        draw.text((x_titik, 285), f": {data_pasien['tempat_lahir']}", fill="black")
        draw.text((x_titik, 445), f": {data_pasien['nik']}", fill="black")
        draw.text((x_titik, 475), f": {data_pasien['perusahaan']}", fill="black")
        draw.text((x_titik, 505), f": {data_pasien['departemen']}", fill="black")
        draw.text((x_titik, 535), f": {data_pasien['jabatan']}", fill="black")
        draw.text((x_titik, 565), f": {data_pasien['blok_mes']}", fill="black")
        draw.text((x_titik, 655), f": {data_pasien['lokasi_kerja']}", fill="black")

        # 3. Tempelkan Tanda Tangan Petugas
        # Kode akan mencari file seperti sig_taufik.png atau sig_wawan.png
        path_ttd = f"sig_{nama_petugas.lower()}.png" 
        ttd = Image.open(path_ttd).convert("RGBA")
        ttd = ttd.resize((180, 110)) # Ukuran disesuaikan agar pas di kotak TTD
        
        # Tempel di area Petugas Penerimaan Pasien (Koordinat X=200, Y=880)
        img.paste(ttd, (200, 880), ttd)
        
        # 4. Simpan hasil sementara
        nama_file_hasil = f"Form_Pendaftaran_{data_pasien['nama'].replace(' ', '_')}.png"
        img.save(nama_file_hasil)
        return nama_file_hasil
        
    except Exception as e:
        return f"Gagal membuat form: {e}"
