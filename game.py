
1. **Visual Karakter:** Pemain (Biru) dan Musuh (Merah) kini memiliki model karakter berbasis piksel yang lebih detail, lengkap dengan gaya visual rambut dan pakaian, menggantikan bentuk kotak sederhana.
2. **Mekanik Animasi:** Kedua karakter sekarang berada dalam posisi sedang saling memukul (menerjang maju) pada saat yang sama, menciptakan momen pertarungan yang dinamis.
3. **Hapus Player 2:** Kontrol manual untuk Player 2 telah sepenuhnya dihilangkan.
4. **Lawan Komputer:** Karakter Merah sekarang secara eksplisit ditandai dengan teks **"(CPU)"** pada bar darahnya untuk menunjukkan bahwa ia dikendalikan oleh AI, bukan pemain kedua.
5. **Pembaruan Panduan:** Teks instruksi di bagian bawah halaman telah diperbarui untuk mencerminkan bahwa game ini sekarang hanya untuk satu pemain (P1 vs CPU).

---

```python
import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit agar responsif dan bersih
st.set_page_config(
    page_title="Pixel Brawler 2D - Streamlit (Solo Mode)",
    layout="centered",
    initial_sidebar_state="collapsed"
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

st.title("🥷 Pixel Brawler 2D (Solo Mode)")
st.subheader("Hadapi Komputer dalam duel seni bela diri!")

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

// Sistem Input Keyboard (Sekarang hanya untuk P1)
const keys = {};
window.addEventListener("keydown", e => { keys[e.key.toLowerCase()] = true; });
window.addEventListener("keyup", e => { keys[e.key.toLowerCase()] = false; });

// Kelas Fighter (Karakter) dengan Visual Piksel
class Fighter {
    constructor(x, color, controls, isPlayer, name) {
        this.x = x;
        this.y = 290;
        this.width = 110;
        this.height = 160;
        this.color = color;
        this.controls = controls;
        this.isPlayer = isPlayer;
        this.name = name;
        
        // Fisika
        this.velY = 0;
        this.isJumping = false;
        this.speed = 7;
        
        // Logika Bertarung
        this.health = 100;
        this.isAttacking = false;
        this.attackCooldown = 0;
        this.attackRect = { x: 0, y: 0, width: 0, height: 0 };
        this.facingRight = isPlayer;
        this.isHitStun = False
    }

    update(target) {
        const GRAVITY = 1.0;
        
        // Otomatis menghadap ke arah lawan
        this.facingRight = (this.x + this.width/2 < target.x + target.width/2);

        // --- Logika Input / AI ---
        let attackWidth = 130;
        
        if (this.isPlayer) {
            // Kontrol Manual Player 1
            if (!this.isAttacking && !this.isHitStun) {
                if (keys[this.controls.left]) this.x -= this.speed;
                if (keys[this.controls.right]) this.x += this.speed;
                
                // Lompat
                if (keys[this.controls.jump] && !this.isJumping) {
                    this.velY = -20;
                    this.isJumping = true;
                }
                
                // Serangan (Maju Sambil Memukul)
                if (keys[this.controls.attack] && this.attackCooldown === 0) {
                    this.isAttacking = true;
                    this.attackCooldown = 35; 
                    
                    let attackX = this.facingRight ? this.x + this.width - 30 : this.x - attackWidth + 30;
                    this.attackRect = { x: attackX, y: this.y + 10, width: attackWidth, height: 60 };
                    
                    // Serangan P1 membuat P1 maju sedikit
                    if (this.facingRight) this.x += 15; else this.x -= 15;
                }
            }
        } else {
            // Kontrol AI (Lawan Merah)
            if (!this.isAttacking && !this.isHitStun && !gameOver) {
                // AI Sederhana: Kejar Pemain
                if (this.x > target.x + target.width + 10) {
                    this.x -= this.speed;
                } else if (this.x < target.x - 10) {
                    this.x += this.speed;
                }
                
                // AI Sederhana: Serang jika dalam jangkauan
                let distX = Math.abs((this.x + this.width/2) - (target.x + target.width/2));
                if (distX < this.width + 20 && this.attackCooldown === 0 && Math.random() < 0.1) {
                    this.isAttacking = true;
                    this.attackCooldown = 40; 
                    
                    let attackX = this.facingRight ? this.x + this.width - 30 : this.x - attackWidth + 30;
                    this.attackRect = { x: attackX, y: this.y + 10, width: attackWidth, height: 60 };
                    
                    // Serangan AI membuat AI maju sedikit
                    if (this.facingRight) this.x += 15; else this.x -= 15;
                }
                
                // AI Sederhana: Acak Lompat
                if (Math.random() < 0.01 && !this.isJumping) {
                    this.velY = -18;
                    this.isJumping = true;
                }
            }
        }

        // --- Deteksi Tabrakan Serangan ---
        if (this.isAttacking) {
            // Cek tabrakan Hitbox dengan Hurtbox musuh
            if (
                this.attackRect.x < target.x + target.width &&
                this.attackRect.x + this.attackRect.width > target.x &&
                this.attackRect.y < target.y + target.height &&
                this.attackRect.y + this.attackRect.height > target.y
            ) {
                target.health -= 10;
                if (target.health < 0) target.health = 0;
                target.isHitStun = True;
                setTimeout(() => { target.isHitStun = False; }, 200); // 200ms HitStun
            }
            this.isAttacking = false; // Matikan status setelah tabrakan dicek
        }

        // --- Fisika Lanjut ---
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
    }

    draw() {
        // --- Menggambar Model Karakter (Visual Orang Piksel) ---
        // (Warna Tubuh Dasar digunakan untuk visual piksel)
        ctx.fillStyle = this.color;
        
        // 1. Gambar Batang Tubuh
        ctx.fillRect(this.x + 20, this.y + 40, this.width - 40, 70);
        
        // 2. Gambar Kepala (dengan rambut sederhana)
        ctx.fillStyle = "#f39c12"; // Rambut oranye
        ctx.fillRect(this.x + 35, this.y + 10, this.width - 70, 30);
        ctx.fillStyle = this.color; // Wajah
        ctx.fillRect(this.x + 40, this.y + 15, this.width - 80, 20);

        // 3. Gambar Lengan (Maju dalam serangan)
        let armX = this.facingRight ? this.x + this.width - 25 : this.x - 5;
        let armY = this.y + 50;
        ctx.fillRect(armX, armY, 30, 20); // Bahu
        ctx.fillRect(armX + (this.facingRight ? 15 : -15), armY + 20, 20, 30); // Kepalan maju

        // 4. Gambar Kaki
        ctx.fillRect(this.x + 25, this.y + 110, 20, 50); // Kaki 1
        ctx.fillRect(this.x + 65, this.y + 110, 20, 50); // Kaki 2
        
        // --- Indikator Visual ---
        // Gambar Mata (Indikator Hadap)
        ctx.fillStyle = "#ffffff";
        let eyeX = this.facingRight ? this.x + this.width - 35 : this.x + 25;
        ctx.fillRect(eyeX, this.y + 20, 8, 8);
        
        // Visualisasi Pukulan Aktif (Hitbox Kuning)
        // (Tampilkan selama beberapa frame cooldown awal)
        if (this.attackCooldown > 30) {
            ctx.fillStyle = "#f1c40f";
            ctx.fillRect(this.attackRect.x, this.attackRect.y, this.attackRect.width, this.attackRect.height);
        }
    }
}

// Inisialisasi Karakter (Player vs CPU)
const p1Controls = { left: 'a', right: 'd', jump: 'w', attack: 'f' };

const player1 = new Fighter(150, "#3498db", p1Controls, true, "Pemain 1");
const computerOpponent = new Fighter(780, "#e74c3c", null, false, "(CPU)"); // Hapus kontrol untuk CPU

let gameOver = false;

// Game Loop Utama
function gameLoop() {
    // Bersihkan layar
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update Logika jika game belum selesai
    if (!gameOver) {
        player1.update(computerOpponent);
        computerOpponent.update(player1);

        if (player1.health <= 0 || computerOpponent.health <= 0) {
            gameOver = true;
        }
    }

    // --- PROSES MENGGAMBAR ---
    // Gambar Tanah/Lantai
    ctx.fillStyle = "#1e272e";
    ctx.fillRect(0, 450, canvas.width, 50);

    // Gambar Karakter
    player1.draw();
    computerOpponent.draw();

    // Gambar UI Bar Darah P1 (Kiri)
    ctx.fillStyle = "#c0392b";
    ctx.fillRect(40, 20, 400, 30);
    ctx.fillStyle = "#2ecc71";
    ctx.fillRect(40, 20, player1.health * 4, 30);
    ctx.fillStyle = "#ffffff"; ctx.font = "bold 16px Arial"; ctx.fillText(player1.name, 45, 41);

    // Gambar UI Bar Darah CPU (Kanan)
    ctx.fillStyle = "#c0392b";
    ctx.fillRect(560, 20, 400, 30);
    ctx.fillStyle = "#2ecc71";
    ctx.fillRect(560 + (400 - computerOpponent.health * 4), 20, computerOpponent.health * 4, 30);
    ctx.fillStyle = "#ffffff"; ctx.font = "bold 16px Arial"; ctx.textAlign = "right"; ctx.fillText(computerOpponent.name, 955, 41);

    // Teks Layar Akhir (Game Over)
    if (gameOver) {
        ctx.fillStyle = "#f1c40f";
        ctx.font = "bold 50px Arial";
        ctx.textAlign = "center";
        let winner = player1.health <= 0 ? "KOMPUTER MENANG!" : "PEMAIN 1 MENANG!";
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
🎮 **Panduan Kontrol (Mode Solo):**
* **Anda (Biru - P1):** Tombol **A / D** untuk Jalan, **W** untuk Lompat, dan **F** untuk Menyerang.
* **Musuh (Merah - CPU):** Dikendalikan secara otomatis oleh komputer. Tidak ada kontrol manual untuk Player 2.
""")

```
