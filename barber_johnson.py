import streamlit as st
import pandas as pd
import plotly.graph_objects as go # Library baru untuk grafik interaktif
import numpy as np
import sqlite3
import hashlib
import datetime
from io import BytesIO

# --- 1. KONFIGURASI HALAMAN & KEAMANAN ---
st.set_page_config(page_title="Klinik Apps - Barber Johnson", layout="wide")

deadline = datetime.date(2026, 4, 28) 
if datetime.date.today() > deadline:
    st.error("⚠️ Masa berlaku aplikasi telah habis. Silakan hubungi pembuat.")
    st.stop()

# --- 2. DATABASE USER ---
def create_user_table():
    conn = sqlite3.connect('database_klinik.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    hashed_pw = hashlib.sha256(str.encode('admin123')).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
    conn.commit()
    conn.close()

create_user_table()

# --- 3. SISTEM LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Login Barber Johnson Apps")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        hpw = hashlib.sha256(str.encode(pw)).hexdigest()
        conn = sqlite3.connect('database_klinik.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (user, hpw))
        data = c.fetchone()
        conn.close()
        if data:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user
            st.session_state['role'] = data[2]
            st.rerun()
        else:
            st.error("Username atau Password salah!")
    st.stop()

# --- 4. SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state['username']}")
st.sidebar.write(f"Role: {st.session_state['role']}")

# MENU KHUSUS ADMIN (Tambahkan ini agar menu muncul)
if st.session_state['role'] == 'admin':
    st.sidebar.markdown("---")
    with st.sidebar.expander("➕ Tambah User Baru"):
        new_user = st.text_input("Username Baru")
        new_pw = st.text_input("Password Baru", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        
        if st.button("Simpan User"):
            if new_user and new_pw:
                h_new_pw = hashlib.sha256(str.encode(new_pw)).hexdigest()
                try:
                    conn = sqlite3.connect('database_klinik.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                              (new_user, h_new_pw, new_role))
                    conn.commit()
                    conn.close()
                    st.sidebar.success(f"User {new_user} berhasil dibuat!")
                except Exception as e:
                    st.sidebar.error("Username sudah ada atau error database!")
            else:
                st.sidebar.warning("Isi semua kolom!")

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 5. FUNGSI PERHITUNGAN & GRAFIK (PLOTLY) ---
def hitung_bj(hp, pk, tt, p):
    bor = (hp / (tt * p)) * 100
    avlos = hp / pk if pk > 0 else 0
    toi = ((tt * p) - hp) / pk if pk > 0 else 0
    bto = pk / tt if tt > 0 else 0
    
    # Logika Efisiensi disesuaikan: BOR & TOI & AVLOS
    # BTO disesuaikan proporsional terhadap periode (p)
    bto_min = (40 / 365) * p
    efisien = (60 <= bor <= 85) and (3 <= avlos <= 9) and (1 <= toi <= 3)
    
    return {"BOR": bor, "AVLOS": avlos, "TOI": toi, "BTO": bto, "Status": efisien}

def buat_grafik_interaktif(toi, avlos):
    fig = go.Figure()

    # Daerah Efisien (Kotak Hijau)
    fig.add_shape(
        type="rect", x0=1, y0=3, x1=3, y1=9,
        fillcolor="rgba(0, 255, 0, 0.2)",
        line=dict(width=0),
        name="Daerah Efisien"
    )

    # Titik Posisi Klinik
    fig.add_trace(go.Scatter(
        x=[toi], y=[avlos],
        mode='markers+text',
        marker=dict(size=15, color='red', line=dict(width=2, color='black')),
        name="Titik Anda",
        text=["Titik Anda"],
        textposition="top center"
    ))

    # Konfigurasi Layout (Auto-scale agar titik tidak hilang)
    fig.update_layout(
        title="<b>Grafik Barber Johnson (Interaktif)</b>",
        xaxis_title="TOI (Hari)",
        yaxis_title="AVLOS (Hari)",
        xaxis=dict(range=[0, max(15, toi + 5)], gridcolor='lightgrey'),
        yaxis=dict(range=[0, max(15, avlos + 5)], gridcolor='lightgrey'),
        plot_bgcolor='white',
        hovermode='closest'
    )
    return fig

# --- 6. TAMPILAN UTAMA MODUL ---
st.title("🏥 Modul Efisiensi Barber Johnson")
st.write("Gunakan form di bawah untuk menghitung indikator efisiensi tempat tidur.")

with st.form("input_form"):
    c1, c2 = st.columns(2)
    tt = c1.number_input("Jumlah Tempat Tidur (TT)", value=50, min_value=1)
    p = c1.number_input("Periode Waktu (Hari)", value=30, min_value=1)
    hp = c2.number_input("Total Hari Perawatan (HP)", value=1200, min_value=1)
    pk = c2.number_input("Pasien Keluar (Hidup + Mati)", value=150, min_value=1)
    
    col_btn1, col_btn2, _ = st.columns([0.25, 0.25, 0.5])
    with col_btn1:
        submit = st.form_submit_button("🚀 Hitung & Tampilkan")
    with col_btn2:
        reset = st.form_submit_button("➕ Input Data Baru")

if reset:
    st.rerun()

if submit:
    res = hitung_bj(hp, pk, tt, p)
    
    st.subheader("📊 Hasil Indikator")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BOR", f"{res['BOR']:.1f}%")
    m2.metric("AVLOS", f"{res['AVLOS']:.1f} Hari")
    m3.metric("TOI", f"{res['TOI']:.1f} Hari")
    m4.metric("BTO", f"{res['BTO']:.1f} Kali")

    if res['Status']:
        st.success("✅ Status: **Efisien** (Masuk dalam range ideal Depkes)")
    else:
        st.warning("⚠️ Status: **Tidak Efisien** (Di luar range ideal Depkes)")

    # Grafik Interaktif
    st.markdown("---")
    st.subheader("Visualisasi Grafik Barber Johnson")
    fig_interaktif = buat_grafik_interaktif(res['TOI'], res['AVLOS'])
    st.plotly_chart(fig_interaktif, use_container_width=True)

    # --- FITUR DOWNLOAD ---
    st.subheader("📥 Download Laporan")
    d1, d2 = st.columns(2)
    
    # Excel
    df_res = pd.DataFrame([res])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_res.to_excel(writer, index=False, sheet_name='Hasil')
    d1.download_button(label="📄 Download Data (Excel)", data=output.getvalue(), file_name="hasil_bj.xlsx")

    # Gambar (Download via Plotly Toolbar di pojok kanan atas grafik)
    st.info("💡 Untuk download grafik, klik ikon kamera 📷 di pojok kanan atas grafik.")
