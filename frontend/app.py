import streamlit as st
from api_client import login, signup, get_me

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cyberify Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Reset & Base */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

/* ── Auth Page Layout ── */
.auth-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #0F0F1A 0%, #1A1A2E 50%, #16213E 100%);
}

.auth-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 20px;
    padding: 48px;
    width: 100%;
    max-width: 440px;
    backdrop-filter: blur(20px);
    box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 0 1px rgba(108,99,255,0.1);
}

.auth-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #6C63FF;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
}

.auth-tagline {
    font-size: 13px;
    color: rgba(232,232,240,0.5);
    margin-bottom: 36px;
    letter-spacing: 0.3px;
}

.auth-heading {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px;
    font-weight: 600;
    color: #E8E8F0;
    margin-bottom: 24px;
}

/* Input fields */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #E8E8F0 !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6C63FF !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
}
.stTextInput label {
    color: rgba(232,232,240,0.7) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    margin-bottom: 6px !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.2s !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(108,99,255,0.4) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: rgba(232,232,240,0.6) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6) !important;
    color: white !important;
}

/* Alerts */
.stAlert {
    border-radius: 10px !important;
    font-size: 13px !important;
}

/* Divider text */
.divider-text {
    text-align: center;
    color: rgba(232,232,240,0.3);
    font-size: 12px;
    margin: 16px 0;
    position: relative;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "auth"


# ── Auth Check ────────────────────────────────────────────────────────────────
def check_auth():
    if st.session_state.token:
        user = get_me()
        if user:
            st.session_state.user = user
            return True
    return False


# ── Auth Page ─────────────────────────────────────────────────────────────────
def show_auth_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Logo
        st.markdown("""
        <div style='text-align:center; padding: 40px 0 10px 0;'>
            <div style='font-family: Space Grotesk, sans-serif; font-size: 32px; font-weight: 700;
                        background: linear-gradient(135deg, #6C63FF, #A78BFA); -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent; margin-bottom: 6px;'>
                🔬 Cyberify
            </div>
            <div style='font-size: 13px; color: rgba(232,232,240,0.45); letter-spacing: 1px;
                        text-transform: uppercase; margin-bottom: 40px;'>
                Autonomous Research Agent
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card container
        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

            # ── Login Tab ──
            with tab_login:
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                email = st.text_input("Email address", key="login_email",
                                      placeholder="you@example.com")
                password = st.text_input("Password", type="password", key="login_pass",
                                         placeholder="Enter your password")
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                if st.button("Sign In →", key="login_btn"):
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    else:
                        with st.spinner("Signing in..."):
                            data, status = login(email, password)
                        if status == 200:
                            st.session_state.token = data["access_token"]
                            st.success("Welcome back! ✨")
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

            # ── Signup Tab ──
            with tab_signup:
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                new_email    = st.text_input("Email address", key="signup_email",
                                             placeholder="you@example.com")
                new_username = st.text_input("Username", key="signup_user",
                                             placeholder="Choose a username")
                new_pass     = st.text_input("Password", type="password", key="signup_pass",
                                             placeholder="Min. 8 characters")
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                if st.button("Create Account →", key="signup_btn"):
                    if not new_email or not new_username or not new_pass:
                        st.error("Please fill in all fields.")
                    elif len(new_pass) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        with st.spinner("Creating account..."):
                            data, status = signup(new_email, new_username, new_pass)
                        if status == 201:
                            st.success("Account created! Please sign in.")
                        else:
                            msg = data.get("detail", "Something went wrong.")
                            st.error(msg)

        # Footer
        st.markdown("""
        <div style='text-align:center; margin-top:24px; font-size:11px;
                    color: rgba(232,232,240,0.2);'>
            Cyberify Research Agent • AI Engineer Assessment
        </div>
        """, unsafe_allow_html=True)


# ── Main Router ───────────────────────────────────────────────────────────────
if check_auth():
    # Logged in — redirect to dashboard
    st.switch_page("pages/1_Dashboard.py")
else:
    show_auth_page()