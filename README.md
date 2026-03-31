import streamlit as st
import pandas as pd
from datetime import date

# Konfigurasi halaman agar terlihat profesional
st.set_page_config(page_title="Pendaftaran Klinik", page_icon="🏥")

def main():
    st.title("🏥 Sistem Pendaftaran Pasien")
    st.write("Silakan lengkapi data di bawah ini untuk mendapatkan nomor antrean.")
    
    # Membuat pembatas garis
    st.divider()

    with st.form("form_pasien", clear_on_submit=True):
        nama = st.text_input("Nama Lengkap Pasien")
        
        col1, col2 = st.columns(2)
        with col1:
            tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1940, 1, 1))
            gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
        with col2:
            poli = st.selectbox("Poli Tujuan", ["Umum", "Gigi", "Anak", "Kesehatan Ibu"])
            whatsapp = st.text_input("Nomor WhatsApp (Aktif)")
            
        keluhan = st.text_area("Keluhan atau Alasan Kunjungan")
        
        submit = st.form_submit_button("Daftarkan Sekarang")

    if submit:
        if nama and whatsapp:
            st.success(f"Pendaftaran Berhasil! Data pasien {nama} telah tersimpan.")
            st.balloons()
            
            # Membuat tombol otomatis ke WhatsApp Admin
            # Ganti nomor di bawah ini dengan nomor WA klinikmu (gunakan format 62)
            no_admin = "628123456789" 
            pesan_wa = f"Halo Admin, saya {nama} baru saja mendaftar di website untuk Poli {poli}. Mohon info nomor antreannya."
            url_wa = f"https://wa.me/{no_admin}?text={pesan_wa.replace(' ', '%20')}"
            
            st.markdown(f'### [👉 Klik di Sini untuk Konfirmasi via WhatsApp]({url_wa})')
        else:
            st.error("Gagal: Nama dan Nomor WhatsApp wajib diisi!")

if __name__ == "__main__":
    main()
