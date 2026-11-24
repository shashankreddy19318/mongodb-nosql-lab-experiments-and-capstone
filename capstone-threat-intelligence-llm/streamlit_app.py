"""
streamlit_app.py
Streamlit Chat Frontend for Threat Intelligence LLM/SLM Platform.
Extends Appendix A with:
- Target platform filter (Windows, Linux, MacOS, Android, iOS, Cloud)
- Threat lifecycle status filter (Anticipated, Active, Evolving, Resolved)
- Conversational mitigation approval loops
- Background Vulnerability Scanner Bot controls
- Exercises 1 - 18 demonstration runner
"""

import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Threat Intelligence LLM/SLM Chat",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Cyber Threat Intelligence - LLM/SLM Chat Application")
st.caption("Powered by MongoDB RAG Vector Search • Multi-Platform Mitigation Decision Engine")

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "st-session-" + str(hash(st.session_state))
if "pending_vuln" not in st.session_state:
    st.session_state.pending_vuln = None

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Target Platform & Filters")
    platform = st.selectbox(
        "Platform Filter:",
        ["All", "Windows", "Linux", "MacOS", "Android", "iOS", "Cloud"]
    )
    lifecycle = st.selectbox(
        "Threat Lifecycle:",
        ["All", "Anticipated", "Active", "Evolving", "Resolved"]
    )
    top_k = st.slider("Vector Retrieval Top-K", 1, 6, 3)

    st.markdown("---")
    st.subheader("🤖 Vulnerability Scanner Bot")
    scan_platform = st.selectbox("Scan Target:", ["Windows", "Linux", "MacOS", "Android", "iOS", "Cloud"])
    if st.button("🔍 Run Vulnerability Scan"):
        with st.spinner("Scanning target configuration and CVE database..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/bot/scan",
                    json={"platform": scan_platform, "scope": "system"},
                    timeout=10
                )
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Scan complete: Found {data['detected_count']} vulnerability.")
                    if data["vulnerabilities"]:
                        st.session_state.pending_vuln = data["vulnerabilities"][0]
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["conversational_alert"]
                        })
            except Exception as e:
                st.error(f"Scan request failed: {e}")

    if st.session_state.pending_vuln:
        v = st.session_state.pending_vuln
        st.warning(f"Pending Mitigation: {v['title']}")
        if st.button("⚡ Confirm & Execute Mitigation"):
            try:
                c_res = requests.post(
                    f"{BACKEND_URL}/bot/confirm-mitigation",
                    json={"vuln_id": v["vuln_id"], "operator": "StreamlitUser"},
                    timeout=10
                )
                if c_res.status_code == 200:
                    st.success("Mitigation executed! State: Resolved.")
                    st.session_state.pending_vuln = None
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"### [BOT] Mitigation Confirmed\n\nRemediation applied for `{v['vuln_id']}`. State transitioned to **Resolved**."
                    })
                    st.rerun()
            except Exception as e:
                st.error(f"Confirmation failed: {e}")

    st.markdown("---")
    st.subheader("🔬 Exercises 1 - 18 Suite")
    if st.button("▶ Run All 18 Exercises"):
        with st.spinner("Running exercises 1-18 over Threat Intelligence MongoDB collection..."):
            try:
                ex_res = requests.get(f"{BACKEND_URL}/exercises/run-all", timeout=30).json()
                st.success(f"Passed: {ex_res['passed']}/{ex_res['total_exercises']}")
                st.json(ex_res)
            except Exception as e:
                st.error(f"Exercises run error: {e}")

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.pending_vuln = None
        st.rerun()

# Health Check Header
try:
    health = requests.get(f"{BACKEND_URL}/health", timeout=3).json()
    st.sidebar.success(f"Backend: {health['status'].upper()} ({health['db_mode']})")
except Exception:
    st.sidebar.error("Backend not reachable (run uvicorn app.chat_api:app)")

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Retrieved Context Sources ({len(msg['sources'])})"):
                for s in msg["sources"]:
                    st.markdown(f"- **[{s['platform']}] {s['title']}** (Score: `{s['score']}`)")
                    st.caption(f"{s['text'][:150]}...")

# Chat Input & RAG Execution
if prompt := st.chat_input("Ask about threats, CVEs, or mitigation procedures..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing threat intelligence and retrieving playbooks..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "message": prompt,
                        "platform": platform,
                        "top_k": top_k
                    },
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                st.markdown(data["response"])

                if data.get("sources"):
                    with st.expander(f"📚 Retrieved Context Sources ({len(data['sources'])})"):
                        for s in data["sources"]:
                            st.markdown(f"- **[{s['platform']}] {s['title']}** (Score: `{s['score']}`)")
                            st.caption(f"{s['text'][:150]}...")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["response"],
                    "sources": data.get("sources", [])
                })
            except Exception as e:
                err_msg = f"Error communicating with backend: {e}"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
