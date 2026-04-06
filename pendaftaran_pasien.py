import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. DATABASE SETUP ---
def get_connection():
    return sqlite3.connect('klinik_data.db', check_same_thread=False)

def get_master(kategori):
    conn = get_connection()
    df = pd.read_sql(f"SELECT id, nama FROM master_data WHERE kategori='{kategori}' ORDER BY nama ASC", conn)
    conn.close()
    return df

# --- 2. LOGIKA NAVIGASI ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'Login'

# Sidebar: Tombol Kembali ke Login
if st.sidebar.button("⬅️ Kembali ke Login / 返回登录"):
    st.session_state['logged_in'] = False
    st.session_state['page'] = 'Login'
    st.rerun()

# --- 3. MENU UTAMA ---
# Pastikan variabel 'menu' didefinisikan sebelum digunakan di elif
menu_list = ["Pendaftaran / 登记"]
if st.session_state.get('logged_in'):
    menu_list += ["Rekam Medis / 病历", "SKD / 医生证明", "Pengaturan Master / 设置"]

menu = st.sidebar.radio("Pilih Halaman / 选择页面", menu_list)

# --- 4. KODE HALAMAN ---

if menu == "Pendaftaran / 登记":
    st.header("📝 Pendaftaran Pasien / 病人登记")
    
    opts_perusahaan = get_master("Perusahaan")['nama'].tolist()
    opts_dept = get_master("Departemen")['nama'].tolist()
    opts_jabatan = get_master("Jabatan")['nama'].tolist()
    custom_fields = get_master("Fitur Pendaftaran")['nama'].tolist()

    pernah = st.radio(
        "PERNAH BEROBAT DISINI? / 您以前在这里看过病吗？", 
        ["Iya Sudah / 是的", "Belum Pernah / 从未"], 
        horizontal=True
    )

    with st.form("form_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("NAMA LENGKAP / 全名")
            nik = st.text_input("NIK / NO KTP / 身份证号")
            perusahaan = st.selectbox("PERUSAHAAN / 公司", opts_perusahaan if opts_perusahaan else ["Default"])
        with col2:
            dept = st.selectbox("DEPARTEMEN / 部门", opts_dept if opts_dept else ["Default"])
            jabatan = st.selectbox("JABATAN / 职位", opts_jabatan if opts_jabatan else ["Default"])
            
        responses = {}
        # Kolom tambahan hanya untuk pasien baru
        if pernah == "Belum Pernah / 从未":
            st.divider()
            st.subheader("📋 Informasi Tambahan / 附加信息")
            for field in custom_fields:
                responses[field] = st.text_input(field.upper())
        else:
            responses = {field: "" for field in custom_fields}

        if st.form_submit_button("KIRIM PENDAFTARAN / 提交登记"):
            if nama and nik:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute('''INSERT INTO pasien (tgl_daftar, nama_lengkap, nik, pernah_berobat, perusahaan, departemen, jabatan) 
                             VALUES (?,?,?,?,?,?,?)''', (datetime.now().date(), nama, nik, pernah, perusahaan, dept, jabatan))
                last_id = cur.lastrowid
                for f_name, f_val in responses.items():
                    cur.execute("INSERT INTO pasien_custom_data (pasien_id, field_name, field_value) VALUES (?,?,?)", 
                                (last_id, f_name, f_val))
                conn.commit()
                conn.close()
                st.success("Berhasil Terdaftar! / 登记成功！")
                st.balloons()
            else:
                st.error("Nama dan NIK wajib diisi! / 姓名和身份证号必填！")

elif menu == "Rekam Medis / 病历":
    st.header("📊 Data Rekam Medis / 病历数据")
    conn = get_connection()
    df_p = pd.read_sql("SELECT * FROM pasien", conn)
    df_c = pd.read_sql("SELECT * FROM pasien_custom_data", conn)
    conn.close()

    if not df_p.empty:
        if not df_c.empty:
            # Menggabungkan kolom custom ke tabel utama
            df_c_pivot = df_c.pivot(index='pasien_id', columns='field_name', values='field_value').reset_index()
            df_final = pd.merge(df_p, df_c_pivot, left_on='id', right_on='pasien_id', how='left').drop(columns=['pasien_id'], errors='ignore')
        else:
            df_final = df_p
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.info("Data kosong / 数据为空")

# Tambahkan bagian elif untuk SKD dan Pengaturan Master di bawahnya...
