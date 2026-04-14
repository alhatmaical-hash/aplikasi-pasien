import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time
from supabase import create_client, Client

# --- 0. KONFIGURASI SUPABASE ---
# Ambil dari: Project Settings -> API
SUPABASE_URL = "https://yfbbkmufyliwznknmpxf.supabase.co"
SUPABASE_KEY = "sb_publishable_E7zuHs4UDqcNCOEFYP20Tw_a9zXLGiK"

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- 1. INISIALISASI SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'role': "",
        'username': "",
        'skd_dept': None
    })

# --- 2. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Klinik Apps Cloud", page_icon="🏥", layout="wide")
st.markdown("""
    <style>
    div[data-testid="stWidgetLabel"] p { font-size: 18px !important; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNGSI HELPER ---
def get_master(kategori):
    res = supabase.table("master_data").select("*").eq("kategori", kategori).execute()
    return pd.DataFrame(res.data)

# --- 4. NAVIGASI ---
params = st.query_params
is_pasien_mode = params.get("mode") == "pasien"

if is_pasien_mode:
    menu = "Pendaftaran / 登记"
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
elif st.session_state['logged_in']:
    st.sidebar.title("🏥 Klinik Apps")
    st.sidebar.success(f"🔓 {st.session_state['role']}: {st.session_state['username']}")
    menu_list = ["Pendaftaran Pasien", "Rekam Medis / 病历", "SKD / 医生证明", "Dashboard Analitik", "Pengaturan Master / 设置"] if st.session_state['role'] == "Admin" else ["SKD / 医生证明"]
    menu = st.sidebar.selectbox("Pilih Menu", menu_list)
    if st.sidebar.button("🚪 Logout"):
        st.session_state.update({"logged_in": False, "role": "", "username": ""})
        st.rerun()
else:
    st.sidebar.title("🏥 Klinik Apps")
    page_mode = st.sidebar.radio("Navigasi", ["Login Staff", "Form Pendaftaran"])
    if page_mode == "Form Pendaftaran":
        menu = "Pendaftaran / 登记"
    else:
        st.markdown("<h2 style='text-align: center;'>🔐 Login Staff</h2>", unsafe_allow_html=True)
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            res = supabase.table("users").select("*").eq("username", user).eq("password", pw).execute()
            if res.data:
                st.session_state.update({"logged_in": True, "username": res.data[0]['username'], "role": res.data[0]['role']})
                st.rerun()
            else: st.error("Akses Ditolak")
        st.stop()

# --- 5. LOGIKA MENU ---

if menu in ["Pendaftaran Pasien", "Pendaftaran / 登记"]:
    st.header("📝 Pendaftaran Pasien")
    
    # Ambil Dokter Jaga Otomatis
    res_dr = supabase.table("dokter_jaga_harian").select("nama_dokter").execute()
    dokter_jaga = [d['nama_dokter'] for d in res_dr.data]
    
    if dokter_jaga:
        tz_wit = pytz.timezone('Asia/Jayapura')
        tgl_hari_ini = datetime.now(tz_wit).strftime("%Y-%m-%d")
        res_count = supabase.table("pasien").select("id", count="exact").filter("tgl_daftar", "gte", tgl_hari_ini).execute()
        idx = (res_count.count // 5) % len(dokter_jaga)
        dokter_terpilih = dokter_jaga[idx]
        st.info(f"Dokter Jaga Hari Ini: **{dokter_terpilih}**")
    else:
        st.error("⚠️ Dokter jaga belum diatur."); st.stop()

    with st.form("form_pendaftaran", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nama = st.text_input("Nama Lengkap *")
            nik = st.text_input("NIK *", max_chars=16)
            gender = st.selectbox("Gender", ["Laki-laki", "Perempuan"])
            agama = st.text_input("Agama")
            no_hp = st.text_input("No HP *")
        with col2:
            tmpt_lhr = st.text_input("Tempat Lahir")
            tgl_lhr = st.date_input("Tanggal Lahir", value=None)
            perusahaan = st.selectbox("Perusahaan", [""] + get_master("Perusahaan")['nama'].tolist())
            dept = st.selectbox("Departemen", [""] + get_master("Departemen")['nama'].tolist())
            jabatan = st.text_input("Jabatan")
        with col3:
            blok_mes = st.text_input("Blok Mes")
            gol_darah = st.selectbox("Gol. Darah", ["-", "A", "B", "AB", "O"])
            alergi = st.text_input("Alergi (Jika ada)")
            jk_kunjungan = st.selectbox("Jenis Kunjungan", ["Berobat", "Kontrol MCU", "Masuk UGD", "Kontrol Post Rujuk"])
            pernah = st.radio("Pernah Berobat?", ["Belum Pernah", "Iya Sudah"], horizontal=True)

        lokasi = st.text_area("Lokasi Kerja Spesifik / Detail Keluhan")
        
        if st.form_submit_button("KIRIM PENDAFTARAN"):
            if not nama or not nik or not no_hp:
                st.warning("Nama, NIK, dan No HP wajib diisi!")
            else:
                tz = pytz.timezone('Asia/Jayapura')
                now = datetime.now(tz).isoformat()
                data_pasien = {
                    "tgl_daftar": now, "nama_lengkap": nama.upper(), "nik": nik,
                    "gender": gender, "agama": agama, "no_hp": no_hp,
                    "pernah_berobat": pernah, "perusahaan": perusahaan, "departemen": dept,
                    "jabatan": jabatan, "blok_mes": blok_mes, "gol_darah": gol_darah,
                    "alergi": alergi, "dokter": dokter_terpilih, "jenis_kunjungan": jk_kunjungan,
                    "lokasi_kerja": lokasi, "tgl_lahir": f"{tmpt_lhr}, {tgl_lhr}",
                    "status_antrian": "Normal"
                }
                supabase.table("pasien").insert(data_pasien).execute()
                st.success("✅ Pendaftaran Berhasil!"); st.balloons(); time.sleep(2); st.rerun()

elif menu == "Rekam Medis / 病历":
    st.header("📊 Rekam Medis & Antrian")
    res_all = supabase.table("pasien").select("*").order("id", desc=True).execute()
    if res_all.data:
        st.dataframe(pd.DataFrame(res_all.data), use_container_width=True)
    else:
        st.info("Belum ada data pasien.")
