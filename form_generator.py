from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # Menggunakan FPDF2 (versi yang mendukung Unicode)
    # Jika menggunakan fpdf standar, ganti ke 'fpdf2' via pip install fpdf2
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    
    # --- PENTING: MENAMBAHKAN FONT UNICODE ---
    # Ganti 'path/to/font.ttf' dengan lokasi file font Mandarin Anda
    try:
        pdf.add_font('UnicodeFont', '', 'msyh.ttf', uni=True)
        pdf.add_font('UnicodeFontB', '', 'msyhbd.ttf', uni=True) # Versi Bold
        font_utama = 'UnicodeFont'
        font_bold = 'UnicodeFontB'
    except:
        # Fallback jika font tidak ditemukan agar tidak crash
        font_utama = 'helvetica'
        font_bold = 'helvetica'

    pdf.add_page()
    
    def clean(text):
        if not text: return "-"
        return str(text)

    # --- KOP FORMULIR (Sesuai Struktur Sebelumnya) ---
    pdf.set_line_width(0.3)
    pdf.rect(10, 10, 90, 32) 
    
    # --- JUDUL BILINGUAL ---
    pdf.ln(34)
    pdf.set_line_width(0.5)
    
    # Gunakan font unicode yang sudah didaftarkan
    pdf.set_font(font_bold, size=11)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN / 患者登记表", border=1, ln=True, align="C")
    
    pdf.set_font(font_bold, size=10)
    pdf.cell(190, 8, "No. Rekam Medis / 病历号 :             ", border=1, ln=True, align="R")

    # --- IDENTITAS PASIEN BILINGUAL ---
    pdf.set_font(font_bold, size=10)
    pdf.cell(190, 8, " IDENTITAS PASIEN / 患者身份 ( bagian ini harus lengkap / 这部分必须完整 )", border=1, ln=True)

    labels = [
        ["NAMA LENGKAP / 姓名", 'nama'], 
        ["TEMPAT LAHIR / 出生地点", 'tempat_lahir'], 
        ["TANGGAL LAHIR / 出生日期", 'tgl_lahir'], 
        ["JENIS KELAMIN / 性别", 'gender'], 
        ["AGAMA / 宗教", 'agama'], 
        ["NO HP (WA) / 手机号码", 'no_hp'], 
        ["NIK / ID CARD / 身份证号", 'nik'], 
        ["PERUSAHAAN / 公司", 'perusahaan'], 
        ["DEPARTEMEN / 部门", 'departemen'], 
        ["JABATAN / 职位", 'jabatan'], 
        ["MES / NO KAMAR / 宿舍/房间号", 'blok_mes'], 
        ["RIWAYAT ALERGI / 过敏史", 'alergi'], 
        ["GOL. DARAH / 血型", 'gol_darah']
    ]

    for label_text, key in labels:
        pdf.set_font(font_bold, size=9)
        pdf.cell(75, 7.5, label_text, border=1) 
        pdf.set_font(font_utama, size=10)
        pdf.cell(115, 7.5, f": {clean(data.get(key))}", border=1, ln=True)

    # --- SURAT PERNYATAAN BILINGUAL ---
    pdf.ln(4)
    y_pernyataan = pdf.get_y()
    pdf.rect(10, y_pernyataan, 190, 75) 

    pdf.set_xy(12, y_pernyataan + 3)
    pdf.set_font(font_bold, size=10)
    pdf.cell(186, 6, "SURAT PERNYATAAN / 声明书", ln=True)
    
    # Isi pernyataan tetap Indonesia sesuai referensi terakhir
    pdf.set_font(font_utama, size=9)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")

    return bytes(pdf.output())
