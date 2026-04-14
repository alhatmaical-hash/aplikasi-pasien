import streamlit as st
import pandas as pd
from datetime import datetime
import io
import pytz
from supabase import create_client, Client

# --- 1. KONEKSI SUPABASE (PERMANEN) ---
try:
    URL = st.secrets["https://yfbbkmufyliwznknmpxf.supabase.co"]
    KEY = st.secrets["sb_publishable_E7zuHs4UDqcNCOEFYP20Tw_a9zXLGiK"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ Koneksi Supabase belum siap. Pastikan Secrets sudah diisi di Streamlit Cloud.")
    st.stop()

# --- 2. INISIALISASI SESSION STATE ---
keys_to_init = ['nama_lengkap', 'nik', 'no_hp', 'blok_mes', 'tgl_lahir', 'lokasi_kerja', 'logged_in', 'username', 'role']
for key in keys_to_init:
    if key not in st.session_state:
        st.session_state[key] = "" if key not in ['logged_in'] else False

# --- 3. KONFIGURASI HALAMAN & CSS ---
st.set_page_config(page_title="Klinik Apps", page_icon="🏥", layout="wide")
st.markdown("""
    <style>
    div[data-testid="stWidgetLabel"] p { font-size: 20px !important; font-weight: bold !important; color: #1E1E1E; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; font-weight: bold; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #d1d3d4; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNGSI MASTER DATA ---
def get_master(kategori):
    # Di masa depan, ini bisa ditarik dari tabel 'master_data' di Supabase
    data = {
        "Dokter": ["DR. JOKO", "DR. DEDEK", "DR. KARTIKA", "DR. DOMINICUS", "DR. ANDIKA", "DR. RANDY"],
        "Perusahaan": ["PT HALMAHERA JAYA FERONIKEL", "PT KARUNIA PERMAI SENTOSA", "PT OBI SINAR TIMUR", "PT CIPTA KEMAKMURAN MITRA"],
        "Departemen": ["HC", "GA", "SAFETY", "PRODUCTION", "ENVIRO", "LOGISTIC", "EXTERNAL"],
        "Jabatan": ["STAFF", "FOREMAN", "SUPERVISOR", "MANAGER", "HELPER", "OPERATOR"],
        "Diagnosis": ["Common Cold", "Dyspepsia", "Myalgia", "Hypertension", "Dermatitis", "Fatigue"]
    }
    return data.get(kategori, [])

# --- 5. LOGIKA NAVIGASI ---
params = st.query_params
is_pasien_mode = params.get("mode") == "pasien"

if is_pasien_mode:
    menu = "Pendaftaran Pasien"
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
elif st.session_state['logged_in']:
    st.sidebar.title("🏥 Klinik Apps")
    st.sidebar.success(f"User: {st.session_state['username']}")
    menu = st.sidebar.radio("Pilih Menu:", ["Pendaftaran Pasien", "Rekam Medis / 病历", "Menu SKD / 医生证明", "Dashboard Analitik", "Pengaturan Master"])
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
else:
    # Halaman Login
    st.markdown("<h2 style='text-align: center;'>🔐 Login Staff Klinik</h2>", unsafe_allow_html=True)
    with st.container():
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        if st.button("Login"):
            # Cek ke tabel 'users' di Supabase
            res = supabase.table("users").select("*").eq("username", user_input).eq("password", pass_input).execute()
            if res.data:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_input
                st.rerun()
            else:
                st.error("Username atau Password salah")
    st.stop()

# --- 6. MENU: PENDAFTARAN PASIEN ---
if menu == "Pendaftaran Pasien":
    st.header("📝 Pendaftaran Pasien Baru")
    tz_wit = pytz.timezone('Asia/Jayapura')
    waktu_sekarang = datetime.now(tz_wit)
    tgl_hari_ini = waktu_sekarang.strftime("%Y-%m-%d")
    
    # Penentuan Dokter Round Robin
    try:
        res_c = supabase.table("pasien").select("id", count="exact").gte("tgl_daftar", f"{tgl_hari_ini} 00:00:00").execute()
        count = res_c.count if res_c.count else 0
        list_dr = get_master("Dokter")
        dr_tujuan = list_dr[(count // 5) % len(list_dr)]
    except: dr_tujuan = "DR. JOKO"

    st.info(f"Pasien diarahkan ke: **{dr_tujuan}**")
    
    with st.form("form_pendaftaran"):
        c1, c2 = st.columns(2)
        with c1:
            nama = st.text_input("Nama Lengkap *", value=st.session_state.nama_lengkap)
            nik = st.text_input("NIK / ID *", value=st.session_state.nik)
            perusahaan = st.selectbox("Perusahaan *", [""] + get_master("Perusahaan"))
            dept = st.selectbox("Departemen *", [""] + get_master("Departemen"))
        with c2:
            hp = st.text_input("No WhatsApp *", value=st.session_state.no_hp)
            tgl_lhr = st.date_input("Tanggal Lahir *", value=None, min_value=datetime(1950,1,1))
            kunjungan = st.selectbox("Jenis Kunjungan", ["Berobat", "Kontrol", "UGD"])
            lokasi = st.text_area("Lokasi Kerja *", value=st.session_state.lokasi_kerja)

        if st.form_submit_button("SIMPAN PENDAFTARAN"):
            if not nama or not nik or not perusahaan:
                st.warning("Mohon isi kolom berbintang (*)")
            else:
                data_ins = {
                    "tgl_daftar": waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S"),
                    "nama_lengkap": nama.upper(), "nik": nik, "perusahaan": perusahaan,
                    "departemen": dept, "no_hp": hp, "tgl_lahir": str(tgl_lhr),
                    "lokasi_kerja": lokasi, "dokter": dr_tujuan, "status_antrian": "Menunggu",
                    "jenis_kunjungan": kunjungan, "is_authorized": 0
                }
                supabase.table("pasien").insert(data_ins).execute()
                st.success(f"Berhasil! Silakan menuju ke {dr_tujuan}")
                st.balloons()

# --- 7. MENU: REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    st.header("📋 Data Rekam Medis Pasien")
    res = supabase.table("pasien").select("*").order("tgl_daftar", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Excel (CSV)", csv, "rekam_medis.csv", "text/csv")

# --- 8. MENU: SKD (SURAT KETERANGAN DOKTER) ---
elif menu == "Menu SKD / 医生证明":
    st.header("📄 Pembuatan SKD")
    st.write("Cari NIK Pasien untuk membuat surat keterangan sakit.")
    search_nik = st.text_input("Masukkan NIK Pasien")
    if search_nik:
        res_skd = supabase.table("pasien").select("*").eq("nik", search_nik).limit(1).execute()
        if res_skd.data:
            p = res_skd.data[0]
            st.success(f"Data ditemukan: {p['nama_lengkap']}")
            st.date_input("Istirahat Mulai Tanggal", value=datetime.now())
            st.number_input("Selama (Hari)", min_value=1, max_value=7)
            if st.button("Cetak SKD (Simulasi)"):
                st.info("Fitur cetak PDF siap diintegrasikan.")
        else:
            st.error("Data NIK tidak ditemukan.")

# --- 9. MENU: DASHBOARD ANALITIK ---
elif menu == "Dashboard Analitik":
    st.header("📊 Dashboard Analitik Klinik")
    res_dash = supabase.table("pasien").select("*").execute()
    if res_dash.data:
        df_dash = pd.DataFrame(res_dash.data)
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Kunjungan", len(df_dash))
        m2.metric("Pasien Hari Ini", len(df_dash[df_dash['tgl_daftar'].str.contains(datetime.now().strftime("%Y-%m-%d"))]))
        m3.metric("Perusahaan Terbanyak", df_dash['perusahaan'].mode()[0] if not df_dash.empty else "-")
        
        st.subheader("Grafik Kunjungan Per Perusahaan")
        st.bar_chart(df_dash['perusahaan'].value_counts())

# --- 10. MENU: PENGATURAN MASTER ---
elif menu == "Pengaturan Master":
    st.header("⚙️ Pengaturan Master Data")
    st.write("Kelola daftar dokter, departemen, dan perusahaan.")
    tab1, tab2, tab3 = st.tabs(["Dokter", "Perusahaan", "Departemen"])
    
    with tab1:
        st.write("Dokter Aktif Saat Ini:")
        st.write(get_master("Dokter"))
        st.text_input("Tambah Dokter Baru")
        st.button("Update Dokter")

    with tab2:
        st.write("Daftar Perusahaan:")
        st.write(get_master("Perusahaan"))
        
    with tab3:
        st.write("Daftar Departemen:")
        st.write(get_master("Departemen"))
