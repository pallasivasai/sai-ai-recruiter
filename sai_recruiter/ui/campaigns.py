from __future__ import annotations
import streamlit as st,pandas as pd
from sai_recruiter.database import get_conn,log_event,utc_now
from sai_recruiter.interview import create_interview_link
from sai_recruiter.matching import evaluate_candidate
from sai_recruiter.ui.dashboard import active_org_id
def render_campaigns()->None:
    org=active_org_id(); st.title("Interview campaigns")
    st.info("This starter creates browser interview links. It does not place mobile calls or provide live voice streaming yet.")
    with get_conn() as conn:
        jobs=conn.execute("SELECT * FROM jobs WHERE organization_id=? AND status='Open' ORDER BY title",(org,)).fetchall()
        people=conn.execute("SELECT * FROM candidates WHERE organization_id=? ORDER BY full_name",(org,)).fetchall()
    if not jobs or not people: st.warning("Add an open job and at least one candidate first."); return
    jm={f'{j["title"]} (#{j["id"]})':dict(j) for j in jobs}; cm={f'{c["full_name"]} — {c["email"] or "no email"} (#{c["id"]})':dict(c) for c in people}
    with st.form("campaign_form"):
        name=st.text_input("Campaign name"); job=jm[st.selectbox("Job",list(jm))]; selected=st.multiselect("Candidates",list(cm))
        base=st.text_input("Deployed HTTPS app URL",placeholder="https://your-app.streamlit.app")
        create=st.form_submit_button("Create interview links",type="primary")
    if create:
        if not name.strip() or not selected or not base.startswith("https://"): st.error("Enter campaign, candidates and deployed HTTPS URL.")
        else:
            with get_conn() as conn:
                cur=conn.execute("INSERT INTO campaigns(organization_id,job_id,name,status,created_at) VALUES(?,?,?,'Active',?)",(org,job["id"],name,utc_now())); campaign_id=int(cur.lastrowid)
            links=[]
            for label in selected:
                person=cm[label]; url=create_interview_link(org,campaign_id,person["id"],job,base); score=evaluate_candidate(job,person)
                with get_conn() as conn: conn.execute("INSERT INTO evaluations(organization_id,candidate_id,job_id,score,evidence,recommendation,created_at) VALUES(?,?,?,?,?,?,?)",(org,person["id"],job["id"],score["score"],str(score["evidence"]),score["recommendation"],utc_now()))
                links.append({"Candidate":person["full_name"],"Interview link":url,"Baseline match":score["score"],"Review":score["recommendation"]})
            log_event(org,"campaign.created",name); st.session_state["new_campaign_links"]=links; st.success("Links created. Share only with intended candidates.")
    if st.session_state.get("new_campaign_links"):
        data=pd.DataFrame(st.session_state["new_campaign_links"]); st.subheader("New invitations"); st.dataframe(data,use_container_width=True,hide_index=True)
        st.download_button("Download invitation links CSV",data.to_csv(index=False),"interview_invitations.csv","text/csv")
    with get_conn() as conn: rows=conn.execute("""SELECT c.name campaign,j.title job,c.status,COUNT(l.id) invitations,SUM(CASE WHEN l.status='Completed' THEN 1 ELSE 0 END) completed FROM campaigns c JOIN jobs j ON j.id=c.job_id AND j.organization_id=c.organization_id LEFT JOIN interview_links l ON l.campaign_id=c.id AND l.organization_id=c.organization_id WHERE c.organization_id=? GROUP BY c.id ORDER BY c.id DESC""",(org,)).fetchall()
    st.subheader("Campaign history")
    if rows: st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
