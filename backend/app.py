"""
Multimodal PDF RAG chat app.

Upload a PDF -> parser.py converts each page to a PNG -> rag_engine.py's
Gemini agent answers questions by picking and inspecting the right page
images. Run with:

    streamlit run app.py
"""

import os
import shutil
import tempfile

import streamlit as st

from services.parser import parse_pdf
from services.rag_engine import RagEngine

st.set_page_config(page_title="Multimodal PDF RAG", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = {
    "session_dir": None,   # temp dir holding the uploaded PDF + page images
    "engine": None,        # RagEngine instance bound to that dir
    "messages": [],        # chat history
    "doc_name": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_session():
    if st.session_state.session_dir and os.path.exists(st.session_state.session_dir):
        shutil.rmtree(st.session_state.session_dir, ignore_errors=True)
    st.session_state.session_dir = None
    st.session_state.engine = None
    st.session_state.messages = []
    st.session_state.doc_name = None


# ---------------------------------------------------------------------------
# Sidebar: upload + process
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📄 Document")

    if not os.getenv("GEMINI_API_KEY"):
        st.warning(
            "No GEMINI_API_KEY found in your environment. "
            "Set it in a .env file before asking questions."
        )

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    if uploaded_file and st.button("Process PDF", use_container_width=True):
        reset_session()
        with st.spinner("Converting pages to images..."):
            temp_root = tempfile.mkdtemp(prefix="rag_")
            pdf_path = os.path.join(temp_root, uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            output_dir = os.path.join(temp_root, "images")
            try:
                parse_pdf(pdf_path, output_dir)
            except Exception as e:
                st.error(f"Failed to parse PDF: {e}")
                shutil.rmtree(temp_root, ignore_errors=True)
                st.stop()

            st.session_state.session_dir = output_dir
            st.session_state.doc_name = uploaded_file.name
            st.session_state.engine = RagEngine(folder_path=output_dir)
            st.session_state.engine.start_chat()

        st.success(f"Processed '{uploaded_file.name}'")

    if st.session_state.session_dir:
        pages = sorted(
            f for f in os.listdir(st.session_state.session_dir) if f.endswith(".png")
        )
        st.caption(f"**{st.session_state.doc_name}** — {len(pages)} page(s) ready")

        if st.button("Clear document", use_container_width=True):
            reset_session()
            st.rerun()

# ---------------------------------------------------------------------------
# Main: chat
# ---------------------------------------------------------------------------
st.title("Multimodal PDF RAG Chat")

if not st.session_state.engine:
    st.info("Upload a PDF and click **Process PDF** in the sidebar to get started.")
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask something about the PDF..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = st.session_state.engine.ask(prompt)
                except Exception as e:
                    answer = f"Something went wrong calling Gemini: {e}"
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})