import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps - Barber Johnson", layout="wide")

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
    
    ax.set_title('Grafik Barber Johnson', fontsize=16, pad=20, fontweight='bold')
    ax.set_xlabel('TOI (Hari)', fontsize=12)
    ax.set_ylabel('AVLOS (Hari)', fontsize=12)
    
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 15)
    
    # Daerah Efisien
    rect = plt.Rectangle((1, 6), 2, 3, color='green', alpha=0.15, label='Daerah Efisien (Depkes)')
    ax.add_patch(rect)
    
    # Garis Bantu BOR
    x_vals = np.linspace(0.1, 15, 100)
    for b in [70, 75, 80, 85]:
        y_vals = (b / (100 - b)) * x_vals
        ax.plot(x_vals, y_vals, '--', color='gray', alpha=0.4, linewidth=1)
        # Menampilkan teks label BOR di ujung garis
        idx = -10 # posisi label sedikit sebelum ujung
        ax.text(x_vals[idx], y_vals[idx], f'{b}%', fontsize=8, alpha=0.7)

    # Plot Titik Posisi
    ax.scatter(toi, avlos, color='red', s=200, edgecolors='black', zorder=10, label='Posisi Saat Ini')
    ax.plot([toi, toi], [0, avlos], 'r--', alpha=0.3)
    ax.plot([0, toi], [avlos, avlos], 'r--', alpha=0.3)
    
    ax.annotate(f'({toi}, {avlos})', (toi, avlos), textcoords="offset points", xytext=(0,15), ha='center', fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
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
