import requests
import streamlit as st
import os

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def get_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

# ── Auth ──────────────────────────────────────────────────────────────────────

def signup(email, username, password):
    res = requests.post(f"{API_BASE}/api/auth/signup", json={"email": email, "username": username, "password": password})
    return res.json(), res.status_code

def login(email, password):
    res = requests.post(f"{API_BASE}/api/auth/login", data={"username": email, "password": password})
    return res.json(), res.status_code

def get_me():
    res = requests.get(f"{API_BASE}/api/auth/me", headers=get_headers())
    return res.json() if res.status_code == 200 else None

# ── Research ──────────────────────────────────────────────────────────────────

def start_research(query, workspace_id=None):
    payload = {"query": query}
    if workspace_id:
        payload["workspace_id"] = workspace_id
    res = requests.post(f"{API_BASE}/api/research/start", json=payload, headers=get_headers())
    return res.json(), res.status_code

def get_research_status(research_id):
    res = requests.get(f"{API_BASE}/api/research/status/{research_id}", headers=get_headers())
    return res.json() if res.status_code == 200 else None

def get_live_progress(research_id):
    res = requests.get(f"{API_BASE}/api/research/progress/{research_id}", headers=get_headers())
    return res.json() if res.status_code == 200 else None

def get_history():
    res = requests.get(f"{API_BASE}/api/research/history", headers=get_headers())
    return res.json() if res.status_code == 200 else []

def delete_research(research_id):
    res = requests.delete(f"{API_BASE}/api/research/{research_id}", headers=get_headers())
    return res.status_code == 204

# ── Workspaces ────────────────────────────────────────────────────────────────

def get_workspaces():
    res = requests.get(f"{API_BASE}/api/workspaces/", headers=get_headers())
    return res.json() if res.status_code == 200 else []

def create_workspace(name, description=""):
    res = requests.post(f"{API_BASE}/api/workspaces/", json={"name": name, "description": description}, headers=get_headers())
    return res.json(), res.status_code


def delete_workspace(workspace_id: int):
    res = requests.delete(f"{API_BASE}/api/workspaces/{workspace_id}", headers=get_headers())
    return res.status_code == 204


def save_chat_message(role: str, content: str, research_id: int = None, mode: str = "general"):
    """Save chat message to PostgreSQL with mode tracking."""
    try:
        requests.post(
            f"{API_BASE}/api/research/chat/save",
            json={"role": role, "content": content, "research_id": research_id, "mode": mode},
            headers=get_headers(),
        )
    except Exception:
        pass


def get_chat_history():
    """Load previous chat messages from PostgreSQL."""
    res = requests.get(f"{API_BASE}/api/research/chat/history", headers=get_headers())
    return res.json() if res.status_code == 200 else []


def clear_chat_history():
    """Delete all chat messages from PostgreSQL."""
    res = requests.delete(f"{API_BASE}/api/research/chat/clear", headers=get_headers())
    return res.status_code == 204


def clear_mode_chat(research_id: int = None):
    """Delete current mode chat from PostgreSQL."""
    params = {}
    if research_id:
        params["research_id"] = research_id
    res = requests.delete(
        f"{API_BASE}/api/research/chat/clear-mode",
        params=params,
        headers=get_headers(),
    )
    return res.status_code == 204