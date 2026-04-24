import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# --- SETUP PATH DATABASE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Pastikan folder database ada di level yang sama atau satu tingkat di atas
DB_PATH = os.path.join(BASE_DIR, "..", "database", "klinik_data.db")

def get_conn():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # 1. Master Obat dengan Kategori & Stock Minimal
    c.execute('''CREATE TABLE IF NOT EXISTS obat_master 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_obat TEXT, 
                  satuan TEXT, harga_jual REAL, stok_min INTEGER)''')
    
    # 2. Stok In (Penting untuk Batch & ED)
    c.execute('''CREATE TABLE IF NOT EXISTS stok_masuk
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, obat_id INTEGER, 
                  batch_no TEXT, expiry_date DATE, jumlah INTEGER, tgl_masuk DATE)''')
    
    # 3. Transaksi/Dispensing
    c.execute('''CREATE TABLE IF NOT EXISTS dispensing
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tgl_transaksi DATE, 
                  nama_pasien TEXT, obat_id INTEGER, jumlah INTEGER, signa TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- UI APP ---
st.set_page_config(page_title="Pro Pharmacy System", layout="wide")
st.title("🏥 Sistem Informasi Farmasi Profesional")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard Stok", "Penerimaan Barang", "Dispensing Resep", "Laporan"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("Inventory & Stok Kritis")
    conn = get_conn()
    df_obat = pd.read_sql("""
        SELECT m.nama_obat, m.satuan, SUM(s.jumlah) as total_stok, m.stok_min 
        FROM obat_master m
        LEFT JOIN stok_masuk s ON m.id = s.obat_obat
        GROUP BY m.id
    """, conn)
    conn.close()
    st.dataframe(df_obat, use_container_width=True)

# --- TAB 2: PENERIMAAN (STOK MASUK) ---
with tab2:
    st.subheader("Input Barang Masuk (Batching)")
    conn = get_conn()
    opsi_obat = pd.read_sql("SELECT id, nama_obat FROM obat_master", conn)
    conn.close()
    
    with st.form("form_masuk"):
        obat_pilih = st.selectbox("Pilih Obat", opsi_obat['nama_obat'].tolist())
        batch = st.text_input("Nomor Batch")
        ed = st.date_input("Expired Date")
        qty = st.number_input("Jumlah Masuk", min_value=1)
        if st.form_submit_button("Simpan Stok"):
            conn = get_conn()
            c = conn.cursor()
            id_obat = opsi_obat[opsi_obat['nama_obat']==obat_pilih]['id'].iloc[0]
            c.execute("INSERT INTO stok_masuk (obat_id, batch_no, expiry_date, jumlah, tgl_masuk) VALUES (?,?,?,?,?)", 
                      (id_obat, batch, ed, qty, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Stok berhasil ditambah!")

# --- TAB 3: DISPENSING (PELAYANAN PASIEN) ---
with tab3:
    st.subheader("Pelayanan Resep Pasien")
    with st.form("form_dispense"):
        nama_pasien = st.text_input("Nama Pasien")
        obat_pilih = st.selectbox("Pilih Obat (Dispensing)", opsi_obat['nama_obat'].tolist())
        qty = st.number_input("Jumlah Keluar", min_value=1)
        signa = st.text_input("Signa / Aturan Pakai (Contoh: 3x1 setelah makan)")
        
        if st.form_submit_button("Proses Resep"):
            conn = get_conn()
            c = conn.cursor()
            # Logic: Kurangi dari stok dengan ED terdekat (FEFO)
            # (Sederhananya di sini, kurangi dari tabel stok_masuk)
            c.execute("UPDATE stok_masuk SET jumlah = jumlah - ? WHERE obat_id = (SELECT id FROM obat_master WHERE nama_obat = ?) AND jumlah >= ?", 
                      (qty, obat_pilih, qty))
            c.execute("INSERT INTO dispensing (tgl_transaksi, nama_pasien, obat_id, jumlah, signa) VALUES (?,?,?,?,?)",
                      (datetime.now().strftime("%Y-%m-%d"), nama_pasien, 1, qty, signa)) # Simplified
            conn.commit()
            conn.close()
            st.success("Obat diserahkan. Jangan lupa cetak etiket!")
