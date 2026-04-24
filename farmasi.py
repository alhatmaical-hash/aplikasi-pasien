import streamlit as st
import sqlite3
import pandas as pd

# 1. KONFIGURASI DATABASE
# Sesuaikan path agar menunjuk ke file database di folder 'database'
DB_PATH = "../database/klinik_data.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

# Inisialisasi Tabel (Jalankan sekali)
def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Tabel Master Obat
    c.execute('''CREATE TABLE IF NOT EXISTS obat_master 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_obat TEXT, stok INTEGER, harga REAL)''')
    # Tabel Transaksi
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi_obat 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_obat TEXT, jumlah INTEGER, tanggal DATE)''')
    conn.commit()
    conn.close()

init_db()

# 2. UI STREAMLIT
st.set_page_config(page_title="Farmasi Klinik", layout="wide")
st.title("💊 Modul Farmasi")

menu = st.sidebar.radio("Menu", ["Dashboard", "Master Obat", "Transaksi Keluar"])

# Halaman Dashboard
if menu == "Dashboard":
    st.subheader("Ringkasan Stok")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM obat_master", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# Halaman Master Obat
elif menu == "Master Obat":
    st.subheader("Input Obat Baru")
    with st.form("input_obat"):
        nama = st.text_input("Nama Obat")
        stok = st.number_input("Stok Awal", min_value=0)
        harga = st.number_input("Harga Satuan", min_value=0)
        submitted = st.form_submit_button("Simpan")
        
        if submitted:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO obat_master (nama_obat, stok, harga) VALUES (?, ?, ?)", (nama, stok, harga))
            conn.commit()
            conn.close()
            st.success(f"Obat {nama} berhasil ditambahkan!")

# Halaman Transaksi
elif menu == "Transaksi Keluar":
    st.subheader("Dispensing Obat")
    conn = get_conn()
    df_obat = pd.read_sql("SELECT * FROM obat_master", conn)
    conn.close()
    
    with st.form("form_transaksi"):
        selected_obat = st.selectbox("Pilih Obat", df_obat['nama_obat'].tolist())
        jumlah = st.number_input("Jumlah Keluar", min_value=1)
        submit_trans = st.form_submit_button("Proses Resep")
        
        if submit_trans:
            conn = get_conn()
            c = conn.cursor()
            # Kurangi stok
            c.execute("UPDATE obat_master SET stok = stok - ? WHERE nama_obat = ?", (jumlah, selected_obat))
            # Catat transaksi
            c.execute("INSERT INTO transaksi_obat (nama_obat, jumlah, tanggal) VALUES (?, ?, DATE('now'))", (selected_obat, jumlah))
            conn.commit()
            conn.close()
            st.success("Stok berhasil diperbarui!")
