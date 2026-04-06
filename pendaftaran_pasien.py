import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import time # Tambahkan ini untuk jeda sebentar

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide"
)

# --- 2. DATABASE SETUP ---
def get_connection():
    return sqlite3.connect('klinik_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS master_data (id INTEGER PRIMARY KEY, kategori TEXT, nama TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tgl_daftar DATE, bulan_daftar TEXT, jenis_kunjungan TEXT, 
                    nama_lengkap TEXT, no_hp TEXT, blok_mes TEXT, agama TEXT, 
                    nik TEXT, gender TEXT, pernah_berobat TEXT, tempat_tgl_lahir TEXT,
                    perusahaan TEXT, departemen TEXT, jabatan TEXT,
                    alergi TEXT, gol_darah TEXT, lokasi_kerja TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNGSI DATA ---
def get_master(kategori):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
        return df['nama'].tolist()
    except:
        return []
    finally:
        conn.close()

# --- 4. NAVIGASI SIDEBAR ---
st.sidebar.title("🏥 Menu Utama / 主菜单")
menu = st.sidebar.radio("Pilih Halaman / 选择页面", ["Pendaftaran / 登记", "Rekam Medis / 病历", "Pengaturan Master / 设置"])

# --- 5. MENU PENDAFTARAN ---
if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
    
    opts_perusahaan = get_master("Perusahaan")
    opts_dept = get_master("Departemen")
    opts_jabatan = get_master("Jabatan")

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN / 就诊类型", ["Berobat / 看病", "Kontrol MCU / 体检复查", "Masuk UGD / 急诊", "Kontrol Post Rujuk / 转院后复查", "Kontrol Rawat luka / 伤口护理"])
            nama = st.text_input("NAMA LENGKAP / 全名")
            hp = st.text_input("NO HP AKTIF / 有效电话号码")
            agama = st.selectbox("AGAMA / 宗教", ["Islam / 伊斯兰教", "Kristen / 基督教", "Hindu / 印度教", "Buddha / 佛教", "Katolik / 天主教", "Tidak Diketahui / 未知"])
            nik = st.text_input("NIK IDCARD / 身份证号")
            gender = st.selectbox("JENIS KELAMIN / 性别", ["Laki-laki / 男", "Perempuan / 女"])
            pernah = st.radio("PERNAH BEROBAT DISINI? / 以前来过这里看病吗？", ["Iya Sudah / 是的", "Belum Pernah / 从未"], horizontal=True)

        with col2:
            blok = st.text_input("BLOK MES & NO KAMAR / 宿舍区和房间号")
            ttl = st.text_input("TEMPAT & TANGGAL LAHIR / 出生地点和日期")
            perusahaan = st.selectbox("PERUSAHAAN / 公司", opts_perusahaan if opts_perusahaan else ["Isi di Pengaturan / 在设置中填写"])
            dept = st.selectbox("DEPARTEMEN / 部门", opts_dept if opts_dept else ["Isi di Pengaturan / 在设置中填写"])
            jabatan = st.selectbox("JABATAN / 职位", opts_jabatan if opts_jabatan else ["Isi di Pengaturan / 在设置中填写"])
            alergi = st.selectbox("JENIS ALERGI / 过敏类型", ["Tidak Ada / 无", "Makanan / 食
