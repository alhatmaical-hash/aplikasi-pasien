import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def buat_grafik_barber_johnson(bor, avlos, toi, bto):
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Setup Sumbu
    ax.set_xlabel('TOI (Hari)')
    ax.set_ylabel('AVLOS (Hari)')
    ax.set_title('Grafik Barber Johnson')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 15)
    
    # 1. Gambar Garis BOR (Diagonal dari titik 0)
    # Rumus: y = (BOR/(100-BOR)) * x
    x_vals = np.linspace(0.1, 15, 100)
    for b in [70, 80, 90]: # Garis bantu BOR
        y_vals = (b / (100 - b)) * x_vals
        ax.plot(x_vals, y_vals, '--', alpha=0.3, label=f'BOR {b}%')
        
    # 2. Gambar Garis BTO (Lengkung)
    # Rumus: y = (Periode/BTO) - x
    # (Di sini kita sederhanakan sebagai referensi visual)
    
    # 3. Arsir DAERAH EFISIEN (Standard Depkes)
    # TOI 1-3, AVLOS 6-9
    ax.axvspan(1, 3, ymin=6/15, ymax=9/15, color='green', alpha=0.2, label='Daerah Efisien')
    
    # 4. PLOT TITIK DATA ANDA
    ax.scatter(toi, avlos, color='red', s=100, edgecolors='black', zorder=5)
    ax.annotate(f' Posisi Klinik\n (TOI:{toi}, AVLOS:{avlos})', (toi, avlos), textcoords="offset points", xytext=(0,10), ha='center')

    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize='small')
    
    return fig

# --- Bagian UI Streamlit ---
# (Gunakan variabel hasil hitung dari form sebelumnya)
if 'hasil' in locals() or submit:
    # ... kode hitung sebelumnya ...
    
    st.subheader("Visualisasi Grafik")
    fig_bj = buat_grafik_barber_johnson(hasil["BOR (%)"], hasil["AVLOS (Hari)"], hasil["TOI (Hari)"], hasil["BTO (Kali)"])
    st.pyplot(fig_bj)
