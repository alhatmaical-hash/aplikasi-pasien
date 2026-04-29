import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import pytz
import base64

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Pendaftaran Pasien Cina", page_icon="🇨🇳", layout="wide")

def get_connection():
    return sqlite3.connect("klinik_data.db", check_same_thread=False)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        # Tabel Pasien Utama dengan kolom tambahan untuk Pasien Cina
        c.execute('''CREATE TABLE IF NOT EXISTS pasien (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tgl_daftar TIMESTAMP,
                        nama_lengkap TEXT, 
                        nama_mandarin TEXT,
                        nik TEXT, 
                        gender TEXT,
                        perusahaan TEXT, 
                        departemen TEXT, 
                        jabatan TEXT,
                        blok_mes TEXT,
                        wechat_id TEXT,
                        gol_darah TEXT,
                        agama TEXT,
                        tempat_lahir TEXT,
                        tgl_lahir TEXT,
                        status_antrian TEXT DEFAULT 'Normal')''')
        conn.commit()

init_db()

# --- 2. FUNGSI PENYIMPANAN ---
def simpan_data_cina(nama, mandarin, nik, gender, wechat, darah, pt, dept, jab, mes, agama, tmpt, tgl):
    tz_wit = pytz.timezone('Asia/Jayapura')
    waktu_sekarang = datetime.now(tz_wit).strftime("%Y-%m-%d %H:%M:%S")
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''INSERT INTO pasien (
                            tgl_daftar, nama_lengkap, nama_mandarin, nik, gender, 
                            perusahaan, departemen, jabatan, blok_mes, wechat_id, 
                            gol_darah, agama, tempat_lahir, tgl_lahir
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (waktu_sekarang, nama, mandarin, nik, gender, 
                     pt, dept, jab, mes, wechat, darah, agama, tmpt, str(tgl)))
        conn.commit()

# --- 3. TAMPILAN FORMULIR (UNTUK PASIEN) ---
def form_pendaftaran_cina():
    st.markdown("<h2 style='text-align: center;'>🇨🇳 挂号表 / Formulir Pendaftaran</h2>", unsafe_allow_html=True)
    
    # Session state untuk mengontrol alur setelah submit
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    if st.session_state.submitted:
        st.success("✅ 提交成功！请等待叫号 / Berhasil! Mohon tunggu panggilan petugas.")
        if st.button("登记新病人 / Daftar Pasien Baru"):
            st.session_state.submitted = False
            st.rerun()
        return

    with st.form("form_cina", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nama_mandarin = st.text_input("中文姓名 / Nama Mandarin", placeholder="例: 王小明")
            nama_pasien = st.text_input("英文姓名 / Nama Sesuai Paspor (Latin) *", placeholder="WANG XIAOMING")
            nik_id = st.text_input("证件号码 / NIK atau No. Paspor *")
            gender = st.radio("性别 / Jenis Kelamin", ["男 (Laki-laki)", "女 (Perempuan)"], horizontal=True)
            wechat = st.text_input("微信 ID 或 手机号 / ID WeChat atau No. HP *")
            darah = st.selectbox("血型 / Golongan Darah", ["A", "B", "AB", "O", "不清楚 (Tidak Tahu)"])

        with col2:
            perusahaan = st.selectbox("公司 / Perusahaan *", ["HPAL", "HJF", "HNC", "TBP", "Lainnya"])
            dept = st.text_input("部门 / Departemen *")
            jabatan = st.text_input("职位 / Jabatan *")
            mes = st.text_input("宿舍号 / Blok & No. Kamar Mes *")
            agama = st.text_input("宗教 / Agama (Jika ada)")
            
        st.divider()
        st.write("📅 **出生信息 / Informasi Kelahiran**")
        c_tmpt, c_tgl = st.columns(2)
        tmpt_lahir = c_tmpt.text_input("出生地点 / Tempat Lahir")
        tgl_lahir = c_tgl.date_input("出生日期 / Tanggal Lahir", min_value=datetime(1950,1,1))

        submit = st.form_submit_button("提交 / KIRIM PENDAFTARAN", use_container_width=True)
        
        if submit:
            if not nama_pasien or not nik_id or not wechat or not dept:
                st.error("❌ 请填写所有必填项 / Mohon lengkapi kolom yang wajib diisi (*)")
            else:
                simpan_data_cina(nama_pasien.upper(), nama_mandarin, nik_id, gender, wechat, 
                                 darah, perusahaan, dept.upper(), jabatan.upper(), mes.upper(), 
                                 agama, tmpt_lahir, tgl_lahir)
                st.session_state.submitted = True
                st.rerun()

# --- 4. TABEL MONITORING (UNTUK ADMIN) ---
@st.fragment(run_every="5s") # Auto refresh setiap 5 detik
def tabel_monitoring_cina():
    st.markdown("### 📋 实时登记名单 / Daftar Pendaftaran Real-time")
    with get_connection() as conn:
        # Ambil data pendaftaran hari ini
        tgl_hari_ini = datetime.now().strftime("%Y-%m-%d")
        query = f"""
        SELECT tgl_daftar, nama_mandarin, nama_lengkap, nik, wechat_id, 
               departemen, blok_mes, status_antrian 
        FROM pasien 
        WHERE tgl_daftar LIKE '{tgl_hari_ini}%'
        ORDER BY id DESC
        """
        df = pd.read_sql(query, conn)
    
    if not df.empty:
        st.dataframe(
            df, 
            column_config={
                "tgl_daftar": st.column_config.DatetimeColumn("时间 / Waktu", format="HH:mm"),
                "nama_mandarin": "姓名 / Mandarin",
                "nama_lengkap": "Nama Latin",
                "wechat_id": "WeChat/HP",
                "status_antrian": "状态 / Status"
            },
            use_container_width=True,
            hide_index=True
        )
        st.caption(f"Daftar diperbarui otomatis: {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.info("等待新登记... / Menunggu pendaftaran baru untuk hari ini...")

# --- 5. LOGIKA NAVIGASI ---
def main():
    # Cek mode dari URL (untuk Barcode)
    # Gunakan: ?mode=admin untuk lihat tabel, atau ?mode=pasien untuk isi form
    params = st.query_params
    mode = params.get("mode", "pasien")

    if mode == "admin":
        st.title("🖥️ Dashboard Monitoring Pasien Cina")
        tabel_monitoring_cina()
    else:
        form_pendaftaran_cina()

if __name__ == "__main__":
    main()

@st.fragment(run_every="5s") # Data akan refresh otomatis tanpa reload halaman
def tampilkan_daftar_pasien():
    st.divider()
    st.subheader("📋 Daftar Pasien Baru Terdaftar (Real-time)")
    
    with get_connection() as conn:
        # Mengambil data terbaru berdasarkan waktu daftar hari ini
        tgl_hari_ini = datetime.now().strftime("%Y-%m-%d")
        query = f"SELECT * FROM pasien WHERE tgl_daftar LIKE '{tgl_hari_ini}%' ORDER BY id DESC"
        df = pd.read_sql(query, conn)

    if not df.empty:
        # Menampilkan tabel dengan kolom yang disesuaikan
        st.dataframe(
            df[[
                'tgl_daftar', 'nama_mandarin', 'nama_lengkap', 'nik', 
                'perusahaan', 'departemen', 'wechat_id', 'status_antrian'
            ]],
            column_config={
                "tgl_daftar": "Jam",
                "nama_mandarin": "姓名 (Mandarin)",
                "nama_lengkap": "Nama Latin",
                "wechat_id": "WeChat/HP",
                "status_antrian": "Status"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Belum ada pasien yang mendaftar hari ini.")
