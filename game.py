import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit agar bersih dan fokus ke game
st.set_page_config(
    page_title="Stickman Fighting 3D",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Khusus untuk menghilangkan komponen bawaan Streamlit agar terasa seperti Game Aplikasi Desktop
st.markdown("""
    <style>
    .block-container { padding: 0.5rem; max-width: 1020px; }
    iframe { border-radius: 12px; box-shadow: 0px 15px 35px rgba(0,0,0,0.8); }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# Kode Game Utama (HTML5 + CSS3 + Three.js WebGL)
game_code = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stickman Fighting 3D Engine</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        * { box-sizing: border-box; user-select: none; }
        body {
            margin: 0;
            padding: 0;
            background-color: #111;
            font-family: 'Arial', sans-serif;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        #game-container {
            width: 1000px;
            height: 550px;
            position: relative;
            background-color: #1a1b20;
            border: 3px solid #deff9a;
            border-radius: 10px;
            overflow: hidden;
        }
        .screen {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: radial-gradient(circle, #2c3e50 0%, #0f171e 100%);
            z-index: 10;
        }
        .active { display: flex; }

        /* --- STYLE MENU UTAMA --- */
        h1 { font-size: 55px; color: #fff; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 3px; }
        h1 span { color: #deff9a; text-shadow: 0 0 10px rgba(222,255,154,0.5); }
        .menu-btn {
            width: 280px;
            padding: 14px;
            margin: 10px;
            font-size: 18px;
            font-weight: bold;
            color: #fff;
            background: rgba(255,255,255,0.05);
            border: 2px solid #deff9a;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
        }
        .menu-btn:hover {
            background: #deff9a;
            color: #000;
            box-shadow: 0 0 15px #deff9a;
            transform: scale(1.05);
        }

        /* --- STYLE MENU OPTIONS --- */
        .options-box { background: rgba(0,0,0,0.5); padding: 30px; border-radius: 8px; border: 1px solid #555; width: 400px; text-align: left; }
        .option-row { margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        select { padding: 8px; background: #222; color: #fff; border: 1px solid #deff9a; border-radius: 4px; font-size: 16px; }

        /* --- STYLE PILIH KARAKTER --- */
        .char-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
        .char-card {
            width: 160px; padding: 20px; background: rgba(0,0,0,0.4); border: 2px solid #555; 
            border-radius: 8px; text-align: center; cursor: pointer; transition: 0.2s;
        }
        .char-card:hover { border-color: #deff9a; background: rgba(222,255,154,0.1); }
        .char-card.selected { border-color: #deff9a; background: #deff9a; color: #000; box-shadow: 0 0 15px #deff9a; }
        .char-card h3 { margin: 0; font-size: 20px; }

        /* --- STYLE HUD ARENA PERTARUNGAN --- */
        #hud {
            position: absolute; top: 0; left: 0; width: 100%; height: 80px;
            display: none; justify-content: space-between; align-items: center; padding: 0 40px; z-index: 5;
        }
        .health-container { width: 380px; height: 25px; background: #c0392b; border: 2px solid #fff; border-radius: 5px; position: relative; }
        .health-bar { width: 100%; height: 100%; background: #2ecc71; transition: width 0.1s ease; }
        .char-name { position: absolute; top: -25px; font-weight: bold; font-size: 16px; color: #fff; }
        #timer { font-size: 32px; font-weight: bold; color: #f1c40f; background: rgba(0,0,0,0.6); padding: 5px 15px; border-radius: 5px; }
        
        /* Canvas Pengolah 3D */
        #three-canvas-container { width: 100%; height: 100%; display: none; }
    </style>
</head>
<body>

<div id="game-container">
    
    <div id="menu-screen" class="screen active">
        <h1>Stickman <span>3D</span></h1>
        <button class="menu-btn" onclick="switchScreen('char-screen')">Mulai Game</button>
        <button class="menu-btn" onclick="switchScreen('options-screen')">Options</button>
    </div>

    <div id="options-screen" class="screen">
        <h2>Pengaturan Game</h2>
        <div class="options-box">
            <div class="option-row">
                <label>Kesulitan AI:</label>
                <select id="difficulty-select">
                    <option value="easy">Easy (PemuIa)</option>
                    <option value="normal" selected>Normal</option>
                    <option value="hard">Hard (Menantang)</option>
                    <option value="hell">Hell (Mustahil)</option>
                </select>
            </div>
            <div class="option-row">
                <label>Kualitas Grafis:</label>
                <select>
                    <option>Tinggi (60 FPS)</option>
                    <option>Medium</option>
                    <option>Rendah</option>
                </select>
            </div>
        </div>
        <button class="menu-btn" style="margin-top: 30px;" onclick="switchScreen('menu-screen')">Kembali</button>
    </div>

    <div id="char-screen" class="screen">
        <h2>Pilih Petarung Anda</h2>
        <div class="char-grid">
            <div class="char-card selected" id="char-ninja" onclick="selectCharacter('Ninja Speedster', 0x3498db, 'char-ninja')">
                <h3>Ninja</h3>
                <p style="font-size:12px; margin:5px 0 0 0; opacity:0.7;">Biru - Cepat</p>
            </div>
            <div class="char-card" id="char-cyber" onclick="selectCharacter('Cyber Shadow', 0x9b59b6, 'char-cyber')">
                <h3>Cyber</h3>
                <p style="font-size:12px; margin:5px 0 0 0; opacity:0.7;">Ungu - Seimbang</p>
            </div>
            <div class="char-card" id="char-monk" onclick="selectCharacter('Gold Monk', 0xf1c40f, 'char-monk')">
                <h3>Monk</h3>
                <p style="font-size:12px; margin:5px 0 0 0; opacity:0.7;">Emas - Kuat</p>
            </div>
        </div>
        <div>
            <button class="menu-btn" onclick="switchScreen('menu-screen')" style="border-color:#e74c3c;">Batal</button>
            <button class="menu-btn" onclick="startGame()">Bertarung!</button>
        </div>
    </div>

    <div id="hud">
        <div class="health-container">
            <div class="char-name" id="p1-hud-name">Player 1</div>
            <div id="p1-bar" class="health-bar"></div>
        </div>
        <div id="timer">99</div>
        <div class="health-container">
            <div class="char-name" style="right:0;" id="cpu-hud-name">CPU (Normal)</div>
            <div id="cpu-bar" class="health-bar" style="float: right;"></div>
        </div>
    </div>

    <div id="three-canvas-container"></div>

</div>

<script>
// --- MANAGEMENT ENGINE STATE & NAVIGASI ---
function switchScreen(screenId) {
    // Sembunyikan semua skrin menu
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    // Aktifkan skrin tujuan
    document.getElementById(screenId).classList.add('active');
}

// Konfigurasi Pilihan Karakter Default
let selectedCharName = "Ninja Speedster";
let selectedCharColor = 0x3498db;

function selectCharacter(name, colorHex, cardId) {
    selectedCharName = name;
    selectedCharColor = colorHex;
    // Reset desain kartu lama
    document.querySelectorAll('.char-card').forEach(c => c.classList.remove('selected'));
    // Tandai kartu baru
    document.getElementById(cardId).classList.add('selected');
}

// --- LOGIKA UTAMA ENGINE GAME 3D (THREE.JS) ---
let scene, camera, renderer, player1, computer, gameOver = false, animationId;
const keys = {};

window.addEventListener("keydown", e => { keys[e.key.toLowerCase()] = true; });
window.addEventListener("keyup", e => { keys[e.key.toLowerCase()] = false; });

function startGame() {
    // 1. Sembunyikan Skrin Pilihan Karakter & Aktifkan HUD
    switchScreen('none'); 
    document.getElementById('hud').style.display = 'flex';
    document.getElementById('three-canvas-container').style.display = 'block';

    // Ambil Level Kesulitan dari Menu Options
    let diff = document.getElementById('difficulty-select').value;
    document.getElementById('cpu-hud-name').innerText = `CPU (${diff.toUpperCase()})`;
    document.getElementById('p1-hud-name').innerText = selectedCharName;

    // Reset status pertandingan
    gameOver = false;
    document.getElementById('p1-bar').style.width = '100%';
    document.getElementById('cpu-bar').style.width = '100%';

    // 2. Setup Dunia 3D Baru
    const container = document.getElementById('three-canvas-container');
    container.innerHTML = ''; // bersihkan sisa render sebelumnya

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x11141a);

    camera = new THREE.PerspectiveCamera(45, 1000 / 550, 0.1, 1000);
    camera.position.set(0, 4, 15);
    camera.lookAt(0, 2, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(1000, 550);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Lampu Pencahayaan Panggung
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 15, 5);
    dirLight.castShadow = true;
    scene.add(dirLight);

    // Lantai Arena 3D
    const floorGeo = new THREE.BoxGeometry(30, 0.5, 8);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x222f3e, roughness: 0.8 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.position.y = -0.25;
    floor.receiveShadow = true;
    scene.add(floor);

    // Kelas Karakter Petarung 3D
    class Fighter3D {
        constructor(startX, colorHex, isPlayer, difficulty) {
            this.isPlayer = isPlayer;
            this.difficulty = difficulty;
            this.health = 100;
            this.speed = 0.14;
            this.velY = 0;
            this.isJumping = false;
            this.isAttacking = false;
            this.attackCooldown = 0;
            this.facingRight = isPlayer;

            this.mesh = new THREE.Group();
            this.mesh.position.set(startX, 0, 0);

            // Anatomi 3D: Badan Stickman tebal
            const bodyGeo = new THREE.BoxGeometry(0.8, 1.8, 0.6);
            const bodyMat = new THREE.MeshStandardMaterial({ color: colorHex, roughness: 0.5 });
            this.body = new THREE.Mesh(bodyGeo, bodyMat);
            this.body.position.y = 1.4;
            this.body.castShadow = true;
            this.mesh.add(this.body);

            // Anatomi 3D: Kepala Bulat
            const headGeo = new THREE.SphereGeometry(0.35, 16, 16);
            const headMat = new THREE.MeshStandardMaterial({ color: 0xffdbac });
            this.head = new THREE.Mesh(headGeo, headMat);
            this.head.position.y = 2.5;
            this.head.castShadow = true;
            this.mesh.add(this.head);

            // Anatomi 3D: Lengan Serang
            const armGeo = new THREE.BoxGeometry(0.25, 0.25, 1.2);
            this.arm = new THREE.Mesh(armGeo, bodyMat);
            this.arm.position.set(0.3, 1.6, 0.4);
            this.arm.castShadow = true;
            this.mesh.add(this.arm);

            scene.add(this.mesh);
        }

        update(target) {
            // Mengatur rotasi arah hadap otomatis
            if (this.mesh.position.x < target.mesh.position.x) {
                this.mesh.rotation.y = Math.PI / 2;
                this.facingRight = true;
            } else {
                this.mesh.rotation.y = -Math.PI / 2;
                this.facingRight = false;
            }

            if (this.isPlayer) {
                // Logika Pergerakan Tombol P1
                if (keys['a']) this.mesh.position.x -= this.speed;
                if (keys['d']) this.mesh.position.x += this.speed;
                if (keys['w'] && !this.isJumping) { this.velY = 0.24; this.isJumping = true; }
                if (keys['f'] && this.attackCooldown === 0) { this.isAttacking = true; this.attackCooldown = 25; }
            } else {
                // Logika Algoritma AI Otomatis Komputer
                let distanceToP1 = Math.abs(this.mesh.position.x - target.mesh.position.x);
                let aiMoveSpeed = this.speed * 0.75;

                // Modifikasi kecepatan respons berdasarkan kesulitan opsi
                if (this.difficulty === 'hard') aiMoveSpeed = this.speed * 0.9;
                if (this.difficulty === 'hell') aiMoveSpeed = this.speed * 1.2;

                if (!this.isAttacking && !gameOver) {
                    // Kejar koordinat X pemain
                    if (this.mesh.position.x > target.mesh.position.x + 1.6) {
                        this.mesh.position.x -= aiMoveSpeed;
                    } else if (this.mesh.position.x < target.mesh.position.x - 1.6) {
                        this.mesh.position.x += aiMoveSpeed;
                    }

                    // Ambang batas peluang serangan AI menyerang pemain
                    let attackChance = 0.05;
                    if (this.difficulty === 'hard') attackChance = 0.1;
                    if (this.difficulty === 'hell') attackChance = 0.25;

                    if (distanceToP1 < 2.0 && this.attackCooldown === 0 && Math.random() < attackChance) {
                        this.isAttacking = true;
                        this.attackCooldown = 30;
                    }
                }
            }

            // Eksekusi Efek Visual Serangan Pukulan
            if (this.isAttacking) {
                this.arm.position.z = 1.6;
                this.arm.scale.set(1, 1, 2.2);

                // Hitung Tabrakan Jarak Sumbu 3D
                let dist = Math.abs(this.mesh.position.x - target.mesh.position.x);
                if (dist < 2.2 && Math.abs(this.mesh.position.y - target.mesh.position.y) < 1.3) {
                    target.health -= 8;
                    if (target.health < 0) target.health = 0;
                    
                    // Sinkronisasi Pengurangan UI Bar Darah di Atas Browser
                    if (target.isPlayer) {
                        document.getElementById('p1-bar').style.width = target.health + '%';
                    } else {
                        document.getElementById('cpu-bar').style.width = target.health + '%';
                    }
                }
                this.isAttacking = false;
            } else {
                if (this.attackCooldown < 15) {
                    this.arm.position.z = 0.4;
                    this.arm.scale.set(1, 1, 1);
                }
            }

            // Gravitasi Lompat
            if (this.isJumping) {
                this.velY -= 0.01;
                this.mesh.position.y += this.velY;
                if (this.mesh.position.y <= 0) {
                    this.mesh.position.y = 0;
                    this.isJumping = false;
                    this.velY = 0;
                }
            }

            if (this.mesh.position.x < -13) this.mesh.position.x = -13;
            if (this.mesh.position.x > 13) this.mesh.position.x = 13;

            if (this.attackCooldown > 0) this.attackCooldown--;
        }
    }

    // Inisialisasi Objek Berdasarkan Data yang Dipilih User di Menu
    player1 = new Fighter3D(-4, selectedCharColor, true, null);
    computer = new Fighter3D(4, 0xe74c3c, false, diff);

    // Pembatalan game loop lama jika ada
    if (animationId) cancelAnimationFrame(animationId);
    animate();
}

// Render Berulang Kamera & Fisika Game 3D
function animate() {
    animationId = requestAnimationFrame(animate);

    if (!gameOver) {
        player1.update(computer);
        computer.update(player1);

        // Verifikasi Penentuan Akhir Pertandingan (Tamat)
        if (player1.health <= 0 || computer.health <= 0) {
            gameOver = true;
            setTimeout(() => {
                alert(player1.health <= 0 ? "GAME OVER! Komputer Menang." : "VICTORY! Anda Menang.");
                // Kembalikan ke layar utama setelah selesai duel
                document.getElementById('hud').style.display = 'none';
                document.getElementById('three-canvas-container').style.display = 'none';
                switchScreen('menu-screen');
            }, 500);
        }
    }

    // Kamera mengikuti posisi penyeimbang di antara dua petarung secara dinamis
    camera.position.x = (player1.mesh.position.x + computer.mesh.position.x) / 2;
    renderer.render(scene, camera);
}
</script>

</body>
</html>
"""

# Tampilkan seluruh susunan antarmuka game ke dalam jendela Streamlit Web
components.html(game_code, height=570, scrolling=False)

st.caption("💡 **Tips Navigasi Proyek:** Setelah menekan tombol 'Bertarung!', klik sekali pada layar permainan agar input keyboard Anda dapat terbaca secara optimal.")
