from __future__ import annotations
import streamlit as st
import pandas as pd
from sai_recruiter.database import get_conn,get_organizations,get_or_create_organization


def active_org_id()->int:
    orgs=get_organizations()
    names=[r["name"] for r in orgs] or ["Demo Staffing"]
    current=st.session_state.get("organization_name",names[0])
    if current not in names:
        current=names[0]
    with st.sidebar:
        choice=st.selectbox("Organization workspace",names,index=names.index(current),key="organization_name")
        with st.expander("Add organization"):
            new=st.text_input("Company name",key="new_org_name")
            if st.button("Create workspace") and new.strip():
                get_or_create_organization(new)
                st.rerun()
    return get_or_create_organization(choice)


def render_dashboard()->None:
    org=active_org_id()
    with get_conn() as conn:
        jobs=conn.execute("SELECT COUNT(*) n FROM jobs WHERE organization_id=?",(org,)).fetchone()["n"]
        people=conn.execute("SELECT COUNT(*) n FROM candidates WHERE organization_id=?",(org,)).fetchone()["n"]
        done=conn.execute("SELECT COUNT(*) n FROM interview_links WHERE organization_id=? AND status='Completed'",(org,)).fetchone()["n"]
        pending=conn.execute("SELECT COUNT(*) n FROM interview_links WHERE organization_id=? AND status='Invited'",(org,)).fetchone()["n"]
        recent=conn.execute("""SELECT c.full_name,j.title,l.status,l.created_at FROM interview_links l JOIN candidates c ON c.id=l.candidate_id AND c.organization_id=l.organization_id JOIN jobs j ON j.id=l.job_id AND j.organization_id=l.organization_id WHERE l.organization_id=? ORDER BY l.id DESC LIMIT 8""",(org,)).fetchall()

    st.markdown("""
    <style>
    .sai-hero{padding:1.5rem 1.7rem;border-radius:18px;background:linear-gradient(120deg,#111827,#263b61);color:white;margin-bottom:1.25rem}
    .sai-hero h1{color:white;margin:0 0 .4rem 0;font-size:2rem}
    .sai-hero p{color:#d5deed;margin:0}
    .sai-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:16px 0 28px}
    .sai-stat{background:var(--secondary-background-color);border:1px solid rgba(128,128,128,.22);border-radius:14px;padding:18px 16px;min-width:0}
    .sai-stat-label{font-size:13px;color:var(--text-color);opacity:.72;margin-bottom:8px}
    .sai-stat-value{font-size:30px;font-weight:700;line-height:1.15;color:var(--text-color)}
    @media(max-width:800px){.sai-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style>
    <section class="sai-hero"><h1>Recruit smarter with SAI AI</h1><p>Manage roles, review candidate evidence, and run structured browser interviews.</p></section>
    """,unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sai-stats">
      <div class="sai-stat"><div class="sai-stat-label">Open roles</div><div class="sai-stat-value">{int(jobs)}</div></div>
      <div class="sai-stat"><div class="sai-stat-label">Candidates</div><div class="sai-stat-value">{int(people)}</div></div>
      <div class="sai-stat"><div class="sai-stat-label">Completed interviews</div><div class="sai-stat-value">{int(done)}</div></div>
      <div class="sai-stat"><div class="sai-stat-label">Pending invitations</div><div class="sai-stat-value">{int(pending)}</div></div>
    </div>
    """,unsafe_allow_html=True)
    st.subheader("Recent interview activity")
    if recent:
        st.dataframe(pd.DataFrame([dict(r) for r in recent]),use_container_width=True,hide_index=True)
    else:
        st.info("No interviews yet. Create a job and add candidates to begin.")
    st.caption("Scores are advisory only. Recruiters make all final decisions.")
