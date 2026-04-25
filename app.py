import streamlit as st

import streamlit as st

# --- SABSE UPAR YE CODE ADD KAREIN ---
import streamlit as st

# Forcefully hamesha ke liye toolbar band karne ka pakka tarika
st.markdown("""
<style>
    /* Sabhi header elements ko disable karo */
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; height: 0 !important; display: none !important;}
    [data-testid="stDecoration"] {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
# ----------------------------------------

# 1. Page configuration (Title aur Layout ke liye)
st.set_page_config(page_title="Papa's Pro Stamper", layout="centered")

# 2. CSS code jo GitHub icon aur menu ko JAD se mita dega
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {display:none;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)
import fitz  # PyMuPDF
from PIL import Image
import io

# Isse top right ke saare icons aur buttons gayab ho jayenge
st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


st.set_page_config(page_title="Papa's Pro Stamper", layout="wide")

st.title("📄 Digital Stamp: Page-by-Page Control")

# --- SESSION STATE INITIALIZATION ---
if 'pages_data' not in st.session_state:
    st.session_state.pages_data = {}  # Format: {page_num: {'active': True, 'x': 100, 'y': 100, 'size': 150}}

with st.sidebar:
    st.header("1. Files Upload")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
    uploaded_stamp = st.file_uploader("Upload Stamp (PNG)", type=["png"])
    
    st.markdown("---")
    st.header("2. Global Settings")
    default_size = st.slider("Default Stamp Size", 20, 500, 150)

if uploaded_pdf and uploaded_stamp:
    # PDF Load
    pdf_bytes = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    # Page Selection
    page_num = st.sidebar.number_input(f"Page (Total: {total_pages})", min_value=1, max_value=total_pages, value=1) - 1
    
    # Initialize page data if not exists
    if page_num not in st.session_state.pages_data:
        st.session_state.pages_data[page_num] = {
            'active': False, 
            'x': int(doc[page_num].rect.width / 2), 
            'y': int(doc[page_num].rect.height / 2),
            'size': default_size
        }

    st.sidebar.markdown(f"---")
    st.sidebar.subheader(f"Editing Page {page_num + 1}")
    
    # Checkbox to enable/disable stamp on THIS specific page
    is_active = st.sidebar.checkbox("Is page par stamp lagani hai?", value=st.session_state.pages_data[page_num]['active'])
    st.session_state.pages_data[page_num]['active'] = is_active

    if is_active:
        # Per-page position and size
        pos_x = st.sidebar.slider("Left <-> Right", 0, int(doc[page_num].rect.width), st.session_state.pages_data[page_num]['x'])
        pos_y = st.sidebar.slider("Up <-> Down", 0, int(doc[page_num].rect.height), st.session_state.pages_data[page_num]['y'])
        p_size = st.sidebar.slider("This Page Stamp Size", 20, 500, st.session_state.pages_data[page_num]['size'])
        
        # Save to session
        st.session_state.pages_data[page_num]['x'] = pos_x
        st.session_state.pages_data[page_num]['y'] = pos_y
        st.session_state.pages_data[page_num]['size'] = p_size

    # --- PREVIEW LOGIC ---
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
    bg_img = Image.open(io.BytesIO(pix.tobytes())).convert("RGBA")
    
    if st.session_state.pages_data[page_num]['active']:
        stamp_img = Image.open(uploaded_stamp).convert("RGBA")
        s_w = st.session_state.pages_data[page_num]['size']
        s_h = int(s_w * (stamp_img.height / stamp_img.width))
        stamp_preview = stamp_img.resize((int(s_w * 1.5), int(s_h * 1.5)), Image.Resampling.LANCZOS)

        preview_x = int(st.session_state.pages_data[page_num]['x'] * 1.5) - int(stamp_preview.width / 2)
        preview_y = int(st.session_state.pages_data[page_num]['y'] * 1.5) - int(stamp_preview.height / 2)

        preview_canvas = bg_img.copy()
        preview_canvas.alpha_composite(stamp_preview, (preview_x, preview_y))
        st.image(preview_canvas, use_container_width=True)
    else:
        st.image(bg_img, use_container_width=True)
        st.warning(f"Page {page_num+1} par koi stamp nahi lagegi.")

    # --- FINAL SAVE LOGIC (LOOP THROUGH ALL PAGES) ---
    if st.button("Download Final PDF with all pages", type="primary"):
        for p_idx in range(total_pages):
            if p_idx in st.session_state.pages_data and st.session_state.pages_data[p_idx]['active']:
                p_obj = doc[p_idx]
                data = st.session_state.pages_data[p_idx]
                
                # Re-calculate height for final insertion
                stamp_img = Image.open(uploaded_stamp)
                final_h = int(data['size'] * (stamp_img.height / stamp_img.width))
                
                rect = fitz.Rect(
                    data['x'] - (data['size']/2), 
                    data['y'] - (final_h/2), 
                    data['x'] + (data['size']/2), 
                    data['y'] + (final_h/2)
                )
                uploaded_stamp.seek(0)
                p_obj.insert_image(rect, stream=uploaded_stamp.read())
        
        output = io.BytesIO()
        doc.save(output)
        st.success("Sari pages process ho gayi hain!")
        st.download_button("📥 Download Final PDF", output.getvalue(), file_name="Stamped_Document.pdf")
