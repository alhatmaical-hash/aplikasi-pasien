import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import time
import base64

# --- 1. FUNGSI UNTUK BACKGROUND GAMBAR LOKAL ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    page_bg_img = f'''
    <style>
    * {{
        font-family: "Times New Roman", Times, serif !important;
    }}
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Container utama agar tulisan terang dan jelas */
    .glass-container {{
        background-color: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(15px);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 20px;
    }}

    /* Pengaturan teks agar kontras (Putih dengan Shadow) */
    h1, h2, h3, p, label {{
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    /* Kotak Input agar tetap terbaca jelas */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: black !important;
