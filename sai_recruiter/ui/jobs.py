from __future__ import annotations
import streamlit as st,pandas as pd
from sai_recruiter.database import get_conn,log_event,utc_now
from sai_recruiter.ui.dashboard import active_org_id
from sai_recruiter.matching import generate_screening_questions
from sai_recruiter.ollama_client import draft_job_questions
def render_jobs()->None:
    org=active_org_id(); st.title("Jobs")
    with st.expander("＋ Create a job"):
        with st.form("create_job_form"):
            title=st.text_input("Job title"); dept=st.text_input("Department"); loc=st.text_input("Location",value="Remote")
            typ=st.selectbox("Employment type",["Full-time","Contract","Part-time","Internship"])
            skills=st.text_input("Required skills (comma-separated)"); desc=st.text_area("Job description",height=180)
            submit=st.form_submit_button("Save job",type="primary")
        if submit:
            if not title.strip() or not desc.strip(): st.error("Job title and description are required.")
            else:
                with get_conn() as conn: conn.execute("""INSERT INTO jobs(organization_id,title,department,location,employment_type,description,required_skills,status,created_at) VALUES(?,?,?,?,?,?,?,'Open',?)""",(org,title.strip(),dept,loc,typ,desc,skills,utc_now()))
                log_event(org,"job.created",title); st.success("Job created."); st.rerun()
    with get_conn() as conn: rows=conn.execute("SELECT * FROM jobs WHERE organization_id=? ORDER BY id DESC",(org,)).fetchall()
    if not rows: st.info("Create your first job."); return
    st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
    opts={f'{r["title"]} (#{r["id"]})':dict(r) for r in rows}; job=opts[st.selectbox("Generate questions for",list(opts))]
    left,right=st.columns(2)
    if left.button("Generate starter questions"): st.session_state["job_questions"]=generate_screening_questions(job)
    if right.button("Draft using Ollama"):
        try: st.session_state["ollama_questions"]=draft_job_questions(job["title"],job["description"])
        except Exception as exc: st.warning(f"Ollama unavailable: {exc}")
    for i,q in enumerate(st.session_state.get("job_questions",[]),1): st.write(f"{i}. {q}")
    if st.session_state.get("ollama_questions"): st.write(st.session_state["ollama_questions"])
