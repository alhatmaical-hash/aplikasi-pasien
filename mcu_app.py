import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Professional MCU System", layout="wide")

# Custom CSS untuk tampilan profesional dan mobile-friendly
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .status-box { padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIKA (BACKEND) ---
def hitung_bmi(berat, tinggi):
    t_meter = tinggi / 100
    bmi = berat / (t_meter ** 2)
    if bmi < 18.5: return "Underweight", "Warning"
    elif 18.5 <= bmi < 25: return "Normal", "Success"
    elif 25 <= bmi < 30: return "Overweight", "Warning"
    else: return "Obesity", "Danger"

def tentukan_kelayakan(tensi_sistolik, gula_darah):
    # Logika otomatis sederhana untuk simulasi
    if tensi_sistolik > 160 or gula_darah > 200:
        return "TEMPORARY UNFIT", "Perlu pengobatan/stabilisasi kondisi sebelum bekerja."
    elif tensi_sistolik > 140:
        return "FIT WITH NOTE", "Hipertensi Grade 1, monitor rutin."
    else:
        return "FIT TO WORK", "Kondisi kesehatan memenuhi syarat."

# --- UI COMPONENT ---
def main():
    st.title("🏥 Sistem Informasi Pelayanan MCU")
    st.info("Modul: Pre-Employment & Annual Medical Check-Up")

    menu = ["Pendaftaran", "Pemeriksaan Fisik", "Hasil Lab & Penunjang", "Kesimpulan & Fit Status"]
    choice = st.sidebar.selectbox("Navigasi Alur MCU", menu)

    if choice == "Pendaftaran":
        st.subheader("📝 Registrasi Peserta")
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap / 姓名")
            nik = st.text_input("NIK / 身份证号码")
            tgl_lahir = st.date_input("Tanggal Lahir", min_value=datetime(1960, 1, 1))
        with col2:
            jenis_mcu = st.selectbox("Jenis Pelayanan", ["Pre-Employment", "Annual MCU", "Special MCU"])
            perusahaan = st.selectbox("Perusahaan", ["PT. HJF", "PT. KPS", "PT. OST", "PT. CKM"])
            dept = st.text_input("Departemen / Bagian")
        
        if st.button("Simpan Data Pendaftaran"):
            st.success(f"Data {nama} berhasil didaftarkan ke sistem.")

    elif choice == "Pemeriksaan Fisik":
        st.subheader("🩺 Pemeriksaan Vital Sign & Fisik")
        col1, col2, col3 = st.columns(3)
        with col1:
            tinggi = st.number_input("Tinggi Badan (cm)", value=170)
            berat = st.number_input("Berat Badan (kg)", value=70)
        with col2:
            sistolik = st.number_input("Sistolik (mmHg)", value=120)
            diastolik = st.number_input("Diastolik (mmHg)", value=80)
        with col3:
            suhu = st.number_input("Suhu (°C)", value=36.5)
            nadi = st.number_input("Nadi (x/menit)", value=80)

        bmi_label, status_color = hitung_bmi(berat, tinggi)
        st.metric("Body Mass Index (BMI)", bmi_label)

    elif choice == "Hasil Lab & Penunjang":
        st.subheader("🔬 Input Hasil Laboratorium")
        tab1, tab2 = st.tabs(["Hematologi", "Kimia Darah"])
        with tab1:
            hb = st.number_input("Hemoglobin (g/dL)", format="%.1f")
            leu = st.number_input("Leukosit (/uL)")
        with tab2:
            gds = st.number_input("Gula Darah Sewaktu (mg/dL)")
            chol = st.number_input("Kolesterol Total (mg/dL)")

    elif choice == "Kesimpulan & Fit Status":
        st.subheader("📋 Verifikasi Akhir & Kelayakan")
        
        # Simulasi data dari input sebelumnya (dalam real app diambil dari DB)
        tensi_val = st.number_input("Konfirmasi Tensi Sistolik Terakhir", value=120)
        gds_val = st.number_input("Konfirmasi Gula Darah Terakhir", value=110)
        
        status, catatan = tentukan_kelayakan(tensi_val, gds_val)
        
        st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 20px; border-left: 10px solid #1976d2;">
                <h3>Status Kelayakan: <b>{status}</b></h3>
                <p>Catatan Dokter: {catatan}</p>
            </div>
        """, unsafe_allow_html=True)

        st.text_area("Saran Medis Tambahan", placeholder="Contoh: Kurangi konsumsi garam dan olahraga teratur...")
        
        if st.button("Generate Laporan PDF (SKD)"):
            st.warning("Fungsi PDF Export memerlukan library fpdf. File siap diunduh.")

if __name__ == "__main__":
    main()
