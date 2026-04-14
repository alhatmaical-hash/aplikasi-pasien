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

def get_master(kategori):
    if kategori == "Dokter":
        return [
            "DR. JOKO", 
            "DR. DEDEK", 
            "DR. KARTIKA", 
            "DR. DOMINICUS", 
            "DR. ANDIKA", 
            "DR. RANDY"
        ]
    # Mengambil data dari tabel master_data
    res = supabase.table("master_data").select("nama").eq("kategori", kategori).execute()
    df = pd.DataFrame(res.data)
    if df.empty:
        return []
    return df['nama'].tolist() # Mengembalikan list nama untuk selectbox

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
# --- MENU REKAM MEDIS ---
elif menu == "Rekam Medis / 病历":
    from streamlit_autorefresh import st_autorefresh
    # Refresh otomatis agar data dari pasien yang mendaftar di HP langsung muncul
    st_autorefresh(interval=5000, key="datarefresh") 
    
    st.header("📊 Menu Rekam Medis")

    # --- BAGIAN 1: ATUR DOKTER JAGA ---
    # --- BAGIAN 1: ATUR DOKTER JAGA ---
    with st.expander("👨‍⚕️ Atur Dokter Jaga Hari Ini", expanded=False):
        # Tambahkan nama-nama dokter baru di sini
        opts_dr = [
            "DR. JOKO", 
            "DR. DEDEK", 
            "DR. KARTIKA", 
            "DR. DOMINICUS", 
            "DR. ANDIKA", 
            "DR. RANDY"
        ]
        
        # Ambil dokter yang sedang aktif di Supabase agar tidak hilang saat refresh
        try:
            res_dr = supabase.table("dokter_jaga_harian").select("nama_dokter").execute()
            dr_aktif_db = [d['nama_dokter'] for d in res_dr.data]
        except:
            dr_aktif_db = []
        
        # Menampilkan multiselect dengan daftar dokter baru
        pilihan = st.multiselect(
            "Pilih Dokter yang Bertugas", 
            opts_dr, 
            default=[d for d in dr_aktif_db if d in opts_dr], 
            placeholder="Pilih dokter..."
        )
        
        if st.button("Simpan Jadwal Dokter"):
            # Hapus jadwal lama di Supabase
            supabase.table("dokter_jaga_harian").delete().neq("nama_dokter", "clear_all").execute()
            
            # Masukkan dokter yang dipilih
            if pilihan:
                data_input = [{"nama_dokter": dr} for dr in pilihan]
                supabase.table("dokter_jaga_harian").insert(data_input).execute()
            
            st.success("Jadwal Dokter Berhasil Diperbarui!")
            st.rerun()

    # --- BAGIAN 2: OTORISASI DAFTAR ULANG ---
    with st.expander("🔐 Otorisasi Daftar Ulang"):
        st.info("Gunakan fitur ini untuk memberi izin NIK yang sudah terdaftar hari ini agar bisa daftar kembali.")
        nik_izin = st.text_input("Masukkan NIK Pasien")
        if st.button("Berikan Izin Akses"):
            if nik_izin:
                tz_wit = pytz.timezone('Asia/Jayapura')
                tgl_skrg = datetime.now(tz_wit).strftime("%Y-%m-%d")
                # Update status izin di Supabase
                supabase.table("pasien").update({"is_authorized": 1}).eq("nik", nik_izin).like("tgl_daftar", f"{tgl_skrg}%").execute()
                st.success(f"Berhasil! NIK {nik_izin} sekarang diizinkan.")
            else:
                st.warning("Silakan masukkan NIK.")

    # --- BAGIAN 3: TABEL ANTRIAN ---
    st.write("---")
    st.subheader("📋 Daftar Antrian Pasien")
    
    # 1. FUNGSI WARNA BARIS
    def color_row(row):
        status = row.get('status_antrian', '')
        if status == "Menunggu Konsul Dokter": 
            return ['background-color: #ffff00; color: black'] * len(row)
        elif status == "Menunggu Hasil Lab & Radiologi": 
            return ['background-color: #00b0f0; color: white'] * len(row)
        elif status == "Batas Download SKD": 
            return ['background-color: #ff9900; color: white'] * len(row)
        elif status == "Batas Operan & Daftar Pasien": 
            return ['background-color: #c8e6c9; color: black'] * len(row)
        elif status == "Batal Berobat": 
            return ['background-color: #ff4b4b; color: white'] * len(row)
        return [''] * len(row)

    # 2. FILTER LAYOUT
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1], gap="small")
    with col_f1:
        search_term = st.text_input("🔍 Cari Nama Pasien", "", key="search_rekam_medis")
    with col_f2:
        list_bulan = ["Semua", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        bulan_selected = st.selectbox("Pilih Bulan", list_bulan, index=datetime.now().month)
    with col_f3:
        list_tahun = ["Semua"] + [str(t) for t in range(2025, 2035)]
        tahun_selected = st.selectbox("Pilih Tahun", list_tahun, index=1)

    # 3. AMBIL DATA DARI CLOUD
    try:
        res = supabase.table("pasien").select("*").order("id", desc=True).execute()
        df = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Gagal koneksi ke Cloud: {e}")
        df = pd.DataFrame()

    if not df.empty:
        # Rename kolom untuk tampilan
        df = df.rename(columns={
            "tgl_daftar": "Tgl Daftar", "nama_lengkap": "Nama Lengkap", "nik": "NIK/ID",
            "no_hp": "WhatsApp", "perusahaan": "Perusahaan", "departemen": "Departemen"
        })
        df['tgl_dt'] = pd.to_datetime(df['Tgl Daftar'], errors='coerce')
        df_tampil = df.copy()

        # Eksekusi Filter
        if search_term:
            df_tampil = df_tampil[df_tampil['Nama Lengkap'].str.contains(search_term, case=False, na=False)]
        if bulan_selected != "Semua":
            df_tampil = df_tampil[df_tampil['tgl_dt'].dt.month == list_bulan.index(bulan_selected)]
        if tahun_selected != "Semua":
            df_tampil = df_tampil[df_tampil['tgl_dt'].dt.year == int(tahun_selected)]

        # Tampilkan Tabel
        st.dataframe(
            df_tampil.style.apply(color_row, axis=1), 
            use_container_width=True, hide_index=True,
            column_config={"id": None, "tgl_dt": None}
        )

        # --- FITUR DOWNLOAD CSV ---
        csv = df_tampil.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "data_rekam_medis.csv", "text/csv")

        # --- FITUR EDIT / RENAME ---
        st.divider()
        with st.expander("✏️ Edit / Rename Nama Pasien"):
            opsi_edit = df_tampil.apply(lambda x: f"{x['id']} | {x['Nama Lengkap']}", axis=1).tolist()
            data_terpilih = st.selectbox("Pilih Pasien untuk diperbaiki", opsi_edit)
            id_target = data_terpilih.split(" | ")[0]
            nama_lama = data_terpilih.split(" | ")[1]
            nama_baru = st.text_input("Input Nama yang Benar", value=nama_lama)
            
            if st.button("Simpan Perubahan Nama"):
                if nama_baru:
                    supabase.table("pasien").update({"nama_lengkap": nama_baru.strip().upper()}).eq("id", id_target).execute()
                    st.success("Nama Berhasil Diperbarui!")
                    st.rerun()

        # --- FITUR UPDATE STATUS (WARNA) ---
        st.divider()
        with st.expander("🔄 Ganti Status Pasien (Ubah Warna)"):
            nama_p = st.selectbox("Pilih Nama Pasien", df['Nama Lengkap'].tolist(), key="sb_status")
            status_list = ["Normal", "Menunggu Konsul Dokter", "Menunggu Hasil Lab & Radiologi", "Batal Berobat"]
            status_baru = st.selectbox("Pilih Status Baru", status_list)
            if st.button("Simpan Status"):
                supabase.table("pasien").update({"status_antrian": status_baru}).eq("nama_lengkap", nama_p).execute()
                st.success("Status Diperbarui!")
                st.rerun()

        # --- FITUR HAPUS ---
        st.divider()
        with st.expander("🗑️ Hapus Data Pasien"):
            pilihan_hapus = df.apply(lambda x: f"{x['id']} | {x['Nama Lengkap']}", axis=1).tolist()
            sel_hapus = st.selectbox("Pilih Data yang akan dihapus", pilihan_hapus)
            if st.button("Hapus Data Sekarang", type="primary"):
                id_hapus = sel_hapus.split(" | ")[0]
                supabase.table("pasien").delete().eq("id", id_hapus).execute()
                st.warning("Data Berhasil Dihapus!")
                st.rerun()

    else:
        st.info("Belum ada data pasien di database Cloud.")

            
# --- MENU SKD ---
elif menu == "SKD / 医生证明":
    st.header("📄 Arsip SKD")
    
   # 1. Tambah Departemen Baru dengan Proteksi Password
    with st.expander("➕ Tambah Folder Departemen Baru"):
        # Input Nama Departemen
        new_f = st.text_input("Nama Departemen Baru", key="input_nama_dept_skd")
        
        # Tambahkan Input Password
        pwd_tambah_dept = st.text_input("Hanya Petugas Rekam Medis Yang Bisa Menambahkan Folder", 
                                       type="password", 
                                       key="pwd_tambah_dept_skd")
        
        if st.button("Buat Folder", key="btn_save_dept_skd"):
            # Cek apakah password benar
            if pwd_tambah_dept == "admin123": # Sesuaikan dengan password Anda
                if new_f:
                    try:
                        with get_connection() as conn:
                            # Pastikan tabel 'master_data' memiliki kolom 'kategori' dan 'nama'
                            conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", 
                                       ("Departemen", new_f))
                            conn.commit()
                        st.success(f"Folder '{new_f}' berhasil dibuat!")
                        # Rerun sangat penting agar daftar di bawahnya langsung terupdate
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Gagal membuat folder: {e}")
                else:
                    st.warning("Nama departemen tidak boleh kosong.")
            else:
                st.error("Sandi Admin Salah! Akses ditolak.")

    # 2. Filter Waktu
    daftar_bulan = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    
    tahun_sekarang = datetime.now().year
    opsi_tahun = list(range(2024, tahun_sekarang + 2))

    col_f1, col_f2 = st.columns(2)
    
    # Pilih Nama Bulan
    f_nama_bulan = col_f1.selectbox(
        "Filter Bulan", 
        options=daftar_bulan, 
        index=datetime.now().month - 1
    )
    
    # Pilih Tahun (Otomatis update tiap tahun)
    f_tahun = col_f2.selectbox(
        "Filter Tahun", 
        options=opsi_tahun, 
        index=opsi_tahun.index(tahun_sekarang)
    )

    # Konversi Nama Bulan ke Angka untuk kebutuhan Database (1-12)
    f_bulan = daftar_bulan.index(f_nama_bulan) + 1
    # --- FITUR HAPUS SEMUA DATA (TEMPEL DI SINI) ---
    st.markdown("---")
    with st.expander("🗑️ Zona Bahaya: Hanya Petugas Rekam Medis Yang Bisa Akses Ini"):
        st.error(f"PERINGATAN: Anda akan menghapus SELURUH file SKD periode {f_nama_bulan} {f_tahun}!")
        pwd_admin = st.text_input("Masukkan Password Admin", type="password", key="pwd_del_all")
        
        if st.button("KONFIRMASI HAPUS SEMUA DATA", type="primary"):
            if pwd_admin == "admin123": # Ganti password sesuai keinginan
                try:
                    with get_connection() as conn:
                        conn.execute("DELETE FROM skd_files WHERE bulan_skd=? AND tahun_skd=?", (f_bulan, f_tahun))
                        conn.commit()
                    st.success(f"Berhasil! Data periode {f_nama_bulan} {f_tahun} telah dibersihkan.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menghapus: {e}")
            else:
                st.error("Password Salah!")

    # 3. Ambil Daftar Departemen (Folder)
    try:
        # Gunakan f_bulan dan f_tahun di bawah ini jika ingin memfilter daftar folder berdasarkan data yang ada
        with get_connection() as conn:
            df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
            daftar_folder = df_dept['nama'].tolist()
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]

    # 3. Ambil Daftar Departemen (Folder)
    try:
        with get_connection() as conn:
            df_dept = pd.read_sql_query("SELECT DISTINCT nama FROM master_data WHERE kategori='Departemen'", conn)
            daftar_folder = df_dept['nama'].tolist()
    except:
        daftar_folder = ["PRODUCTION", "OFFICE", "LOGISTIC"]

    st.write("### Pilih Departemen:")
    cols = st.columns(4)
    for idx, d in enumerate(daftar_folder):
        if cols[idx % 4].button(f"📂 {d}", use_container_width=True, key=f"fldr_{d}_{idx}"):
            st.session_state['sel_dept'] = d
            st.rerun()

    # 4. Tampilkan Isi Folder Jika Sudah Dipilih
    if 'sel_dept' in st.session_state:
        # Baris 488: Semua kode di bawah ini HARUS menjorok ke dalam
        st.divider() 
        target = st.session_state['sel_dept']
        st.subheader(f"Folder: {target} ({f_bulan}/{f_tahun})")
    
        # Form Upload (juga harus menjorok)
        with st.expander("➕ Upload PDF Baru"):
            with st.form("upload_skd_form", clear_on_submit=True):
                u_files = st.file_uploader("Pilih PDF", type=['pdf'], accept_multiple_files=True)
            
                if st.form_submit_button("Simpan Ke Folder"):
                    if u_files:
                        try:
                            with get_connection() as conn:
                                for u_f in u_files:
                                    file_content = u_f.read()
                                    conn.execute("""
                                        INSERT INTO skd_files 
                                        (nama_pasien, departemen, nama_file, file_data, tgl_upload, bulan_skd, tahun_skd) 
                                        VALUES (?,?,?,?,?,?,?)""", 
                                        (u_f.name, target, u_f.name, file_content, datetime.now(), f_bulan, f_tahun))
                                conn.commit()
                            st.success(f"Berhasil menyimpan {len(u_files)} file!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                else:
                        st.warning("Silakan pilih file terlebih dahulu.")

        # --- BAGIAN PENCARIAN & DAFTAR (HANYA SATU KALI) ---
        st.write("### Daftar File:")
        search_q = st.text_input("🔍 Cari Nama Pasien...", placeholder="Ketik nama untuk mencari...", key="search_skd_final")

        with get_connection() as conn:
            query = f"SELECT * FROM skd_files WHERE departemen='{target}' AND bulan_skd={f_bulan} AND tahun_skd={f_tahun}"
            files = pd.read_sql(query, conn)
            
            if search_q:
                files = files[files['nama_pasien'].str.contains(search_q, case=False, na=False)]

        if not files.empty:
            for i, r in files.iterrows():
                c_n, c_v, c_d, c_x = st.columns([4, 1.2, 1.2, 0.8])
                c_n.text(f"📄 {r['nama_file']}") 
                
                # Tombol Lihat
                if c_v.button("👁️ Lihat", key=f"v_btn_{r['id']}_{i}"):
                    st.download_button("Klik untuk Buka", data=r['file_data'], file_name=r['nama_file'], mime='application/pdf', key=f"dl_v_{i}")
                
                # Tombol Unduh
                c_d.download_button("📥 Unduh", data=r['file_data'], file_name=r['nama_file'], mime='application/pdf', key=f"dl_d_{i}")

                # Tombol Hapus
                if c_x.button("🗑️", key=f"del_btn_{i}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM skd_files WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()
        else:
            st.info("Tidak ada file ditemukan.")
# --- MENU PENGATURAN ---
elif menu == "Pengaturan Master / 设置":
    
    t1, t2, t3 = st.tabs(["Master List", "Fitur Pendaftaran", "Manajemen Akun"])
    
    with t1:
        kat = st.selectbox("Kategori Master", ["Perusahaan", "Departemen", "Jabatan"])
        c_i, c_l = st.columns([1, 2])
        with c_i:
            n = st.text_input(f"Tambah Ke {kat}")
            if st.button("Tambah Data", key="btn_add_master"):
                if n:
                    conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", (kat, n)); conn.commit(); conn.close(); st.rerun()
        with c_l:
            df_master = get_master(kat)
            for i, r in df_master.iterrows():
                ca, cb = st.columns([3, 1])
                ca.text(r['nama'])
                if cb.button("Hapus", key=f"m_del_{r['id']}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()

    with t2:
        st.subheader("🛠 Custom Kolom Form Pendaftaran")
        st.info("Ketik nama kolom baru (misal: 'No WhatsApp' atau 'Nama Ayah') untuk ditambahkan ke form.")
        c_i2, c_l2 = st.columns([1, 2])
        with c_i2:
            f_baru = st.text_input("Nama Fitur Baru")
            if st.button("Simpan Fitur", key="btn_add_fitur"):
                if f_baru:
                    conn = get_connection(); conn.execute("INSERT INTO master_data (kategori, nama) VALUES (?,?)", ("Fitur Pendaftaran", f_baru)); conn.commit(); conn.close(); st.rerun()
        with c_l2:
            df_f = get_master("Fitur Pendaftaran")
            for i, r in df_f.iterrows():
                ca, cb = st.columns([3, 1])
                ca.text(r['nama'])
                if cb.button("Hapus", key=f"fit_del_{r['id']}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM master_data WHERE id=?", (r['id'],))
                        conn.commit()
                    st.rerun()

    with t3:
        st.subheader("👥 Manajemen Akun Tim")
        with st.form("tambah_user_form"):
            un = st.text_input("Username Baru")
            up = st.text_input("Password Baru", type="password")
            # Menambahkan pilihan Role
            ur = st.selectbox("Role", ["Admin", "Staff"])
            
            submit_user = st.form_submit_button("Tambah User")
            
            if submit_user:
                if un and up:
                    try:
                        with get_connection() as conn:
                            conn.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (un, up, ur))
                            conn.commit()
                        st.success(f"User {un} berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah user: {e}")
                else:
                    st.warning("Mohon isi username dan password.")

        # Menampilkan daftar user yang ada
        st.write("---")
        st.write("### Daftar User Aktif")
        with get_connection() as conn:
            df_users = pd.read_sql("SELECT username, role FROM users", conn)
            st.table(df_users)
        
        st.write("Daftar Akun:")
        conn = get_connection()
        # Ambil username dan role untuk ditampilkan
        u_df = pd.read_sql("SELECT username, role FROM users", conn)
        conn.close()
        
        for i, row in u_df.iterrows():
            # Jangan hapus admin utama
            if row['username'] != 'admin':
                cx, cy = st.columns([3, 1])
                # Menampilkan username dan role-nya
                cx.text(f"👤 {row['username']} ({row['role']})")
                if cy.button("Hapus Akun", key=f"u_del_{row['username']}"):
                    conn = get_connection()
                    conn.execute("DELETE FROM users WHERE username=?", (row['username'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
        # update files check 09-04-2026
elif menu == "Dashboard Analitik":
    st.header("📊 Analisis Data Kunjungan Pasien")
    
    # --- 1. FILTER PERIODE SHIFT (Sudah Menjorok ke Dalam) ---
    with st.container(border=True):
        st.subheader("⏱️ Pilih Waktu Laporan")
        col_shift, col_tgl = st.columns([1, 2])
        
        with col_shift:
            shift = st.radio(
                "Pilih Shift:", 
                [
                    "Pagi (07:00 - 18:00)", 
                    "Jam Malam (1) 18:00 - 22:00", 
                    "Jam Malam (2) 22:00 - 06:00",
                    "Malam Full (18:00 - 07:00)"
                ], 
                horizontal=False
            )
            
        with col_tgl:
            tgl_laporan = st.date_input("📅 Tanggal Laporan", datetime.now())

        # --- Logika Jam & Rentang Data ---
        if "Pagi" in shift:
            j1, j2 = "07:00:00", "18:00:00"
            t1, t2 = tgl_laporan, tgl_laporan
        elif "(1)" in shift:
            j1, j2 = "18:00:00", "22:00:00"
            t1, t2 = tgl_laporan, tgl_laporan
        elif "(2)" in shift:
            j1, j2 = "22:00:01", "06:00:00"
            t1, t2 = tgl_laporan, tgl_laporan + timedelta(days=1)
        else:
            j1, j2 = "18:00:00", "07:00:00"
            t1, t2 = tgl_laporan, tgl_laporan + timedelta(days=1)

        dt_mulai, dt_selesai = f"{t1} {j1}", f"{t2} {j2}"
        st.caption(f"🔎 Rentang Data: **{dt_mulai}** s/d **{dt_selesai}**")

    # --- 2. AMBIL DATA ---
    with get_connection() as conn:
        df_dash = pd.read_sql("SELECT * FROM pasien WHERE tgl_daftar BETWEEN ? AND ?", conn, params=(dt_mulai, dt_selesai))

    if not df_dash.empty:
        # --- 3. PROSES DATA ---
        df_dash['jk'] = df_dash['jenis_kunjungan'].fillna('').astype(str).str.upper()
        df_dash['pb'] = df_dash['pernah_berobat'].fillna('').astype(str).str.upper()

        df_dash['Berobat'] = df_dash['jk'].apply(lambda x: 1 if x == 'BEROBAT' else 0)
        list_k = ['KONTROL', 'RAWAT LUKA', 'POST', 'MCU']
        df_dash['Pasien Kontrol'] = df_dash['jk'].apply(lambda x: 1 if any(k in x for k in list_k) else 0)
        df_dash['UGD'] = df_dash['jk'].apply(lambda x: 1 if 'UGD' in x else 0)
        df_dash['Baru'] = df_dash['pb'].apply(lambda x: 1 if 'BELUM' in x else 0)
        df_dash['Lama'] = df_dash['pb'].apply(lambda x: 1 if 'IYA' in x or 'SUDAH' in x else 0)

        # --- 4. TAMPILKAN METRICS ---
        st.subheader(f"📌 Ringkasan Shift {'Pagi' if 'Pagi' in shift else 'Malam'}")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Pasien", len(df_dash))
        m2.metric("Berobat", int(df_dash['Berobat'].sum()))
        m3.metric("Kontrol", int(df_dash['Pasien Kontrol'].sum()))
        m4.metric("Masuk UGD", int(df_dash['UGD'].sum()))
        m5.metric("Pasien Baru", int(df_dash['Baru'].sum()))
        m6.metric("Pasien Lama", int(df_dash['Lama'].sum()))

        st.divider()

        # --- 5. TABEL RINCIAN ---
        st.subheader("📋 Rincian Departemen & Perusahaan")
        summary = df_dash.groupby(['perusahaan', 'departemen']).agg({
            'Baru': 'sum', 'Lama': 'sum', 'Berobat': 'sum', 'Pasien Kontrol': 'sum', 'UGD': 'sum'
        }).reset_index()
        summary['Total'] = summary[['Berobat', 'Pasien Kontrol', 'UGD']].sum(axis=1)
        st.dataframe(summary.sort_values('Total', ascending=False), use_container_width=True, hide_index=True)

        # --- 6. GRAFIK ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏢 Per Perusahaan")
            pt_data = df_dash.groupby('perusahaan').size().reset_index(name='Jml')
            st.bar_chart(pt_data.set_index('perusahaan'))
        with c2:
            st.subheader("📁 Per Departemen")
            dept_data = df_dash.groupby('departemen').size().reset_index(name='Jml')
            st.bar_chart(dept_data.set_index('departemen'))
    else:
        st.warning(f"⚠️ Tidak ada data pendaftaran untuk shift ini.")
