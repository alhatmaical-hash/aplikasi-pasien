import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Klinik Terpadu - Sistem Antrean", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_custom_design(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    st.markdown(f'''
    <style>
    /* Font Global */
    * {{ font-family: "Times New Roman", Times, serif !important; }}

    /* Background Utama */
    .stApp {{
        background-image: linear-gradient(rgba(0, 20, 40, 0.6), rgba(0, 10, 20, 0.8)), 
                          url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Judul Utama */
    .main-title {{
        color: white;
        font-size: 42px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 5px;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
    }}

    /* Glassmorphism Card (Efek Kaca) */
    .glass-card {{
        background: rgba(0, 50, 80, 0.4);
        backdrop-filter: blur(10px);
        border: 2px solid #00d4ff;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        margin-top: 20px;
    }}

    /* Statistik Antrean di Bagian Bawah */
    .stat-bar {{
        background: rgba(0, 0, 0, 0.6);
        border: 1px solid #00d4ff;
        border-radius: 10px;
        padding: 10px 20px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin-top: 30px;
        color: white;
    }}
    .stat-item
