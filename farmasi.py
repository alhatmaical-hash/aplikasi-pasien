import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# --- KONFIGURASI DATABASE (AMAN & ROBUST) ---
# Mengambil folder tempat file script ini berada
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Database diletakkan di folder 'database' di level folder atasnya
DB_PATH = os.path.join(BASE_DIR, "..", "database", "klinik_data.db")

def get_conn():
    # Pastikan folder database ada
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Tabel Obat
    c.execute('''CREATE TABLE IF NOT EXISTS obat_master 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_obat TEXT, stok INTEGER, 
                  satuan TEXT, harga_jual REAL, stok_minimal INTEGER DEFAULT 5)''')
    # Tabel Resep/Transaksi
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi_farmasi 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_pasien TEXT, 
                  obat_id INTEGER, jumlah INTEGER, tanggal TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- UI FARMASI ---
st.set_page_config(page_title="Sistem Informasi Farmasi", layout="wide")
st.title("💊 Sistem Informasi Farmasi Klinik")

tab1, tab2, tab3 = st.tabs(["Dashboard Stok", "Dispensing (Resep)", "Manajemen Obat"])

# 1. TAB DASHBOARD (Notifikasi Stok Kritis)
with tab1:
    st.subheader("Ringkasan Stok")
    conn = get_conn()
    df_obat = pd.read_sql("SELECT * FROM obat_master", conn)
    conn.close()
    
    # Indikator Stok Kritis
    stok_kritis = df_obat[df_obat['stok'] <= df_obat['stok_minimal']]
    if not stok_kritis.empty:
        st.warning(f"⚠️ Perhatian: {len(stok_kritis)} obat mencapai stok minimal!")
        st.dataframe(stok_kritis)
    
    st.dataframe(df_obat, use_container_width=True)

# 2. TAB DISPENSING (Input Resep)
with tab2:
    st.subheader("Formulir Penyerahan Obat")
    with st.form("form_resep"):
        pasien = st.text_input("Nama Pasien")
        obat_pilihan = st.selectbox("Pilih Obat", df_obat['nama_obat'].tolist())
        jumlah = st.number_input("Jumlah Keluar", min_value=1)
        submit = st.form_submit_button("Proses Resep")
        
        if submit:
            conn = get_conn()
            c = conn.cursor()
            # Cek stok cukup
            obat = c.execute("SELECT id, stok FROM obat_master WHERE nama_obat = ?", (obat_pilihan,)).fetchone()
            if obat and obat[1] >= jumlah:
                # Update stok
                c.execute("UPDATE obat_master SET stok = stok - ? WHERE nama_obat = ?", (jumlah, obat_pilihan))
                # Simpan transaksi
                c.execute("INSERT INTO transaksi_farmasi (nama_pasien, obat_id, jumlah, tanggal) VALUES (?, ?, ?, ?)", 
                          (pasien, obat[0], jumlah, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"Obat {obat_pilihan} berhasil diserahkan!")
            else:
                st.error("Stok tidak mencukupi atau obat tidak ditemukan!")
            conn.close()

# 3. TAB MANAJEMEN OBAT
with tab3:
    st.subheader("Input Data Obat Baru")
    with st.form("add_obat"):
        nama = st.text_input("Nama Obat")
        satuan = st.text_input("Satuan (Tablet/Botol/Sirup)")
        stok = st.number_input("Stok Awal", min_value=0)
        harga = st.number_input("Harga Jual", min_value=0)
        submit_add = st.form_submit_button("Simpan Obat")
        
        if submit_add:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO obat_master (nama_obat, stok, satuan, harga_jual) VALUES (?, ?, ?, ?)", 
                      (nama, stok, satuan, harga))
            conn.commit()
            conn.close()
            st.success("Obat berhasil ditambahkan!")
            st.rerun()
