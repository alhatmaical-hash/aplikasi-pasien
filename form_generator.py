from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # Menggunakan fpdf2 untuk dukungan Unicode
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    
    # --- LOAD FONT UNICODE ---
    # Pastikan file .ttf ini ada di folder proyek Anda
    font_path = "msyh.ttf" # Ganti dengan font Mandarin yang Anda miliki
    if os.path.exists(font_path):
        pdf.add_font("Mandarin", "", font_path)
        pdf.add_font("MandarinB", "", font_path) # Gunakan file yang sama jika tidak ada versi Bold
        font_utama = "Mandarin"
        font_bold = "MandarinB"
    else:
        # Fallback jika font tidak ditemukan (akan error jika ada Mandarin)
        font_utama = "helvetica"
        font_bold = "helvetica"

    pdf.add_page()
    
    def clean(text):
        return str(text) if text else "-"

    # --- KOP & JUDUL BILINGUAL ---
    pdf.ln(34)
    pdf.set_font(font_bold, size=12)
    # Teks Mandarin sekarang aman digunakan dengan font Unicode
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN / 患者登记表", border=1, ln=True, align="C")
    
    pdf.set_font(font_bold, size=10)
    pdf.cell(190, 8, "No. Rekam Medis / 病历号 :             ", border=1, ln=True, align="R")

    # --- IDENTITAS PASIEN BILINGUAL ---
    pdf.set_font(font_bold, size=10)
    pdf.cell(190, 8, " IDENTITAS PASIEN / 患者身份 ( bagian ini harus lengkap / 这部分必须完整 )", border=1, ln=True)

    # Label Bilingual sesuai referensi gambar
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

    # --- SURAT PERNYATAAN ---
    pdf.ln(4)
    y_pernyataan = pdf.get_y()
    pdf.rect(10, y_pernyataan, 190, 80) 
    pdf.set_xy(12, y_pernyataan + 3)
    pdf.set_font(font_bold, size=10)
    pdf.cell(186, 6, "SURAT PERNYATAAN / 声明书", ln=True)
    pdf.set_font(font_utama, size=9)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")

    return bytes(pdf.output())
