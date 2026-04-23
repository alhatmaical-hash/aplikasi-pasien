import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io
import hashlib
import xlsxwriter

import io

def unduh_rekap_sick_per_grup(df_raw, list_hjf, list_kps, list_ost, list_ckm):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 1. Sheet HJF GROUP
        hjf_data = df_raw[df_raw['company'].str.contains("HALMAHERA", na=False) | df_raw['company'].isin(list_hjf)]
        if not hjf_data.empty:
            hjf_data.to_excel(writer, sheet_name='HJF_GROUP', index=False)
        
        # 2. Sheet KPS GROUP
        kps_data = df_raw[df_raw['company'].str.contains("KARUNIA", na=False) | df_raw['company'].isin(list_kps)]
        if not kps_data.empty:
            kps_data.to_excel(writer, sheet_name='KPS_GROUP', index=False)
            
        # 3. Sheet OST GROUP
        ost_data = df_raw[df_raw['company'].str.contains("OBI SINAR", na=False) | df_raw['company'].isin(list_ost)]
        if not ost_data.empty:
            ost_data.to_excel(writer, sheet_name='OST_GROUP', index=False)
            
        # 4. Sheet CKM GROUP
        ckm_data = df_raw[df_raw['company'].str.contains("CIPTA KEMAKMURAN", na=False) | df_raw['company'].isin(list_ckm)]
        if not ckm_data.empty:
            ckm_data.to_excel(writer, sheet_name='CKM_GROUP', index=False)
            
    return output.getvalue()

# --- 0. KONFIGURASI HALAMAN ---
DB_PATH = 'klinik_data.db'
st.set_page_config(
    page_title="Klinik Apps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)
def tampilkan_laporan_klb():
    st.title("🚨 LAPORAN KEJADIAN LUAR BIASA (KLB)")
    
    try:
        # Gunakan DB_PATH yang sudah kamu definisikan di atas ('klinik_data.db')
        conn = sqlite3.connect(DB_PATH) 
        
        # Ambil data dari tabel rekap_penyakit
        query = "SELECT visit_time, patient_name, diagnosa, clinic, departemen, company FROM rekap_penyakit ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            st.success(f"✅ Terkoneksi! Menampilkan {len(df)} data pasien dari database.")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Database 'rekap_penyakit' ditemukan, tapi isinya masih kosong. Silakan upload CSV dulu.")
            
    except Exception as e:
        st.error(f"❌ Gagal mengambil data: {e}")


    
   

# --- 1. LOGIKA LOGIN & MANAJEMEN USER ---

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_user_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Pastikan tabel user memiliki kolom role
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Cek admin default
    c.execute('SELECT * FROM userstable WHERE username = "admin"')
    if not c.fetchone():
        c.execute('INSERT INTO userstable(username, password, role) VALUES (?,?,?)', 
                  ('admin', make_hashes('admin123'), 'admin'))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password, role FROM userstable WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data and make_hashes(password) == data[0]:
        return data[1] # Mengembalikan Role (admin/user)
    return False

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT username, role FROM userstable", conn)
    conn.close()
    return df

def hapus_user_db(username):
    if username == 'admin':
        return False
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM userstable WHERE username=?", (username,))
    conn.commit()
    conn.close()
    return True

init_user_db()

# --- SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "role" not in st.session_state:
    st.session_state["role"] = "user"

# --- Tampilan Form Login ---
if not st.session_state["authenticated"]:
    st.title("🏥 Akses Terbatas - Klinik Apps")
    with st.container(border=True):
        u_input = st.text_input("Username:", key="login_user")
        p_input = st.text_input("Password:", type="password", key="login_pwd")
        
        if st.button("🚀 MASUK KE SISTEM", use_container_width=True, type="primary"):
            role_found = login_user(u_input, p_input)
            if role_found:
                st.session_state["authenticated"] = True
                st.session_state["username"] = u_input
                st.session_state["role"] = role_found
                st.rerun()
            else:
                st.error("❌ Username atau Password Salah!")
    st.stop()
# --- 2. SETTING DATABASE & FUNGSI ---


def get_date_range():
    try:
        conn = sqlite3.connect(DB_PATH)
        df_range = pd.read_sql_query("SELECT MIN(visit_time) as awal, MAX(visit_time) as akhir FROM rekap_penyakit", conn)
        conn.close()
        if df_range['awal'].iloc[0] is None:
            return date.today(), date.today()
        awal = pd.to_datetime(df_range['awal'].iloc[0]).date()
        akhir = pd.to_datetime(df_range['akhir'].iloc[0]).date()
        return awal, akhir
    except:
        return date.today(), date.today()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Membuat tabel dengan kolom terpisah sesuai gambar
    c.execute('''CREATE TABLE IF NOT EXISTS rekap_penyakit 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  visit_time TEXT, patient_name TEXT, diagnosa TEXT, 
                  clinic TEXT, departemen TEXT, company TEXT,
                  rest_status TEXT, istirahat_hari INTEGER, istirahat_jam INTEGER)''')
    
    # Pastikan migrasi kolom baru masuk ke DB yang sudah ada
    kolom_baru = [('istirahat_hari', 'INTEGER'), ('istirahat_jam', 'INTEGER')]
    for kolom, tipe in kolom_baru:
        try:
            c.execute(f"ALTER TABLE rekap_penyakit ADD COLUMN {kolom} {tipe}")
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- 3. STYLE CSS ---
st.markdown("""
<style>
    div.stButton > button { font-weight: bold !important; color: black !important; border-radius: 8px; }
    button[kind="primary"] { background-color: #FF4B4B !important; }
    h1 { color: #2e7d32; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR NAVIGASI ---
st.sidebar.title("🏥 MENU KLINIK")
menu = st.sidebar.radio("NAVIGASI", 
    ["Upload Data CSV", "Laporan 10 Penyakit", "Laporan Analisis Kunjungan", "Laporan Data Sick", "Analisis Istirahat", "Laporan KLB", "Database Rekam Medis", "Manajemen User"])

if st.sidebar.button("🔴 KELUAR APLIKASI", type="primary", use_container_width=True):
    st.session_state["authenticated"] = False
    st.rerun()

# --- 5. MODUL 1: UPLOAD DATA (VERSI LENGKAP DENGAN SANDI & FIX TANGGAL) ---
if menu == "Upload Data CSV":
    st.markdown("<h1>📤 UPLOAD DATA PASIEN</h1>", unsafe_allow_html=True)
    
    # 1. Definisikan uploader (Mencegah NameError)
    uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # 2. Baca file dan normalisasi nama kolom
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            
            st.write("### 🔍 Pratinjau Data:")
            st.dataframe(df.head(), use_container_width=True)
            
            st.markdown("---")
            
            # 3. AREA VALIDASI ADMIN (Muncul sebelum tombol simpan)
            st.subheader("🔐 Konfirmasi Admin")
            pwd_upload = st.text_input("Masukkan Sandi Admin untuk memproses upload:", type="password", key="pwd_csv_upload")

            if st.button("💾 SIMPAN KE DATABASE", use_container_width=True, type="primary"):
                # Cek apakah sandi benar
                if pwd_upload == "admin123": 
                    conn = sqlite3.connect(DB_PATH)
                    
                    # 4. Pembersihan Baris Kosong & Nama Pasien 'None'
                    df = df.dropna(subset=['patient_name'])
                    df['p_name_check'] = df['patient_name'].astype(str).str.strip().str.lower()
                    df = df[~df['p_name_check'].isin(['none', 'nan', '', 'null'])].copy()

                    if not df.empty:
                    # 5. Fix Tanggal: Versi Pintar (Otomatis deteksi format)
                        try:
                            # Coba konversi dengan mendeteksi format secara otomatis
                            # Kita hapus parameter format kaku dan biarkan pandas menebak
                            df['visit_time'] = pd.to_datetime(
                                df['visit_time'], 
                                errors='coerce'
                            ).dt.strftime('%Y-%m-%d')
                        except:
                            # Jika gagal, gunakan cara manual yang lebih aman
                            df['visit_time'] = pd.to_datetime(
                                df['visit_time'], 
                                dayfirst=False, # Karena kamu mau Bulan dulu baru Hari
                                errors='coerce'
                            ).dt.strftime('%Y-%m-%d')
                        st.write(f"DEBUG: Berhasil konversi {df['visit_time'].notna().sum()} baris tanggal.")
                   
                        
                        
                        # 6. Kolom Wajib (Pastikan sesuai dengan struktur tabel database kamu)
                        kolom_wajib = ['visit_time', 'patient_name', 'diagnosa', 'clinic', 'departemen', 'company', 'rest_status', 'istirahat_hari', 'istirahat_jam']
                        
                        # Tambahkan kolom jika tidak ada di CSV agar tidak error saat simpan
                        for col in kolom_wajib:
                            if col not in df.columns:
                                df[col] = 0 if 'istirahat' in col else "-"
                        
                        # 7. Siapkan data final & Konversi angka
                        df_to_save = df[kolom_wajib].copy()
                        df_to_save['istirahat_hari'] = pd.to_numeric(df_to_save['istirahat_hari'], errors='coerce').fillna(0).astype(int)
                        df_to_save['istirahat_jam'] = pd.to_numeric(df_to_save['istirahat_jam'], errors='coerce').fillna(0).astype(int)

                        # 8. Simpan ke SQLite
                        df_to_save.to_sql('rekap_penyakit', conn, if_exists='append', index=False)
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Berhasil! {len(df_to_save)} data pasien telah tersambung ke database.")
                        st.balloons()
                    else:
                        st.warning("⚠️ File tidak berisi data pasien yang valid.")
                        if 'conn' in locals(): conn.close()
                
                elif pwd_upload == "":
                    st.warning("⚠️ Silakan masukkan sandi admin terlebih dahulu.")
                else:
                    st.error("❌ Sandi salah! Anda tidak memiliki izin untuk menambah data.")

        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {str(e)}")
            if 'conn' in locals(): conn.close()
# --- 6. MODUL 2: LAPORAN 10 PENYAKIT ---
elif menu == "Laporan 10 Penyakit":
    st.markdown("<h1 style='text-align: center;'>📊 10 PENYAKIT TERBESAR</h1>", unsafe_allow_html=True)
    
    # --- FILTER TANGGAL ---
    t1, t2 = st.columns(2)
    start = t1.date_input("Mulai", value=get_date_range()[0])
    end = t2.date_input("Sampai", value=get_date_range()[1])
    
    # --- AMBIL DATA DARI DATABASE ---
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT diagnosa, COUNT(*) as jumlah 
        FROM rekap_penyakit 
        WHERE visit_time BETWEEN '{start}' AND '{end}' 
        GROUP BY diagnosa 
        ORDER BY jumlah DESC 
        LIMIT 10
    """
    df_top = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_top.empty:
        # --- PERBAIKAN NOMOR URUT (MULAI DARI 1) ---
        df_top.index = range(1, len(df_top) + 1)
        df_top.index.name = 'No'
        
        # 1. Menampilkan Tabel (Tanpa Index Bawaan Pandas)
        st.write("### Tabel Data")
        st.dataframe(df_top.reset_index(), use_container_width=True, hide_index=True)
        
        # 2. Menampilkan Grafik Batang (Menggunakan Altair agar urutan konsisten)
        import altair as alt
        
        st.write("### Visualisasi Grafik")
        
        # Membuat chart dengan altair, sort=None akan menjaga urutan data
        chart = alt.Chart(df_top).mark_bar().encode(
            x=alt.X('diagnosa', sort=None), 
            y='jumlah',
            tooltip=['diagnosa', 'jumlah'] # Menambah interaksi saat mouse diarahkan
        ).properties(height=400)
        
        st.altair_chart(chart, use_container_width=True)
        
        # --- MODUL DOWNLOAD DATA (CSV & EXCEL) ---
        st.markdown("---")
        st.write("#### 📥 Opsi Unduh Laporan")
        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            # Fitur Download CSV
            csv_data = df_top.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data (CSV)",
                data=csv_data,
                file_name=f'10_penyakit_{start}_sd_{end}.csv',
                mime='text/csv',
                use_container_width=True
            )

        with col_dl2:
            # Fitur Download Excel (Memerlukan xlsxwriter)
            import io
            output = io.BytesIO()
            try:
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Simpan data ke sheet 'Laporan'
                    df_top.reset_index().to_excel(writer, index=False, sheet_name='Laporan_10_Besar')
                
                st.download_button(
                    label="📊 Download Data (Excel)",
                    data=output.getvalue(),
                    file_name=f'10_penyakit_{start}_sd_{end}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Gagal memproses Excel: {e}")
                st.info("Gunakan tombol CSV sebagai alternatif.")
                
    else:
        st.warning(f"Tidak ada data ditemukan untuk rentang tanggal {start} sampai {end}.")

# --- MENU 1: ANALISIS KUNJUNGAN ---
elif menu == "Laporan Analisis Kunjungan":
    st.title("📊 Analisis Kunjungan Pasien")
    
    # 1. SETUP TANGGAL (Penting agar variabel t1/t2 tersedia untuk nama file)
    t_awal, t_akhir = get_date_range()
    c1, c2 = st.columns(2)
    start = c1.date_input("Mulai", value=t_awal, key="visit_start")
    end = c2.date_input("Sampai", value=t_akhir, key="visit_end")
    t1_str = start.strftime('%d%m%Y') # Untuk penamaan file download

    # 2. TARIK DATA DARI DATABASE (Solusi Utama agar tidak Blank)
    conn = sqlite3.connect(DB_PATH)
    df_raw = pd.read_sql_query(
        "SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", 
        conn, params=[start, end]
    )
    conn.close()

    # 3. LOGIKA CHECBOX & TAB
    if not df_raw.empty:
        # Inisialisasi Session State untuk Reset Checkbox
        if 'count_dept' not in st.session_state: st.session_state.count_dept = 0
        if 'chk_dept' not in st.session_state: st.session_state.chk_dept = True
        if 'count_corp' not in st.session_state: st.session_state.count_corp = 0
        if 'chk_corp' not in st.session_state: st.session_state.chk_corp = True

        tab1, tab2 = st.tabs(["📊 Departemen", "🏢 Perusahaan"])
        
        # --- TAB 1: DEPARTEMEN ---
        with tab1:
            st.write("### Rekapitulasi Kunjungan Per Departemen")
            dept_counts = df_raw['departemen'].value_counts().reset_index()
            dept_counts.columns = ['Nama Departemen', 'Total Kunjungan']
            
            # Tombol Kontrol
            cb1, cb2, _ = st.columns([1, 1, 3])
            if cb1.button("✅ Pilih Semua Dept", key="btn_all_dept"):
                st.session_state.chk_dept = True
                st.session_state.count_dept += 1
                st.rerun()
            if cb2.button("❌ Kosongkan Dept", key="btn_none_dept"):
                st.session_state.chk_dept = False
                st.session_state.count_dept += 1
                st.rerun()

            dept_counts.insert(0, "Pilih", st.session_state.chk_dept)
            
            col1, col2 = st.columns([1.2, 1.8])
            with col1:
                edited_dept = st.data_editor(
                    dept_counts,
                    column_config={"Pilih": st.column_config.CheckboxColumn("Pilih", default=st.session_state.chk_dept)},
                    disabled=["Nama Departemen", "Total Kunjungan"], 
                    hide_index=True, use_container_width=True,
                    key=f"editor_dept_{st.session_state.count_dept}" 
                )
            
            df_dept_final = edited_dept[edited_dept["Pilih"] == True]
            
            with col2:
                if not df_dept_final.empty:
                    import altair as alt
                    
                    # Membuat grafik dengan Altair agar urutan mengikuti DataFrame
                    chart = alt.Chart(df_dept_final).mark_bar().encode(
                        x=alt.X('Nama Departemen', sort=None),
                        y='Total Kunjungan',
                        tooltip=['Nama Departemen', 'Total Kunjungan']
                    ).properties(height=400)
                    
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.warning("⚠️ Pilih minimal satu departemen.")

            # Tombol Download Dept
            st.markdown("---")
            cd1, cd2 = st.columns(2)
            if not df_dept_final.empty:
                with cd1:
                    csv_dept = df_dept_final[["Nama Departemen", "Total Kunjungan"]].to_csv(index=False).encode('utf-8')
                    st.download_button("📥 CSV (Dept)", data=csv_dept, file_name=f'dept_{t1_str}.csv', mime='text/csv', use_container_width=True)
                with cd2:
                    output_dept = io.BytesIO()
                    with pd.ExcelWriter(output_dept, engine='xlsxwriter') as writer:
                        df_dept_final[["Nama Departemen", "Total Kunjungan"]].to_excel(writer, index=False, sheet_name='Rekap')
                    st.download_button("📊 Excel (Dept)", data=output_dept.getvalue(), file_name=f'dept_{t1_str}.xlsx', use_container_width=True)

        # --- TAB 2: PERUSAHAAN ---
        with tab2:
            st.write("### Rekapitulasi Kunjungan Per Perusahaan")
            corp_counts = df_raw['company'].value_counts().reset_index()
            corp_counts.columns = ['Nama Perusahaan', 'Total Kunjungan']
            
            # Tombol Kontrol
            pb1, pb2, _ = st.columns([1, 1, 3])
            if pb1.button("✅ Pilih Semua Pers", key="btn_all_corp"):
                st.session_state.chk_corp = True
                st.session_state.count_corp += 1
                st.rerun()
            if pb2.button("❌ Kosongkan Pers", key="btn_none_corp"):
                st.session_state.chk_corp = False
                st.session_state.count_corp += 1
                st.rerun()

            corp_counts.insert(0, "Pilih", st.session_state.chk_corp)
            
            p1, p2 = st.columns([1.2, 1.8])
            with p1:
                edited_corp = st.data_editor(
                    corp_counts,
                    column_config={"Pilih": st.column_config.CheckboxColumn("Pilih", default=st.session_state.chk_corp)},
                    disabled=["Nama Perusahaan", "Total Kunjungan"],
                    hide_index=True, use_container_width=True,
                    key=f"editor_corp_{st.session_state.count_corp}"
                )
            
            df_corp_final = edited_corp[edited_corp["Pilih"] == True]
            
            with p2:
                if not df_corp_final.empty:
                    import altair as alt
                    
                    # Grafik diurutkan sesuai urutan DataFrame (tidak diacak secara alfabetis)
                    chart = alt.Chart(df_corp_final).mark_bar().encode(
                        x=alt.X('Nama Perusahaan', sort=None),
                        y='Total Kunjungan',
                        tooltip=['Nama Perusahaan', 'Total Kunjungan']
                    ).properties(height=400)
                    
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.warning("⚠️ Pilih minimal satu perusahaan.")

            # Tombol Download Pers
            st.markdown("---")
            cp1, cp2 = st.columns(2)
            if not df_corp_final.empty:
                with cp1:
                    csv_corp = df_corp_final[["Nama Perusahaan", "Total Kunjungan"]].to_csv(index=False).encode('utf-8')
                    st.download_button("📥 CSV (Pers)", data=csv_corp, file_name=f'corp_{t1_str}.csv', mime='text/csv', use_container_width=True)
                with cp2:
                    output_corp = io.BytesIO()
                    with pd.ExcelWriter(output_corp, engine='xlsxwriter') as writer:
                        df_corp_final[["Nama Perusahaan", "Total Kunjungan"]].to_excel(writer, index=False, sheet_name='Rekap')
                    st.download_button("📊 Excel (Pers)", data=output_corp.getvalue(), file_name=f'corp_{t1_str}.xlsx', use_container_width=True)

    else:
        st.info("ℹ️ Tidak ada data pada periode ini.")


# --- 8. MODUL 4: ANALISIS ISTIRAHAT (VERSI FINAL DOWNLOAD PER GRUP) ---
elif menu == "Laporan Data Sick":
    st.markdown("<h1>📋 REKAPITULASI TOTAL DATA SICK</h1>", unsafe_allow_html=True)
    
    # 1. Filter Bulan & Tahun (Ganti dari date_input)
    import calendar # Pastikan ini diimpor di atas file Anda
    
    col_a, col_b = st.columns(2)
    tahun_pilih = col_a.selectbox("Pilih Tahun", [2024, 2025, 2026], index=2, key="sick_year")
    bulan_pilih = col_b.selectbox("Pilih Bulan", [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ], key="sick_month")
    
    # Mapping nama bulan ke angka
    bulan_map = {
        "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
        "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
        "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    
    bulan_idx = bulan_map[bulan_pilih]
    
    # Membuat variabel start (tanggal 1) dan end (tanggal terakhir bulan tersebut)
    start = date(tahun_pilih, bulan_idx, 1)
    last_day = calendar.monthrange(tahun_pilih, bulan_idx)[1]
    end = date(tahun_pilih, bulan_idx, last_day)

    # 2. Ambil Data dari Database
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?"
    df_raw = pd.read_sql_query(query, conn, params=[start, end])
    conn.close()

    # --- DAFTAR LIST KONTRAKTOR ---
    list_hjf = ["PT INDO FUDONG (HJF)", "PT IMJ ( INOVASI MAJU JAYA) HJF", "PT BTG-ZJYC (ONC)", "PT. ZJYC ONC", "PT. GDSK (HJF)", "PT GLOBEL DARMA SARANA KARYA GDSK (HJF)", "PT GOBEL DHARMA SARANA KARYA GDSK (HJF)", "PT GEOSERVICES MAKASSAR", "PT. RENTOKIL INDONESIA", "PT.MATAHARI PUTRA PRIMA (HYPERMART) HJF"]
    list_kps = ["PT MCC BAOYE (KPS)", "PT MCC6 (KPS)", "PT. JINRUI KPS", "PT YAOHUA (KPS)", "PT CREC (KPS)", "PT. CISDI (KPS)", "PT CISDI-KPS", "PT JME-KPS", "PT. ETGH-KPS", "PT. BTG ZJYC (KPS)"]
    list_ost = ["PT. MCCBY DCM", "PT LONGI & CENTER OST", "PT CREC (OST)", "PT STHB (OST)", "PT ZTPI -OST", "PT ZTPI-(OST)", "ZTPI (OST)", "PT. ZTPI/ OST", "PT ZTPI (OST)", "PT JIANGXI (OST)", "PT. CCEPC OST", "PT INDO FUDONG (OST)", "PT CSCEC (OST)"]
    list_ckm = ["PT. MCC BAOYE (CKM)"]

    if not df_raw.empty:
        # 3. PRE-PROCESSING DATA
        df_raw['company'] = df_raw['company'].fillna('UNKNOWN').str.upper().str.strip()
        df_raw['status_lower'] = df_raw['rest_status'].fillna('tidak').str.lower().str.strip()
        df_raw['h_num'] = pd.to_numeric(df_raw['istirahat_hari'], errors='coerce').fillna(0)
        df_raw['j_num'] = pd.to_numeric(df_raw['istirahat_jam'], errors='coerce').fillna(0)
        
        selisih_hari = (end - start).days + 1
        bulan_nama = start.strftime("%B").upper()

        # 4. TOMBOL DOWNLOAD EXCEL (Satu Tombol untuk Semua Sheet Grup)
        # Memanggil fungsi yang membagi sheet berdasarkan grup perusahaan
        excel_data = unduh_rekap_sick_per_grup(df_raw, list_hjf, list_kps, list_ost, list_ckm)
        
        st.download_button(
            label="📥 Download Rekap Sick Semua Grup (Excel)",
            data=excel_data,
            file_name=f'Rekap_Sick_Grup_{start}_sd_{end}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
            key="btn_download_sick_final"
        )
        st.info("💡 Hasil download berupa 1 file Excel dengan sheet terpisah: HJF, KPS, OST, dan CKM.")
        st.markdown("---")

        # 5. FUNGSI RINGKASAN UNTUK TAMPILAN TABEL DI WEB
        def get_summary_table(df_filtered):
            if df_filtered.empty: return None
            total_pasien = len(df_filtered)
            ist_hari = len(df_filtered[(df_filtered['status_lower'].isin(['ya', 'yes', 'y'])) & (df_filtered['h_num'] > 0)])
            ist_jam = len(df_filtered[(df_filtered['status_lower'].isin(['ya', 'yes', 'y'])) & (df_filtered['j_num'] > 0)])
            return pd.DataFrame({
                "TAHUN": [start.year], "BULAN": [bulan_nama],
                "TANGGAL": [f"{start.day} SAMPAI {end.day}"],
                "ANGKA KUNJUNGAN SAKIT": [f"{total_pasien} PASIEN"],
                "REKOMENDASI PER-HARI": [f"{ist_hari} PASIEN"],
                "REKOMENDASI PER-JAM": [f"{ist_jam} PASIEN"],
                "HARI KERJA": [f"{selisih_hari} HARI"]
            })

        # 6. TAMPILAN SISTEM TAB
        st.write("### 🏢 Pilih Ringkasan Perusahaan")
        tab1, tab2, tab3, tab4 = st.tabs(["HJF GROUP", "KPS GROUP", "OST GROUP", "CKM GROUP"])

        with tab1:
            st.subheader("PT. HALMAHERA JAYA FERONIKEL (HJF)")
            induk = df_raw[df_raw['company'].str.contains("HALMAHERA", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            
            st.subheader("KONTRAKTOR HJF")
            kon = df_raw[df_raw['company'].isin(list_hjf)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)

        with tab2:
            st.subheader("PT. KARUNIA PERMAI SENTOSA (KPS)")
            induk = df_raw[df_raw['company'].str.contains("KARUNIA", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            
            st.subheader("KONTRAKTOR KPS")
            kon = df_raw[df_raw['company'].isin(list_kps)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)

        with tab3:
            st.subheader("PT. OBI SINAR TIMUR (OST)")
            induk = df_raw[df_raw['company'].str.contains("OBI SINAR", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            
            st.subheader("KONTRAKTOR OST")
            kon = df_raw[df_raw['company'].isin(list_ost)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)

        with tab4:
            st.subheader("PT. CIPTA KEMAKMURAN MITRA (CKM)")
            induk = df_raw[df_raw['company'].str.contains("CIPTA KEMAKMURAN", na=False)]
            res_induk = get_summary_table(induk)
            if res_induk is not None: st.table(res_induk)
            
            st.subheader("KONTRAKTOR CKM")
            kon = df_raw[df_raw['company'].isin(list_ckm)]
            res_kon = get_summary_table(kon)
            if res_kon is not None: st.table(res_kon)

        st.markdown("---")
        st.markdown("<p style='color:red; font-weight:bold; text-align:center;'>NOTE : DAFTAR KUNJUNGAN DAN JUMLAH REKOMENDASI ISTIRAHAT GABUNG DENGAN 3 DEVISI (RANAP, RAJAL, UGD).</p>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ Belum ada data untuk periode tanggal ini.")
# --- 9. MODUL: LIHAT SEMUA DATA (DENGAN DURASI, DEPT, & PERUSAHAAN) ---
elif menu == "Database Rekam Medis":
    st.markdown("<h1>📂 DATABASE REKAM MEDIS</h1>", unsafe_allow_html=True)
    
    t_awal, t_akhir = get_date_range()
    
    with st.expander("🔍 Filter & Statistik", expanded=True):
        c1, c2, c3 = st.columns([1,1,2])
        f1 = c1.date_input("Mulai Tanggal", t_awal)
        f2 = c2.date_input("Sampai Tanggal", t_akhir)
        st_filter = c3.selectbox("Filter Tampilan Status Istirahat:", ["Semua", "Ya", "Tidak"])

    conn = sqlite3.connect(DB_PATH)
    df_raw = pd.read_sql_query("SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", conn, params=[f1, f2])
    
    if not df_raw.empty:
        # Pembersihan data
        df_raw = df_raw.dropna(subset=['patient_name'])
        df_raw['p_name_check'] = df_raw['patient_name'].astype(str).str.strip().str.lower()
        df_raw = df_raw[~df_raw['p_name_check'].isin(['none', 'nan', '', 'null'])].copy()

        if not df_raw.empty:
            # Normalisasi Status & Durasi untuk tampilan
            df_raw['status_clean'] = df_raw['rest_status'].fillna('Tidak').astype(str).str.strip().str.lower()
            df_raw['h_num'] = pd.to_numeric(df_raw['istirahat_hari'], errors='coerce').fillna(0)
            df_raw['j_num'] = pd.to_numeric(df_raw['istirahat_jam'], errors='coerce').fillna(0)
            
            # Eksekusi Filter
            if st_filter == "Ya":
                df_tampil = df_raw[df_raw['status_clean'].isin(['ya', 'yes', 'y'])].copy()
            elif st_filter == "Tidak":
                df_tampil = df_raw[~df_raw['status_clean'].isin(['ya', 'yes', 'y'])].copy()
            else:
                df_tampil = df_raw.copy()

            st.metric(f"Data Terfilter ({st_filter})", f"{len(df_tampil)} Orang")
            st.markdown("---")

          # --- PERBAIKAN PENYUSUNAN TABEL (AGAR HARI & JAM TAMPIL) ---
            df_display = pd.DataFrame()
            df_display['No.'] = range(1, len(df_tampil) + 1)
            df_display['Pilih'] = False
            df_display['Tanggal'] = df_tampil['visit_time']
            df_display['Nama Pasien'] = df_tampil['patient_name']
            df_display['Diagnosa'] = df_tampil['diagnosa']
            df_display['Clinic'] = df_tampil['clinic']
            df_display['Departemen'] = df_tampil['departemen']
            df_display['Perusahaan'] = df_tampil['company']
            df_display['Status'] = df_tampil['rest_status'].astype(str).str.upper()
            
            # 1. Pastikan data None/NaN diubah jadi 0 dulu agar bisa diproses
            # 2. Kemudian ubah angka 0 menjadi '-' agar tampilan di tabel rapi
            df_display['Istirahat Hari'] = pd.to_numeric(df_tampil['istirahat_hari'], errors='coerce').fillna(0).replace(0, '-')
            df_display['Istirahat Jam'] = pd.to_numeric(df_tampil['istirahat_jam'], errors='coerce').fillna(0).replace(0, '-')
            
            df_display['db_id'] = df_tampil['id']

            # Render Tabel
            edited_df = st.data_editor(
                df_display, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "db_id": None, 
                    "Pilih": st.column_config.CheckboxColumn("Hapus?")
                },
                disabled=[c for c in df_display.columns if c != "Pilih"]
            )

            # Tombol Aksi
            col_btn1, col_btn2 = st.columns(2)
            with col_btn2:
                with st.expander("🔐 Hapus Semua (Admin Only)"):
                    st.write("Tindakan ini akan menghapus data pada periode yang dipilih.")
                    
                    # Input sandi admin
                    pwd_admin = st.text_input("Masukkan Sandi Admin:", type="password", key="pwd_all")
                    
                    if st.button("🔥 KONFIRMASI HAPUS SEMUA", use_container_width=True, type="primary"):
                        if pwd_admin == "admin123": # <--- Ganti sandi di sini
                            all_ids = df_display['db_id'].tolist()
                            if all_ids:
                                conn.cursor().execute(f"DELETE FROM rekap_penyakit WHERE id IN ({','.join(['?']*len(all_ids))})", all_ids)
                                conn.commit()
                                st.success("💥 Data periode ini telah dibersihkan.")
                                st.rerun()
                        elif pwd_admin == "":
                            st.warning("Silakan masukkan sandi.")
                        else:
                            st.error("❌ Sandi salah!")

    else:
        st.info("ℹ️ Tidak ada data untuk ditampilkan.")
            
        
# --- 10. MODUL: ANALISIS ISTIRAHAT (TAMPILKAN SEMUA DATA & HITUNG) ---
elif menu == "Analisis Istirahat":
    st.markdown("<h1>📊 ANALISIS DETAIL ISTIRAHAT</h1>", unsafe_allow_html=True)
    
    t_awal, t_akhir = get_date_range()
    
    with st.expander("📅 Pengaturan Periode", expanded=True):
        c1, c2 = st.columns(2)
        f1 = c1.date_input("Dari Tanggal", t_awal, key="ana_date_1")
        f2 = c2.date_input("Sampai Tanggal", t_akhir, key="ana_date_2")

    conn = sqlite3.connect(DB_PATH)
    # Mengambil semua data tanpa filter DISTINCT agar data double tetap muncul
    df = pd.read_sql_query("SELECT * FROM rekap_penyakit WHERE visit_time BETWEEN ? AND ?", conn, params=[f1, f2])
    conn.close()

    if not df.empty:
        # 1. Normalisasi tampilan agar TIDAK ADA "NONE"
        # Semua sel kosong diisi "-" agar tabel terlihat bersih
        df = df.fillna("-")
        
        # Konversi kolom istirahat ke angka hanya untuk keperluan perhitungan statistik
        df['istirahat_hari_num'] = pd.to_numeric(df['istirahat_hari'], errors='coerce').fillna(0)
        df['istirahat_jam_num'] = pd.to_numeric(df['istirahat_jam'], errors='coerce').fillna(0)
        df['status_clean'] = df['rest_status'].astype(str).str.strip().str.lower()
        
        # 2. Perhitungan Statistik (Hanya Menghitung)
        df_istirahat = df[df['status_clean'].isin(['ya', 'yes', 'y'])].copy()
        df_tidak = df[~df['status_clean'].isin(['ya', 'yes', 'y'])].copy()
        
        df_hari_only = df_istirahat[df_istirahat['istirahat_hari_num'] > 0]
        df_jam_only = df_istirahat[df_istirahat['istirahat_jam_num'] > 0]
        
        # 3. Tampilan Ringkasan (Metric)
        st.subheader("📌 Ringkasan Status Pasien")
        
        if 'filter_pilihan' not in st.session_state:
            st.session_state.filter_pilihan = "Semua"

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Data", f"{len(df)} Orang")
        if m1.button("Lihat Semua Data", use_container_width=True):
            st.session_state.filter_pilihan = "Semua"
            
        m2.metric("Total Istirahat", f"{len(df_istirahat)} Orang")
        if m2.button("Lihat Daftar Istirahat", use_container_width=True):
            st.session_state.filter_pilihan = "Istirahat"
            
        m3.metric("Kembali Bekerja", f"{len(df_tidak)} Orang")
        if m3.button("Lihat Daftar Kembali Kerja", use_container_width=True):
            st.session_state.filter_pilihan = "Tidak"

        # 4. Statistik Durasi
        st.markdown("---")
        s1, s2 = st.columns(2)
        s1.metric("🛌 Kategori HARI", f"{len(df_hari_only)} Orang")
        s2.metric("⏱️ Kategori JAM", f"{len(df_jam_only)} Orang")
        
        if s1.button("Filter Kategori HARI", use_container_width=True):
            st.session_state.filter_pilihan = "Hari"
        if s2.button("Filter Kategori JAM", use_container_width=True):
            st.session_state.filter_pilihan = "Jam"

        # 5. Penentuan Data yang Ditampilkan Tabel
        if st.session_state.filter_pilihan == "Istirahat":
            df_final = df_istirahat
        elif st.session_state.filter_pilihan == "Tidak":
            df_final = df_tidak
        elif st.session_state.filter_pilihan == "Hari":
            df_final = df_hari_only
        elif st.session_state.filter_pilihan == "Jam":
            df_final = df_jam_only
        else:
            df_final = df

        # 6. Tampilkan Tabel Apa Adanya (Sesuai Data Mentah)
        st.write(f"### 📋 Menampilkan: {st.session_state.filter_pilihan}")
        
        if not df_final.empty:
            df_view = pd.DataFrame()
            df_view['No.'] = range(1, len(df_final) + 1)
            df_view['Tanggal'] = df_final['visit_time']
            df_view['Nama Pasien'] = df_final['patient_name']
            df_view['Diagnosa'] = df_final['diagnosa']
            df_view['Clinic'] = df_final['clinic']
            df_view['Departemen'] = df_final['departemen']
            df_view['Perusahaan'] = df_final['company']
            df_view['Status'] = df_final['rest_status'].astype(str).str.upper()
            
            # Tampilkan angka asli dari database, ganti 0 dengan "-" untuk kerapian
            df_view['Istirahat Hari'] = df_final['istirahat_hari'].replace(0, '-')
            df_view['Istirahat Jam'] = df_final['istirahat_jam'].replace(0, '-')
            
            st.dataframe(df_view, hide_index=True, use_container_width=True)
        else:
            st.warning("Data tidak ditemukan untuk kategori ini.")
            
    else:
        st.info("ℹ️ Database kosong untuk periode tanggal ini.")

# --- MODUL BARU: LAPORAN KLB (KEJADIAN LUAR BIASA) ---
elif menu == "Laporan KLB":
    st.markdown("<h1>🚨 LAPORAN KEJADIAN LUAR BIASA (KLB)</h1>", unsafe_allow_html=True)
    st.write("Menyaring penyakit potensial wabah berdasarkan data yang ada di database.")

    # 1. Pengaturan Filter Bulan dan Tahun
    c1, c2 = st.columns(2)
    tahun_pilih = c1.selectbox("Pilih Tahun", [2024, 2025, 2026], index=2)
    bulan_pilih = c2.selectbox("Pilih Bulan", 
        ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
         "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
    
    bulan_map = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    periode_str = f"{tahun_pilih}-{bulan_map[bulan_pilih]}"

    # 2. Daftar Kata Kunci KLB (Input Huruf Kecil)
    # Kamu bisa bebas menambah kata kunci di sini, sistem akan mencarinya di database
    keywords_klb = [
        "Low back pain", "Fever, unspecified", "gastroenteritis", "Diarrhoea and gastroenteritis of presumed infectious origin", 
        "Acute pharyngitis, unspecified", "Acute nasopharyngitis [common cold]", "Dengue fever [classical dengue]", "Conjunctivitis, unspecified", "Pneumonia, unspecified", 
        "Dermatitis, unspecified", "varicella", "Typhoid fever", "Fever with chills", "Cough",
        "Functional diarrhoea", "Acute upper respiratory infection, unspecified", "Allergic contact dermatitis due to other chemical products", "Allergic contact dermatitis, unspecified cause", 
        "Acute tonsillitis, unspecified", "Allergic contact dermatitis due to metals", "Acute tonsillitis, unspecified", "Influenza with other respiratory manifestations, virus not identified", 
        "Influenza with other respiratory manifestations, influenza virus identified", "Malaise and fatigue", "Urinary tract infection, site not specified", "Varicella without complication", 
        "Dengue hemorrhagic fever", " Bacterial foodborne intoxication, unspecified"
    ]

    # 3. Ambil Data dari Database
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT visit_time, patient_name, diagnosa, company, departemen FROM rekap_penyakit WHERE visit_time LIKE '{periode_str}%'"
    df_mentah = pd.read_sql_query(query, conn)
    conn.close()

    if not df_mentah.empty:
        # Proses Normalisasi: Ubah kolom diagnosa ke huruf kecil untuk pengecekan
        # Namun kita tetap simpan data aslinya untuk ditampilkan
        df_mentah['diagnosa_lower'] = df_mentah['diagnosa'].astype(str).str.lower().str.strip()
        
        # Filter: Mencari baris yang mengandung salah satu keyword KLB
        pattern = '|'.join(keywords_klb)
        df_klb = df_mentah[df_mentah['diagnosa_lower'].str.contains(pattern, na=False)].copy()

       # Pastikan baris 'if' ini sejajar dengan kode di atasnya (biasanya menjorok 8 spasi atau 2 tab)
        if not df_klb.empty:
            st.warning(f"⚠️ Terdeteksi {len(df_klb)} kasus potensial KLB pada {bulan_pilih} {tahun_pilih}.")
            
            st.write("### 📊 Ringkasan Kasus KLB")
            rekap_klb = df_klb['diagnosa_lower'].value_counts().reset_index()
            rekap_klb.columns = ['Diagnosa Terdeteksi', 'Jumlah Kasus']
            
            # Hitung total
            total_kasus = rekap_klb['Jumlah Kasus'].sum()
            row_total = pd.DataFrame({
                'Diagnosa Terdeteksi': ['**TOTAL KESELURUHAN**'], 
                'Jumlah Kasus': [f"**{total_kasus}**"]
            })
            
            rekap_dengan_total = pd.concat([rekap_klb, row_total], ignore_index=True)
            st.table(rekap_dengan_total)

            # Detail Pasien
            st.write("### 📋 Detail Identitas Pasien KLB")
            df_display = df_klb[['visit_time', 'patient_name', 'diagnosa', 'company', 'departemen']].copy()
            df_display.columns = ['Tanggal', 'Nama Pasien', 'Diagnosa Asli', 'Perusahaan', 'Departemen']
            
            df_display.index = range(1, len(df_display) + 1)
            st.dataframe(df_display, use_container_width=True)

            # Download Button
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_display.to_excel(writer, sheet_name='LAPORAN_KLB', index=True)
            
            st.download_button(
                label="📥 Download Laporan KLB (Excel)",
                data=output.getvalue(),
                file_name=f'Laporan_KLB_{periode_str}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )
        else:
            st.success(f"✅ Tidak ada temuan kasus KLB untuk periode {bulan_pilih} {tahun_pilih}.")
# --- MODUL: MANAJEMEN USER (TEMPEL DI PALING BAWAH) ---
elif menu == "Manajemen User":
    if st.session_state["role"] != "admin":
        st.error("⛔ Anda tidak memiliki akses ke menu ini!")
    else:
        st.markdown("<h1>👥 MANAJEMEN PENGGUNA</h1>", unsafe_allow_html=True)
        
        # TAB 1: TAMBAH USER
        with st.expander("➕ Tambah User Baru", expanded=True):
            new_u = st.text_input("Username Baru")
            new_p = st.text_input("Password Baru", type="password")
            new_r = st.selectbox("Pilih Role", ["user", "admin"])
            if st.button("Simpan Akun Baru"):
                if new_u and new_p:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO userstable VALUES (?,?,?)", (new_u, make_hashes(new_p), new_r))
                        conn.commit()
                        st.success(f"Akun {new_u} berhasil disimpan!")
                        st.rerun()
                    except:
                        st.error("Username sudah ada!")
                    finally:
                        conn.close()

        st.markdown("---")
        
        # TAB 2: DAFTAR & HAPUS USER
        st.subheader("📋 Daftar Akun Tersimpan")
        df_u = get_all_users()
        
        for index, row in df_u.iterrows():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{row['username']}**")
            c2.code(row['role'])
            if row['username'] != 'admin':
                if c3.button("🗑️ Hapus", key=f"del_{row['username']}"):
                    if hapus_user_db(row['username']):
                        st.success("Terhapus!")
                        st.rerun()
            else:
                c3.write("🔒 System")
# --- LOGIKA HALAMAN (TARUH DI BARIS PALING BAWAH) ---

if st.query_params.get("page") == "klb":
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none !important;}
            section[data-testid="stSidebar"] {width: 0px !important; visibility: hidden !important;}
            .stAppHeader {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    tampilkan_laporan_klb()
    st.stop() # Ini yang akan menghilangkan menu upload data

