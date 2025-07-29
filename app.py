import streamlit as st
import tempfile
import subprocess
import shutil
from io import BytesIO
import time


from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}


# ---------------- Session State Init ----------------
for key, default in {
    "history": [],
    "show_history": True,
    "current_summary": {},
    "selected_filename": "",
    "selected_from_history": False,
    "toggle_pressed": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- Page Setup ----------------
st.set_page_config(page_title="Azure MDD Summary Generator", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap');
    html, body, [class*="css"] {
        font-family: 'Playfair Display', serif;
        background-image: url('background.JPG');
        background-size: cover;
        background-color: #fdfdfd;
        transition: all 0.3s ease-in-out;
    }
    .main h1 { color: #0a2f5c; font-weight: 700; margin-bottom: 0.2rem; }
    .main h3, .main h4, .main h5 { color: #2c3e50; }
    .stButton>button {
        background-color: #f36f21; color: white; border: None; border-radius: 6px;
        padding: 0.5em 1em; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #d95f1d; transform: scale(1.03);
    }
    .stTextInput>div>input, .stTextArea>div>textarea {
        background-color: #ffffffcc; color: #333; border-radius: 6px;
        padding: 0.5em; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    .stTextInput>div>input:focus, .stTextArea>div>textarea:focus {
        box-shadow: 0 0 0 3px rgba(243, 111, 33, 0.3);
    }
    .block-container { padding: 2rem 2rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1><i class='fas fa-brain'></i> AI-Powered MDD Summary Generator</h1>", unsafe_allow_html=True)
st.markdown("##### <span style='color:#4a4a4a;'>Powered by Azure Document Intelligence | GSK Hackathon</span>", unsafe_allow_html=True)
st.markdown("---")

# ---------------- Toggle History Panel ----------------
def toggle_history():
    st.session_state["show_history"] = not st.session_state["show_history"]
    st.session_state["toggle_pressed"] = True

st.button("Hide History" if st.session_state["show_history"] else "Show History", on_click=toggle_history)

if st.session_state.toggle_pressed:
    st.session_state.toggle_pressed = False
    st.query_params.update(dummy_toggle=str(st.session_state["show_history"]))

# ---------------- Layout Columns ----------------
col1, col2 = st.columns([1, 3]) if st.session_state["show_history"] else st.columns([0.1, 4])

# ---------------- Sidebar History ----------------
with col1:
    if st.session_state["show_history"]:
        st.markdown("### <i class='far fa-clock'></i> Summary History", unsafe_allow_html=True)
        if st.session_state["history"]:
            for idx, entry in enumerate(reversed(st.session_state["history"])):
                if st.button(f"{entry['filename']}", key=f"hist_{idx}"):
                    st.session_state["current_summary"] = entry["summary"]
                    st.session_state["selected_filename"] = entry["filename"]
                    st.session_state["selected_from_history"] = True
        else:
            st.info("No summary history yet.")

# ---------------- Main App UI ----------------
with col2:
    st.markdown("### <i class='fas fa-file-upload'></i> Upload Clinical Study Protocol (.docx)", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Protocol DOCX", type=["docx"])

    if st.button("Generate Summary Report", use_container_width=True):
        if not uploaded_file:
            st.warning("Please upload a valid Protocol DOCX file.")
        else:
            with st.spinner("Running complete pipeline..."):
                try:
                    # Save uploaded file as Protocol.docx

                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    input_filename = f"Protocol_{timestamp}.docx"

                    # Save uploaded file with timestamped name
                    with open(input_filename, "wb") as f:
                        f.write(uploaded_file.read())
                    with open("latest_protocol.txt", "w") as f:
                        f.write(input_filename)

# Also update the hardcoded references to Protocol.docx in parse_doc.ipynb to use this dynamic name


                    # Execute pipeline notebooks & script
                    subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "parse_doc.ipynb", "--inplace"], check=True)
                    subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "semantic_matching.ipynb", "--inplace"], check=True)
                    subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "Summarise.ipynb", "--inplace"], check=True)
                    subprocess.run(["python3", "file_generator.py"], check=True)

                    # Let user download the final file
                    with open("Filled_Summary.docx", "rb") as final_docx:
                        st.download_button(
                            label="📄 Download Final Summary Report",
                            data=final_docx,
                            file_name="Filled_Summary.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        st.success("🎉 Summary generation complete!")

                except subprocess.CalledProcessError:
                    st.error("One of the pipeline steps failed. Please check console logs.")
