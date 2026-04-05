import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import sqlite3
import hashlib
import datetime

# 1. Kunci berdasarkan Tanggal (Expired Date)
deadline = datetime.date(2026, 4, 28) # Setel tanggal kadaluarsa
if datetime.date.today() > deadline:
    st.error("Masa berlaku aplikasi telah habis. Silakan hubungi pembuat (Nama Kamu).")
    st.stop()

# 2. Kunci berdasarkan Password Sederhana
password_akses = "Rahasia123"
user_input = st.sidebar.text_input("Masukkan Kode Aktivasi", type="password")

if user_input != password_akses:
    st.info("Silakan masukkan kode aktivasi di sidebar untuk menggunakan aplikasi.")
    st.stop()

def create_user_table():
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    # Tambahkan admin default jika belum ada
    # Password di-hash (misal: 'admin123') agar aman
    hashed_pw = hashlib.sha256(str.encode('admin123')).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
    conn.commit()
    conn.close()
create_user_table()
def login_user(username, password):
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(str.encode(password)).hexdigest()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, hashed_pw))
    data = c.fetchone()
    conn.close()
    return data

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login Klinik Apps")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        result = login_user(user, pw)
        if result:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user
            st.session_state['role'] = result[2] # Simpan role (admin/user)
            st.rerun()
        else:
            st.error("Username atau Password salah")
    st.stop() # Stop aplikasi jika belum login

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps - Barber Johnson", layout="wide")
if st.session_state['role'] == 'admin':
    with st.expander("🛠️ Menu Admin: Tambah User Baru"):
        new_user = st.text_input("Username Baru")
        new_pw = st.text_input("Password Baru", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        
        if st.button("Simpan User"):
            conn = sqlite3.connect('database_klinik.db')
            c = conn.cursor()
            hashed_new_pw = hashlib.sha256(str.encode(new_pw)).hexdigest()
            try:
                c.execute("INSERT INTO users VALUES (?, ?, ?)", (new_user, hashed_new_pw, new_role))
                conn.commit()
                st.success(f"User {new_user} berhasil ditambahkan!")
            except:
                st.error("Username sudah ada!")
            conn.close()

# --- 2. FUNGSI PERHITUNGAN ---
def hitung_barber_johnson(hp, pasien_keluar, tt, periode):
    bor = (hp / (tt * periode)) * 100
    avlos = hp / pasien_keluar
    toi = ((tt * periode) - hp) / pasien_keluar
    bto = pasien_keluar / tt
    
    # Standar Depkes RI
    is_efisien = (60 <= bor <= 85) and (6 <= avlos <= 9) and (1 <= toi <= 3) and (bto >= 40)
    
    return {
        "BOR": round(bor, 2),
        "AVLOS": round(avlos, 2),
        "TOI": round(toi, 2),
        "BTO": round(bto, 2),
        "Status": "Efisien" if is_efisien else "Tidak Efisien"
    }

# --- 3. FUNGSI EKSPOR DATA (EXCEL & IMAGE) ---
def to_excel(hasil_dict):
    output = BytesIO()
    df = pd.DataFrame([hasil_dict])
    # Hapus kolom status dari tabel data jika hanya ingin angka
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Indikator_BJ')
    return output.getvalue()

def to_image(fig):
    imgdata = BytesIO()
    fig.savefig(imgdata, format='png', dpi=300, bbox_inches='tight')
    return imgdata.getvalue()

# --- 4. FUNGSI GRAFIK ---
def buat_grafik(bor, avlos, toi, bto):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Judul dan Label
    ax.set_title('Grafik Barber Johnson', fontsize=16, pad=20, fontweight='bold')
    ax.set_xlabel('TOI (Hari)', fontsize=12)
    ax.set_ylabel('AVLOS (Hari)', fontsize=12)
    
    # Batas Skala (0 - 15 hari) agar grafik tidak terlihat kosong
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 15)
    
    # 1. Gambar Kotak Efisiensi (Warna Hijau Muda)
    # Standar Depkes: TOI 1-3 hari, AVLOS 6-9 hari
    rect = plt.Rectangle((1, 6), 2, 3, color='green', alpha=0.15, label='Daerah Efisien (Depkes)')
    ax.add_patch(rect)
    
    # 2. Gambar Garis Bantu BOR (Diagonal)
    # Rumus: AVLOS = (BOR / (100 - BOR)) * TOI
    x_vals = np.linspace(0.1, 15, 100)
    for b in [50, 60, 70, 80, 90]: # Menambahkan beberapa variasi BOR
        y_vals = (b / (100 - b)) * x_vals
        ax.plot(x_vals, y_vals, '--', color='gray', alpha=0.3, linewidth=1)
        
        # Munculkan teks label di ujung garis agar tidak kosong
        if y_vals[-1] < 15:
            ax.text(14.5, y_vals[-1], f'{b}%', fontsize=8, verticalalignment='bottom')
        else:
            # Jika garis memotong sumbu Y atas (15)
            x_pos = (15 * (100 - b)) / b
            ax.text(x_pos, 14.5, f'{b}%', fontsize=8, horizontalalignment='center')

    # 3. Plot Titik Posisi Klinik (Titik Merah Besar)
    ax.scatter(toi, avlos, color='red', s=250, edgecolors='black', zorder=10, label='Posisi Klinik')
    
    # Garis Putus-putus bantuan ke arah sumbu X dan Y
    ax.plot([toi, toi], [0, avlos], 'r--', alpha=0.4)
    ax.plot([0, toi], [avlos, avlos], 'r--', alpha=0.4)
    
    # Anotasi angka koordinat di atas titik merah
    ax.annotate(f'({toi}, {avlos})', (toi, avlos), textcoords="offset points", 
                xytext=(0,15), ha='center', fontweight='bold', color='red')

    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper right')
    
    return fig

# --- 5. TAMPILAN UI STREAMLIT ---
st.title("🏥 Modul Efisiensi Barber Johnson")
st.write("Gunakan form di bawah untuk menghitung indikator efisiensi tempat tidur.")

# Container Form
with st.container(border=True):
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            tt = st.number_input("Jumlah Tempat Tidur (TT)", min_value=1, value=50)
            periode = st.number_input("Periode Waktu (Hari)", min_value=1, value=30)
        with col2:
            hp = st.number_input("Total Hari Perawatan (HP)", min_value=1, value=1200)
            pasien_keluar = st.number_input("Pasien Keluar (Hidup + Mati)", min_value=1, value=150)
        
        submit = st.form_submit_button("🚀 Hitung & Tampilkan Grafik")

if submit:
    # 1. Hitung Data
    hasil = hitung_barber_johnson(hp, pasien_keluar, tt, periode)
    
    # 2. Tampilkan Metrik Utama
    st.markdown("### Hasil Indikator")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BOR", f"{hasil['BOR']}%")
    m2.metric("AVLOS", f"{hasil['AVLOS']} Hari")
    m3.metric("TOI", f"{hasil['TOI']} Hari")
    m4.metric("BTO", f"{hasil['BTO']} Kali")
    
    # Status Efisiensi
    if hasil["Status"] == "Efisien":
        st.success(f"✅ Status: **{hasil['Status']}** (Masuk dalam daerah efisien)")
    else:
        st.warning(f"⚠️ Status: **{hasil['Status']}** (Di luar range ideal Depkes)")

    # 3. Tombol Download (Excel & Image)
    st.markdown("### 📥 Download Laporan")
    btn_col1, btn_col2 = st.columns(2)
    
    # Persiapkan file
    excel_file = to_excel(hasil)
    fig_bj = buat_grafik(hasil["BOR"], hasil["AVLOS"], hasil["TOI"], hasil["BTO"])
    image_file = to_image(fig_bj)

    with btn_col1:
        st.download_button(
            label="📄 Download Data (Excel)",
            data=excel_file,
            file_name=f"Indikator_BJ_{periode}hari.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with btn_col2:
        st.download_button(
            label="🖼️ Download Grafik (PNG)",
            data=image_file,
            file_name="Grafik_Barber_Johnson.png",
            mime="image/png",
            use_container_width=True
        )

    # 4. Tampilkan Grafik
    st.markdown("---")
    st.subheader("Visualisasi Grafik Barber Johnson")
    st.pyplot(fig_bj, use_container_width=True)

st.markdown("""
---
**© 2026 Developer Klinik Apps.** *Aplikasi ini Dibuat Oleh Alhatma. Dilarang keras memperjualbelikan atau mendistribusikan ulang tanpa izin tertulis.*
""", unsafe_allow_html=True)
