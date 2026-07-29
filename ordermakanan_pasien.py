import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import hashlib

# ---------------------------------------------------------
# KONFIGURASI PATH PENYIMPANAN DI DRIVE D KOMPUTER
# ---------------------------------------------------------
BASE_DIR = r"D:\Data_Order_Makanan"
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "order_makanan.db")

# Buat folder penyimpanan di Drive D jika belum ada
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)

# ---------------------------------------------------------
# KONFIGURASI HALAMAN
# ---------------------------------------------------------
st.set_page_config(
    page_title="Order Makanan Pasien - Klinik Harita Obi",
    page_icon="🍲",
    layout="wide"
)

# ---------------------------------------------------------
# DATABASE SETUP (SQLite di Drive D)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Tabel Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nama_lengkap TEXT,
            unit_kerja TEXT
        )
    ''')
    
    # Check & tambahkan kolom 'role' jika belum ada (Safe Migration)
    c.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in c.fetchall()]
    if 'role' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    
    # 2. Tabel Orders Makanan
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tgl_order DATE,
            nama_pasien TEXT,
            perusahaan TEXT,
            jabatan TEXT,
            departemen TEXT,
            nik_idcard TEXT,
            pilihan_makanan TEXT,
            catatan_diet TEXT,
            nama_pemesan TEXT,
            unit_pemesan TEXT,
            idcard_filename TEXT,
            waktu_input TIMESTAMP
        )
    ''')

    # 3. Tabel Master Data Dinamis (Perusahaan, Departemen, Jabatan)
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategori TEXT,
            nama TEXT UNIQUE
        )
    ''')
    
    # 4. Inisialisasi Akun Admin Default (User: admin / Pass: admin123)
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, nama_lengkap, unit_kerja, role) VALUES (?, ?, ?, ?, ?)",
                  ('admin', admin_pass, 'Administrator Klinik', 'MEDICAL RECORD / IT', 'admin'))

    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# FUNGSI HELPER & DATABASE
# ---------------------------------------------------------
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

def register_user(username, password, nama_lengkap, unit_kerja, role='user'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, nama_lengkap, unit_kerja, role) VALUES (?, ?, ?, ?, ?)",
                  (username, make_hash(password), nama_lengkap, unit_kerja, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    data = c.fetchone()
    conn.close()
    if data and check_hash(password, data[2]):
        return {
            "username": data[1],
            "nama_lengkap": data[3],
            "unit_kerja": data[4],
            "role": data[5] if len(data) > 5 else 'user'
        }
    return None

def get_master_list(kategori):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT nama FROM master_data WHERE kategori = ? ORDER BY nama ASC", (kategori,))
    res = [r[0] for r in c.fetchall()]
    conn.close()
    res.append("Lainnya")
    return res

def add_master_item(kategori, nama):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO master_data (kategori, nama) VALUES (?, ?)", (kategori, nama.strip()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_master_item(kategori, nama):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM master_data WHERE kategori = ? AND nama = ?", (kategori, nama))
    conn.commit()
    conn.close()

def save_order(tgl_order, nama_pasien, perusahaan, jabatan, departemen, 
               nik_idcard, pilihan_makanan, catatan_diet, nama_pemesan, 
               unit_pemesan, idcard_filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (
            tgl_order, nama_pasien, perusahaan, jabatan, departemen,
            nik_idcard, pilihan_makanan, catatan_diet, nama_pemesan,
            unit_pemesan, idcard_filename, waktu_input
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tgl_order, nama_pasien, perusahaan, jabatan, departemen,
          nik_idcard, pilihan_makanan, catatan_diet, nama_pemesan,
          unit_pemesan, idcard_filename, datetime.now()))
    conn.commit()
    conn.close()

def delete_order(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT idcard_filename FROM orders WHERE id = ?", (order_id,))
    row = c.fetchone()
    if row and row[0]:
        file_path = os.path.join(UPLOAD_DIR, row[0])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
    
    c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM orders ORDER BY id DESC", conn)
    conn.close()
    return df

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}

# ---------------------------------------------------------
# TAMPILAN AUTENTIKASI (HANYA LOGIN)
# ---------------------------------------------------------
if not st.session_state['logged_in']:
    st.title("🔐 Login Sistem - Klinik Harita Obi")
    st.markdown("Silakan masuk menggunakan akun yang telah terdaftar.")
    
    col_login, _ = st.columns([1, 1])
    with col_login:
        st.subheader("Form Login Pengguna")
        with st.form("login_form"):
            l_username = st.text_input("Username")
            l_password = st.text_input("Password", type="password")
            l_submit = st.form_submit_button("Masuk")
            
            if l_submit:
                user = login_user(l_username, l_password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user
                    st.success(f"Berhasil masuk, selamat datang {user['nama_lengkap']}!")
                    st.rerun()
                else:
                    st.error("⚠️ Username atau Password salah!")
        
        st.info("ℹ️ Belum memiliki akun? Silakan hubungi **Administrator Klinik / Tim IT** untuk dibuatkan akun baru.")

else:
    # ---------------------------------------------------------
    # MAIN APPLICATION (AFTER LOGIN)
    # ---------------------------------------------------------
    user = st.session_state['user_info']
    is_admin = user.get('role') == 'admin'
    
    # Sidebar Info
    with st.sidebar:
        st.write(f"👤 **{user['nama_lengkap']}**")
        st.write(f"🏢 Unit: {user['unit_kerja']}")
        st.write(f"🛡️ Role: **{user.get('role', 'user').upper()}**")
        st.caption(f"📂 Lokasi DB: `{DB_PATH}`")
        st.divider()
        if st.button("🚪 Keluar (Logout)"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = {}
            st.rerun()

    st.title("🍲 Aplikasi Order Makanan Pasien")
    st.caption("Klinik Harita Feronikel Obi")

    # DYNAMIC TAB SETTINGS BERDASARKAN ROLE
    if is_admin:
        tab_titles = ["📝 Form Order Makanan", "📊 Rekap & Monitoring Data", "⚙️ Manajemen Aplikasi"]
    else:
        tab_titles = ["📝 Form Order Makanan"]
    
    tabs = st.tabs(tab_titles)
    tab_form = tabs[0]

    # =========================================================
    # TAB 1: FORM INPUT ORDER (AKSES: USER & ADMIN)
    # =========================================================
    with tab_form:
        st.subheader("Input Data Pemesanan Makanan Pasien")
        
        with st.form(key="form_order_makanan", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 👤 Data Pasien")
                tgl_order = st.date_input("Tanggal Order", datetime.now())
                nama_pasien = st.text_input("Nama Pasien*")
                
                perusahaan = st.selectbox("Perusahaan*", get_master_list('perusahaan'), index=None, placeholder="Pilih Perusahaan...")
                jabatan = st.selectbox("Jabatan*", get_master_list('jabatan'), index=None, placeholder="Pilih Jabatan...")
                departemen = st.selectbox("Departemen*", get_master_list('departemen'), index=None, placeholder="Pilih Departemen...")
                
                nik_idcard = st.text_input("NIK / ID Card Pasien*")
                uploaded_file = st.file_uploader("Upload Foto/Scan ID Card (JPG/PNG/PDF)*", type=["jpg", "jpeg", "png", "pdf"])

            with col2:
                st.markdown("### 🍱 Detail Pesanan & Pemesan")
                pilihan_makanan = st.radio("Pilihan Menu Makanan*", ["Bubur", "Pack Meal"], index=None)
                catatan_diet = st.text_area("Catatan Tambahan / Diet Khusus (Opsional)", placeholder="Contoh: Diet Rendah Garam, Tidak Pedas, Alergi Udang")
                
                st.divider()
                nama_pemesan = st.text_input("Nama Pemesan (Petugas)*", value=user['nama_lengkap'])
                unit_pemesan = st.text_input("Unit / Divisi Pemesan*", value=user['unit_kerja'])
            
            submit_btn = st.form_submit_button("🚀 Kirim Pesanan Makanan")
            
        if submit_btn:
            if not nama_pasien or not perusahaan or not jabatan or not departemen or not nik_idcard or not pilihan_makanan or not nama_pemesan or not unit_pemesan:
                st.error("⚠️ Mohon lengkapi seluruh field wajib (bertanda *)!")
            elif uploaded_file is None:
                st.error("⚠️ Mohon upload lampiran ID Card Pasien!")
            else:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = os.path.splitext(uploaded_file.name)[1]
                saved_filename = f"{nik_idcard}_{timestamp_str}{file_ext}"
                file_path = os.path.join(UPLOAD_DIR, saved_filename)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
                save_order(tgl_order, nama_pasien, perusahaan, jabatan, departemen,
                           nik_idcard, pilihan_makanan, catatan_diet, nama_pemesan,
                           unit_pemesan, saved_filename)
                
                st.success(f"✅ Pesanan makanan untuk Pasien **{nama_pasien}** berhasil disimpan di Drive D!")

    # =========================================================
    # TAB 2 & 3: REKAP DATA & MANAJEMEN APLIKASI (KHUSUS ADMIN)
    # =========================================================
    if is_admin:
        tab_rekap = tabs[1]
        tab_admin = tabs[2]

        # --- TAB 2: REKAP & MONITORING DATA ---
        with tab_rekap:
            st.subheader("Data Pesanan Masuk")
            df = load_data()
            
            if df.empty:
                st.info("Belum ada data pemesanan yang masuk.")
            else:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    filter_tgl = st.date_input("Filter Tanggal Order", None)
                with col_f2:
                    filter_menu = st.multiselect("Filter Pilihan Menu", ["Bubur", "Pack Meal"])
                    
                df_filtered = df.copy()
                if filter_tgl:
                    df_filtered = df_filtered[df_filtered['tgl_order'] == str(filter_tgl)]
                if filter_menu:
                    df_filtered = df_filtered[df_filtered['pilihan_makanan'].isin(filter_menu)]
                    
                st.markdown(f"**Total Pesanan Ditampilkan:** {len(df_filtered)} Order")
                st.dataframe(df_filtered.drop(columns=['idcard_filename']), use_container_width=True, hide_index=True)
                
                st.divider()
                st.markdown("### 🔍 Detail & Pengaturan Data Pesanan")
                
                if not df_filtered.empty:
                    selected_id = st.selectbox(
                        "Pilih ID Order / Nama Pasien untuk Lihat Detail atau Hapus:", 
                        options=df_filtered['id'].tolist(),
                        format_func=lambda x: f"ID Order #{x} - {df_filtered[df_filtered['id']==x]['nama_pasien'].values[0]} ({df_filtered[df_filtered['id']==x]['nik_idcard'].values[0]})"
                    )
                    
                    if selected_id:
                        row = df_filtered[df_filtered['id'] == selected_id].iloc[0]
                        filename = row['idcard_filename']
                        file_path = os.path.join(UPLOAD_DIR, filename)
                        
                        col_info, col_img = st.columns([1, 1])
                        with col_info:
                            st.write(f"**Nama Pasien:** {row['nama_pasien']}")
                            st.write(f"**NIK/ID Card:** {row['nik_idcard']}")
                            st.write(f"**Perusahaan:** {row['perusahaan']}")
                            st.write(f"**Jabatan / Dept:** {row['jabatan']} / {row['departemen']}")
                            st.write(f"**Menu:** {row['pilihan_makanan']}")
                            st.write(f"**Catatan:** {row['catatan_diet']}")
                            st.write(f"**Pemesan:** {row['nama_pemesan']} ({row['unit_pemesan']})")
                            
                            st.divider()
                            st.markdown("#### 🗑️ Hapus Pesanan Ini")
                            st.caption("Menghapus pesanan ini akan menghapus data dari database beserta file ID Card di Drive D.")
                            
                            if st.button(f"🗑️ Hapus Order ID #{selected_id}", type="primary", key=f"del_order_{selected_id}"):
                                delete_order(selected_id)
                                st.success(f"✅ Data pesanan untuk **{row['nama_pasien']}** (ID #{selected_id}) berhasil dihapus!")
                                st.rerun()
                            
                        with col_img:
                            if os.path.exists(file_path):
                                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    image = Image.open(file_path)
                                    st.image(image, caption=f"ID Card: {filename}", use_container_width=True)
                                else:
                                    st.write("📄 Dokumen berupa PDF/File Non-Gambar.")
                                    with open(file_path, "rb") as f:
                                        st.download_button("📥 Download ID Card File", f, file_name=filename)
                            else:
                                st.warning("File ID Card tidak ditemukan.")

        # --- TAB 3: MANAJEMEN APLIKASI ---
        with tab_admin:
            st.subheader("⚙️ Panel Manajemen Admin")
            
            admin_sub_tab1, admin_sub_tab2 = st.tabs(["👥 Manajemen Akun", "🏷️ Kelola List Dropdown"])
            
            # --- SUB TAB 1: MANAJEMEN AKUN ---
            with admin_sub_tab1:
                st.markdown("### ➕ Buat Akun Baru (Oleh Admin)")
                with st.form("admin_create_user"):
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        new_u_username = st.text_input("Username Baru")
                        new_u_password = st.text_input("Password", type="password")
                        new_u_nama = st.text_input("Nama Lengkap")
                    with col_u2:
                        new_u_unit = st.text_input("Unit / Divisi")
                        new_u_role = st.selectbox("Role Akses", ["user", "admin"])
                        st.write("")
                        st.write("")
                        submit_new_u = st.form_submit_button("➕ Tambahkan Akun")
                        
                    if submit_new_u:
                        if new_u_username and new_u_password and new_u_nama:
                            if register_user(new_u_username, new_u_password, new_u_nama, new_u_unit, new_u_role):
                                st.success(f"Akun **{new_u_username}** ({new_u_role}) berhasil dibuat!")
                                st.rerun()
                            else:
                                st.error("Username sudah terdaftar!")
                        else:
                            st.warning("Mohon lengkapi seluruh field data akun!")

                st.divider()
                st.markdown("### 📋 Daftar Seluruh Akun Terdaftar")
                conn = sqlite3.connect(DB_PATH)
                df_users = pd.read_sql_query("SELECT id, username, nama_lengkap, unit_kerja, role FROM users", conn)
                conn.close()
                st.dataframe(df_users, use_container_width=True, hide_index=True)

                st.divider()
                st.markdown("### 🗑️ Hapus Akun Pengguna")
                if not df_users.empty:
                    col_del1, col_del2 = st.columns([2, 1])
                    with col_del1:
                        user_to_delete = st.selectbox(
                            "Pilih Akun yang Akan Dihapus:",
                            options=df_users['id'].tolist(),
                            format_func=lambda x: f"{df_users[df_users['id']==x]['username'].values[0]} ({df_users[df_users['id']==x]['nama_lengkap'].values[0]} - Role: {df_users[df_users['id']==x]['role'].values[0]})"
                        )
                    with col_del2:
                        st.write("")
                        st.write("")
                        if st.button("🗑️ Hapus Akun Terpilih", type="primary"):
                            selected_username = df_users[df_users['id'] == user_to_delete]['username'].values[0]
                            
                            if selected_username == user['username']:
                                st.error("⚠️ Anda tidak bisa menghapus akun yang sedang digunakan saat ini!")
                            elif selected_username == 'admin':
                                st.error("⚠️ Akun utama 'admin' tidak dapat dihapus!")
                            else:
                                delete_user(user_to_delete)
                                st.success(f"✅ Akun **{selected_username}** berhasil dihapus!")
                                st.rerun()

            # --- SUB TAB 2: KELOLA MASTER DROPDOWN ---
            with admin_sub_tab2:
                col_m1, col_m2 = st.columns([1, 1])
                
                # ➕ TAMBAH OPTION
                with col_m1:
                    st.markdown("### ➕ Tambah Pilihan Dropdown")
                    kat_pilihan = st.selectbox("Pilih Kategori List (Tambah)", ["perusahaan", "departemen", "jabatan"], key="kat_add")
                    nama_baru = st.text_input("Nama Pilihan Baru")
                    btn_add_master = st.button("➕ Tambah Pilihan")
                    
                    if btn_add_master:
                        if nama_baru:
                            if add_master_item(kat_pilihan, nama_baru):
                                st.success(f"Berhasil menambahkan '{nama_baru}' ke list {kat_pilihan}!")
                                st.rerun()
                            else:
                                st.error("Pilihan tersebut sudah ada dalam list.")
                        else:
                            st.warning("Nama opsi tidak boleh kosong.")

                # 🗑️ HAPUS OPTION
                with col_m2:
                    st.markdown("### 🗑️ Hapus Pilihan Dropdown")
                    kat_hapus = st.selectbox("Pilih Kategori List (Hapus)", ["perusahaan", "departemen", "jabatan"], key="kat_del")
                    
                    raw_items = get_master_list(kat_hapus)[:-1] 
                    
                    if raw_items:
                        item_to_delete = st.selectbox("Pilih Item yang Akan Dihapus:", options=raw_items)
                        btn_del_master = st.button("🗑️ Hapus Pilihan", type="primary")
                        
                        if btn_del_master:
                            delete_master_item(kat_hapus, item_to_delete)
                            st.success(f"Berhasil menghapus '{item_to_delete}' dari list {kat_hapus}!")
                            st.rerun()
                    else:
                        st.info("Belum ada pilihan data pada kategori ini.")

                st.divider()
                st.markdown(f"### 📋 List Current ({kat_pilihan.capitalize()})")
                current_items = get_master_list(kat_pilihan)[:-1]
                st.write(current_items)
