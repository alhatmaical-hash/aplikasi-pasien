import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
import io

# --- KONFIGURASI DATABASE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "klinik_data.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # 1. Master Obat
    c.execute('''CREATE TABLE IF NOT EXISTS obat_master 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_obat TEXT, 
                  satuan TEXT, harga_jual REAL, stok_min INTEGER)''')
    # 2. Stok Masuk
    c.execute('''CREATE TABLE IF NOT EXISTS stok_masuk
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, obat_id INTEGER, 
                  batch_no TEXT, expiry_date DATE, jumlah INTEGER, tgl_masuk DATE)''')
    # 3. Dispensing (Keluar)
    c.execute('''CREATE TABLE IF NOT EXISTS dispensing
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tgl_transaksi DATE, 
                  nama_pasien TEXT, obat_id INTEGER, jumlah INTEGER, signa TEXT)''')
    # 4. Opname (Penyesuaian Fisik)
    c.execute('''CREATE TABLE IF NOT EXISTS stok_adjustment
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, obat_id INTEGER, 
                  jumlah_adj INTEGER, alasan TEXT, tanggal DATE)''')
    conn.commit()
    conn.close()

init_db()

# --- UI APP ---
st.set_page_config(page_title="Sistem Farmasi RS", layout="wide")
st.title("🏥 Sistem Informasi Farmasi Rumah Sakit")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Dispensing", "Penerimaan", "Opname", "Laporan"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("Inventory & Stok Kritis")
    conn = get_conn()
    # Query gabungan untuk melihat stok akhir (Masuk - Keluar + Adjustment)
    query = """
        SELECT m.nama_obat, m.satuan, m.stok_min,
               COALESCE(SUM(s.jumlah), 0) as total_masuk,
               COALESCE(SUM(d.jumlah), 0) as total_keluar,
               COALESCE(SUM(a.jumlah_adj), 0) as total_adj
        FROM obat_master m
        LEFT JOIN stok_masuk s ON m.id = s.obat_id
        LEFT JOIN dispensing d ON m.id = d.obat_id
        LEFT JOIN stok_adjustment a ON m.id = a.obat_id
        GROUP BY m.id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Hitung stok akhir di pandas
    df['stok_akhir'] = df['total_masuk'] - df['total_keluar'] + df['total_adj']
    st.dataframe(df, use_container_width=True)

# --- TAB 2: DISPENSING (PELAYANAN) ---
with tab2:
    st.subheader("Dispensing Resep")
    conn = get_conn()
    df_m = pd.read_sql("SELECT id, nama_obat FROM obat_master", conn)
    conn.close()
    
    with st.form("form_dispense"):
        pasien = st.text_input("Nama Pasien")
        obat_pilih = st.selectbox("Pilih Obat", df_m['nama_obat'].tolist())
        qty = st.number_input("Jumlah Keluar", min_value=1)
        signa = st.text_input("Signa (Contoh: 3x1 setelah makan)")
        if st.form_submit_button("Proses Resep"):
            conn = get_conn()
            id_obat = df_m[df_m['nama_obat']==obat_pilih]['id'].iloc[0]
            conn.execute("INSERT INTO dispensing (tgl_transaksi, nama_pasien, obat_id, jumlah, signa) VALUES (?,?,?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d"), pasien, id_obat, qty, signa))
            conn.commit()
            conn.close()
            st.success("Obat berhasil diserahkan!")

# --- TAB 3: PENERIMAAN BARANG ---
with tab3:
    st.subheader("Penerimaan Barang (Stok Masuk)")
    with st.form("form_masuk"):
        obat_pilih = st.selectbox("Pilih Obat", df_m['nama_obat'].tolist())
        qty = st.number_input("Jumlah Masuk", min_value=1)
        if st.form_submit_button("Tambah Stok"):
            conn = get_conn()
            id_obat = df_m[df_m['nama_obat']==obat_pilih]['id'].iloc[0]
            conn.execute("INSERT INTO stok_masuk (obat_id, jumlah, tgl_masuk) VALUES (?,?,?)", 
                         (id_obat, qty, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Stok masuk tercatat!")

# --- TAB 4: STOCK OPNAME ---
with tab4:
    st.subheader("Stock Opname (Penyesuaian)")
    with st.form("form_opname"):
        obat_pilih = st.selectbox("Pilih Obat untuk Opname", df_m['nama_obat'].tolist())
        selisih = st.number_input("Selisih (+/-)", step=1)
        alasan = st.text_input("Alasan (Contoh: ED/Rusak)")
        if st.form_submit_button("Simpan Penyesuaian"):
            conn = get_conn()
            id_obat = df_m[df_m['nama_obat']==obat_pilih]['id'].iloc[0]
            conn.execute("INSERT INTO stok_adjustment (obat_id, jumlah_adj, alasan, tanggal) VALUES (?,?,?,?)", 
                         (id_obat, selisih, alasan, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Data Opname tersimpan!")

# --- TAB 5: LAPORAN EXCEL ---
with tab5:
    st.subheader("Unduh Laporan Mutasi Stok")
    if st.button("Generate Laporan Excel"):
        conn = get_conn()
        df_laporan = pd.read_sql(query, conn)
        df_laporan['stok_akhir'] = df_laporan['total_masuk'] - df_laporan['total_keluar'] + df_laporan['total_adj']
        conn.close()
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_laporan.to_excel(writer, index=False, sheet_name='Laporan_Stok')
        st.download_button("Klik untuk Unduh Excel", output.getvalue(), "Laporan_Farmasi.xlsx", "application/vnd.ms-excel")
