from __future__ import annotations
import streamlit as st
import pandas as pd
from sai_recruiter.database import get_conn,get_organizations,get_or_create_organization
def active_org_id()->int:
    orgs=get_organizations(); names=[r["name"] for r in orgs] or ["Demo Staffing"]
    current=st.session_state.get("organization_name",names[0])
    if current not in names: current=names[0]
    with st.sidebar:
        choice=st.selectbox("Organization workspace",names,index=names.index(current),key="organization_name")
        with st.expander("Add organization"):
            new=st.text_input("Company name",key="new_org_name")
            if st.button("Create workspace") and new.strip(): get_or_create_organization(new); st.rerun()
    return get_or_create_organization(choice)
def render_dashboard()->None:
    org=active_org_id()
    with get_conn() as conn:
        jobs=conn.execute("SELECT COUNT(*) n FROM jobs WHERE organization_id=?",(org,)).fetchone()["n"]
        people=conn.execute("SELECT COUNT(*) n FROM candidates WHERE organization_id=?",(org,)).fetchone()["n"]
        done=conn.execute("SELECT COUNT(*) n FROM interview_links WHERE organization_id=? AND status='Completed'",(org,)).fetchone()["n"]
        pending=conn.execute("SELECT COUNT(*) n FROM interview_links WHERE organization_id=? AND status='Invited'",(org,)).fetchone()["n"]
        recent=conn.execute("""SELECT c.full_name,j.title,l.status,l.created_at FROM interview_links l JOIN candidates c ON c.id=l.candidate_id AND c.organization_id=l.organization_id JOIN jobs j ON j.id=l.job_id AND j.organization_id=l.organization_id WHERE l.organization_id=? ORDER BY l.id DESC LIMIT 8""",(org,)).fetchall()
    st.markdown('<div class="hero"><h1>Recruit smarter with SAI AI</h1><p>Manage roles, review candidate evidence, and run structured browser interviews.</p></div>',unsafe_allow_html=True)
    a,b,c,d=st.columns(4); a.metric("Open roles",jobs); b.metric("Candidates",people); c.metric("Completed interviews",done); d.metric("Pending invitations",pending)
    st.subheader("Recent interview activity")
    if recent: st.dataframe(pd.DataFrame([dict(r) for r in recent]),use_container_width=True,hide_index=True)
    else: st.info("No interviews yet. Create a job and add candidates to begin.")
    st.caption("Scores are advisory only. Recruiters make all final decisions.")
