import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit agar bersih dan fokus ke game
st.set_page_config(
    page_title="Stickman Fighting 3D",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Khusus untuk menghilangkan komponen bawaan Streamlit agar pas 100%
st.markdown("""
    <style>
    .block-container { padding: 0.5rem; max-width: 1020px; }
    iframe { border-radius: 12px; box-shadow: 0px 15px 35px rgba(0,0,0,0.8); }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# Kode Game Utama yang Sudah Diperbaiki (Fix Layar Gelap)
game_code = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stickman Fighting 3D</title>
    <style>
        * { box-sizing: border-box; user-select: none; }
        body {
            margin: 0; padding: 0; background-color: #111;
            font-family: 'Impact', 'Arial Black', sans-serif; color: #fff;
            display: flex; justify-content: center; align-items: center; min-height: 100vh;
        }
        #game-container {
            width: 1000px; height: 550px; position: relative;
            background-color: #000; border: 3px solid #deff9a;
            border-radius: 10px; overflow: hidden;
        }
        .screen {
            position: absolute; width: 100%; height: 100%; top: 0; left: 0;
            display: none; flex-direction: column; justify-content: center;
            align-items: center; background: radial-gradient(circle, #222 0%, #050505 100%);
            z-index: 10; padding: 20px;
        }
        .active { display: flex; }

        /* --- MENU UTAMA STYLE --- */
        h1 { font-size: 60px; color: #fff; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 4px; text-shadow: 2px 2px #000; }
        h1 span { color: #deff9a; text-shadow: 0 0 15px rgba(222,255,154,0.6); }
        .subtitle { font-family: Arial; font-size: 14px; color: #888; margin-bottom: 30px; letter-spacing: 2px; text-transform: uppercase; }
        
        .menu-layout { display: flex; width: 80%; justify-content: space-around; align-items: center; }
        .menu-buttons { display: flex; flex-direction: column; gap: 15px; }
        
        .menu-btn {
            width: 260px; padding: 15px; font-size: 18px; font-weight: bold; color: #fff;
            background: #111; border: 2px solid #fff; border-radius: 4px; cursor: pointer;
            transition: all 0.2s ease; text-transform: uppercase; font-family: Arial;
        }
        .menu-btn:hover {
            background: #deff9a; color: #000; border-color: #deff9a;
            box-shadow: 0 0 15px #deff9a; transform: scale(1.05);
        }

        /* --- OPTIONS / DIFFICULTY PANEL --- */
        .panel-box { background: rgba(0,0,0,0.6); padding: 25px; border-radius: 6px; border: 2px solid #333; width: 340px; }
        .panel-title { color: #deff9a; font-size: 20px; margin-bottom: 15px; text-transform: uppercase; text-align: center; }
        .diff-option {
            display: flex; align-items: center; justify-content: space-between;
            padding: 10px; margin: 8px 0; background: #1a1a1a; border: 1px solid #444;
            border-radius: 4px; cursor: pointer; font-family: Arial; font-size: 14px;
        }
        .diff-option:hover { border-color: #deff9a; }
        .diff-option.selected { background: rgba(222,255,154,0.15); border-color: #deff9a; color: #deff9a; font-weight: bold; }
        .radio-dot { width: 14px; height: 14px; border: 2px solid #fff; border-radius: 50%; display: inline-block; }
        .diff-option.selected .radio-dot { background: #deff9a; border-color: #deff9a; }

        /* --- CHARACTER SELECTION GRID --- */
        .selection-layout { display: flex; width: 95%; height: 80%; justify-content: space-between; align-items: center; }
        .preview-box { width: 250px; height: 100%; background: rgba(255,255,255,0.02); border: 2px dashed #444; border-radius: 6px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        .preview-avatar { width: 120px; height: 120px; border-radius: 50%; margin-bottom: 15px; border: 4px solid #fff; }
        
        .grid-container { width: 420px; height: 320px; overflow-y: auto; padding-right: 5px; }
        .char-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
        .char-card {
            aspect-ratio: 1; background: #151515; border: 2px solid #333; border-radius: 6px;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            cursor: pointer; transition: 0.2s; padding: 5px;
        }
        .char-card:hover { border-color: #fff; }
        .char-card.selected { border-color: #deff9a; background: rgba(222,255,154,0.1); }
        .char-circle { width: 45px; height: 45px; border-radius: 50%; margin-bottom: 5px; border: 2px solid #fff; }
        .char-card span { font-size: 11px; font-family: Arial; font-weight: bold; color: #aaa; }
        .char-card.selected span { color: #deff9a; }

        /* --- GAMEPLAY HUD --- */
        #hud {
            position: absolute; top: 0; left: 0; width: 100%; height: 85px;
            display: none; justify-content: space-between; align-items: center; padding: 0 30px; z-index: 5;
            background: linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%);
        }
        .hp-container { width: 360px; height: 22px; background: #551a1a; border: 2px solid #fff; border-radius: 3px; position: relative; }
        .hp-bar { width: 100%; height: 100%; background: #2ecc71; }
        .hud-name { position: absolute; top: -22px; font-family: Arial; font-weight: bold; font-size: 15px; color: #fff; text-shadow: 1px 1px #000; }
        #timer-box { font-size: 34px; color: #deff9a; background: rgba(0,0,0,0.7); padding: 2px 15px; border: 2px solid #333; border-radius: 4px; }
        
        #three-canvas { width: 100%; height: 100%; display: none; }
    </style>
    
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
</head>
<body>

<div id="game-container">
    
    <div id="menu-screen" class="screen active">
        <h1>Stickman <span>Fighting 3D</span></h1>
        <div class="subtitle">Arsitektur UI & Arena Duel Komputer</div>
        
        <div class="menu-layout">
            <div class="menu-buttons">
                <button class="menu-btn" onclick="openSelection('story')">Story Mode</button>
                <button class="menu-btn" onclick="openSelection('1match')">1 Match</button>
                <button class="menu-btn" onclick="openSelection('training')">Training Mode</button>
            </div>
            
            <div class="panel-box">
                <div class="panel-title">Difficulty</div>
                <div class="diff-option" id="opt-easy" onclick="setDifficulty('easy')"><span>EASY</span><span class="radio-dot"></span></div>
                <div class="diff-option selected" id="opt-normal" onclick="setDifficulty('normal')"><span>NORMAL</span><span class="radio-dot"></span></div>
                <div class="diff-option" id="opt-hard" onclick="setDifficulty('hard')"><span>HARD</span><span class="radio-dot"></span></div>
                <div class="diff-option" id="opt-hell" onclick="setDifficulty('hell')"><span>HELL</span><span class="radio-dot"></span></div>
            </div>
        </div>
    </div>

    <div id="char-screen" class="screen">
        <h2 style="font-size:32px; margin:0 0 20px 0; text-transform:uppercase;">Select Character</h2>
        
        <div class="selection-layout">
            <div class="preview-box">
                <div style="font-size:12px; color:#deff9a; margin-bottom:5px;">PLAYER 1</div>
                <div class="preview-avatar" id="p1-avatar" style="background:#3498db;"></div>
                <div id="p1-preview-name" style="font-size:22px; text-align:center;">DEFAULT</div>
            </div>

            <div class="grid-container">
                <div class="char-grid" id="roster-mount">
                    </div>
            </div>

            <div class="preview-box">
                <div style="font-size:12px; color:#e74c3c; margin-bottom:5px;">ENEMY CPU</div>
                <div class="preview-avatar" style="background:#e74c3c;"></div>
                <div id="cpu-preview-name" style="font-size:22px; color:#e74c3c;">VILLAIN</div>
            </div>
        </div>

        <div style="margin-top:20px; display:flex; gap:20px;">
            <button class="menu-btn" style="width:160px; border-color:#e74c3c;" onclick="backToMenu()">BACK</button>
            <button class="menu-btn" style="width:200px; border-color:#deff9a;" onclick="launchBattle()">FIGHT!</button>
        </div>
    </div>

    <div id="hud">
        <div class="hp-container">
            <div class="hud-name" id="hud-p1-name">PLAYER 1</div>
            <div id="p1-bar" class="hp-bar"></div>
        </div>
        <div id="timer-box">99</div>
        <div class="hp-container">
            <div class="hud-name" style="right:0;" id="hud-cpu-name">CPU</div>
            <div id="cpu-bar" class="hp-bar" style="float:right;"></div>
        </div>
    </div>

    <div id="three-canvas"></div>

</div>

<script>
// --- DATA ROSTER STICKMAN (Total 16 Variasi Sesuai Gambar Referensi) ---
const rosterData = [
    { id: 'st-classic', name: 'Stickman', color: '#3498db', desc: 'Classic Blue' },
    { id: 'st-zombie', name: 'Zombie', color: '#2ecc71', desc: 'Undead Green' },
    { id: 'st-cyber', name: 'Cyber', color: '#9b59b6', desc: 'Neon Neon' },
    { id: 'st-soldier', name: 'Soldier', color: '#27ae60', desc: 'Military' },
    { id: 'st-pyro', name: 'Pyro', color: '#e67e22', desc: 'Fire Flame' },
    { id: 'st-frost', name: 'Frost', color: '#a5dff9', desc: 'Ice Frost' },
    { id: 'st-demon', name: 'Demon', color: '#95a5a6', desc: 'Dark Soul' },
    { id: 'st-void', name: 'Void', color: '#111111', desc: 'Shadow' },
    { id: 'st-orange', name: 'Orange', color: '#f39c12', desc: 'Burst' },
    { id: 'st-pink', name: 'Pinky', color: '#f1c40f', desc: 'Sparkle' },
    { id: 'st-vip', name: 'Gentleman', color: '#34495e', desc: 'Top Hat' },
    { id: 'st-anon', name: 'Anon', color: '#ffffff', desc: 'Masked' },
    { id: 'st-rainbow', name: 'Rainbow', color: '#e74c3c', desc: 'Spectrum' },
    { id: 'st-ninja', name: 'Shadow', color: '#2c3e50', desc: 'Assassin' },
    { id: 'st-titan', name: 'Titan', color: '#d35400', desc: 'Colossus' },
    { id: 'st-bot', name: 'Mecha', color: '#bdc3c7', desc: 'Android' }
];

let selectedDifficulty = 'normal';
let selectedP1Index = 0;
let selectedGameMode = '1match';

// Render Grid Pilihan Karakter secara Otomatis saat Halaman Dimuat
const rosterMount = document.getElementById('roster-mount');
rosterData.forEach((char, index) => {
    const card = document.createElement('div');
    card.className = `char-card ${index === 0 ? 'selected' : ''}`;
    card.id = `card-${index}`;
    card.onclick = () => selectCharIndex(index);
    
    card.innerHTML = `
        <div class="char-circle" style="background:${char.color}"></div>
        <span>${char.name}</span>
    `;
    rosterMount.appendChild(card);
});

// Update Data Pilihan Tingkat Kesulitan
function setDifficulty(level) {
    document.querySelectorAll('.diff-option').forEach(opt => opt.classList.remove('selected'));
    document.getElementById(`opt-${level}`).classList.add('selected');
    selectedDifficulty = level;
}

// Ganti Karakter Terpilih
function selectCharIndex(idx) {
    document.querySelectorAll('.char-card').forEach(c => c.classList.remove('selected'));
    document.getElementById(`card-${idx}`).classList.add('selected');
    
    selectedP1Index = idx;
    // Update Tampilan Kotak Preview Kiri
    document.getElementById('p1-avatar').style.background = rosterData[idx].color;
    document.getElementById('p1-preview-name').innerText = rosterData[idx].name;
}

// Navigasi Antar Layar Menu
function openSelection(mode) {
    selectedGameMode = mode;
    document.getElementById('menu-screen').style.display = 'none';
    document.getElementById('char-screen').style.display = 'flex';
    selectCharIndex(selectedP1Index); // Triger info awal
}

function backToMenu() {
    document.getElementById('char-screen').style.display = 'none';
    document.getElementById('menu-screen').style.display = 'flex';
}

// --- LOGIKA UTAMA 3D ENGINE (THREE.JS) ---
let scene, camera, renderer, p1Model, cpuModel, animationId, isBattleOver = false;
const inputKeys = {};

window.addEventListener("keydown", e => { inputKeys[e.key.toLowerCase()] = true; });
window.addEventListener("keyup", e => { inputKeys[e.key.toLowerCase()] = false; });

function buildStickmanMesh(colorHex) {
    // Membuat grup objek utama stickman
    const group = new THREE.Group();
    const material = new THREE.MeshStandardMaterial({ color: colorHex, roughness: 0.4 });
    const jointMat = new THREE.MeshStandardMaterial({ color: 0xffffff });

    // Kepala (Bola Bulat Stickman)
    const headGeo = new THREE.SphereGeometry(0.35, 32, 32);
    const head = new THREE.Mesh(headGeo, material);
    head.position.y = 2.4;
    group.add(head);

    // Tulang Badan Utama (Silinder/Tabung Panjang)
    const spineGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.2, 16);
    const spine = new THREE.Mesh(spineGeo, material);
    spine.position.y = 1.4;
    group.add(spine);

    // Lengan Tangan Kiri & Kanan
    const armGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.9, 16);
    
    const leftArm = new THREE.Mesh(armGeo, material);
    leftArm.position.set(-0.35, 1.5, 0.2);
    leftArm.rotation.z = Math.PI / 4;
    group.add(leftArm);

    // Lengan Serang Kanan (Bisa memanjang saat menekan tombol F)
    const rightArmGroup = new THREE.Group();
    rightArmGroup.position.set(0.35, 1.6, 0);
    
    const rightArm = new THREE.Mesh(armGeo, material);
    rightArm.position.y = -0.4;
    rightArm.name = "forearm";
    rightArmGroup.add(rightArm);
    group.add(rightArmGroup);

    // Kaki Kiri & Kanan
    const legGeo = new THREE.CylinderGeometry(0.07, 0.07, 1.0, 16);
    const leftLeg = new THREE.Mesh(legGeo, material);
    leftLeg.position.set(-0.25, 0.5, 0);
    leftLeg.rotation.z = 0.1;
    group.add(leftLeg);

    const rightLeg = new THREE.Mesh(legGeo, material);
    rightLeg.position.set(0.25, 0.5, 0);
    rightLeg.rotation.z = -0.1;
    group.add(rightLeg);

    // Beri kemampuan memancarkan bayangan di arena pertarungan
    group.traverse(child => {
        if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
        }
    });

    return { group, rightArmGroup };
}

function launchBattle() {
    // Pastikan library Three.js sudah siap di dalam jendela browser
    if (typeof THREE === 'undefined') {
        alert("Sistem 3D WebGL sedang memuat komponen, harap tunggu 3 detik dan klik FIGHT lagi!");
        return;
    }

    // Ganti Tampilan Layar dari Menu ke Arena 3D
    document.getElementById('char-screen').style.display = 'none';
    document.getElementById('hud').style.display = 'flex';
    document.getElementById('three-canvas').style.display = 'block';

    // Ambil Informasi Karakter Pilihan User
    const player1Data = rosterData[selectedP1Index];
    // Pilih acak musuh dari roster untuk variasi bertanding
    const cpuData = rosterData[(selectedP1Index + 3) % rosterData.length];

    document.getElementById('hud-p1-name').innerText = player1Data.name;
    document.getElementById('hud-cpu-name').innerText = `${cpuData.name} (${selectedDifficulty.toUpperCase()})`;

    // Reset status HP bar game
    isBattleOver = false;
    document.getElementById('p1-bar').style.width = '100%';
    document.getElementById('cpu-bar').style.width = '100%';

    // --- SETUP DUNIA THREE.JS ---
    const container = document.getElementById('three-canvas');
    container.innerHTML = ''; // bersihkan render lama

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x14191f);

    camera = new THREE.PerspectiveCamera(45, 1000 / 550, 0.1, 1000);
    camera.position.set(0, 3.5, 13);
    camera.lookAt(0, 1.8, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(1000, 550);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Pencahayaan Efek Panggung Neon 3D
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const spotLight = new THREE.SpotLight(0xdeff9a, 1.2);
    spotLight.position.set(0, 15, 5);
    spotLight.castShadow = true;
    scene.add(spotLight);

    // Lantai Grid Arena 3D
    const floorGeo = new THREE.BoxGeometry(26, 0.4, 6);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x1e272e, roughness: 0.7 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.position.y = -0.2;
    floor.receiveShadow = true;
    scene.add(floor);

    const gridHelper = new THREE.GridHelper(26, 26, 0xdeff9a, 0x444444);
    gridHelper.position.y = 0.01;
    scene.add(gridHelper);

    // Struktur Kontrol Logika Karakter Petarung Stickman
    class FighterController {
        constructor(startX, colorHex, isPlayer) {
            this.isPlayer = isPlayer;
            this.health = 100;
            this.speed = 0.13;
            this.velY = 0;
            this.isJumping = false;
            this.attackCooldown = 0;
            this.isPunching = false;
            this.facingRight = isPlayer;

            const assets = buildStickmanMesh(colorHex);
            this.mesh = assets.group;
            this.armJoint = assets.rightArmGroup;
            
            this.mesh.position.set(startX, 0, 0);
            scene.add(this.mesh);
        }

        update(opponent) {
            // Pengaturan Rotasi Sumbu Arah Hadap Otomatis Menghadap Musuh
            if (this.mesh.position.x < opponent.mesh.position.x) {
                this.mesh.rotation.y = Math.PI / 2;
                this.facingRight = true;
            } else {
                this.mesh.rotation.y = -Math.PI / 2;
                this.facingRight = false;
            }

            if (this.isPlayer) {
                // Input Deteksi Keyboard Player 1
                if (inputKeys['a']) this.mesh.position.x -= this.speed;
                if (inputKeys['d']) this.mesh.position.x += this.speed;
                if (inputKeys['w'] && !this.isJumping) { this.velY = 0.22; this.isJumping = true; }
                if (inputKeys['f'] && this.attackCooldown === 0) { this.isPunching = true; this.attackCooldown = 20; }
            } else {
                // Logika Pergerakan AI Komputer Otomatis (CPU)
                let distance = Math.abs(this.mesh.position.x - opponent.mesh.position.x);
                let cpuSpeed = this.speed * 0.75;
                let attackThreshold = 0.04;

                // Modifikasi Algoritma Agresivitas Berdasarkan Opsi Kesulitan
                if (selectedDifficulty === 'hard') { cpuSpeed = this.speed * 0.95; attackThreshold = 0.09; }
                if (selectedDifficulty === 'hell') { cpuSpeed = this.speed * 1.3; attackThreshold = 0.22; }

                if (!this.isPunching && !isBattleOver) {
                    if (this.mesh.position.x > opponent.mesh.position.x + 1.4) {
                        this.mesh.position.x -= cpuSpeed;
                    } else if (this.mesh.position.x < opponent.mesh.position.x - 1.4) {
                        this.mesh.position.x += cpuSpeed;
                    }

                    if (distance < 1.8 && this.attackCooldown === 0 && Math.random() < attackThreshold) {
                        this.isPunching = true;
                        this.attackCooldown = 25;
                    }
                }
            }

            // Animasi Pukulan Lengan Menembak Maju ke Depan
            if (this.isPunching) {
                this.armJoint.rotation.x = -Math.PI / 2; // Angkat tangan lurus ke depan
                this.armJoint.scale.set(1, 2.0, 1);     // Panjangkan struktur silinder lengan

                // Deteksi Tabrakan Hitbox Serangan
                let targetDist = Math.abs(this.mesh.position.x - opponent.mesh.position.x);
                if (targetDist < 2.0 && Math.abs(this.mesh.position.y - opponent.mesh.position.y) < 1.2) {
                    opponent.health -= 7;
                    if (opponent.health < 0) opponent.health = 0;
                    
                    // Update Tampilan UI Bar Darah Hijau di Browser
                    if (opponent.isPlayer) {
                        document.getElementById('p1-bar').style.width = opponent.health + '%';
                    } else {
                        document.getElementById('cpu-bar').style.width = opponent.health + '%';
                    }
                }
                this.isPunching = false;
            } else {
                // Kembalikan posisi lengan secara perlahan ke mode normal siap sedia
                if (this.attackCooldown < 10) {
                    this.armJoint.rotation.x = 0;
                    this.armJoint.scale.set(1, 1, 1);
                }
            }

            // Simulasi Fisika Jatuh Gravitasi Bumi
            if (this.isJumping) {
                this.velY -= 0.012;
                this.mesh.position.y += this.velY;
                if (this.mesh.position.y <= 0) {
                    this.mesh.position.y = 0;
                    this.isJumping = false;
                    this.velY = 0;
                }
            }

            // Batas Pinggir Garis Panggung Arena Match
            if (this.mesh.position.x < -12) this.mesh.position.x = -12;
            if (this.mesh.position.x > 12) this.mesh.position.x = 12;

            if (this.attackCooldown > 0) this.attackCooldown--;
        }
    }

    p1Model = new FighterController(-4, player1Data.color, true);
    cpuModel = new FighterController(4, cpuData.color, false);

    if (animationId) cancelAnimationFrame(animationId);
    battleLoop();
}

function battleLoop() {
    animationId = requestAnimationFrame(battleLoop);

    if (!isBattleOver) {
        p1Model.update(cpuModel);
        cpuModel.update(p1Model);

        // Validasi Pemenang Pertandingan Duel Ronde Selesai
        if (p1Model.health <= 0 || cpuModel.health <= 0) {
            isBattleOver = true;
            setTimeout(() => {
                alert(p1Model.health <= 0 ? "🏆 GAME OVER! CPU Menang Duel." : "🏆 VICTORY! Anda Menang Duel.");
                
                // Bersihkan Arena 3D dan Balikkan User ke Menu Utama Depan
                document.getElementById('hud').style.display = 'none';
                document.getElementById('three-canvas').style.display = 'none';
                document.getElementById('menu-screen').style.display = 'flex';
            }, 300);
        }
    }

    // Kamera Mengikuti Titik Tengah Koordinat Antara 2 Stickman (Kamera Sinematik)
    camera.position.x = (p1Model.mesh.position.x + cpuModel.mesh.position.x) / 2;
    renderer.render(scene, camera);
}
</script>

</body>
</html>
"""

# Tampilkan seluruh susunan antarmuka game ke dalam jendela Streamlit Web
components.html(game_code, height=570, scrolling=False)

st.info("💡 **Petunjuk Bermain:** Setelah menekan tombol **FIGHT!**, silakan klik kiri satu kali pada area panggung pertarungan hitam agar browser Anda fokus menerima input tombol **A, D, W, F**.")
