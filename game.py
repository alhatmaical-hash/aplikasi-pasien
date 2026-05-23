import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit agar bersih dan fokus ke game
st.set_page_config(
    page_title="Stickman Fighting 3D - Advanced Combat",
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

# Kode Game Utama dengan Fitur: Tendangan, Bantingan, dan Fatality
game_code = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stickman Fighting 3D - Advanced Combat</title>
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
        
        /* OVERLAY TEXT UNTUK FATALITY / FINISH HIM */
        #announcer-text {
            position: absolute; width: 100%; text-align: center; top: 35%;
            font-size: 75px; color: #e74c3c; font-weight: bold; display: none;
            text-transform: uppercase; letter-spacing: 5px; z-index: 6;
            text-shadow: 0 0 20px rgba(231,76,60,0.8), 4px 4px #000;
        }

        #three-canvas { width: 100%; height: 100%; display: none; }
    </style>
    
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
</head>
<body>

<div id="game-container">
    
    <div id="announcer-text">FINISH HIM!</div>

    <div id="menu-screen" class="screen active">
        <h1>Stickman <span>Fighting 3D</span></h1>
        <div class="subtitle">Update: Tendangan, Bantingan & Fatality System</div>
        
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
// --- DATA ROSTER STICKMAN ---
const rosterData = [
    { id: 'st-classic', name: 'Stickman', color: '#3498db' },
    { id: 'st-zombie', name: 'Zombie', color: '#2ecc71' },
    { id: 'st-cyber', name: 'Cyber', color: '#9b59b6' },
    { id: 'st-soldier', name: 'Soldier', color: '#27ae60' },
    { id: 'st-pyro', name: 'Pyro', color: '#e67e22' },
    { id: 'st-frost', name: 'Frost', color: '#a5dff9' },
    { id: 'st-demon', name: 'Demon', color: '#7f8c8d' },
    { id: 'st-void', name: 'Void', color: '#2c3e50' },
    { id: 'st-orange', name: 'Orange', color: '#f39c12' },
    { id: 'st-pink', name: 'Pinky', color: '#ff7675' },
    { id: 'st-vip', name: 'Gentleman', color: '#dfe6e9' },
    { id: 'st-anon', name: 'Anon', color: '#ffffff' },
    { id: 'st-rainbow', name: 'Rainbow', color: '#fdcb6e' },
    { id: 'st-ninja', name: 'Shadow', color: '#2d3436' },
    { id: 'st-titan', name: 'Titan', color: '#e17055' },
    { id: 'st-bot', name: 'Mecha', color: '#ffeaa7' }
];

let selectedDifficulty = 'normal';
let selectedP1Index = 0;
let selectedGameMode = '1match';

const rosterMount = document.getElementById('roster-mount');
rosterData.forEach((char, index) => {
    const card = document.createElement('div');
    card.className = `char-card ${index === 0 ? 'selected' : ''}`;
    card.id = `card-${index}`;
    card.onclick = () => selectCharIndex(index);
    card.innerHTML = `<div class="char-circle" style="background:${char.color}"></div><span>${char.name}</span>`;
    rosterMount.appendChild(card);
});

function setDifficulty(level) {
    document.querySelectorAll('.diff-option').forEach(opt => opt.classList.remove('selected'));
    document.getElementById(`opt-${level}`).classList.add('selected');
    selectedDifficulty = level;
}

function selectCharIndex(idx) {
    document.querySelectorAll('.char-card').forEach(c => c.classList.remove('selected'));
    document.getElementById(`card-${idx}`).classList.add('selected');
    selectedP1Index = idx;
    document.getElementById('p1-avatar').style.background = rosterData[idx].color;
    document.getElementById('p1-preview-name').innerText = rosterData[idx].name;
}

function openSelection(mode) {
    selectedGameMode = mode;
    document.getElementById('menu-screen').style.display = 'none';
    document.getElementById('char-screen').style.display = 'flex';
    selectCharIndex(selectedP1Index);
}

function backToMenu() {
    document.getElementById('char-screen').style.display = 'none';
    document.getElementById('menu-screen').style.display = 'flex';
}

// --- ENGINE 3D COMBAT SYSTEM ---
let scene, camera, renderer, p1Model, cpuModel, animationId;
let fatalityState = false; // Menandai fase "Finish Him" aktif
let matchEnded = false;
const inputKeys = {};

window.addEventListener("keydown", e => { inputKeys[e.key.toLowerCase()] = true; });
window.addEventListener("keyup", e => { inputKeys[e.key.toLowerCase()] = false; });

function buildStickmanMesh(colorHex) {
    const group = new THREE.Group();
    const material = new THREE.MeshStandardMaterial({ color: colorHex, roughness: 0.3 });

    // Kepala (Bisa copot/hancur saat Fatality!)
    const headGeo = new THREE.SphereGeometry(0.35, 32, 32);
    const head = new THREE.Mesh(headGeo, material);
    head.position.y = 2.4;
    head.name = "head";
    group.add(head);

    // Badan
    const spineGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.2, 16);
    const spine = new THREE.Mesh(spineGeo, material);
    spine.position.y = 1.4;
    group.add(spine);

    // Tangan Kiri
    const armGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.9, 16);
    const leftArm = new THREE.Mesh(armGeo, material);
    leftArm.position.set(-0.35, 1.5, 0.2);
    leftArm.rotation.z = Math.PI / 4;
    group.add(leftArm);

    // Tangan Kanan Serang (Pukulan / Fatality)
    const rightArmGroup = new THREE.Group();
    rightArmGroup.position.set(0.35, 1.6, 0);
    const rightArm = new THREE.Mesh(armGeo, material);
    rightArm.position.y = -0.4;
    rightArmGroup.add(rightArm);
    rightArmGroup.name = "rightArm";
    group.add(rightArmGroup);

    // Kaki Kiri
    const legGeo = new THREE.CylinderGeometry(0.06, 0.06, 1.0, 16);
    const leftLeg = new THREE.Mesh(legGeo, material);
    leftLeg.position.set(-0.25, 0.5, 0);
    group.add(leftLeg);

    // Kaki Kanan Serang (Tendangan)
    const rightLegGroup = new THREE.Group();
    rightLegGroup.position.set(0.25, 1.0, 0);
    const rightLeg = new THREE.Mesh(legGeo, material);
    rightLeg.position.y = -0.5;
    rightLegGroup.add(rightLeg);
    rightLegGroup.name = "rightLeg";
    group.add(rightLegGroup);

    group.traverse(child => { if (child.isMesh) child.castShadow = true; });
    return { group, rightArmGroup, rightLegGroup, headMesh: head };
}

function launchBattle() {
    document.getElementById('char-screen').style.display = 'none';
    document.getElementById('hud').style.display = 'flex';
    document.getElementById('three-canvas').style.display = 'block';
    document.getElementById('announcer-text').style.display = 'none';

    const player1Data = rosterData[selectedP1Index];
    const cpuData = rosterData[(selectedP1Index + 4) % rosterData.length];

    document.getElementById('hud-p1-name').innerText = player1Data.name;
    document.getElementById('hud-cpu-name').innerText = `${cpuData.name} (${selectedDifficulty.toUpperCase()})`;

    fatalityState = false;
    matchEnded = false;
    document.getElementById('p1-bar').style.width = '100%';
    document.getElementById('cpu-bar').style.width = '100%';

    // SETUP THREE.JS
    const container = document.getElementById('three-canvas');
    container.innerHTML = '';

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x11141c);

    camera = new THREE.PerspectiveCamera(45, 1000 / 550, 0.1, 1000);
    camera.position.set(0, 3.5, 13);
    camera.lookAt(0, 1.8, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(1000, 550);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Cahaya Arena
    scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    const light = new THREE.SpotLight(0xffffff, 1.3);
    light.position.set(0, 15, 3);
    light.castShadow = true;
    scene.add(light);

    // Lantai Grid
    const floor = new THREE.Mesh(new THREE.BoxGeometry(26, 0.4, 6), new THREE.MeshStandardMaterial({ color: 0x1e272e }));
    floor.position.y = -0.2;
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(26, 26, 0xe74c3c, 0x333333);
    grid.position.y = 0.01;
    scene.add(grid);

    // FIGHTER CONTROLLER LOGIC ENGINE
    class FighterController {
        constructor(startX, colorHex, isPlayer) {
            this.isPlayer = isPlayer;
            this.health = 100;
            this.speed = 0.13;
            this.velY = 0;
            this.isJumping = false;
            this.attackCooldown = 0;
            
            // State Aksi Tempur
            this.combatAction = 'idle'; // 'punch', 'kick', 'throw', 'fatality', 'dizzy', 'airborne'
            this.actionTimer = 0;

            const assets = buildStickmanMesh(colorHex);
            this.mesh = assets.group;
            this.arm = assets.rightArmGroup;
            this.leg = assets.rightLegGroup;
            this.head = assets.headMesh;
            
            this.mesh.position.set(startX, 0, 0);
            scene.add(this.mesh);
        }

        update(opponent) {
            // Logika Arah Hadap Otomatis (Kecuali saat dibanting/airborne)
            if (this.combatAction !== 'airborne') {
                if (this.mesh.position.x < opponent.mesh.position.x) {
                    this.mesh.rotation.y = Math.PI / 2;
                } else {
                    this.mesh.rotation.y = -Math.PI / 2;
                }
            }

            // PENGURANGAN TIMER AKSI ANIMASI
            if (this.actionTimer > 0) {
                this.actionTimer--;
                this.animateAction();
                return; 
            } else if (this.combatAction !== 'idle' && this.combatAction !== 'dizzy') {
                this.resetSkeleton();
            }

            // JIKA MUSUH DIKANDANGI STATUS DIZZY (MENUNGGU FATALITY)
            if (this.combatAction === 'dizzy') {
                this.mesh.rotation.z = Math.sin(Date.now() * 0.01) * 0.15; // Goyang sempoyongan
                return;
            }

            let distance = Math.abs(this.mesh.position.x - opponent.mesh.position.x);

            // INPUT KONTROL KEYBOARD PLAYER
            if (this.isPlayer && !matchEnded) {
                if (inputKeys['a']) this.mesh.position.x -= this.speed;
                if (inputKeys['d']) this.mesh.position.x += this.speed;
                if (inputKeys['w'] && !this.isJumping) { this.velY = 0.22; this.isJumping = true; }
                
                // [FITUR 1]: Pukulan Biasa (F)
                if (inputKeys['f'] && this.attackCooldown === 0) {
                    this.executeAttack('punch', 15, 6, 1.8, opponent);
                }
                // [FITUR 2]: Tendangan Kaki Maut (G)
                if (inputKeys['g'] && this.attackCooldown === 0) {
                    this.executeAttack('kick', 20, 12, 2.0, opponent);
                }
                // [FITUR 3]: Bantingan Judo Jarak Dekat (E)
                if (inputKeys['e'] && this.attackCooldown === 0) {
                    if (distance < 1.4) {
                        this.executeAttack('throw', 40, 20, 1.5, opponent);
                    }
                }
                // [FITUR 4]: TOMBOL EKSEKUSI FATALITY (R)
                if (inputKeys['r'] && fatalityState && distance < 1.8) {
                    this.executeAttack('fatality', 60, 100, 2.0, opponent);
                }
            } else if (!this.isPlayer && !matchEnded && !fatalityState) {
                // LOGIKA AI KOMPUTER OTOMATIS
                let cpuMove = this.speed * 0.75;
                if (selectedDifficulty === 'hard') cpuMove = this.speed * 1.0;
                if (selectedDifficulty === 'hell') cpuMove = this.speed * 1.3;

                if (this.mesh.position.x > opponent.mesh.position.x + 1.5) this.mesh.position.x -= cpuMove;
                else if (this.mesh.position.x < opponent.mesh.position.x - 1.5) this.mesh.position.x += cpuMove;

                // AI Memilih Acak Pukulan, Tendangan, atau Bantingan
                if (distance < 1.9 && this.attackCooldown === 0 && Math.random() < 0.06) {
                    let rand = Math.random();
                    if (rand < 0.5) this.executeAttack('punch', 15, 6, 1.8, opponent);
                    else if (rand < 0.85) this.executeAttack('kick', 20, 10, 2.0, opponent);
                    else if (distance < 1.3) this.executeAttack('throw', 40, 18, 1.4, opponent);
                }
            }

            // SIMULASI GRAVITASI LOMPATAN
            if (this.isJumping) {
                this.velY -= 0.012;
                this.mesh.position.y += this.velY;
                if (this.mesh.position.y <= 0) {
                    this.mesh.position.y = 0;
                    this.isJumping = false;
                    this.velY = 0;
                }
            }

            if (this.mesh.position.x < -12) this.mesh.position.x = -12;
            if (this.mesh.position.x > 12) this.mesh.position.x = 12;
            if (this.attackCooldown > 0) this.attackCooldown--;
        }

        executeAttack(type, duration, damage, range, opponent) {
            this.combatAction = type;
            this.actionTimer = duration;
            this.attackCooldown = duration + 15;

            let currentDist = Math.abs(this.mesh.position.x - opponent.mesh.position.x);
            
            if (currentDist <= range && Math.abs(this.mesh.position.y - opponent.mesh.position.y) < 1.5) {
                // Konsekuensi jika serangan mendarat telak
                if (type === 'throw') {
                    // Memicu musuh masuk kondisi terlempar ke udara (Bantingan)
                    opponent.combatAction = 'airborne';
                    opponent.actionTimer = 40;
                    opponent.velY = 0.25;
                }
                
                if (type === 'fatality') {
                    opponent.combatAction = 'headless';
                    opponent.actionTimer = 999; 
                    opponent.head.visible = false; // Kepala musuh hilang tertebas!
                    matchEnded = true;
                    triggerFinalVictory("FATALITY! PLAYER 1 WIN");
                    return;
                }

                opponent.health -= damage;
                if (opponent.health < 0) opponent.health = 0;

                // Sync Bar Darah
                if (opponent.isPlayer) document.getElementById('p1-bar').style.width = opponent.health + '%';
                else document.getElementById('cpu-bar').style.width = opponent.health + '%';

                // CEK APAKAH FATALITY SENGGOLAN SUDAH BISA DIMULAI
                if (opponent.health <= 0 && !fatalityState) {
                    fatalityState = true;
                    opponent.combatAction = 'dizzy';
                    document.getElementById('announcer-text').style.display = 'block';
                    // Beri waktu 8 detik bagi player untuk menekan tombol R (Fatality)
                    setTimeout(() => {
                        if (!matchEnded) {
                            matchEnded = true;
                            triggerFinalVictory(opponent.isPlayer ? "CPU WIN" : "PLAYER 1 WIN");
                        }
                    }, 8000);
                }
            }
        }

        animateAction() {
            // MENGGERAKKAN TULANG 3D BERDASARKAN COMBAT ACTION ACTIVE
            if (this.combatAction === 'punch') {
                this.arm.rotation.x = -Math.PI / 2;
                this.arm.scale.set(1, 1.8, 1);
            } 
            else if (this.combatAction === 'kick') {
                this.leg.rotation.x = -Math.PI / 2.3; // Angkat kaki memutar kedepan
                this.leg.scale.set(1, 1.5, 1);
            } 
            else if (this.combatAction === 'throw') {
                this.arm.rotation.x = -Math.PI / 1.5;
                this.mesh.position.x += this.facingRight ? 0.05 : -0.05;
            }
            else if (this.combatAction === 'fatality') {
                this.arm.rotation.x = -Math.PI / 2;
                this.arm.scale.set(1, 2.5, 1); // Pukulan pemungkas super panjang
                this.mesh.position.y = 0.5;
            }
            else if (this.combatAction === 'airborne') {
                // Animasi berputar di udara akibat dibanting
                this.mesh.rotation.z += 0.3;
                this.velY -= 0.012;
                this.mesh.position.y += this.velY;
                this.mesh.position.x += this.mesh.position.x > 0 ? -0.08 : 0.08;
                if (this.mesh.position.y <= 0) {
                    this.mesh.position.y = 0;
                    this.velY = 0;
                }
            }
        }

        resetSkeleton() {
            this.combatAction = 'idle';
            this.arm.rotation.set(0, 0, 0);
            this.arm.scale.set(1, 1, 1);
            this.leg.rotation.set(0, 0, 0);
            this.leg.scale.set(1, 1, 1);
            this.mesh.rotation.z = 0;
        }
    }

    p1Model = new FighterController(-4, player1Data.color, true);
    cpuModel = new FighterController(4, cpuData.color, false);

    if (animationId) cancelAnimationFrame(animationId);
    battleLoop();
}

function triggerFinalVictory(winnerText) {
    document.getElementById('announcer-text').innerText = winnerText;
    document.getElementById('announcer-text').style.display = 'block';
    setTimeout(() => {
        document.getElementById('hud').style.display = 'none';
        document.getElementById('three-canvas').style.display = 'none';
        document.getElementById('announcer-text').style.display = 'none';
        document.getElementById('menu-screen').style.display = 'flex';
    }, 4000);
}

function battleLoop() {
    animationId = requestAnimationFrame(battleLoop);
    p1Model.update(cpuModel);
    cpuModel.update(p1Model);
    camera.position.x = (p1Model.mesh.position.x + cpuModel.mesh.position.x) / 2;
    renderer.render(scene, camera);
}
</script>

</body>
</html>
"""

# Tampilkan game ke Streamlit Web
components.html(game_code, height=570, scrolling=False)

st.info("""
🥋 **Daftar Kombo Tombol Baru (Klik layar game 1x agar aktif):**
* **Tombol A / D:** Bergerak Kiri & Kanan
* **Tombol W:** Melompat ke Udara
* **Tombol F:** Pukulan Tangan (Damage kecil)
* **Tombol G:** **Tendangan Memutar (Damage Besar!)**
* **Tombol E:** **Bantingan Judo** (Hanya bekerja saat tubuh Anda menempel intim dengan CPU, musuh akan berputar salto dan terhempas ke lantai).
* **Tombol R:** **Ekssekusi FATALITY!** (Tombol ini terkunci, baru bisa ditekan jika darah CPU sudah habis 0%, layar memancarkan teks merah **FINISH HIM!**, dan Anda berdiri dekat di depannya!).
""")
