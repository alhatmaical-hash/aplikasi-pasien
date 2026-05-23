import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit agar responsif dan bersih
st.set_page_config(
    page_title="Mortal Kombat Clone - Streamlit",
    layout="centered",
    initial_sidebar_state="collapsed" # Menyembunyikan sidebar agar fokus pada game
)

# Menghilangkan padding bawaan Streamlit menggunakan CSS khusus
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 1020px;
    }
    iframe {
        border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🥷 Prototipe Game Fighting 2D")
st.subheader("Bisa dimainkan langsung di browser / HP!")

# Kode HTML5 + JavaScript Game Engine (Client-Side Rendering untuk performa 60 FPS)
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body {
            margin: 0;
            background-color: #2c3e50;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
            touch-action: none;
        }
        canvas {
            background-color: #34495e;
            border: 2px solid #ffffff;
            display: block;
        }
    </style>
</head>
<body>

<canvas id="gameCanvas" width="1000" height="500"></canvas>

<script>
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// Sistem Input Keyboard
const keys = {};
window.addEventListener("keydown", e => { keys[e.key.toLowerCase()] = true; });
window.addEventListener("keyup", e => { keys[e.key.toLowerCase()] = false; });

// Kelas Fighter (Karakter)
class Fighter {
    constructor(x, color, controls, isPlayer1) {
        this.x = x;
        this.y = 290;
        this.width = 70;
        this.height = 160;
        this.color = color;
        this.controls = controls;
        this.isPlayer1 = isPlayer1;
        
        // Fisika
        this.velY = 0;
        this.isJumping = false;
        this.speed = 7;
        
        // Logika Bertarung
        this.health = 100;
        this.isAttacking = false;
        this.attackCooldown = 0;
        this.attackRect = { x: 0, y: 0, width: 0, height: 0 };
        this.facingRight = isPlayer1;
    }

    update(target) {
        const GRAVITY = 1.0;
        
        // Otomatis menghadap ke arah lawan
        this.facingRight = (this.x + this.width/2 < target.x + target.width/2);

        // Pergerakan Horizontal
        if (!this.isAttacking) {
            if (keys[this.controls.left]) this.x -= this.speed;
            if (keys[this.controls.right]) this.x += this.speed;
            
            // Lompat
            if (keys[this.controls.jump] && !this.isJumping) {
                this.velY = -20;
                this.isJumping = true;
            }
        }

        // Menerapkan Gravitasi
        this.velY += GRAVITY;
        this.y += this.velY;

        // Batasan Lantai (Y = 450 adalah batas bawah kaki)
        if (this.y + this.height > 450) {
            this.y = 450 - this.height;
            this.isJumping = false;
            this.velY = 0;
        }

        // Batasan Dinding Layar
        if (this.x < 0) this.x = 0;
        if (this.x + this.width > canvas.width) this.x = canvas.width - this.width;

        // Jeda waktu serangan
        if (this.attackCooldown > 0) this.attackCooldown--;

        // Logika Serangan (Pukulan)
        if (keys[this.controls.attack] && this.attackCooldown === 0) {
            this.isAttacking = true;
            this.attackCooldown = 25; // jeda frame sebelum bisa mukul lagi
            
            let attackWidth = 90;
            let attackX = this.facingRight ? this.x + this.width : this.x - attackWidth;
            this.attackRect = { x: attackX, y: this.y + 30, width: attackWidth, height: 40 };

            // Deteksi tabrakan Hitbox dengan Hurtbox musuh
            if (
                this.attackRect.x < target.x + target.width &&
                this.attackRect.x + this.attackRect.width > target.x &&
                this.attackRect.y < target.y + target.height &&
                this.attackRect.y + this.attackRect.height > target.y
            ) {
                target.health -= 10;
                if (target.health < 0) target.health = 0;
            }
        }
    }

    draw() {
        // Gambar Tubuh Utama
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.width, this.height);

        // Gambar Mata (Indikator Hadap)
        ctx.fillStyle = "#ffffff";
        let eyeX = this.facingRight ? this.x + this.width - 20 : this.x + 10;
        ctx.fillRect(eyeX, this.y + 20, 10, 10);

        // Gambar Efek Pukulan (Hitbox Kuning)
        if (this.isAttacking) {
            ctx.fillStyle = "#f1c40f";
            ctx.fillRect(this.attackRect.x, this.attackRect.y, this.attackRect.width, this.attackRect.height);
            this.isAttacking = false; // Matikan status setelah digambar 1 frame
        }
    }
}

// Inisialisasi Karakter & Tombol Kontrol
const p1Controls = { left: 'a', right: 'd', jump: 'w', attack: 'f' };
const p2Controls = { left: 'arrowleft', right: 'arrowright', jump: 'arrowup', attack: 'j' };

const player1 = new Fighter(150, "#3498db", p1Controls, true);
const player2 = new Fighter(780, "#e74c3c", p2Controls, false);

let gameOver = false;

// Game Loop Utama
function gameLoop() {
    // Bersihkan layar
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update Logika jika game belum selesai
    if (!gameOver) {
        player1.update(player2);
        player2.update(player1);

        if (player1.health <= 0 || player2.health <= 0) {
            gameOver = true;
        }
    }

    // --- PROSES MENGGAMBAR ---
    // Gambar Tanah/Lantai
    ctx.fillStyle = "#1e272e";
    ctx.fillRect(0, 450, canvas.width, 50);

    // Gambar Karakter
    player1.draw();
    player2.draw();

    // Gambar UI Bar Darah P1 (Kiri)
    ctx.fillStyle = "#c0392b";
    ctx.fillRect(40, 20, 400, 30);
    ctx.fillStyle = "#2ecc71";
    ctx.fillRect(40, 20, player1.health * 4, 30);

    // Gambar UI Bar Darah P2 (Kanan)
    ctx.fillStyle = "#c0392b";
    ctx.fillRect(560, 20, 400, 30);
    ctx.fillStyle = "#2ecc71";
    ctx.fillRect(560 + (400 - player2.health * 4), 20, player2.health * 4, 30);

    // Teks Layar Akhir (Game Over)
    if (gameOver) {
        ctx.fillStyle = "#f1c40f";
        ctx.font = "bold 50px Arial";
        ctx.textAlign = "center";
        let winner = player1.health <= 0 ? "PEMAIN 2 MENANG!" : "PEMAIN 1 MENANG!";
        ctx.fillText(winner, canvas.width / 2, canvas.height / 2);
    }

    requestAnimationFrame(gameLoop);
}

// Jalankan Mesin Game
gameLoop();
</script>

</body>
</html>
"""

# Render komponen game ke dalam Streamlit (Tinggi disesuaikan agar pas tanpa scrollbar)
components.html(game_html, height=520, scrolling=False)

# Informasi petunjuk kontrol di bagian bawah aplikasi Streamlit
st.info("""
🎮 **Panduan Kontrol Karakter:**
* **Pemain 1 (Biru):** Tombol **A / D** untuk Jalan, **W** untuk Lompat, dan **F** untuk Memukul.
* **Pemain 2 (Merah):** Tombol **Panah Kiri / Kanan** untuk Jalan, **Panah Atas** untuk Lompat, dan **J** untuk Memukul.
""")
