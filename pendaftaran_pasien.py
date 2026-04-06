import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

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
    # --- TOGGLE BAHASA ---
    st.header("📝 Pendaftaran Pasien / 病人登记")
    
    # Opsi Dropdown Master Data
    opts_perusahaan = get_master("Perusahaan")
    opts_dept = get_master("Departemen")
    opts_jabatan = get_master("Jabatan")

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            kunjungan = st.selectbox("JENIS KUNJUNGAN / 就诊类型", [
                "Berobat / 看病", 
                "Kontrol MCU / 体检复查", 
                "Masuk UGD / 急诊", 
                "Kontrol Post Rujuk / 转院后复查", 
                "Kontrol Rawat luka / 伤口护理"
            ])
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
            alergi = st.selectbox("JENIS ALERGI / 过敏类型", ["Tidak Ada / 无", "Makanan / 食物", "Obat / 药物", "Cuaca / 天气"])
            darah = st.selectbox("GOLONGAN DARAH / 血型", ["A", "B", "AB", "O", "Tidak Tahu / 不知道"])
            
        lokasi = st.text_area("LOKASI AREA KERJA / 工作地点")
        
        # Tombol Submit
        btn_label = "KIRIM PENDAFTARAN / 提交登记"
        if st.form_submit_button(btn_label):
            if nama and hp:
                conn = get_connection()
                c = conn.cursor()
                now = datetime.now()
                c.execute('''INSERT INTO pasien (tgl_daftar, bulan_daftar, jenis_kunjungan, nama_lengkap, no_hp, blok_mes, agama, nik, gender, pernah_berobat, tempat_tgl_lahir, perusahaan, departemen, jabatan, alergi, gol_darah, lokasi_kerja) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (now.date(), now.strftime("%B %Y"), kunjungan, nama, hp, blok, agama, nik, gender, pernah, ttl, perusahaan, dept, jabatan, alergi, darah, lokasi))
                conn.commit()
                conn.close()
                st.success("Pendaftaran berhasil! Silakan menunggu. / 登记成功！请稍候。")
                st.balloons()
            else:
                st.error("Nama dan No HP tidak boleh kosong! / 姓名和电话号码不能为空！")

# --- 6. MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📊 Rekam Medis / 病历数据")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        f_bln = st.multiselect("Filter Bulan / 按月份筛选", df['bulan_daftar'].unique())
        if f_bln:
            df = df[df['bulan_daftar'].isin(f_bln)]
            
        st.dataframe(df, use_container_width=True)
        
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 Download Excel", data=towrite.getvalue(), file_name="Data_Pasien.xlsx")
    else:
        st.info("Belum ada data / 暂无数据。")

# --- 7. PENGATURAN MASTER ---
elif menu == "Pengaturan Master / 设置":
    st.header("⚙️ Master Data / 基础数据设置")
    kat = st.selectbox("Pilih Kategori / 选择类别", ["Perusahaan", "Departemen", "Jabatan"])
    
    c1, c2 = st.columns(2)
    with c1:
        n_baru = st.text_input(f"Tambah {kat} Baru / 添加新{kat}")
        if st.button("Simpan Baru / 保存"):
            if n_baru:
                conn = get_connection()
                conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kat, n_baru))
                conn.commit()
                conn.close()
                st.rerun()
    with c2:
        d_lama = get_master(kat)
        p_hapus = st.selectbox("Hapus Data / 删除数据", ["-- Pilih / 选择 --"] + d_lama)
        if st.button("Hapus Terpilih / 删除"):
            if p_hapus != "-- Pilih / 选择 --":
                conn = get_connection()
                conn.execute("DELETE FROM master_data WHERE kategori=? AND nama=?", (kat, p_hapus))
                conn.commit()
                conn.close()
                st.rerun()
