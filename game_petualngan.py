import streamlit as st
import streamlit.components.v1 as components
import textwrap

# Konfigurasi Halaman agar tampilan bersih dan profesional
st.set_page_config(page_title="Hunter of the Black Forest", layout="centered", page_icon="⚔️")

st.title("⚔️ Hunter of the Black Forest")
st.markdown("Klik pada kotak game, lalu gunakan **Panah** untuk gerak dan **Spasi** untuk menebas!")

# Bagian Game (HTML, CSS, JS) dalam satu blok string
# Perhatikan: Saya tidak menggunakan f-string agar tidak bentrok dengan kurung kurawal JS
game_code = textwrap.dedent("""
<div id="game-ui" style="text-align: center; font-family: sans-serif; color: white; background: #111; padding: 20px; border-radius: 15px;">
    <canvas id="gameCanvas" width="600" height="400" style="border:3px solid #333; background-color: #000; border-radius: 8px;"></canvas>
    <div style="display: flex; justify-content: space-around; margin-top: 15px; font-weight: bold; font-size: 1.1em;">
        <div style="color: #ff4d4d;">❤️ HP: <span id="playerHp">100</span></div>
        <div style="color: #ffcc00;">💀 MONSTER: <span id="killCount">0</span></div>
    </div>
    <div id="gameStatus" style="margin-top: 15px; font-size: 1.4em; font-weight: bold; min-height: 30px;"></div>
</div>

<script>
    const canvas = document.getElementById("gameCanvas");
    const ctx = canvas.getContext("2d");
    const hpEl = document.getElementById("playerHp");
    const killEl = document.getElementById("killCount");
    const statusEl = document.getElementById("gameStatus");

    let isGameOver = false;
    let kills = 0;
    let keys = {};
    const VISION_RADIUS = 130;
