import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# 1. Konfigurasi Halaman (Zona Waktu WIT / Asia/Jayapura Friendly)
st.set_page_config(
    page_title="Klinik Apps HJF - Surat Rujukan External",
    page_icon="🏥",
    layout="wide"
)

# 2. Inisialisasi Database dengan Kolom Lengkap Sesuai Form HJF
def init_db():
    conn = sqlite3.connect('rujukan_hjf.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rujukan_external (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no_rujukan TEXT UNIQUE,
            tanggal_input TEXT,
            triase TEXT,
            nama_pasien TEXT,
            tanggal_lahir TEXT,
            jenis_kelamin TEXT,
            no_id_rm TEXT,
            alamat TEXT,
            gcs_e TEXT, gcs_v TEXT, gcs_m TEXT,
            pupil TEXT, reflex_cahaya TEXT,
            td TEXT, nadi TEXT, suhu TEXT, pernapasan TEXT, spo2 TEXT,
            alasan_klinikal TEXT, alasan_bedah TEXT,
            diagnosa_medis TEXT, diagnosa_tambahan TEXT,
            alergi TEXT, riwayat_penyakit TEXT, riwayat_lain TEXT,
            pengobatan TEXT, tindakan TEXT, penunjang TEXT,
            peralatan_medis TEXT, peralatan_lain TEXT,
            dokter_merujuk TEXT,
            status_rujukan TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect('rujukan_hjf.db')

def generate_no_rujukan():
    # Format: XXX/RUJUKAN/EXT/MM/2026
    current_year = datetime.now().year
    current_month = datetime.now().strftime("%m")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rujukan_external WHERE tanggal_input LIKE ?", (f"{datetime.now().strftime('%Y-%m')}%",))
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"{count:03d}/RUJUKAN/EXT/{current_month}/{current_year}"

# 3. Antarmuka Menu Utama
menu = st.sidebar.radio("Navigasi Menu Rujukan", ["Form Rujukan Baru HJF", "Data & Status Rujukan"])

st.title("🏥 HJF - SURAT RUJUKAN EXTERNAL (转诊说明)")
st.markdown("---")

if menu == "Form Rujukan Baru HJF":
    st.subheader("📝 Input Formulir Rujukan External")
    
    with st.form("form_rujukan_hjf", clear_on_submit=True):
        # Bagian Atas: Triase
        st.markdown("### **Kategori Triase (患者鉴别分类)**")
        triase = st.radio(
            "Pilih Tingkat Kegawatan:",
            options=["🔴 Merah (红)", "🟡 Kuning (黄)", "🟢 Hijau (绿)"],
            index=0,
            horizontal=True
        )
        st.markdown("---")
        
        # Identitas Pasien
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### **Identitas Pasien**")
            nama_pasien = st.text_input("Nama (名字)")
            tanggal_lahir = st.date_input("Tanggal Lahir (出生日期)", value=None, min_value=datetime(1900, 1, 1))
            jenis_kelamin = st.selectbox("Jenis Kelamin (性别)", options=["", "Laki-laki (男)", "Perempuan (女)"], index=0)
        with col2:
            st.markdown("##### **Administrasi**")
            no_id_rm = st.text_input("Nomor ID / RM (ID号/病历)")
            alamat = st.text_area("Alamat (地址)", height=85)
            
        st.markdown("---")
        
        # Kondisi Pasien Saat Ini
        st.markdown("### **Kondisi Pasien Saat Ini (患者本状况)**")
        col3, col4, col5 = st.columns(3)
        with col3:
            st.markdown("**Kesadaran (意识)**")
            gcs_e = st.text_input("GCS : E", placeholder="E")
            gcs_v = st.text_input("GCS : V", placeholder="V")
            gcs_m = st.text_input("GCS : M", placeholder="M")
        with col4:
            st.markdown("**Pemeriksaan Mata**")
            pupil = st.text_input("Pupil (瞳孔) mm")
            reflex_cahaya = st.text_input("Reflex Cahaya (对光反应)", placeholder="e.g. +/+")
        with col5:
            st.markdown("**Tanda-Tanda Vital (TTV)**")
            td = st.text_input("TD (血压) mmHg")
            nadi = st.text_input("Nadi (脉搏) X/m")
            suhu = st.text_input("Suhu (体温) °C")
            pernapasan = st.text_input("Pernapasan (呼吸) X/m")
            spo2 = st.text_input("SpO2 (血氧饱和度) %")
            
        st.markdown("---")
        
        # Alasan Rujukan & Diagnosis
        st.markdown("### **Alasan Dirujuk & Diagnosa (转诊原因 & 临床诊断)**")
        col6, col7 = st.columns(2)
        with col6:
            alasan_klinikal = st.text_area("Alasan Klinikal (临床)")
            alasan_bedah = st.text_area("Alasan Bedah (手术)")
        with col7:
            diagnosa_medis = st.text_area("Diagnosa Medis (临床诊断)")
            diagnosa_tambahan = st.text_area("Diagnosa Tambahan (附加诊断)")
            
        st.markdown("---")
        
        # Catatan Klinis & Riwayat Penyakit
        st.markdown("### **Catatan Klinis (临床备注)**")
        col8, col9 = st.columns(2)
        with col8:
            alergi = st.text_input("Alergi Obat / Makanan (过敏药物/食物)")
            riwayat_penyakit = st.multiselect(
                "Riwayat Penyakit (既往史)",
                options=["Tidak ada (无)", "Diabetes (糖尿病)", "Jantung (心脏病)", "Stroke (中风)"]
            )
            riwayat_lain = st.text_input("Riwayat Penyakit Lain-lain (其他)")
        with col9:
            tindakan = st.text_area("Tindakan yang telah dilakukan (已经采取的措施)")
            penunjang = st.text_area("Pemeriksaan penunjang terlampir (附辅助检查)")
            
        st.markdown("##### **Pengobatan yang telah diberikan (已给予的治疗)**")
        pengobatan = st.text_area("Masukkan daftar obat (pisahkan dengan koma atau baris baru)", placeholder="1. Paracetamol\n2. IV FD RL")
        
        st.markdown("##### **Peralatan Medis yang Digunakan Pasien (患者使用的医疗设备)**")
        peralatan_medis = st.multiselect(
            "Peralatan Medis:",
            options=["Tidak (无)", "Infus (输液)", "Oksigen (氧气)", "ETT (气管导管)", "NGT (胃管插管)", "Catheter (导尿管)", "Bidai (夹板)"]
        )
        peralatan_lain = st.text_input("Peralatan Medis Lain-lain (其他)")
        
        st.markdown("---")
        dokter_merujuk = st.text_input("Dokter yang Merujuk (转诊医生)")
        
        submit_btn = st.form_submit_button("Simpan & Sinkronisasi Formulir HJF")
        
        if submit_btn:
            if not nama_pasien or not no_id_rm or jenis_kelamin == "" or tanggal_lahir is None:
                st.error("❌ Mohon lengkapi Nama, No ID/RM, Tanggal Lahir, dan Jenis Kelamin!")
            else:
                no_rujukan = generate_no_rujukan()
                waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO rujukan_external (
                            no_rujukan, tanggal_input, triase, nama_pasien, tanggal_lahir, jenis_kelamin, no_id_rm, alamat,
                            gcs_e, gcs_v, gcs_m, pupil, reflex_cahaya, td, nadi, suhu, pernapasan, spo2,
                            alasan_klinikal, alasan_bedah, diagnosa_medis, diagnosa_tambahan,
                            alergi, riwayat_penyakit, riwayat_lain, pengobatan, tindakan, penunjang,
                            peralatan_medis, peralatan_lain, dokter_merujuk
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        no_rujukan, waktu_sekarang, triase, nama_pasien, str(tanggal_lahir), jenis_kelamin, no_id_rm, alamat,
                        gcs_e, gcs_v, gcs_m, pupil, reflex_cahaya, td, nadi, suhu, pernapasan, spo2,
                        alasan_klinikal, alasan_bedah, diagnosa_medis, diagnosa_tambahan,
                        alergi, ",".join(riwayat_penyakit), riwayat_lain, pengobatan, tindakan, penunjang,
                        ",".join(peralatan_medis), peralatan_lain, dokter_merujuk
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Data Rujukan HJF Berhasil Disimpan! Nomor: {no_rujukan}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Gagal menyimpan ke database: {e}")

elif menu == "Data & Status Rujukan":
    st.subheader("📋 Monitoring Dokumen Rujukan HJF")
    
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM rujukan_external ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("Belum ada rekam rujukan.")
    else:
        search_query = st.text_input("🔍 Cari Pasien (Nama / No. ID / RM)", "")
        if search_query:
            df = df[df['nama_pasien'].str.contains(search_query, case=False, na=False) | df['no_id_rm'].str.contains(search_query, case=False, na=False)]
            
        df.insert(0, "Pilih", False)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False, width="small"),
                "id": None, "no_rujukan": "No. Rujukan", "tanggal_input": "Waktu Input",
                "nama_pasien": "Nama Pasien", "no_id_rm": "No. ID / RM", "triase": "Triase",
                "status_rujukan": st.column_config.SelectboxColumn("Status", options=["Pending", "Diterima", "Ditolak"], required=True)
            },
            disabled=[c for c in df.columns if c != "Pilih" and c != "status_rujukan"],
            use_container_width=True
        )
        
        selected_rows = edited_df[edited_df["Pilih"] == True]
        
        col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 5])
        with col_btn1:
            if st.button("💾 Simpan Perubahan", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                for _, row in edited_df.iterrows():
                    cursor.execute("UPDATE rujukan_external SET status_rujukan = ? WHERE id = ?", (row['status_rujukan'], int(row['id'])))
                conn.commit()
                conn.close()
                st.success("Status Diperbarui!")
                st.rerun()
                
        if not selected_rows.empty:
            with col_btn2:
                btn_print = st.button("🖨️ Cetak Form HJF", type="primary", use_container_width=True)
            with col_btn3:
                if st.button("🗑️ Hapus Data"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    for _, row in selected_rows.iterrows():
                        cursor.execute("DELETE FROM rujukan_external WHERE id = ?", (int(row['id']),))
                    conn.commit()
                    conn.close()
                    st.success("Data Terhapus!")
                    st.rerun()
            
            if btn_print:
                for _, row in selected_rows.iterrows():
                    # Generate list pengobatan dan checkbox checklist
                    riwayat_db = row['riwayat_penyakit']
                    peralatan_db = row['peralatan_medis']
                    
                    html_template = f"""
                    <div id="hjf-print-area" style="padding: 20px; font-family: 'SimSun', 'Arial', sans-serif; background-color: #fff; color: #000; width: 210mm; min-height: 297mm; box-sizing: border-box; font-size: 13px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px;">
                            <div style="font-weight: bold; font-size: 16px;">
                                PT HALMAHERA JAYA FERONIKEL
                            </div>
                            <div style="text-align: right;">
                                <h3 style="margin:0;">SURAT RUJUKAN EXTERNAL (转转说明)</h3>
                                <p style="margin:2px 0 0 0; font-size:11px;">Nomor Rujukan: {row['no_rujukan']}</p>
                            </div>
                        </div>

                        <div style="margin: 10px 0; font-weight: bold;">
                            Triase (患者鉴别分类): 
                            <span style="margin-left:15px;">{"[X]" if "Merah" in row['triase'] else "[ ]"} Merah (红)</span>
                            <span style="margin-left:15px;">{"[X]" if "Kuning" in row['triase'] else "[ ]"} Kuning (黄)</span>
                            <span style="margin-left:15px;">{"[X]" if "Hijau" in row['triase'] else "[ ]"} Hijau (绿)</span>
                        </div>

                        <p style="margin: 5px 0;">Dengan Hormat (尊敬的), Mohon dilakukan pemeriksaan dan penanganan lebih lanjut untuk pasien:</p>
                        
                        <table style="width:100%; margin-bottom:10px; border-collapse: collapse;">
                            <tr><td style="width:25%; font-weight:bold;">Nama (名字)</td><td>: {row['nama_pasien']}</td></tr>
                            <tr><td style="font-weight:bold;">Tanggal Lahir (出生日期)</td><td>: {row['tanggal_lahir']}</td></tr>
                            <tr><td style="font-weight:bold;">Jenis Kelamin (性别)</td><td>: {row['jenis_kelamin']}</td></tr>
                            <tr><td style="font-weight:bold;">Nomor ID / RM (ID号/病历)</td><td>: {row['no_id_rm']}</td></tr>
                            <tr><td style="font-weight:bold;">Alamat (地址)</td><td>: {row['alamat']}</td></tr>
                        </table>

                        <fieldset style="border: 1px solid #000; padding: 8px; margin-bottom: 10px;">
                            <legend style="font-weight:bold;">Kondisi pasien saat ini (患者本状况)</legend>
                            <table style="width:100%;">
                                <tr>
                                    <td>Kesadaran (意识): GCS: E:{row['gcs_e']} V:{row['gcs_v']} M:{row['gcs_m']}</td>
                                    <td>Pupil (瞳孔): {row['pupil']} mm</td>
                                    <td>Reflex Cahaya: {row['reflex_cahaya']}</td>
                                </tr>
                                <tr>
                                    <td colspan="3">
                                        TD: {row['td']} mmHg | Nadi: {row['nadi']} X/m | Suhu: {row['suhu']} °C | Pernapasan: {row['pernapasan']} X/m | SpO2: {row['spo2']}%
                                    </td>
                                </tr>
                            </table>
                        </fieldset>

                        <table style="width:100%; border:1px solid #000; border-collapse:collapse; margin-bottom:10px;">
                            <tr style="border-bottom: 1px solid #000;">
                                <td style="width:50%; border-right:1px solid #000; padding:5px; vertical-align:top;">
                                    <strong>Alasan dirujuk (转诊原因)</strong><br>
                                    • Klinikal (临床): {row['alasan_klinikal']}<br>
                                    • Bedah (手术): {row['alasan_bedah']}
                                </td>
                                <td style="padding:5px; vertical-align:top;">
                                    <strong>Diagnosa Medis (临床诊断)</strong>: {row['diagnosa_medis']}<br>
                                    <strong>Diagnosa Tambahan (附加诊断)</strong>: {row['diagnosa_tambahan']}
                                </td>
                            </tr>
                        </table>

                        <fieldset style="border: 1px solid #000; padding: 8px; margin-bottom: 10px;">
                            <legend style="font-weight:bold;">Catatan Klinis (临床备注)</legend>
                            <p style="margin:3px 0;"><strong>Alergi (过敏):</strong> {row['alergi']}</p>
                            <p style="margin:3px 0;">
                                <strong>Riwayat Penyakit (既往史):</strong> 
                                {"[X]" if "Tidak ada" in riwayat_db else "[ ]"} Tidak ada 
                                {"[X]" if "Diabetes" in riwayat_db else "[ ]"} Diabetes 
                                {"[X]" if "Jantung" in riwayat_db else "[ ]"} Jantung 
                                {"[X]" if "Stroke" in riwayat_db else "[ ]"} Stroke | Lainnya: {row['riwayat_lain']}
                            </p>
                        </fieldset>

                        <div style="border:1px solid #000; padding:5px; margin-bottom:10px;">
                            <strong>Pengobatan yang telah diberikan (已给予的治疗):</strong>
                            <p style="white-space: pre-wrap; margin:3px 0;">{row['pengobatan']}</p>
                        </div>

                        <div style="border:1px solid #000; padding:5px; margin-bottom:10px;">
                            <strong>Tindakan & Pemeriksaan Penunjang (已经采取的措施 & 附辅助检查):</strong>
                            <p style="margin:3px 0;">• Tindakan: {row['tindakan']}</p>
                            <p style="margin:3px 0;">• Penunjang: {row['penunjang']}</p>
                        </div>

                        <fieldset style="border: 1px solid #000; padding: 8px; margin-bottom: 20px;">
                            <legend style="font-weight:bold;">Pasien memakai peralatan medis (患者使用的医疗设备)</legend>
                            {"[X]" if "Tidak" in peralatan_db else "[ ]"} Tidak 
                            {"[X]" if "Infus" in peralatan_db else "[ ]"} Infus 
                            {"[X]" if "Oksigen" in peralatan_db else "[ ]"} Oksigen 
                            {"[X]" if "ETT" in peralatan_db else "[ ]"} ETT 
                            {"[X]" if "NGT" in peralatan_db else "[ ]"} NGT 
                            {"[X]" if "Catheter" in peralatan_db else "[ ]"} Catheter 
                            {"[X]" if "Bidai" in peralatan_db else "[ ]"} Bidai | Lainnya: {row['peralatan_lain']}
                        </fieldset>

                        <table style="width:100%; margin-top:30px;">
                            <tr>
                                <td style="width:60%;">Tanggal (日期): {datetime.now().strftime('%d/%m/%Y')}</td>
                                <td style="text-align:center;">
                                    Dokter yang merujuk (转诊医生),<br><br><br><br>
                                    ( {row['dokter_merujuk']} )
                                </td>
                            </tr>
                        </table>
                    </div>

                    <script>window.print();</script>
                    <style>
                        @media print {{
                            body * {{ visibility: hidden; }}
                            #hjf-print-area, #hjf-print-area * {{ visibility: visible; }}
                            #hjf-print-area {{ position: absolute; left: 0; top: 0; width: 100%; }}
                        }}
                    </style>
                    """
                    st.components.v1.html(html_template, height=800, scrolling=True)
