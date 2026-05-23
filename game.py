import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit agar responsif dan bersih
st.set_page_config(
    page_title="3D Brawler Arena - Streamlit",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🥋 3D Pixel Brawler Arena")
st.subheader("Prototipe Game Fighting dengan Grafis 3D Real-Time!")

# Kode HTML5 + Three.js (WebGL Engine untuk performa grafis 3D 60 FPS)
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body {
            margin: 0;
            background-color: #1a1a1a;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        #canvas-container {
            width: 1000px;
            height: 500px;
            border: 3px solid #ffffff;
            border-radius: 8px;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.7);
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

<div id="canvas-container"></div>

<script>
// --- 1. SETUP ENGINE 3D (THREE.JS) ---
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1e272e);

// Kamera Perspektif 3D
const camera = new THREE.PerspectiveCamera(45, 1000 / 500, 0.1, 1000);
camera.position.set(0, 4, 16); // Posisi kamera melihat dari depan agak atas
camera.lookAt(0, 2, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(1000, 500);
renderer.shadowMap.enabled = true; // Mengaktifkan efek bayangan nyata
container.appendChild(renderer.domElement);

// --- 2. PENCAHAYAAN (LIGHTING) ---
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(5, 15, 5);
dirLight.castShadow = true;
scene.add(dirLight);

// --- 3. ARENA & LANTAI 3D ---
const floorGeo = new THREE.BoxGeometry(30, 0.5, 10);
const floorMat = new THREE.MeshStandardMaterial({ color: 0x2c3e50, roughness: 0.8 });
const floor = new THREE.Mesh(floorGeo, floorMat);
floor.position.y = -0.25;
floor.receiveShadow = true;
scene.add(floor);

// --- 4. SISTEM INPUT KEYBOARD ---
const keys = {};
window.addEventListener("keydown", e => { keys[e.key.toLowerCase()] = true; });
window.addEventListener("keyup", e => { keys[e.key.toLowerCase()] = false; });

// --- 5. KELAS KARAKTER 3D (MANEKIN PETARUNG) ---
class Fighter3D {
    constructor(startX, colorHex, isPlayer, name) {
        this.isPlayer = isPlayer;
        this.name = name;
        this.health = 100;
        this.speed = 0.15;
        this.velY = 0;
        this.isJumping = false;
        this.isAttacking = false;
        this.attackCooldown = 0;
        this.facingRight = isPlayer;

        // Group Utama untuk menampung bagian tubuh karakter
        this.mesh = new THREE.Group();
        this.mesh.position.set(startX, 0, 0);

        // Bagian Tubuh 1: Badan (Kotak 3D)
        const bodyGeo = new THREE.BoxGeometry(1, 1.8, 0.8);
        const bodyMat = new THREE.MeshStandardMaterial({ color: colorHex, roughness: 0.5 });
        this.body = new THREE.Mesh(bodyGeo, bodyMat);
        this.body.position.y = 1.4;
        this.body.castShadow = true;
        this.mesh.add(this.body);

        // Bagian Tubuh 2: Kepala (Bola 3D)
        const headGeo = new THREE.SphereGeometry(0.4, 16, 16);
        const headMat = new THREE.MeshStandardMaterial({ color: 0xffdbac }); // Warna kulit dasar
        this.head = new THREE.Mesh(headGeo, headMat);
        this.head.position.y = 2.6;
        this.head.castShadow = true;
        this.mesh.add(this.head);

        // Bagian Tubuh 3: Tangan untuk Memukul
        const armGeo = new THREE.BoxGeometry(0.3, 0.3, 1.2);
        this.arm = new THREE.Mesh(armGeo, bodyMat);
        this.arm.position.set(0.4, 1.6, 0.5); // Posisi default tangan di samping depan
        this.arm.castShadow = true;
        this.mesh.add(this.arm);

        scene.add(this.mesh);
    }

    update(target) {
        const GRAVITY = 0.01;

        // Logika Arah Hadap (Rotasi Model 3D ke arah musuh)
        if (this.mesh.position.x < target.mesh.position.x) {
            this.mesh.rotation.y = Math.PI / 2; // Hadap Kanan
            this.facingRight = true;
        } else {
            this.mesh.rotation.y = -Math.PI / 2; // Hadap Kiri
            this.facingRight = false;
        }

        // --- KONTROL GERAKAN ---
        if (this.isPlayer) {
            // Pergerakan Player 1
            if (keys['a']) this.mesh.position.x -= this.speed;
            if (keys['d']) this.mesh.position.x += this.speed;
            
            // Lompat P1
            if (keys['w'] && !this.isJumping) {
                this.velY = 0.25;
                this.isJumping = true;
            }

            // Serangan P1 (Tombol F)
            if (keys['f'] && this.attackCooldown === 0) {
                this.isAttacking = true;
                this.attackCooldown = 25;
            }
        } else {
            // PERGERAKAN AI (KOMPUTER)
            if (!this.isAttacking && !gameOver) {
                // AI Mengejar Posisi Pemain
                if (this.mesh.position.x > target.mesh.position.x + 1.8) {
                    this.mesh.position.x -= this.speed * 0.8;
                } else if (this.mesh.position.x < target.mesh.position.x - 1.8) {
                    this.mesh.position.x += this.speed * 0.8;
                }

                // AI Menyerang secara acak jika jarak dekat
                let dist = Math.abs(this.mesh.position.x - target.mesh.position.x);
                if (dist < 2.2 && this.attackCooldown === 0 && Math.random() < 0.07) {
                    this.isAttacking = true;
                    this.attackCooldown = 30;
                }
            }
        }

        // --- ANIMASI & LOGIKA SERANGAN (PUKULAN 3D) ---
        if (this.isAttacking) {
            // Menggerakkan lengan 3D maju ke depan (memanjang)
            this.arm.position.z = 1.8;
            this.arm.scale.set(1, 1, 2);

            // Hitung Jarak Jangkauan Pukulan (Deteksi Hitbox 3D)
            let distance = Math.abs(this.mesh.position.x - target.mesh.position.x);
            if (distance < 2.3 && Math.abs(this.mesh.position.y - target.mesh.position.y) < 1.5) {
                target.health -= 10;
                if (target.health < 0) target.health = 0;
            }
            this.isAttacking = false;
        } else {
            // Mengembalikan posisi lengan ke semula secara bertahap jika tidak memukul
            if (this.attackCooldown < 15) {
                this.arm.position.z = 0.5;
                this.arm.scale.set(1, 1, 1);
            }
        }

        // --- FISIKA GRAVITASI 3D ---
        if (this.isJumping) {
            this.velY -= GRAVITY;
            this.mesh.position.y += this.velY;

            // Deteksi menyentuh lantai
            if (this.mesh.position.y <= 0) {
                this.mesh.position.y = 0;
                this.isJumping = false;
                this.velY = 0;
            }
        }

        // Pembatas Pinggir Arena 3D
        if (this.mesh.position.x < -14) this.mesh.position.x = -14;
        if (this.mesh.position.x > 14) this.mesh.position.x = 14;

        if (this.attackCooldown > 0) this.attackCooldown--;
    }
}

// Inisialisasi Karakter Player (Biru) vs CPU (Merah)
const player1 = new Fighter3D(-5, 0x3498db, true, "Pemain 1");
const computer = new Fighter3D(5, 0xe74c3c, false, "(CPU)");

let gameOver = false;

// --- 6. GAME LOOP UTAMA (RENDERER 3D) ---
function animate() {
    requestAnimationFrame(animate);

    if (!gameOver) {
        player1.update(computer);
        computer.update(player1);

        if (player1.health <= 0 || computer.health <= 0) {
            gameOver = true;
        }
    }

    // Kamera mengikuti posisi tengah antara kedua pemain (Sistem Kamera Dinamis)
    camera.position.x = (player1.mesh.position.x + computer.mesh.position.x) / 2;

    renderer.render(scene, camera);
}

animate();
</script>

</body>
</html>
"""

# Render komponen game ke dalam Streamlit beserta bar informasi darah standar
components.html(game_html, height=520, scrolling=False)

st.info("""
🎮 **Panduan Kontrol Arena 3D:**
* **Ingat:** Silakan **Klik Kiri 1x pada area game 3D** di atas agar tombol keyboard aktif!
* **Navigasi Anda (P1 - Biru):** Tombol **A / D** untuk Jalan, **W** untuk Lompat 3D, dan **F** untuk Meluncurkan Pukulan Lengan.
* **Lawan (CPU - Merah):** Bergerak dan melancarkan pukulan otomatis menggunakan kecerdasan buatan komputer.
""")
