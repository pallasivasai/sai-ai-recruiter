from __future__ import annotations
import streamlit as st
from sai_recruiter.database import get_conn
from sai_recruiter.ui.dashboard import active_org_id
def render_settings()->None:
    org=active_org_id(); st.title("Settings")
    st.write("SQLite is used for this prototype. The organization selector is not secure authentication or tenant isolation.")
    st.subheader("Optional Ollama configuration")
    st.code('OLLAMA_BASE_URL = "https://your-private-model-endpoint"\nOLLAMA_MODEL = "qwen2.5:3b"',language="toml")
    st.warning("Do not expose Ollama directly to the public internet. Use private networking, authentication and TLS.")
    st.subheader("Audit events")
    with get_conn() as conn: rows=conn.execute("SELECT actor,action,detail,created_at FROM audit_logs WHERE organization_id=? ORDER BY id DESC LIMIT 50",(org,)).fetchall()
    if rows:
        import pandas as pd
        st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
    st.subheader("Production checklist")
    st.markdown("- Verified authentication and server-side organization membership\n- PostgreSQL RLS and tenant-safe relationships\n- Private object storage with signed URLs\n- Retention, export and deletion workflows\n- Candidate notice, consent/authorization and opt-out controls\n- Separate WebRTC/WebSocket voice service")
