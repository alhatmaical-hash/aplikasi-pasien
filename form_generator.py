from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # Gunakan font yang mendukung karakter luas jika tersedia, 
    # namun secara default fpdf menggunakan latin-1. 
    # Untuk Mandarin murni dibutuhkan font Unicode (.ttf).
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- KOP FORMULIR (Sesuai Referensi Sebelumnya) ---
    pdf.set_line_width(0.3)
    margin_x, kop_y = 10, 10
    pdf.rect(margin_x, kop_y, 90, 32) 
    
    # --- BAGIAN JUDUL & NO REKAM MEDIS BILINGUAL ---
    pdf.ln(34) # Jarak setelah Kop
    pdf.set_line_width(0.5)
    
    # 1. Baris Judul: Indonesia & Mandarin
    pdf.set_font("helvetica", "B", 11)
    # Menambahkan teks Mandarin secara manual agar layout mirip referensi
    pdf.cell(190, 10, "FORMULIR PENDAFTARAN PASIEN / 患者登记表", border=1, ln=True, align="C")
    
    # 2. Baris No Rekam Medis: Indonesia & Mandarin
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, "No. Rekam Medis / 病历号 :             ", border=1, ln=True, align="R")

    # --- IDENTITAS PASIEN BILINGUAL ---
    pdf.set_font("helvetica", "B", 10)
    # Teks Sub-judul Bilingual
    pdf.cell(190, 8, " IDENTITAS PASIEN / 患者身份 ( bagian ini harus lengkap / 这部分必须完整 )", border=1, ln=True)

    # Definisi Label dengan Bahasa Mandarin
    labels = [
        "NAMA LENGKAP / 姓名", 
        "TEMPAT LAHIR / 出生地点", 
        "TANGGAL LAHIR / 出生日期", 
        "JENIS KELAMIN / 性别", 
        "AGAMA / 宗教", 
        "NO HP (WA) / 手机号码", 
        "NIK / ID CARD / 身份证号", 
        "PERUSAHAAN / 公司", 
        "DEPARTEMEN / 部门", 
        "JABATAN / 职位", 
        "MES / NO KAMAR / 宿舍/房间号", 
        "RIWAYAT ALERGI / 过敏史", 
        "GOL. DARAH / 血型"
    ]
    
    val = [
        clean(data.get('nama')), clean(data.get('tempat_lahir')), clean(data.get('tgl_lahir')), 
        clean(data.get('gender')), clean(data.get('agama')), clean(data.get('no_hp')), 
        clean(data.get('nik')), clean(data.get('perusahaan')), clean(data.get('departemen')), 
        clean(data.get('jabatan')), clean(data.get('blok_mes')), clean(data.get('alergi')), 
        clean(data.get('gol_darah'))
    ]

    pdf.set_font("helvetica", "", 9) # Ukuran font sedikit dikecilkan agar teks bilingual muat
    for i in range(len(labels)):
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(70, 7.5, labels[i], border=1) # Lebar label ditambah jadi 70mm
        pdf.set_font("helvetica", "", 10)
        pdf.cell(120, 7.5, f": {val[i]}", border=1, ln=True)

    # --- AREA SURAT PERNYATAAN ---
    pdf.ln(4)
    y_pernyataan = pdf.get_y()
    pdf.rect(10, y_pernyataan, 190, 75) 

    pdf.set_xy(12, y_pernyataan + 3)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(186, 6, "SURAT PERNYATAAN / 声明书", ln=True)
    pdf.set_font("helvetica", "", 9)
    pdf.set_x(12)
    pdf.multi_cell(186, 5, "Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")

    # --- TANDA TANGAN ---
    pdf.ln(10)
    pdf.cell(186, 5, f"Kawasi, {datetime.now().strftime('%d %B %Y')}", ln=True, align="R")
    
    pdf.set_font("helvetica", "B", 9)
    pdf.set_x(12)
    pdf.cell(93, 5, "Petugas Penerimaan / 接待人员", align="C")
    pdf.cell(93, 5, "Pasien / Keluarga / 患者/家属", align="C", ln=True)

    # TTD logic ... (seperti sebelumnya)
    pdf.ln(30)
    pdf.set_x(12)
    pdf.cell(93, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(93, 5, "( ............................ )", align="C", ln=True)
    
    y_akhir = pdf.get_y() + 1
    pdf.line(10, y_akhir, 200, y_akhir)

    return bytes(pdf.output())
