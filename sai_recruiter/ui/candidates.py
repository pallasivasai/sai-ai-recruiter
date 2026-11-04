from __future__ import annotations
import streamlit as st,pandas as pd
from sai_recruiter.database import get_conn,log_event,utc_now
from sai_recruiter.resume_parser import extract_resume_text
from sai_recruiter.ui.dashboard import active_org_id
def _insert(org,name,email,phone,location,skills,years,resume,filename,source):
    with get_conn() as conn: conn.execute("""INSERT INTO candidates(organization_id,full_name,email,phone,location,skills,experience_years,resume_text,resume_filename,source,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(org,name.strip(),email.strip(),phone.strip(),location.strip(),skills.strip(),years,resume,filename,source,utc_now()))
    log_event(org,"candidate.created",name)
def render_candidates()->None:
    org=active_org_id(); st.title("Candidates")
    tab1,tab2=st.tabs(["Add candidate","Import CSV"])
    with tab1:
        with st.form("candidate_form"):
            name=st.text_input("Full name"); email=st.text_input("Email"); phone=st.text_input("Phone (optional)"); location=st.text_input("Location")
            skills=st.text_input("Skills (comma-separated)"); years=st.number_input("Experience (years)",min_value=0.0,max_value=60.0,step=0.5)
            resume=st.file_uploader("Resume (PDF, DOCX or TXT)",type=["pdf","docx","txt"])
            ok=st.checkbox("I confirm appropriate candidate notice/authorization is in place.")
            save=st.form_submit_button("Save candidate",type="primary")
        if save:
            if not name.strip(): st.error("Candidate name is required.")
            elif not ok: st.error("Confirm appropriate notice/authorization first.")
            else:
                text=""; filename=""
                if resume:
                    try: text=extract_resume_text(resume.name,resume.getvalue()); filename=resume.name
                    except Exception as exc: st.error(f"Resume read failed: {exc}"); st.stop()
                _insert(org,name,email,phone,location,skills,years,text,filename,"Manual"); st.success("Candidate saved."); st.rerun()
    with tab2:
        st.caption("CSV columns: full_name (required), email, phone, location, skills, experience_years.")
        sample=pd.DataFrame([{"full_name":"Candidate Example","email":"candidate@example.com","phone":"","location":"Remote","skills":"SQL, Python","experience_years":1}])
        st.download_button("Download CSV template",sample.to_csv(index=False),"candidate_import_template.csv","text/csv")
        upload=st.file_uploader("Upload candidate CSV",type=["csv"],key="csv_upload")
        ok=st.checkbox("I confirm imported candidate details may be processed for this recruitment purpose.",key="csv_ok")
        if upload and ok and st.button("Import candidates"):
            try:
                df=pd.read_csv(upload).fillna("")
                if "full_name" not in df.columns: st.error("CSV must contain full_name.")
                else:
                    count=0
                    for _,r in df.iterrows():
                        if str(r.get("full_name","")).strip():
                            _insert(org,str(r.get("full_name","")),str(r.get("email","")),str(r.get("phone","")),str(r.get("location","")),str(r.get("skills","")),float(r.get("experience_years") or 0),"","","CSV import"); count+=1
                    st.success(f"Imported {count} candidates."); st.rerun()
            except Exception as exc: st.error(f"CSV import failed: {exc}")
    with get_conn() as conn: rows=conn.execute("SELECT id,full_name,email,phone,location,skills,experience_years,source,consent_status,created_at FROM candidates WHERE organization_id=? ORDER BY id DESC",(org,)).fetchall()
    st.subheader("Candidate directory")
    if rows: st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
    else: st.info("No candidates yet.")
