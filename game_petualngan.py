import streamlit as st

# Konfigurasi Halaman
st.set_page_config(page_title="Petualangan Hutan Hitam", page_icon="⚔️")

# Inisialisasi State Game
if 'scene' not in st.session_state:
    st.session_state.scene = "start"
if 'inventory' not in st.session_state:
    st.session_state.inventory = []
if 'hp' not in st.session_state:
    st.session_state.hp = 100

def change_scene(scene_name):
    st.session_state.scene = scene_name

# --- LOGIKA GAME ---

st.title("🌲 Misteri Hutan Hitam")
st.sidebar.header("Status Karakter")
st.sidebar.write(f"❤️ HP: {st.session_state.hp}")
st.sidebar.write(f"🎒 Inventaris: {', '.join(st.session_state.inventory) if st.session_state.inventory else 'Kosong'}")

if st.session_state.hp <= 0:
    st.error("Anda telah gugur dalam petualangan...")
    if st.button("Ulangi Dari Awal"):
        st.session_state.clear()
        st.rerun()

# --- SCENE: START ---
elif st.session_state.scene == "start":
    st.image("https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000", caption="Gerbang Hutan")
    st.write("""
    Anda berdiri di depan gerbang Hutan Hitam yang legendaris. 
    Konon ada harta karun tersembunyi di dalamnya, namun banyak monster yang menjaga.
    Di tanah, Anda melihat sebuah **Pedang Karat**.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ambil Pedang & Masuk Hutan"):
            st.session_state.inventory.append("Pedang Karat")
            change_scene("forest_entry")
            st.rerun()
    with col2:
        if st.button("Masuk Tanpa Senjata"):
            change_scene("forest_entry")
            st.rerun()

# --- SCENE: FOREST ENTRY ---
elif st.session_state.scene == "forest_entry":
    st.write("""
    Hutan sangat gelap. Tiba-tiba seekor **Serigala Hutan** muncul menghadang!
    Apa yang akan Anda lakukan?
    """)
    
    if st.button("Lawan Serigala"):
        if "Pedang Karat" in st.session_state.inventory:
            st.success("Dengan Pedang Karat, Anda berhasil mengalahkan serigala!")
            change_scene("treasure_room")
        else:
            st.error("Anda tidak punya senjata! Serigala melukai Anda.")
            st.session_state.hp -= 50
            if st.session_state.hp > 0:
                if st.button("Lari ke Dalam"):
                    change_scene("treasure_room")
                    st.rerun()

    if st.button("Coba Bersembunyi"):
        st.write("Anda berhasil bersembunyi, tapi kehilangan jejak jalan utama.")
        change_scene("lost")
        st.rerun()

# --- SCENE: TREASURE ROOM ---
elif st.session_state.scene == "treasure_room":
    st.balloons()
    st.write("""
    ### 🎉 Selamat!
    Anda menemukan sebuah peti emas tua di tengah reruntuhan kuil. 
    Petualangan Anda berakhir dengan kemenangan!
    """)
    if st.button("Main Lagi"):
        st.session_state.clear()
        st.rerun()

# --- SCENE: LOST ---
elif st.session_state.scene == "lost":
    st.warning("Anda tersesat di kegelapan...")
    if st.button("Kembali ke Gerbang"):
        change_scene("start")
        st.rerun()
