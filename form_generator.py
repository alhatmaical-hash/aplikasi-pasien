from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

WARNA_HITAM = (0, 0, 0)
WARNA_PUTIH = (255, 255, 255)

def buat_formulir_otomatis(data, petugas):
    # --- 1. Kertas A4 (300 DPI) ---
    width, height = 2480, 3508
    template = Image.new('RGB', (width, height), color=WARNA_PUTIH)
    draw = ImageDraw.Draw(template)
    
    # --- 2. Pengaturan Font (Skala Besar) ---
    try:
        path_font_bold = "timesbd.ttf" if os.path.exists("timesbd.ttf") else "arialbd.ttf"
        path_font_reg = "times.ttf" if os.path.exists("times.ttf") else "arial.ttf"
        
        font_kop = ImageFont.truetype(path_font_bold, 80)   # Sangat Besar untuk Kop
        font_isi_bold = ImageFont.truetype(path_font_bold, 50) # Untuk Label
        font_isi = ImageFont.truetype(path_font_reg, 50)      # Untuk Data
        font_pernyataan = ImageFont.truetype(path_font_reg, 45)
    except:
        font_kop = font_isi = ImageFont.load_default()

    # --- 3. Kop Formulir ---
    margin = 150
    draw.rectangle([margin, 100, width - margin, 500], outline=WARNA_HITAM, width=8)
    
    t1, t2 = "FORMULIR PENDAFTARAN PASIEN", "KLINIK HARITA FERONICKEL OBI"
    draw.text(((width - draw.textlength(t1, font=font_kop))/2, 180), t1, fill=WARNA_HITAM, font=font_kop)
    draw.text(((width - draw.textlength(t2, font=font_kop))/2, 300), t2, fill=WARNA_HITAM, font=font_kop)

    # --- 4. Penempelan Logo (Ukuran Besar) ---
    def paste_logo(path, pos, size=(350, 250)):
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            template.paste(img, pos, img)

    paste_logo("harita.jpg", (margin + 40, 150))    # Kiri 1
    paste_logo("hjf.jpg", (margin + 420, 150))      # Kiri 2
    paste_logo("smk3.jpg", (width - margin - 380, 150)) # Kanan

    # --- 5. Tabel Data Pasien ---
    y_table = 600
    baris_h = 140
    col_split = 900 # Jarak label ke titik dua
    
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

    for i in range(len(labels)):
        curr_y = y_table + (i * baris_h)
        draw.rectangle([margin, curr_y, width - margin, curr_y + baris_h], outline=WARNA_HITAM, width=4)
        draw.text((margin + 40, curr_y + 40), labels[i], fill=WARNA_HITAM, font=font_isi_bold)
        draw.text((margin + col_split, curr_y + 40), f":  {val[i]}", fill=WARNA_HITAM, font=font_isi)

    # --- 6. Pernyataan & Tanda Tangan ---
    y_sign = curr_y + baris_h + 150
    p_txt = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan\n"
             "dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    draw.text((margin + 40, y_sign), "SURAT PERNYATAAN:", fill=WARNA_HITAM, font=font_isi_bold)
    draw.text((margin + 40, y_sign + 80), p_txt, fill=WARNA_HITAM, font=font_pernyataan)

    # Tanda Tangan
    y_bottom = y_sign + 450
    tgl_str = f"Kawasi, {datetime.now().strftime('%d %B %Y')}"
    draw.text((width - margin - 600, y_bottom), tgl_str, fill=WARNA_HITAM, font=font_isi)
    
    draw.text((margin + 100, y_bottom + 100), "Petugas Penerimaan,", fill=WARNA_HITAM, font=font_isi)
    draw.text((width - margin - 600, y_bottom + 100), "Pasien / Keluarga,", fill=WARNA_HITAM, font=font_isi)

    # TTD Petugas Otomatis
    path_ttd = f"sig_{petugas.lower()}.png"
    if os.path.exists(path_ttd):
        ttd = Image.open(path_ttd).convert("RGBA").resize((400, 250))
        template.paste(ttd, (margin + 100, y_bottom + 200), ttd)

    draw.text((margin + 100, y_bottom + 450), f"( {petugas} )", fill=WARNA_HITAM, font=font_isi_bold)
    draw.text((width - margin - 600, y_bottom + 450), "( ............................ )", fill=WARNA_HITAM, font=font_isi)

    fname = f"Form_{data.get('nama','pasien').replace(' ','_')}.png"
    template.save(fname)
    return fname
