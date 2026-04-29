import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import pytz

# --- KONFIGURASI ---
st.set_page_config(page_title="Klinik Apps - China Patient", layout="wide")

def get_connection():
    return sqlite3.connect("klinik_data.db", check_same_thread=False)

# 1. INISIALISASI DATABASE
def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tgl_daftar TIMESTAMP,
                        nama_mandarin TEXT,
                        nama_lengkap TEXT, 
                        nik TEXT, 
                        gender TEXT,
                        wechat_id TEXT,
                        gol_darah TEXT,
                        perusahaan TEXT, 
                        departemen TEXT, 
                        jabatan TEXT,
                        blok_mes TEXT,
                        agama TEXT,
                        tempat_lahir TEXT,
                        tgl_lahir TEXT)''')
        conn.commit()

init_db()

# 2. FUNGSI SIMPAN DATA
def simpan_data(data):
    tz_wit = pytz.timezone('Asia/Jayapura')
    waktu_sekarang = datetime.now(tz_wit).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO pasien (
            tgl_daftar, nama_mandarin, nama_lengkap, nik, gender, 
            wechat_id, gol_darah, perusahaan, departemen, jabatan, 
            blok_mes, agama, tempat_lahir, tgl_lahir
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            waktu_sekarang, data['mandarin'], data['nama'], data['nik'], data['gender'],
            data['wechat'], data['darah'], data['pt'], data['dept'], data['jab'],
            data['mes'], data['agama'], data['tmpt'], data['tgl']
        ))
        conn.commit()

# --- NAVIGATION ---
# Gunakan Sidebar untuk berpindah antara Form Pasien dan Tabel Petugas
st.sidebar.title("Menu Navigasi")
pilihan = st.sidebar.radio("Pilih Tampilan:", ["Pendaftaran (Pasien)", "Data Terdaftar (Petugas)"])

# --- HALAMAN 1: FORMULIR PENDAFTARAN ---
if pilihan == "Pendaftaran (Pasien)":
    st.markdown("<h2 style='text-align: center;'>CN 挂号表 / Formulir Pendaftaran</h2>", unsafe_allow_html=True)
    
    with st.form("form_pendaftaran", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama_m = st.text_input("中文姓名 / Nama Mandarin", placeholder="例: 王小明")
            nama_l = st.text_input("英文姓名 / Nama Sesuai Paspor (Latin) *").upper()
            nik = st.text_input("证件号码 / NIK atau No. Paspor *")
            gender = st.radio("性别 / Jenis Kelamin", ["男 (Laki-laki)", "女 (Perempuan)"], horizontal=True)
            wechat = st.text_input("微信 ID 或 手机号 / ID WeChat atau No. HP *")
            darah = st.selectbox("血型 / Golongan Darah", ["A", "B", "AB", "O", "不清楚"])
        
        with col2:
            pt = st.selectbox("公司 / Perusahaan *", ["HPAL", "HJF", "HNC", "TBP"])
            dept = st.text_input("部门 / Departemen *").upper()
            jab = st.text_input("职位 / Jabatan *").upper()
            mes = st.text_input("宿舍号 / Blok & No. Kamar Mes *").upper()
            agama = st.text_input("宗教 / Agama (Jika ada)")
            
        st.write("📅 **出生信息 / Informasi Kelahiran**")
        c3, c4 = st.columns(2)
        tmpt = c3.text_input("出生地点 / Tempat Lahir")
        tgl = c4.date_input("出生日期 / Tanggal Lahir", value=datetime(2026, 4, 29))

        if st.form_submit_button("提交 / KIRIM PENDAFTARAN", use_container_width=True):
            if not nama_l or not nik or not wechat:
                st.error("❌ Mohon isi kolom wajib (*)")
            else:
                data_pasien = {
                    'mandarin': nama_m, 'nama': nama_l, 'nik': nik, 'gender': gender,
                    'wechat': wechat, 'darah': darah, 'pt': pt, 'dept': dept,
                    'jab': jab, 'mes': mes, 'agama': agama, 'tmpt': tmpt, 'tgl': str(tgl)
                }
                simpan_data(data_pasien)
                st.success("✅ Berhasil terdaftar! / 提交成功！")

# --- HALAMAN 2: MONITORING PETUGAS ---
elif pilihan == "Data Terdaftar (Petugas)":
    st.header("📋 Daftar Pasien Terdaftar")
    
    # Fragment untuk auto-refresh data setiap 5 detik
    @st.fragment(run_every="5s")
    def refresh_data():
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
        
        if not df.empty:
            st.dataframe(
                df[['tgl_daftar', 'nama_mandarin', 'nama_lengkap', 'perusahaan', 'wechat_id', 'status_antrian']],
                column_config={
                    "tgl_daftar": "Waktu Daftar",
                    "nama_mandarin": "姓名 (Mandarin)",
                    "nama_lengkap": "Nama Latin",
                    "wechat_id": "WeChat/HP",
                    "status_antrian": "Status"
                },
                hide_index=True,
                use_container_width=True
            )
            st.caption(f"Terakhir diperbarui: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.info("Belum ada data pasien.")
            
    refresh_data()
