from __future__ import annotations
import streamlit as st
from sai_recruiter.config import APP_NAME
from sai_recruiter.database import init_db, seed_demo_data
from sai_recruiter.ui.dashboard import render_dashboard
from sai_recruiter.ui.jobs import render_jobs
from sai_recruiter.ui.candidates import render_candidates
from sai_recruiter.ui.campaigns import render_campaigns
from sai_recruiter.ui.interviews import render_interviews, render_candidate_interview
from sai_recruiter.ui.settings import render_settings

st.set_page_config(page_title=APP_NAME, page_icon="🎙️", layout="wide")
init_db()
seed_demo_data()
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.block-container { padding-top: 1.8rem; padding-bottom: 2.5rem; }
[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,.18); }
.hero { padding:1.35rem 1.5rem; border-radius:18px; background:linear-gradient(120deg,#111827,#263b61); color:white; margin-bottom:1rem; }
.hero h1 { color:white; margin:0 0 .35rem 0; font-size:2rem; }
.hero p { color:#d5deed; margin:0; }
div[data-testid="stMetric"] { background:var(--secondary-background-color); border:1px solid rgba(128,128,128,.16); padding:14px 16px; border-radius:14px; }
</style>
""", unsafe_allow_html=True)
token=st.query_params.get("interview")
if token:
    render_candidate_interview(str(token))
else:
    with st.sidebar:
        st.markdown("## 🎙️ SAI AI Recruiter")
        st.caption("AI-powered recruitment workspace")
        page=st.radio("Workspace",["Overview","Jobs","Candidates","Interview campaigns","Interview responses","Settings"],label_visibility="collapsed")
        st.divider()
        st.caption("Prototype • Browser interview workflow")
        st.caption("No phone calls are placed by this app.")
    if page=="Overview": render_dashboard()
    elif page=="Jobs": render_jobs()
    elif page=="Candidates": render_candidates()
    elif page=="Interview campaigns": render_campaigns()
    elif page=="Interview responses": render_interviews()
    else: render_settings()
st.divider()
st.caption("SAI AI Recruiter • Handle candidate information confidentially and only with appropriate authorization.")
