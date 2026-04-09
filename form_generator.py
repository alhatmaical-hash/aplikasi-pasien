from fpdf import FPDF
import os
from datetime import datetime

def buat_formulir_otomatis(data, petugas):
    # Fungsi pembantu untuk membersihkan teks agar tidak error PDF
    def clean(text):
        if not text: return "-"
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # Inisialisasi PDF (A4)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- BAGIAN KOP SURAT ---
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(190, 7, "FORMULIR PENDAFTARAN PASIEN", ln=True, align="C")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(190, 5, "Klinik Pratama - PT. Jaya Feronikel", ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, 25, 200, 25)

    # --- TABEL IDENTITAS PASIEN ---
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 7, "DATA PRIBADI / 个人资料", ln=True)
    
    pdf.set_font("helvetica", "", 10)
    # List data untuk looping tabel agar rapi
    items = [
        ("NAMA LENGKAP", data.get('nama')),
        ("NIK / ID CARD", data.get('nik')),
        ("TEMPAT LAHIR", data.get('tempat_lahir')),
        ("TANGGAL LAHIR", data.get('tgl_lahir')),
        ("JENIS KELAMIN", data.get('gender')),
        ("AGAMA", data.get('agama')),
        ("NO HP (WA)", data.get('no_hp')),
        ("PERUSAHAAN", data.get('perusahaan')),
        ("DEPARTEMEN", data.get('departemen')),
        ("JABATAN", data.get('jabatan')),
        ("MES / NO KAMAR", data.get('blok_mes')),
        ("RIWAYAT ALERGI", data.get('alergi')),
        ("GOL. DARAH", data.get('gol_darah'))
    ]

    for label, value in items:
        pdf.cell(50, 7, f"{label}", border=1)
        pdf.cell(140, 7, f": {clean(value)}", border=1, ln=True)

    # --- SURAT PERNYATAAN ---
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 7, "SURAT PERNYATAAN / 声明书", ln=True)
    pdf.set_font("helvetica", "", 9)
    pernyataan = ("Dengan ini saya menyatakan setuju untuk dilakukan pemeriksaan dan tindakan "
                  "yang diperlukan dalam upaya kesembuhan/keselamatan jiwa saya/pasien tersebut.")
    pdf.multi_cell(190, 5, pernyataan, border=1)

    # --- AREA TANDA TANGAN ---
    pdf.ln(10)
    pdf.set_font("helvetica", "", 10)
    # Tanggal di kanan
    pdf.cell(186, 5, f"Kawasi, {datetime.now().strftime('%d %B %Y')}", ln=True, align="R")
    
    # 1. Tentukan Posisi Y (PENTING: Agar tidak error 'is not defined')
    y_ttd_label = pdf.get_y() 
    
    # 2. Cetak Label TTD
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 5, "Petugas Penerimaan", align="C")
    pdf.cell(95, 5, "Pasien / Keluarga", align="C", ln=True)

    # 3. Logika Menempelkan Gambar Tanda Tangan
    # Mencari file berdasarkan nama petugas (kecil semua .png)
    file_petugas = f"{str(petugas).lower()}.png" 
    
    # TTD Petugas (Lokasi x=40 adalah di bawah kolom Petugas Penerimaan)
    if os.path.exists(file_petugas):
        pdf.image(file_petugas, x=40, y=y_ttd_label + 7, h=15)
    
    # 4. Beri Jarak untuk Nama Terang
    pdf.ln(20) 
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 5, f"( {clean(petugas).upper()} )", align="C")
    pdf.cell(95, 5, f"( {clean(data.get('nama')).upper()} )", align="C", ln=True)

    # Kembalikan file dalam bentuk bytes untuk di-download Streamlit
    return bytes(pdf.output())
