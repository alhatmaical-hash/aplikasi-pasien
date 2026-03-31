import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Pendaftaran Pasien Online", page_icon="🏥")

st.title("🏥 Pendaftaran Pasien Online")
st.write("Silakan isi formulir di bawah ini untuk pendaftaran.")

with st.form("main_form"):
    nama = st.text_input("Nama Lengkap")
    tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1940, 1, 1))
    poli = st.selectbox("Poli Tujuan", ["Umum", "Gigi", "Anak", "Penyakit Dalam"])
    wa = st.text_input("Nomor WhatsApp (Aktif)")
    keluhan = st.text_area("Keluhan Utama")
    
    submit = st.form_submit_button("Daftar Sekarang")

if submit:
    if nama and wa:
        st.success(f"Terima kasih {nama}! Pendaftaran Anda telah kami terima.")
        st.info("Admin kami akan segera menghubungi Anda melalui WhatsApp.")
        # Link otomatis ke WA Admin (Ganti nomor di bawah dengan nomormu)
        nomor_admin = "628123456789" 
        pesan = f"Halo Admin, saya {nama} ingin konfirmasi pendaftaran Poli {poli}."
        st.markdown(f"[Klik di sini untuk Konfirmasi via WhatsApp](https://wa.me/{nomor_admin}?text={pesan.replace(' ', '%20')})")
    else:
        st.error("Mohon isi Nama dan Nomor WhatsApp!")
