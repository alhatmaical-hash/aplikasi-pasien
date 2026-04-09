from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # Menggunakan fpdf2 untuk dukungan Unicode
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    
    # --- LOAD FONT MANDARIN ---
    # Gunakan font 'msyh.ttf' (Microsoft YaHei) atau font unicode lain yang Anda miliki
    font_file = "msyh.ttf" 
    
    if os.path.exists(font_file):
        # Mendaftarkan font ke fpdf2
        pdf.add_font("MandarinFont", "", font_file)
        pdf.add_font("MandarinFontB", "", font_file) # Bisa gunakan file sama jika tidak ada versi bold khusus
        f_reg = "MandarinFont"
        f_bold = "MandarinFontB"
    else:
        # Jika font tidak ditemukan, aplikasi akan tetap berjalan tapi Mandarin mungkin tidak muncul
        f_reg = "helvetica"
        f_bold = "helvetica"

    pdf.add_page()
    
    def clean(text):
        return str(text) if text else "-"

    # --- KOP FORMULIR (Sesuai Logo Harita & HJF) ---
    pdf.set_line_width(0.3)
    pdf.rect(10, 10, 90, 32) 
    
    # --- JUDUL BILINGUAL (DIBUAT TERPISAH) ---
    pdf.ln(34)
    pdf.set_line_width(0.5)
    
    # 1. Baris Judul
    pdf.set_font(f_bold, size=11)
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN / 患者登记表", border=1, ln=True, align="C")
    
    # 2. Baris No Rekam Medis (Top Align & Right)
    pdf.set_font(f_bold, size=10)
    pdf.cell(190, 8, "No. Rekam Medis / 病历号 :             ", border=1, ln=True, align="R")

    # --- IDENTITAS PASIEN BILINGUAL ---
    pdf.set_font(f_bold, size=10)
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
        pdf.set_font(f_bold, size=9)
        pdf.cell(70, 7.5, label_text, border=1) 
        pdf.set_font(f_reg, size=10)
        # Menghilangkan teks KHFO-000000 di dalam data jika ada
        pdf.cell(120, 7.5, f": {clean(data.get(key))}", border=1, ln=True)

    # --- SURAT PERNYATAAN & TTD (Garis Bawah) ---
    pdf.ln(4)
    y_pernyataan = pdf.get_y()
    pdf.rect(10, y_pernyataan, 190, 80) # Kotak diperpanjang ke bawah

    pdf.set_xy(12, y_pernyataan + 3)
    pdf.set_font(f_bold, size=10)
    pdf.cell(186, 6, "SURAT PERNYATAAN / 声明书", ln=True)
    
    pdf.set_font(f_reg, size=9)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")

    pdf.ln(10)
    pdf.cell(186, 5, f"Kawasi, {datetime.now().strftime('%d %B %Y')}", ln=True, align="R")
    
    pdf.set_x(12)
    pdf.set_font(f_bold, size=9)
    pdf.cell(93, 5, "Petugas Penerimaan / 接待人员", align="C")
    pdf.cell(93, 5, "Pasien / Keluarga / 患者/家属", align="C", ln=True)

    pdf.ln(35) # Spasi tanda tangan
    
    # Nama Petugas & Pasien di atas garis
    pdf.set_x(12)
    pdf.cell(93, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(93, 5, "( ............................ )", align="C", ln=True)
    
    # Garis penutup paling bawah
    pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)

    return bytes(pdf.output())
