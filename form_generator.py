from PIL import Image, ImageDraw, ImageFont

def buat_formulir_otomatis(data_pasien, nama_petugas):
    # 1. Buka template formulir (image_81e01c.png)
    # Kita asumsikan template sudah ada di folder aplikasi
    try:
        img = Image.open("template_form.png")
        draw = ImageDraw.Draw(img)
        
        # 2. Tulis data pasien ke formulir
        # Angka di bawah adalah koordinat (bisa kamu sesuaikan nanti)
        draw.text((250, 200), f": {data_pasien['nama']}", fill="black")
        draw.text((250, 230), f": {data_pasien['tempat_lahir']}", fill="black")
        draw.text((250, 420), f": {data_pasien['perusahaan']}", fill="black")

        # 3. Tempelkan Tanda Tangan Petugas
        path_ttd = f"sig_{nama_petugas.lower()}.png" # Contoh: sig_taufik.png
        ttd = Image.open(path_ttd).convert("RGBA")
        ttd = ttd.resize((150, 100)) # Kecilkan ukuran tanda tangan
        
        # Tempel di area tanda tangan petugas
        img.paste(ttd, (150, 850), ttd)
        
        # 4. Simpan hasilnya
        nama_file_hasil = f"Form_{data_pasien['nama']}.png"
        img.save(nama_file_hasil)
        return nama_file_hasil
        
    except Exception as e:
        return f"Gagal membuat form: {e}"
