import streamlit as st
import time
from api_client import get_me, start_research, get_research_status, get_history, get_workspaces, delete_research, get_live_progress, get_headers, API_BASE

st.set_page_config(
    page_title="Dashboard — Cyberify",
    page_icon="🔬",
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
.metric-card {
    background: rgba(108,99,255,0.08); border: 1px solid rgba(108,99,255,0.2);
    border-radius: 14px; padding: 20px 24px; text-align: center;
}
.metric-number { font-family: 'Space Grotesk', sans-serif; font-size: 36px; font-weight: 700; color: #6C63FF; line-height: 1; }
.metric-label { font-size: 12px; color: rgba(232,232,240,0.5); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.8px; }
.stTextArea textarea {
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(108,99,255,0.25) !important;
    border-radius: 12px !important; color: #E8E8F0 !important; font-size: 15px !important; padding: 16px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 14px !important; transition: all 0.2s !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 8px 25px rgba(108,99,255,0.35) !important; }
.badge-pending  { background:#374151; color:#9CA3AF; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-running  { background:#1E3A5F; color:#60A5FA; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-completed{ background:#064E3B; color:#34D399; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-failed   { background:#4C1D1D; color:#F87171; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.pipeline-box {
    background: rgba(255,255,255,0.02); border: 1px solid rgba(108,99,255,0.2);
    border-radius: 14px; padding: 20px 24px; margin-top: 16px;
}
.agent-active {
    background: rgba(108,99,255,0.12); border: 1px solid rgba(108,99,255,0.3);
    border-radius: 10px; padding: 12px 16px; margin-bottom: 10px;
}
.agent-name { font-family: 'Space Grotesk', sans-serif; font-size: 15px; font-weight: 600; color: #A78BFA; }
.agent-step { font-size: 13px; color: rgba(232,232,240,0.7); margin-top: 4px; }
.agent-tool { font-size: 11px; color: rgba(108,99,255,0.8); margin-top: 4px; }
.log-entry { font-size: 11px; color: rgba(232,232,240,0.4); font-family: monospace; padding: 2px 0; }
.history-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
}
.section-header {
    font-family: 'Space Grotesk', sans-serif; font-size: 20px; font-weight: 600;
    color: #E8E8F0; margin-bottom: 20px; padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(108,99,255,0.2) !important;
    border-radius: 10px !important; color: #E8E8F0 !important;
}
.delete-btn > button {
    background: rgba(239,68,68,0.15) !important;
    border: 1px solid rgba(239,68,68,0.3) !important;
    color: #F87171 !important; font-size: 12px !important;
    padding: 4px 10px !important; border-radius: 8px !important;
}
.delete-btn > button:hover {
    background: rgba(239,68,68,0.3) !important;
    transform: none !important; box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# Session init
if "active_research_id" not in st.session_state:
    st.session_state.active_research_id = None
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='padding: 20px 0 24px 0;'>
        <div style='font-family: Space Grotesk, sans-serif; font-size: 22px; font-weight: 700;
            background: linear-gradient(135deg, #6C63FF, #A78BFA);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            🔬 Cyberify
        </div>
        <div style='font-size: 11px; color: rgba(232,232,240,0.35); letter-spacing: 1px; text-transform: uppercase; margin-top: 2px;'>Research Agent</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    user = get_me()
    if user:
        st.markdown(f"""
        <div style='background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.2);
                    border-radius: 10px; padding: 12px 14px; margin-bottom: 20px;'>
            <div style='font-size: 13px; font-weight: 600; color: #E8E8F0;'>👤 {user['username']}</div>
            <div style='font-size: 11px; color: rgba(232,232,240,0.45); margin-top: 2px;'>{user['email']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='font-size:11px; color:rgba(232,232,240,0.3); letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>Navigation</div>", unsafe_allow_html=True)
    if st.button("🏠  Dashboard", use_container_width=True): st.rerun()
    if st.button("📁  Workspaces", use_container_width=True): st.switch_page("pages/2_Workspaces.py")
    if st.button("📎  Documents", use_container_width=True): st.switch_page("pages/3_Documents.py")
    if st.button("💬  Chat", use_container_width=True): st.switch_page("pages/4_Chat.py")
    st.markdown("---")
    if st.button("🚪  Sign Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("app.py")

# Main
history    = get_history()
workspaces = get_workspaces()

# Stats
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="metric-card"><div class="metric-number">{len(history)}</div><div class="metric-label">Total Queries</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card"><div class="metric-number">{len([h for h in history if h["status"]=="completed"])}</div><div class="metric-label">Completed</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card"><div class="metric-number">{len([h for h in history if h["status"]=="running"])}</div><div class="metric-label">Running</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card"><div class="metric-number">{len(workspaces)}</div><div class="metric-label">Workspaces</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

left, right = st.columns([1.6, 1], gap="large")

with left:
    st.markdown('<div class="section-header">🚀 New Research Query</div>', unsafe_allow_html=True)

    query = st.text_area("Query", placeholder="e.g. Analyze the competitive landscape of AI-powered CRM tools...", height=120, label_visibility="collapsed")

    col_ws, col_btn = st.columns([1, 1])
    with col_ws:
        ws_options = {"No Workspace": None, **{ws["name"]: ws["id"] for ws in workspaces}}
        selected_ws  = st.selectbox("Workspace", list(ws_options.keys()), label_visibility="collapsed")
        workspace_id = ws_options[selected_ws]
    with col_btn:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        run_clicked = st.button("▶  Run Research", use_container_width=True)

    if run_clicked:
        if not query.strip():
            st.error("Please enter a research query.")
        else:
            with st.spinner("Starting..."):
                data, status = start_research(query.strip(), workspace_id)
            if status == 201:
                st.session_state.active_research_id = data["id"]
                st.session_state.current_report = None
                st.rerun()
            else:
                st.error("Failed to start research.")

    # Live Pipeline
    if st.session_state.active_research_id:
        res = get_research_status(st.session_state.active_research_id)
        if res:
            status     = res["status"]
            badge_map  = {"pending":"badge-pending","running":"badge-running","completed":"badge-completed","failed":"badge-failed"}
            badge_icon = {"pending":"⏳","running":"⚡","completed":"✅","failed":"❌"}

            st.markdown(f"""
            <div style='display:flex; align-items:center; gap:12px; margin: 16px 0 8px 0;'>
                <span style='font-size:13px; color:rgba(232,232,240,0.6);'>Research #{st.session_state.active_research_id}</span>
                <span class='{badge_map.get(status,"badge-pending")}'>{badge_icon.get(status,"")} {status.upper()}</span>
            </div>""", unsafe_allow_html=True)

            if status == "running":
                progress = get_live_progress(st.session_state.active_research_id)
                if progress:
                    pct = progress.get("percent", 0)
                    st.progress(pct / 100, text=f"{pct}% complete")
                    st.markdown('<div class="pipeline-box">', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:12px; color:rgba(232,232,240,0.4); text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;">⚡ Live Execution Pipeline</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="agent-active">
                        <div class="agent-name">{progress.get("current_agent","")}</div>
                        <div class="agent-step">📌 {progress.get("current_step","")}</div>
                        {"<div class='agent-tool'>🔧 Tool: " + progress.get("current_tool","") + "</div>" if progress.get("current_tool") else ""}
                    </div>""", unsafe_allow_html=True)
                    agents = [("🧠 Planner", pct >= 25), ("🔍 Researcher", pct >= 65), ("✅ Verifier", pct >= 85), ("📝 Reporter", pct >= 95)]
                    cols = st.columns(4)
                    for i, (name, done) in enumerate(agents):
                        with cols[i]:
                            color = "#34D399" if done else "#6C63FF"
                            st.markdown(f"""
                            <div style='text-align:center; padding:8px; background:rgba(255,255,255,0.03);
                                        border-radius:8px; border:1px solid {color}33;'>
                                <div style='font-size:18px;'>{"✅" if done else "⏳"}</div>
                                <div style='font-size:11px; color:{color}; margin-top:4px;'>{name}</div>
                            </div>""", unsafe_allow_html=True)
                    logs = progress.get("logs", [])
                    if logs:
                        with st.expander("📋 Activity Logs"):
                            for log in logs[-10:]:
                                st.markdown(f'<div class="log-entry">→ {log}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                time.sleep(2)
                st.rerun()

            elif status == "completed":
                st.session_state.current_report = res
                conf = res.get("confidence_score", 0) or 0
                st.success(f"Research complete! Confidence: {conf:.0%}")

            elif status == "failed":
                st.error("Research failed. Please try again.")

    # Report Display
    if st.session_state.current_report:
        r = st.session_state.current_report
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">📄 Research Report</div>', unsafe_allow_html=True)
        conf    = r.get("confidence_score", 0) or 0
        sources = r.get("sources") or []
        st.metric("Confidence Score", f"{conf:.0%}")
        st.markdown(r.get("report", "No report."))
        if sources:
            with st.expander("📎 Sources"):
                for i, src in enumerate(sources, 1):
                    st.markdown(f"{i}. [{src}]({src})")
        col_pdf, col_md = st.columns(2)
        with col_pdf:
            if st.button("⬇ Download PDF", use_container_width=True, key=f"pdf_{r['id']}"):
                import requests as req
                pdf_res = req.get(f"{API_BASE}/api/export/pdf/{r['id']}", headers=get_headers())
                if pdf_res.status_code == 200:
                    safe_name = r.get("query","research")[:30].strip().replace(" ","_").replace("/","-")
                    st.download_button("📥 Save PDF", data=pdf_res.content,
                                       file_name=f"{safe_name}_{r['id']}.pdf",
                                       mime="application/pdf", key=f"save_pdf_{r['id']}")
                else:
                    st.error("PDF generate nahi hua.")
        with col_md:
            safe_name = r.get("query","research")[:30].strip().replace(" ","_").replace("/","-")
            st.download_button("⬇ Download MD", data=r.get("report", ""),
                               file_name=f"{safe_name}_{r['id']}.md",
                               mime="text/markdown", use_container_width=True, key=f"md_{r['id']}")

# ── Recent History (right panel) ──
with right:
    st.markdown('<div class="section-header">📋 Recent Research</div>', unsafe_allow_html=True)

    if not history:
        st.markdown("""
        <div style='text-align:center; padding:40px; color:rgba(232,232,240,0.3);'>
            <div style='font-size:32px'>🔍</div>
            <div style='font-size:13px; margin-top:8px;'>No research yet.</div>
        </div>""", unsafe_allow_html=True)
    else:
        badge_map  = {"pending":"badge-pending","running":"badge-running","completed":"badge-completed","failed":"badge-failed"}
        badge_icon = {"pending":"⏳","running":"⚡","completed":"✅","failed":"❌"}

        for item in history[:8]:
            status   = item["status"]
            q_short  = item["query"][:50] + "..." if len(item["query"]) > 50 else item["query"]
            conf     = item.get("confidence_score")
            conf_str = f"• {conf:.0%}" if conf else ""

            st.markdown(f"""
            <div class="history-card">
                <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                    <div style='font-size:13px; color:#E8E8F0; font-weight:500; flex:1; margin-right:8px;'>{q_short}</div>
                    <span class='{badge_map.get(status,"badge-pending")}'>{badge_icon.get(status,"")} {status}</span>
                </div>
                <div style='font-size:11px; color:rgba(232,232,240,0.35); margin-top:6px;'>#{item['id']} {conf_str}</div>
            </div>""", unsafe_allow_html=True)

            # Action buttons
            if status == "completed":
                col_view, col_del = st.columns([2, 1])
                with col_view:
                    if st.button(f"📄 View Report", key=f"view_{item['id']}", use_container_width=True):
                        full = get_research_status(item["id"])
                        if full:
                            st.session_state.current_report = full
                            st.session_state.active_research_id = item["id"]
                            st.rerun()
                with col_del:
                    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                    if st.button(f"🗑️ Delete", key=f"del_{item['id']}", use_container_width=True):
                        st.session_state.confirm_delete = item["id"]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                col_empty, col_del = st.columns([2, 1])
                with col_del:
                    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                    if st.button(f"🗑️ Delete", key=f"del_{item['id']}", use_container_width=True):
                        st.session_state.confirm_delete = item["id"]
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # Confirm delete
            if st.session_state.confirm_delete == item["id"]:
                st.warning(f"Are you sure you want to delete Research #{item['id']}?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Yes, Delete", key=f"confirm_{item['id']}", use_container_width=True):
                        if delete_research(item["id"]):
                            if st.session_state.active_research_id == item["id"]:
                                st.session_state.active_research_id = None
                                st.session_state.current_report = None
                            st.session_state.confirm_delete = None
                            st.success("Deleted!")
                            st.rerun()
                with col_no:
                    if st.button("❌ Cancel", key=f"cancel_{item['id']}", use_container_width=True):
                        st.session_state.confirm_delete = None
                        st.rerun()