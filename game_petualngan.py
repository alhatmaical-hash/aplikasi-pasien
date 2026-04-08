import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi Halaman
st.set_page_config(page_title="Hunter of the Black Forest", layout="centered", page_icon="⚔️")

st.title("⚔️ Hunter of the Black Forest")
st.write("Gunakan **Panah** untuk bergerak, **Spasi** untuk menebas pedang. Berhati-hatilah, hutan ini gelap...")

# --- Bagian HTML & JAVASCRIPT ---
# Ini adalah inti dari game real-time.
game_code = """
<div id="game-ui" style="text-align: center; font-family: 'Courier New', Courier, monospace; color: white;">
    <canvas id="gameCanvas" width="600" height="400" style="border:4px solid #444; background-color: #050505; border-radius: 8px; cursor: crosshair;"></canvas>
    <div style="display: flex; justify-content: space-around; margin-top: 10px; font-weight: bold; font-size: 1.2em;">
        <div>❤️ HP: <span id="playerHp" style="color: #ff4d4d;">100</span></div>
        <div>💀 Monster Dikalahkan: <span id="killCount" style="color: #ffcc00;">0</span></div>
    </div>
    <div id="gameStatus" style="margin-top: 10px; font-size: 1.5em; font-weight: bold;"></div>
</div>

<script>
    const canvas = document.getElementById("gameCanvas");
    const ctx = canvas.getContext("2d");
    const hpEl = document.getElementById("playerHp");
    const killEl = document.getElementById("killCount");
    const statusEl = document.getElementById("gameStatus");

    // --- Konfigurasi Game ---
    const TILE_SIZE = 20;
    const PLAYER_SPEED = 4;
    const MONSTER_SPEED = 1.5;
    const ATTACK_RANGE = 35;
    const VISION_RADIUS = 120; // Radius cahaya di sekitar pemain

    // State Game
    let isGameOver = False;
    let kills = 0;
    let keys = {};

    // Objek Pemain
    let player = {
        x: canvas.width / 2,
        y: canvas.height / 2,
        size: TILE_SIZE,
        hp: 100,
        color: "#00bfff", // Biru Cerah
        isAttacking: False,
        attackTimer: 0
    };

    // Objek Monster (Array)
    let monsters = [];
    function spawnMonster() {
        if (monsters.length < 5 && !isGameOver) {
            monsters.push({
                x: Math.random() < 0.5 ? -20 : canvas.width + 20, // Spawn di luar layar
                y: Math.random() * canvas.height,
                size: TILE_SIZE,
                hp: 30,
                color: "#ff3333", // Merah
                state: "idle" // idle atau chasing
            });
        }
    }
    // Spawn awal dan berkala
    for(let i=0; i<3; i++) spawnMonster();
    setInterval(spawnMonster, 5000); 


    // --- Input Keyboard ---
    window.addEventListener("keydown", e => {
        keys[e.key] = true;
        if (e.key === " " && !player.isAttacking && !isGameOver) {
            player.isAttacking = true;
