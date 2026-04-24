import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Pastikan folder database ada. Jika belum, buat folder 'database' di root folder
DB_PATH = os.path.join(BASE_DIR, "klinik_data.db") 

def get_conn():
    return sqlite3.connect(DB_PATH)

# --- INISIALISASI DATABASE ---
def init_db():
    conn = get_conn()
    c = conn.cursor()
    # 1. Tabel Master Obat
    c.execute('''CREATE TABLE IF NOT EXISTS obat_master 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_obat TEXT, 
                  satuan TEXT, harga_jual REAL, stok_min INTEGER)''')
    
    # 2. Tabel Stok Masuk (dengan Foreign Key obat_id)
    c.execute('''CREATE TABLE IF NOT EXISTS stok_masuk
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, obat_id INTEGER, 
                  batch_no TEXT, expiry_date DATE, jumlah INTEGER, tgl_masuk DATE,
                  FOREIGN KEY(obat_id) REFERENCES obat_master(id))''')
    
    # 3. Tabel Transaksi/Dispensing
    c.execute('''CREATE TABLE IF NOT EXISTS dispensing
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tgl_transaksi DATE, 
                  nama_pasien TEXT, obat_id INTEGER, jumlah INTEGER, signa TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- TAMPILAN APLIKASI ---
st.set_page_config(page_title="Sistem Farmasi Pro", layout="wide")
st.title("💊 Sistem Informasi Farmasi Klinik")

tab1, tab2, tab3 = st.tabs(["Dashboard Stok", "Penerimaan & Dispensing", "Manajemen Master Obat"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("Inventory & Stok Kritis")
    conn = get_conn()
    # Query Join yang sudah diperbaiki
    query = """
        SELECT m.nama_obat, m.satuan, COALESCE(SUM(s.jumlah), 0) as total_stok, m.stok_min 
        FROM obat_master m
        LEFT JOIN stok_masuk s ON m.id = s.obat_id
        GROUP BY m.id
    """
    df_obat = pd.read_sql(query, conn)
    conn.close()
    
    # Indikator visual stok kritis
    st.dataframe(df_obat, use_container_width=True)
    
    stok_kritis = df_obat[df_obat['total_stok'] <= df_obat['stok_min']]
    if not stok_kritis.empty:
        st.warning("⚠️ Perhatian: Obat berikut mencapai batas stok minimal!")
        st.table(stok_kritis)

# --- TAB 2: PENERIMAAN & DISPENSING ---
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Penerimaan Barang")
        conn = get_conn()
        df_master = pd.read_sql("SELECT id, nama_obat FROM obat_master", conn)
        conn.close()
        
        with st.form("form_stok_masuk"):
            obat_pilih = st.selectbox("Pilih Obat", df_master['nama_obat'].tolist())
            batch = st.text_input("Nomor Batch")
            ed = st.date_input("Expired Date")
            qty = st.number_input("Jumlah Masuk", min_value=1)
            if st.form_submit_button("Tambah Stok"):
                conn = get_conn()
                id_obat = df_master[df_master['nama_obat']==obat_pilih]['id'].iloc[0]
                conn.execute("INSERT INTO stok_masuk (obat_id, batch_no, expiry_date, jumlah, tgl_masuk) VALUES (?,?,?,?,?)", 
                             (id_obat, batch, ed, qty, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("Stok berhasil ditambah!")
                st.rerun()

    with col2:
        st.subheader("Dispensing (Penyerahan Obat)")
        with st.form("form_dispense"):
            pasien = st.text_input("Nama Pasien")
            obat_pilih = st.selectbox("Pilih Obat (Dispensing)", df_master['nama_obat'].tolist())
            qty = st.number_input("Jumlah Keluar", min_value=1)
            signa = st.text_input("Signa / Aturan Pakai (Contoh: 3x1 setelah makan)")
            if st.form_submit_button("Proses Resep"):
                conn = get_conn()
                id_obat = df_master[df_master['nama_obat']==obat_pilih]['id'].iloc[0]
                # Logika sederhana pengurangan stok
                conn.execute("INSERT INTO dispensing (tgl_transaksi, nama_pasien, obat_id, jumlah, signa) VALUES (?,?,?,?,?)",
                             (datetime.now().strftime("%Y-%m-%d"), pasien, id_obat, qty, signa))
                conn.commit()
                conn.close()
                st.success(f"Obat {obat_pilih} diserahkan kepada {pasien}")

# --- TAB 3: MANAJEMEN MASTER ---
with tab3:
    st.subheader("Tambah Data Obat Baru")
    with st.form("add_obat"):
        nama = st.text_input("Nama Obat")
        satuan = st.text_input("Satuan (Tablet/Botol)")
        harga = st.number_input("Harga Jual", min_value=0)
        s_min = st.number_input("Stok Minimal (Peringatan)", min_value=1)
        if st.form_submit_button("Simpan Master Obat"):
            conn = get_conn()
            conn.execute("INSERT INTO obat_master (nama_obat, satuan, harga_jual, stok_min) VALUES (?,?,?,?)", 
                         (nama, satuan, harga, s_min))
            conn.commit()
            conn.close()
            st.success("Obat berhasil didaftarkan!")
            st.rerun()
