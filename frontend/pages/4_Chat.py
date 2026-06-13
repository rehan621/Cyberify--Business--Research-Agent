import streamlit as st
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from api_client import (
    get_headers, API_BASE, get_history,
    save_chat_message, get_chat_history, clear_chat_history, clear_mode_chat
)

load_dotenv()

st.set_page_config(
    page_title="Chat — Cyberify",
    page_icon="💬",
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
.section-header {
    font-family: 'Space Grotesk', sans-serif; font-size: 20px; font-weight: 600;
    color: #E8E8F0; margin-bottom: 20px; padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.msg-user {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6);
    border-radius: 16px 16px 4px 16px;
    padding: 12px 18px; margin: 8px 0 8px 60px;
    color: white; font-size: 14px; line-height: 1.6;
}
.msg-assistant {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 16px 16px 16px 4px;
    padding: 12px 18px; margin: 8px 60px 8px 0;
    color: #E8E8F0; font-size: 14px; line-height: 1.6;
}
.msg-label-user { text-align:right; font-size:11px; color:rgba(232,232,240,0.3); margin-bottom:4px; }
.msg-label-assistant { font-size:11px; color:rgba(232,232,240,0.3); margin-bottom:4px; }
.chat-tab-active {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6);
    border-radius: 8px; padding: 8px 14px; font-size: 12px;
    color: white; font-weight: 600; margin-bottom: 6px;
}
.chat-tab {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px; padding: 8px 14px; font-size: 12px;
    color: rgba(232,232,240,0.5); margin-bottom: 6px;
}
.history-divider {
    text-align: center; font-size: 11px; color: rgba(232,232,240,0.25);
    margin: 12px 0; padding: 4px 0;
    border-top: 1px solid rgba(255,255,255,0.05);
}
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(108,99,255,0.25) !important;
    border-radius: 12px !important; color: #E8E8F0 !important;
    font-size: 14px !important; padding: 12px 16px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(108,99,255,0.2) !important;
    border-radius: 10px !important; color: #E8E8F0 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
if "chat_sessions" not in st.session_state:
    # Each mode has its own conversation
    st.session_state.chat_sessions = {
        "general":   [],
        "research":  [],
        "documents": [],
    }
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "general"
if "chat_research_id" not in st.session_state:
    st.session_state.chat_research_id = None
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False
if "input_key" not in st.session_state:
    st.session_state.input_key = 0


def get_current_messages():
    """Get messages for current active mode."""
    return st.session_state.chat_sessions.get(st.session_state.chat_mode, [])


def add_message(role: str, content: str, from_db: bool = False):
    """Add message to current mode's session."""
    st.session_state.chat_sessions[st.session_state.chat_mode].append({
        "role": role, "content": content, "from_db": from_db
    })


# ── Load Previous Chat History ────────────────────────────────────────────────
def load_previous_history():
    """Load chat history from PostgreSQL — restore all 3 modes on login."""
    if not st.session_state.history_loaded:
        previous = get_chat_history()
        if previous:
            for m in previous[-60:]:
                # Use saved mode from database
                mode = m.get("mode", "general")
                if mode not in ("general", "research", "documents"):
                    mode = "general"

                st.session_state.chat_sessions[mode].append({
                    "role":        m["role"],
                    "content":     m["content"],
                    "from_db":     True,
                    "research_id": m.get("research_id"),
                })

        st.session_state.history_loaded = True


# ── Document Search ───────────────────────────────────────────────────────────
def search_user_docs(question: str, user_id: int) -> str:
    """Search uploaded documents via Vector DB (RAG)."""
    try:
        res = requests.post(
            f"{API_BASE}/api/documents/search",
            json={"query": question, "user_id": user_id},
            headers=get_headers(),
        )
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                parts = [
                    f"[{r.get('filename','')} | {r.get('score',0):.0%} match]\n{r.get('content','')[:500]}"
                    for r in results
                ]
                return "\n\n---\n\n".join(parts)
        return ""
    except Exception:
        return ""


def get_current_user_id() -> int:
    """Get current user ID from API."""
    try:
        res = requests.get(f"{API_BASE}/api/auth/me", headers=get_headers())
        if res.status_code == 200:
            return res.json().get("id", 0)
    except Exception:
        pass
    return 0


# ── AI Chat Function ──────────────────────────────────────────────────────────
def chat_with_ai(research_id, messages, question, chat_mode, user_id):
    """
    Send message to AI with context based on chat mode.
    - general:   No extra context
    - research:  Research report context
    - documents: Uploaded documents via RAG
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY is not set in .env file."

    client = OpenAI(api_key=api_key)
    context_used = []

    system_content = (
        "You are a helpful AI research assistant for Cyberify Research Agent. "
        "Answer clearly, concisely, and professionally in English."
    )

    # Add research report context
    if chat_mode == "research" and research_id:
        res = requests.get(
            f"{API_BASE}/api/research/status/{research_id}",
            headers=get_headers()
        )
        if res.status_code == 200:
            report = res.json().get("report", "")
            if report:
                system_content += f"\n\n## Research Report:\n{report[:3000]}"
                context_used.append("Research Report")

    # Add RAG document context
    if chat_mode in ("documents", "research") and user_id:
        doc_context = search_user_docs(question, user_id)
        if doc_context:
            system_content += f"\n\n## Relevant Document Sections:\n{doc_context}"
            context_used.append("Uploaded Documents")

    # Build message history (last 10 only)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in messages[-10:]
        if m["role"] in ("user", "assistant")
    ]
    history.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_content}] + history,
        max_tokens=1000,
    )

    answer = response.choices[0].message.content
    if context_used:
        answer += f"\n\n---\n*Sources used: {' • '.join(context_used)}*"

    return answer


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
        st.switch_page("pages/3_Documents.py")
    if st.button("💬  Chat", use_container_width=True):
        st.rerun()
    st.markdown("---")

    # Clear current mode chat (session + database)
    if st.button("🗑  Clear Current Chat", use_container_width=True):
        # Delete from PostgreSQL
        research_id = st.session_state.chat_research_id if st.session_state.chat_mode == "research" else None
        clear_mode_chat(research_id)
        # Clear from session
        st.session_state.chat_sessions[st.session_state.chat_mode] = []
        st.session_state.input_key += 1
        st.rerun()

    # Clear all chats including DB
    if st.button("🗑  Clear All Chats", use_container_width=True):
        clear_chat_history()  # Delete from PostgreSQL
        st.session_state.chat_sessions = {"general": [], "research": [], "documents": []}
        st.session_state.history_loaded = False
        st.session_state.input_key += 1
        st.success("All chats cleared!")
        st.rerun()

    if st.button("🚪  Sign Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("app.py")


# ── Load Previous History ─────────────────────────────────────────────────────
load_previous_history()

# ── Main Content ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">💬 AI Chat Mode</div>', unsafe_allow_html=True)

left, right = st.columns([2.5, 1], gap="large")
user_id = get_current_user_id()

# ── Right Panel ──
with right:
    # Mode selector tabs
    st.markdown("<div style='font-size:13px; font-weight:600; color:rgba(232,232,240,0.6); margin-bottom:10px;'>Chat Mode</div>", unsafe_allow_html=True)

    mode_options = {
        "💬 General Chat":         "general",
        "📊 Research Report Chat": "research",
        "📄 Documents Chat (RAG)": "documents",
    }
    selected_label = st.selectbox("Mode:", list(mode_options.keys()), label_visibility="collapsed")
    new_mode = mode_options[selected_label]

    if new_mode != st.session_state.chat_mode:
        st.session_state.chat_mode = new_mode
        st.session_state.input_key += 1  # Clear input box
        st.rerun()

    # Mode description
    mode_desc = {
        "general":   "💬 Any question — general AI assistant",
        "research":  "📊 Answers based on your research report",
        "documents": "📄 Answers from uploaded PDF/DOCX/TXT files",
    }
    st.markdown(f"""
    <div style='background:rgba(108,99,255,0.08); border:1px solid rgba(108,99,255,0.2);
                border-radius:10px; padding:10px 12px; margin:8px 0 16px 0;
                font-size:12px; color:rgba(232,232,240,0.6);'>
        {mode_desc[st.session_state.chat_mode]}
    </div>""", unsafe_allow_html=True)

    # Research selector (research mode only)
    if st.session_state.chat_mode == "research":
        history  = get_history()
        completed = [h for h in history if h["status"] == "completed"]
        if completed:
            res_opts = {f"#{h['id']} — {h['query'][:28]}...": h["id"] for h in completed}
            sel      = st.selectbox("Select Research:", list(res_opts.keys()), label_visibility="collapsed")
            st.session_state.chat_research_id = res_opts[sel]
        else:
            st.warning("Complete a research first.")

    # Message count per mode
    counts = {k: len(v) for k, v in st.session_state.chat_sessions.items()}
    st.markdown(f"""
    <div style='font-size:11px; color:rgba(232,232,240,0.3); margin-bottom:16px;'>
        General: {counts['general']} msgs &nbsp;|&nbsp;
        Research: {counts['research']} msgs &nbsp;|&nbsp;
        Docs: {counts['documents']} msgs
    </div>""", unsafe_allow_html=True)

    # Quick questions
    st.markdown("<div style='font-size:13px; font-weight:600; color:rgba(232,232,240,0.6); margin-bottom:8px;'>Quick Questions</div>", unsafe_allow_html=True)
    quick_by_mode = {
        "general":   ["What is AI?", "How does RAG work?", "Explain LangGraph", "What is vector DB?"],
        "research":  ["Summarize findings", "Main risks?", "Recommendations?", "Market trends?"],
        "documents": ["What is in my documents?", "Summarize uploaded files", "Key points", "Important data?"],
    }
    for q in quick_by_mode[st.session_state.chat_mode]:
        if st.button(q, key=f"q_{q}", use_container_width=True):
            st.session_state["pending_q"] = q
            st.rerun()


# ── Left Panel — Chat Window ──────────────────────────────────────────────────
with left:
    current_messages = get_current_messages()

    if not current_messages:
        mode_icons = {"general": "💬", "research": "📊", "documents": "📄"}
        mode_names = {"general": "General Chat", "research": "Research Chat", "documents": "Document Chat"}
        st.markdown(f"""
        <div style='text-align:center; padding:60px 20px; color:rgba(232,232,240,0.3);'>
            <div style='font-size:48px; margin-bottom:12px;'>{mode_icons[st.session_state.chat_mode]}</div>
            <div style='font-family:Space Grotesk; font-size:18px; font-weight:600;
                        color:rgba(232,232,240,0.4); margin-bottom:8px;'>
                {mode_names[st.session_state.chat_mode]}
            </div>
            <div style='font-size:13px;'>Type a message below and press Send</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Show divider if history loaded from DB
        db_messages = [m for m in current_messages if m.get("from_db")]
        new_messages = [m for m in current_messages if not m.get("from_db")]

        if db_messages:
            for msg in db_messages:
                if msg["role"] == "user":
                    st.markdown('<div class="msg-label-user">You</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="msg-label-assistant">🔬 Cyberify AI</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="msg-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

            if new_messages:
                st.markdown('<div class="history-divider">— New conversation —</div>', unsafe_allow_html=True)

        for msg in new_messages:
            if msg["role"] == "user":
                st.markdown('<div class="msg-label-user">You</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="msg-label-assistant">🔬 Cyberify AI</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="msg-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Input area — key changes to clear input after send
    col_in, col_send = st.columns([5, 1])
    with col_in:
        user_input = st.text_input(
            "Message",
            placeholder="Type your message here...",
            label_visibility="collapsed",
            key=f"chat_input_{st.session_state.input_key}",
        )
    with col_send:
        send = st.button("Send →", use_container_width=True)

    # Handle message send
    pending  = st.session_state.pop("pending_q", None)
    question = pending or (user_input if send and user_input.strip() else None)

    if question:
        # Add user message
        add_message("user", question)
        save_chat_message("user", question, st.session_state.chat_research_id, st.session_state.chat_mode)

        # Clear input box
        st.session_state.input_key += 1

        with st.spinner("AI is thinking..."):
            try:
                answer = chat_with_ai(
                    research_id=st.session_state.chat_research_id,
                    messages=get_current_messages(),
                    question=question,
                    chat_mode=st.session_state.chat_mode,
                    user_id=user_id,
                )
                add_message("assistant", answer)
                save_chat_message("assistant", answer, st.session_state.chat_research_id, st.session_state.chat_mode)
            except Exception as e:
                st.error(f"Error: {e}")
        st.rerun()