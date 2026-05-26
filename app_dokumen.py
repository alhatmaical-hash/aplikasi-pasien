import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime
import base64

# --- 1. CONFIGURATION & DIRECTORIES ---
st.set_page_config(
    page_title="DocManager Pro", 
    page_icon="📂", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Struktur direktori utama dan sub-folder fisik untuk tiap jenis dokumen
BASE_UPLOAD_DIR = "stored_documents"
SUB_DIRS = {
    "SOP": os.path.join(BASE_UPLOAD_DIR, "sop"),
    "Formulir": os.path.join(BASE_UPLOAD_DIR, "formulir"),
    "Instruksi Kerja": os.path.join(BASE_UPLOAD_DIR, "instruksi_kerja")
}

# Membuat folder secara otomatis jika belum terbentuk di server
for folder_path in SUB_DIRS.values():
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

DB_NAME = "document_management.db"


# --- 2. DATABASE FUNCTIONS (SQLite) ---
def init_db():
    """Inisialisasi database dan tabel metadata dokumen jika belum ada"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dokumen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomor_dokumen TEXT UNIQUE,
            judul TEXT,
            jenis_dokumen TEXT,
            departemen TEXT,
            file_name TEXT,
            file_path TEXT,
            tanggal_terbit TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_document(nomor, judul, jenis, dept, file_name, file_path, tanggal):
    """Memasukkan data dokumen baru ke database dengan validasi nomor unik"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dokumen (nomor_dokumen, judul, jenis_dokumen, departemen, file_name, file_path, tanggal_terbit, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nomor, judul, jenis, dept, file_name, file_path, tanggal, 'Aktif'))
        conn.commit()
        return True, "Dokumen berhasil disimpan ke database!"
    except sqlite3.IntegrityError:
        return False, "Error: Nomor dokumen sudah terdaftar di dalam sistem."
    except Exception as e:
        return False, f"Error Sistem: {str(e)}"
    finally:
        conn.close()

def get_all_documents():
    """Mengambil semua daftar dokumen yang statusnya masih Aktif"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT id, nomor_dokumen, judul, jenis_dokumen, departemen, tanggal_terbit, status, file_path FROM dokumen WHERE status='Aktif'", 
        conn
    )
    conn.close()
    return df


# --- 3. HELPER FUNCTIONS ---
def show_pdf(file_path):
    """Fungsi untuk merender preview PDF langsung di dalam layout aplikasi"""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="750" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# --- 4. INITIALIZATION ---
init_db()


# --- 5. CUSTOM CSS FOR APP INTERFACE (MOBILE OPTIMIZED) ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { color: #1E3A8A; font-weight: 700; font-size: 26px; }
    h3 { color: #2D3748; font-weight: 600; font-size: 18px; margin-bottom: 2px; }
    .stButton>button { background-color: #1E3A8A; color: white; border-radius: 6px; width: 100%; height: 42px; font-weight: 500; }
    .stButton>button:hover { background-color: #2563EB; color: white; border-color: #2563EB; }
    [data-testid="stSidebar"] { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; }
    .doc-meta { color: #4A5568; font-size: 13px; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)


# --- 6. SIDEBAR NAVIGATION ---
st.sidebar.title("📂 DocManager Pro")
st.sidebar.markdown("<small style='color: gray;'>Sistem Arsip Internal v2.0</small>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Pilih Menu Navigasi:", ["🔍 Cari & Lihat Dokumen", "📤 Unggah Dokumen Baru"])


# --- 7. MENU 1: CARI & LIHAT DOKUMEN ---
if menu == "🔍 Cari & Lihat Dokumen":
    st.title("🗂️ Pusat Arsip Dokumen")
    st.caption("Gunakan fitur di bawah untuk mencari, memfilter, dan meninjau dokumen internal perusahaan.")
    
    df_docs = get_all_documents()
    
    if df_docs.empty:
        st.info("Belum ada dokumen yang tersimpan di server. Silakan pilih menu 'Unggah Dokumen Baru' di sidebar.")
    else:
        # Bar Filter Pencarian (Fleksibel & Responsif)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_query = st.text_input("Pencarian Kata Kunci", placeholder="Ketik judul atau nomor dokumen...")
        with col2:
            jenis_options = ["Semua"] + list(SUB_DIRS.keys())
            filter_jenis = st.selectbox("Filter Jenis", jenis_options)
        with col3:
            dept_options = ["Semua"] + sorted(list(df_docs['departemen'].unique()))
            filter_dept = st.selectbox("Filter Departemen / Perusahaan", dept_options)
        
        # Eksekusi Filter Logika
        filtered_df = df_docs.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df['judul'].str.contains(search_query, case=False, na=False) | 
                filtered_df['nomor_dokumen'].str.contains(search_query, case=False, na=False)
            ]
        if filter_jenis != "Semua":
            filtered_df = filtered_df[filtered_df['jenis_dokumen'] == filter_jenis]
        if filter_dept != "Semua":
            filtered_df = filtered_df[filtered_df['departemen'] == filter_dept]
            
        st.markdown(f"Menampilkan **{len(filtered_df)}** dokumen yang cocok.")
        st.markdown("---")
        
        # Render Baris Dokumen (Sangat ramah jika dibuka di HP dibanding tabel excel kaku)
        for idx, row in filtered_df.iterrows():
            with st.container():
                c_info, c_action = st.columns([4, 1])
                with c_info:
                    st.markdown(f"### {row['judul']}")
                    st.markdown(
                        f"<div class='doc-meta'>"
                        f"<b>No. Dokumen:</b> <code>{row['nomor_dokumen']}</code> &nbsp;|&nbsp; "
                        f"<b>Kategori:</b> {row['jenis_dokumen']} &nbsp;|&nbsp; "
                        f"<b>Unit/Dept:</b> {row['departemen']} &nbsp;|&nbsp; "
                        f"<b>Tanggal Terbit:</b> {row['tanggal_terbit']}"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
                with c_action:
                    st.write("")  # Penyelaras vertikal spacing
                    if st.button("👁️ Buka File", key=f"btn_{row['id']}"):
                        st.session_state['active_pdf'] = row['file_path']
                        st.session_state['active_title'] = row['judul']
                st.markdown("<hr style='margin: 12px 0px; border-color: #E2E8F0;'>", unsafe_allow_html=True)

        # Container Preview File (Muncul di area bawah jika salah satu tombol 'Buka File' diklik)
        if 'active_pdf' in st.session_state:
            st.markdown("---")
            st.subheader(f"📄 Preview Dokumen: {st.session_state['active_title']}")
            
            if st.button("❌ Tutup Layar Preview"):
                del st.session_state['active_pdf']
                st.rerun()
            else:
                if os.path.exists(st.session_state['active_pdf']):
                    # Jalankan preview jika formatnya pdf
                    if st.session_state['active_pdf'].lower().endswith('.pdf'):
                        show_pdf(st.session_state['active_pdf'])
                    else:
                        st.warning("Preview langsung saat ini hanya didukung untuk format PDF. Silakan periksa file langsung di direktori server.")
                else:
                    st.error("Gagal Memuat: File fisik tidak ditemukan atau telah dipindahkan dari folder penyimpanan server.")


# --- 8. MENU 2: UNGHAH DOKUMEN BARU ---
elif menu == "📤 Unggah Dokumen Baru":
    st.title("📤 Unggah Komponen Dokumen Baru")
    st.caption("Formulir ini otomatis mendeteksi jenis dokumen dan memisahkannya ke folder server yang tepat.")
    
    # Form input pembersihan otomatis setelah submit sukses
    with st.form("form_upload_dokumen", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nomor_dokumen = st.text_input("Nomor Registrasi Dokumen *", placeholder="Contoh: SOP-KLINIK-002 atau IK-KPS-01")
            judul_dokumen = st.text_input("Judul / Nama Dokumen *", placeholder="Contoh: Prosedur Penanganan Tanggap Darurat")
            jenis_dokumen = st.selectbox("Jenis Kategori Dokumen *", [None, "SOP", "Formulir", "Instruksi Kerja"], index=0)
        
        with col_f2:
            departemen = st.text_input("Departemen / Perusahaan Induk *", placeholder="Contoh: Klinik, HRD, HJF, KPS, OST, CKM")
            tanggal_terbit = st.date_input("Tanggal Berlaku", datetime.today())
            uploaded_file = st.file_uploader("Pilih File Dokumen (Disarankan format PDF) *", type=["pdf", "doc", "docx", "xls", "xlsx"])
            
        submitted = st.form_submit_button("Simpan Dokumen")
        
        if submitted:
            # Proteksi Validasi Form Kosong
            if not nomor_dokumen or not judul_dokumen or not jenis_dokumen or not departemen or not uploaded_file:
                st.error("Gagal Menyimpan: Mohon lengkapi seluruh kolom input yang bertanda bintang (*)!")
            else:
                # 1. Menentukan target sub-folder secara dinamis (sop / formulir / instruksi_kerja)
                target_folder = SUB_DIRS[jenis_dokumen]
                
                # 2. Standarisasi nama file fisik agar aman dari karakter unik "/"
                safe_doc_num = nomor_dokumen.replace('/', '_').replace('\\', '_')
                clean_filename = f"{safe_doc_num}_{uploaded_file.name}"
                save_path = os.path.join(target_folder, clean_filename)
                
                try:
                    # 3. Menulis/menyimpan file fisik ke sub-folder tujuan
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 4. Input rekap log metadata ke database SQLite
                    success, msg = insert_document(
                        nomor=nomor_dokumen,
                        judul=judul_dokumen,
                        jenis=jenis_dokumen,
                        dept=departemen,
                        file_name=uploaded_file.name,
                        file_path=save_path, # Path tersimpan otomatis merekam sub-folder aslinya
                        tanggal=tanggal_terbit.strftime("%Y-%m-%d")
                    )
                    
                    if success:
                        st.success(f"🎉 {msg} File fisik berhasil masuk ke folder terpisah: `stored_documents/{jenis_dokumen.lower().replace(' ', '_')}/`")
                    else:
                        # Rollback: Hapus file fisik jika database gagal menginput entri (agar storage tidak penuh sampah)
                        if os.path.exists(save_path):
                            os.remove(save_path)
                        st.error(msg)
                        
                except Exception as e:
                    st.error(f"Gagal memproses unggahan file fisik: {str(e)}")
