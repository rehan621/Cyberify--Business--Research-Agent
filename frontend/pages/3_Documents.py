import streamlit as st
import requests
from api_client import get_headers, API_BASE

st.set_page_config(
    page_title="Documents — Cyberify",
    page_icon="📎",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not st.session_state.get("token"):
    st.switch_page("app.py")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stSidebar"] {
    background: #0F0F1A !important;
    border-right: 1px solid rgba(108,99,255,0.15) !important;
}
.block-container { padding: 2rem 3rem !important; }

.section-header {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 20px; font-weight: 600;
    color: #E8E8F0; margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}

.doc-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(108,99,255,0.15);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.stButton > button {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
}

.upload-box {
    background: rgba(108,99,255,0.05);
    border: 2px dashed rgba(108,99,255,0.3);
    border-radius: 14px;
    padding: 32px;
    text-align: center;
}

.file-icon { font-size: 40px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────

def get_documents():
    res = requests.get(f"{API_BASE}/api/documents/", headers=get_headers())
    return res.json() if res.status_code == 200 else []

def upload_document(file):
    res = requests.post(
        f"{API_BASE}/api/documents/upload",
        files={"file": (file.name, file.getvalue(), file.type)},
        headers=get_headers(),
    )
    return res.json(), res.status_code

def delete_document(doc_id: int):
    res = requests.delete(f"{API_BASE}/api/documents/{doc_id}", headers=get_headers())
    return res.status_code == 204


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 20px 0 24px 0;'>
        <div style='font-family: Space Grotesk; font-size: 22px; font-weight: 700;
            background: linear-gradient(135deg, #6C63FF, #A78BFA);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            🔬 Cyberify
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🏠  Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
    if st.button("📁  Workspaces", use_container_width=True):
        st.switch_page("pages/2_Workspaces.py")
    if st.button("📎  Documents", use_container_width=True):
        st.rerun()
    if st.button("💬  Chat", use_container_width=True):
        st.switch_page("pages/4_Chat.py")
    st.markdown("---")
    if st.button("🚪  Sign Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("app.py")


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📎 Document Library</div>', unsafe_allow_html=True)

st.markdown("""
<div style='background: rgba(108,99,255,0.08); border: 1px solid rgba(108,99,255,0.2);
            border-radius: 12px; padding: 14px 18px; margin-bottom: 24px; font-size: 13px;
            color: rgba(232,232,240,0.7);'>
    💡 Upload kiye gaye documents automatically research mein use honge (RAG).
    Supported formats: <strong>PDF, DOCX, TXT</strong>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1, 1.4], gap="large")

# ── Upload Section ──
with left:
    st.markdown("<div style='font-size:15px; font-weight:600; color:#E8E8F0; margin-bottom:16px;'>Upload Document</div>", unsafe_allow_html=True)

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "PDF, DOCX, or TXT file choose karo",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
        )

        if uploaded_file:
            st.markdown(f"""
            <div style='background: rgba(108,99,255,0.1); border-radius: 8px;
                        padding: 10px 14px; margin: 10px 0; font-size: 13px; color: #E8E8F0;'>
                📄 <strong>{uploaded_file.name}</strong>
                <span style='color: rgba(232,232,240,0.4); margin-left: 8px;'>
                    {round(uploaded_file.size/1024, 1)} KB
                </span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("⬆ Upload & Index", use_container_width=True):
                with st.spinner("Uploading aur indexing..."):
                    data, status = upload_document(uploaded_file)
                if status == 201:
                    st.success(f"✅ '{uploaded_file.name}' upload ho gaya!")
                    st.rerun()
                else:
                    err = data.get("detail", "Upload failed.")
                    st.error(err)

# ── Documents List ──
with right:
    st.markdown("<div style='font-size:15px; font-weight:600; color:#E8E8F0; margin-bottom:16px;'>Indexed Documents</div>", unsafe_allow_html=True)

    docs = get_documents()

    if not docs:
        st.markdown("""
        <div style='text-align:center; padding:40px; color:rgba(232,232,240,0.3);'>
            <div style='font-size:36px'>📂</div>
            <div style='font-size:13px; margin-top:8px;'>
                Koi document upload nahi hua.<br>
                Upload karo aur research mein use karo!
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        # Stats
        st.markdown(f"""
        <div style='font-size:12px; color:rgba(232,232,240,0.4); margin-bottom:14px;'>
            {len(docs)} document(s) indexed in ChromaDB
        </div>""", unsafe_allow_html=True)

        type_icons = {"pdf": "📕", "docx": "📘", "txt": "📄"}

        for doc in docs:
            icon = type_icons.get(doc.get("file_type", ""), "📄")
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.03); border: 1px solid rgba(108,99,255,0.15);
                            border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;'>
                    <div style='font-size:14px; font-weight:500; color:#E8E8F0;'>
                        {icon} {doc['filename']}
                    </div>
                    <div style='font-size:11px; color:rgba(232,232,240,0.35); margin-top:4px;'>
                        {doc.get('file_type','').upper()} • ID #{doc['id']}
                    </div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button("🗑", key=f"del_{doc['id']}"):
                    if delete_document(doc["id"]):
                        st.success("Deleted!")
                        st.rerun()