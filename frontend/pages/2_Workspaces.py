import streamlit as st
from api_client import get_workspaces, create_workspace, get_history, delete_workspace

st.set_page_config(
    page_title="Workspaces — Cyberify",
    page_icon="📁",
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
[data-testid="stSidebar"] { background: #0F0F1A !important; border-right: 1px solid rgba(108,99,255,0.15) !important; }
.block-container { padding: 2rem 3rem !important; }

.ws-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(108,99,255,0.15);
    border-radius: 14px; padding: 20px 24px; margin-bottom: 12px;
    transition: all 0.2s;
}
.ws-card:hover { border-color: rgba(108,99,255,0.35); background: rgba(108,99,255,0.06); }
.ws-name { font-family: 'Space Grotesk', sans-serif; font-size: 17px; font-weight: 600; color: #E8E8F0; }
.ws-desc { font-size: 13px; color: rgba(232,232,240,0.45); margin-top: 4px; }
.ws-meta { font-size: 11px; color: rgba(232,232,240,0.25); margin-top: 8px; }
.section-header {
    font-family: 'Space Grotesk', sans-serif; font-size: 20px;
    font-weight: 600; color: #E8E8F0; margin-bottom: 20px;
    padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.07);
}
.stButton > button {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
}
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(108,99,255,0.2) !important;
    border-radius: 10px !important; color: #E8E8F0 !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
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
        st.rerun()
    if st.button("📎  Documents", use_container_width=True):
        st.switch_page("pages/3_Documents.py")
    if st.button("💬  Chat", use_container_width=True):
        st.switch_page("pages/4_Chat.py")
    st.markdown("---")
    if st.button("🚪  Sign Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("app.py")

# Main
st.markdown('<div class="section-header">📁 Workspaces</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1.4], gap="large")

# ── Create Workspace ──
with left:
    st.markdown("<div style='font-size:15px; font-weight:600; color:#E8E8F0; margin-bottom:16px;'>Create New Workspace</div>", unsafe_allow_html=True)
    with st.container(border=True):
        ws_name = st.text_input("Workspace Name", placeholder="e.g. Competitor Analysis")
        ws_desc = st.text_input("Description (optional)", placeholder="What is this workspace for?")
        if st.button("+ Create Workspace", use_container_width=True):
            if not ws_name.strip():
                st.error("Please enter a workspace name.")
            else:
                data, status = create_workspace(ws_name.strip(), ws_desc.strip())
                if status == 201:
                    st.success(f"✅ Workspace '{ws_name}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create workspace.")

# ── Workspaces List ──
with right:
    st.markdown("<div style='font-size:15px; font-weight:600; color:#E8E8F0; margin-bottom:16px;'>Your Workspaces</div>", unsafe_allow_html=True)

    workspaces = get_workspaces()
    history    = get_history()

    if not workspaces:
        st.markdown("""
        <div style='text-align:center; padding:40px; color:rgba(232,232,240,0.3);'>
            <div style='font-size:32px'>📁</div>
            <div style='font-size:13px; margin-top:8px;'>No workspaces yet.<br>Create one to organize your research.</div>
        </div>""", unsafe_allow_html=True)
    else:
        for ws in workspaces:
            ws_research = [h for h in history if h.get("workspace_id") == ws["id"]]

            col_info, col_del = st.columns([4, 1])
            with col_info:
                st.markdown(f"""
                <div class="ws-card">
                    <div class="ws-name">📁 {ws['name']}</div>
                    <div class="ws-desc">{ws.get('description') or 'No description'}</div>
                    <div class="ws-meta">{len(ws_research)} research queries</div>
                </div>""", unsafe_allow_html=True)
            with col_del:
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_ws_{ws['id']}", help="Delete workspace"):
                    if delete_workspace(ws["id"]):
                        st.success(f"✅ '{ws['name']}' deleted!")
                        st.rerun()
                    else:
                        st.error("Delete failed.")