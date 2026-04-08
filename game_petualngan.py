import streamlit as st
import streamlit.components.v1 as components
import textwrap

# Konfigurasi Halaman agar tampilan bersih dan profesional
st.set_page_config(page_title="Hunter of the Black Forest", layout="centered", page_icon="⚔️")

st.title("⚔️ Hunter of the Black Forest")
st.markdown("Klik pada kotak game, lalu gunakan **Panah** untuk gerak dan **Spasi** untuk menebas!")

# Bagian Game (HTML, CSS, JS) dalam satu blok string
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

    let player = {
        x: 300, y: 200, size: 20, hp: 100,
        color: "#00d4ff", isAttacking: false, attackTimer: 0
    };

    let monsters = [];

    function spawnMonster() {
        if (monsters.length < 6 && !isGameOver) {
            const side = Math.floor(Math.random() * 4);
            let x, y;
            if(side === 0) { x = Math.random()*600; y = -20; }
            else if(side === 1) { x = 620; y = Math.random()*400; }
            else if(side === 2) { x = Math.random()*600; y = 420; }
            else { x = -20; y = Math.random()*400; }
            monsters.push({ x, y, size: 20, hp: 40, color: "#ff3e3e" });
        }
    }

    for(let i=0; i<3; i++) spawnMonster();
    setInterval(spawnMonster, 4000);

    window.addEventListener("keydown", e => {
        keys[e.key] = true;
        if (e.key === " " && !player.isAttacking && !isGameOver) {
            player.isAttacking = true;
            player.attackTimer = 12;
            checkAttack();
        }
        if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key)) e.preventDefault();
    });
    window.addEventListener("keyup", e => keys[e.key] = false);

    function checkAttack() {
        monsters.forEach((m, index) => {
            let dist = Math.hypot(m.x - player.x, m.y - player.y);
            if (dist < 45) {
                m.hp -= 20;
                if (m.hp <= 0) {
                    monsters.splice(index, 1);
                    kills++;
                    killEl.innerText = kills;
                }
            }
        });
    }

    function update() {
        if (isGameOver) return;
        if (keys["ArrowUp"] && player.y > 0) player.y -= 4;
        if (keys["ArrowDown"] && player.y < 380) player.y += 4;
        if (keys["ArrowLeft"] && player.x > 0) player.x -= 4;
        if (keys["ArrowRight"] && player.x < 580) player.x += 4;
        if (player.isAttacking) {
            player.attackTimer--;
            if (player.attackTimer <= 0) player.isAttacking = false;
        }
        monsters.forEach(m => {
            let dist = Math.hypot(player.x - m.x, player.y - m.y);
            if (dist < 250) {
                let angle = Math.atan2(player.y - m.y, player.x - m.x);
                m.x += Math.cos(angle) * 1.8;
                m.y += Math.sin(angle) * 1.8;
            }
            if (dist < 20) {
                player.hp -= 0.4;
                hpEl.innerText = Math.max(0, Math.floor(player.hp));
                if (player.hp <= 0) {
                    isGameOver = true;
                    statusEl.innerText = "💀 TEWAS DI HUTAN HITAM";
                    statusEl.style.color = "#ff4d4d";
                }
            }
        });
    }

    function draw() {
        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, 600, 400);
        ctx.save();
        ctx.beginPath();
        let grad = ctx.createRadialGradient(player.x+10, player.y+10, 0, player.x+10, player.y+10, VISION_RADIUS);
        grad.addColorStop(0, "rgba(255,255,255,0.2)");
        grad.addColorStop(1, "rgba(0,0,0,1)");
        ctx.fillStyle = grad;
        ctx.arc(player.x+10, player.y+10, VISION_RADIUS, 0, Math.PI*2);
        ctx.fill();
        ctx.clip();
        monsters.forEach(m => {
            ctx.fillStyle = m.color;
            ctx.shadowBlur = 8;
            ctx.shadowColor = m.color;
            ctx.fillRect(m.x, m.y, m.size, m.size);
        });
        ctx.restore();
        ctx.fillStyle = player.color;
        ctx.shadowBlur = 15;
        ctx.shadowColor = player.color;
        ctx.fillRect(player.x, player.y, player.size, player.size);
        ctx.shadowBlur = 0;
        if (player.isAttacking) {
            ctx.strokeStyle = "white";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(player.x+10, player.y+10, 40, 0, Math.PI*2);
            ctx.stroke();
        }
        requestAnimationFrame(draw);
    }
    setInterval(update, 1000/60);
    draw();
</script>
""").strip()

# Menampilkan Game ke Streamlit
components.html(game_code, height=550)

st.divider()
st.info("💡 Klik area hitam game agar keyboard terdeteksi.")
