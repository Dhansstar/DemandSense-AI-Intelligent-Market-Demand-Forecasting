import streamlit as st
import streamlit.components.v1 as components
import eda
import prediction
import os
import base64

# --- 1. SET PAGE CONFIG (HARUS DI PALING ATAS) ---
st.set_page_config(page_title="DemandSense AI", layout="wide")

# --- 2. ASSETS & INJECTORS ---
def get_base64_of_bin_file(bin_file):
    """Fungsi untuk encode file GIF ke base64 agar bisa dibaca CSS."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg_gif(gif_file):
    """Menyuntikkan GIF sebagai background utama aplikasi."""
    if os.path.exists(gif_file):
        bin_str = get_base64_of_bin_file(gif_file)
        page_bg_img = f'''
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/gif;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Overlay tipis agar konten tetap mudah dibaca di atas GIF */
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.6); /* Gelapkan GIF 60% */
            z-index: -1;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def inject_anime_js():
    anime_script = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
    <script>
        const observer = new MutationObserver((mutations) => {
            const target = document.querySelector('.stSelectbox');
            if (target && !target.dataset.animated) {
                target.dataset.animated = "true";
                target.addEventListener('mouseenter', () => {
                    anime({ targets: '.stSelectbox', scale: 1.02, duration: 400, easing: 'easeOutExpo' });
                });
                target.addEventListener('mouseleave', () => {
                    anime({ targets: '.stSelectbox', scale: 1, duration: 400, easing: 'easeOutExpo' });
                });
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    components.html(anime_script, height=0)

# --- 3. MAIN APPLICATION ---
def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # PANGGIL BACKGROUND GIF
    # Ganti 'background.gif' dengan nama file GIF lo yang ada di satu folder
    set_bg_gif(os.path.join(current_dir, "6.gif"))
    
    # Load CSS Global & Anime.js
    local_css(os.path.join(current_dir, "style.css"))
    inject_anime_js()

    # SIDEBAR WITH BOOTSTRAP DESIGN
    st.sidebar.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("<h1 class='animated-sidebar-text'>DemandSense</h1>", unsafe_allow_html=True)
        st.markdown("---")

        # Practitioner Card
        st.markdown("""
            <div class="card bg-dark border-secondary mb-4 shadow-sm" style="background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(10px);">
                <div class="card-body p-3">
                    <div class="d-flex align-items-center mb-2">
                        <div class="badge bg-primary me-2">Time Series</div>
                        <span class="fw-bold text-white small">Practitioner Info</span>
                    </div>
                    <p class="text-light small mb-1"><strong>Name:</strong> Risyadhana Syaifuddin</p>
                    <p class="text-light small mb-0"><strong>Project ID:</strong> DemandSense AI</p>
                </div>
            </div>
            <p class='text-white fw-bold mb-1 small' style='opacity: 0.8;'>Navigate Menu:</p>
        """, unsafe_allow_html=True)
        
        menu = st.selectbox(
            "Navigate Menu:", 
            ["EDA Analysis", "Demand Forecasting"], 
            label_visibility="collapsed"
        )
        st.markdown("---")
        
    # NAVIGATION LOGIC
    if menu == "EDA Analysis":
        eda.run()
    else:
        prediction.run()

if __name__ == "__main__":
    main()