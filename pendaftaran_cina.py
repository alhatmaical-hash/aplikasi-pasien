import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import pytz

# --- KONFIGURASI ---
st.set_page_config(page_title="Klinik Apps - China Patient", layout="wide")

def get_connection():
    return sqlite3.connect("klinik_data.db", check_same_thread=False)

# 1. INISIALISASI DATABASE (UPDATE: Tambah Tabel Master)
def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        # Tabel Pasien
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
                        tgl_lahir TEXT,
                        status_antrian TEXT DEFAULT 'Menunggu')''')
        
        # Tabel Master Perusahaan, Dept, Jabatan
        c.execute('CREATE TABLE IF NOT EXISTS master_pt (nama TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS master_dept (nama TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS master_jabatan (nama TEXT UNIQUE)')
        
        # Isi data awal jika kosong
        c.execute("INSERT OR IGNORE INTO master_pt VALUES ('HPAL'), ('HJF'), ('HNC'), ('TBP')")
        conn.commit()

init_db()

# --- FUNGSI AMBIL DATA MASTER ---
def get_master(table):
    with get_connection() as conn:
        return [r[0] for r in conn.execute(f"SELECT nama FROM {table} ORDER BY nama ASC").fetchall()]

# --- FUNGSI SIMPAN DATA PASIEN ---
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
st.sidebar.title("🏥 Menu Navigasi")
pilihan = st.sidebar.radio("Pilih Tampilan:", [
    "📝 Pendaftaran (Pasien)", 
    "📋 Data Terdaftar (Petugas)",
    "⚙️ Pengaturan Master"
])

# --- HALAMAN 1: FORMULIR PENDAFTARAN ---
if pilihan == "📝 Pendaftaran (Pasien)":
    st.markdown("<h2 style='text-align: center;'>CN 挂号表 / Formulir Pendaftaran</h2>", unsafe_allow_html=True)
    
    # Ambil list dari database master
    list_pt = get_master("master_pt")
    list_dept = get_master("master_dept")
    list_jabatan = get_master("master_jabatan")

    with st.form("form_pendaftaran", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama_m = st.text_input("中文姓名 / Nama Mandarin", placeholder="例: 王小明")
            nama_l = st.text_input("英文姓名 / Nama Sesuai Paspor (Latin) *").upper()
            nik = st.text_input("证件号码 / NIK atau No. Paspor *")
            gender = st.radio("性别 / Jenis Kelamin", ["男 (Laki-laki)", "女 (Perempuan)"], horizontal=True)
            wechat = st.text_input("微信 ID 或 手机号 / ID WeChat atau No. HP *")
            darah = st.selectbox("血型 / Golongan Darah", ["A", "B", "AB", "O", "不清楚 (Tidak Tahu)"])
        
        with col2:
            pt = st.selectbox("公司 / Perusahaan *", list_pt)
            dept = st.selectbox("部门 / Departemen *", list_dept) if list_dept else st.text_input("部门 / Departemen *").upper()
            jab = st.selectbox("职位 / Jabatan *", list_jabatan) if list_jabatan else st.text_input("职位 / Jabatan *").upper()
            mes = st.text_input("宿舍号 / Blok & No. Kamar Mes *").upper()
            
            opsi_agama = ["伊斯兰教 (Islam)", "基督教 (Kristen)", "天主教 (Katolik)", "印度教 (Hindu)", "佛教 (Buddha)", "儒教 (Konghucu)", "无宗教/不详 (Tidak Diketahui)"]
            agama = st.selectbox("宗教 / Agama", opsi_agama)
            
        st.write("📅 **出生信息 / Informasi Kelahiran**")
        c3, c4 = st.columns(2)
        tmpt = c3.text_input("出生地点 / Tempat Lahir")
        tgl = c4.date_input("出生日期 / Tanggal Lahir", value=datetime(2026, 4, 29))

        if st.form_submit_button("提交 / KIRIM PENDAFTARAN", use_container_width=True):
            if not nama_l or not nik or not wechat:
                st.error("❌ Mohon isi kolom wajib (*)")
            else:
                simpan_data({'mandarin': nama_m, 'nama': nama_l, 'nik': nik, 'gender': gender, 'wechat': wechat, 'darah': darah, 'pt': pt, 'dept': dept, 'jab': jab, 'mes': mes, 'agama': agama, 'tmpt': tmpt, 'tgl': str(tgl)})
                st.success("✅ Berhasil terdaftar! / 提交成功！")

# --- HALAMAN 2: MONITORING PETUGAS ---
elif pilihan == "📋 Data Terdaftar (Petugas)":
    st.header("📋 Daftar Pasien Terdaftar")
    @st.fragment(run_every="5s")
    def refresh_data():
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM pasien ORDER BY id DESC", conn)
        if not df.empty:
            st.dataframe(df[['tgl_daftar', 'nama_mandarin', 'nama_lengkap', 'perusahaan', 'wechat_id', 'status_antrian']], use_container_width=True, hide_index=True)
    refresh_data()

# --- HALAMAN 3: PENGATURAN MASTER (BARU) ---
elif pilihan == "⚙️ Pengaturan Master":
    st.header("⚙️ Pengaturan List Dropdown")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.subheader("🏢 Perusahaan")
        baru_pt = st.text_input("Tambah Perusahaan")
        if st.button("Tambah PT"):
            if baru_pt:
                with get_connection() as conn:
                    conn.execute("INSERT OR IGNORE INTO master_pt VALUES (?)", (baru_pt.upper(),))
                st.rerun()
        st.write(get_master("master_pt"))

    with col_b:
        st.subheader("📁 Departemen")
        baru_dept = st.text_input("Tambah Departemen")
        if st.button("Tambah Dept"):
            if baru_dept:
                with get_connection() as conn:
                    conn.execute("INSERT OR IGNORE INTO master_dept VALUES (?)", (baru_dept.upper(),))
                st.rerun()
        st.write(get_master("master_dept"))

    with col_c:
        st.subheader("💼 Jabatan")
        baru_jabatan = st.text_input("Tambah Jabatan")
        if st.button("Tambah Jabatan"):
            if baru_jabatan:
                with get_connection() as conn:
                    conn.execute("INSERT OR IGNORE INTO master_jabatan VALUES (?)", (baru_jabatan.upper(),))
                st.rerun()
        st.write(get_master("master_jabatan"))
