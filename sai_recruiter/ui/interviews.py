from __future__ import annotations
import streamlit as st,pandas as pd
from sai_recruiter.database import get_conn
from sai_recruiter.interview import get_interview_by_token,save_answers
from sai_recruiter.matching import generate_screening_questions
from sai_recruiter.ui.dashboard import active_org_id
def render_candidate_interview(token:str)->None:
    link=get_interview_by_token(token)
    if not link: st.error("Interview link is invalid."); return
    st.title("SAI AI Recruiter — Candidate Interview")
    st.write(f"Hello {link['full_name']}. You are invited to a screening for **{link['title']}**.")
    st.warning("This initial version is a text-response form, not a live AI voice conversation. Your answers are shared with the recruiting organization for this hiring process.")
    st.write("Please do not include sensitive personal information unrelated to the job.")
    if link["status"]=="Completed": st.success("This interview was already submitted."); return
    questions=generate_screening_questions(dict(link))
    with st.form("candidate_interview"):
        notice=st.checkbox("I understand how my answers will be used for this recruitment process.")
        answers=[st.text_area(q,key=f"candidate_answer_{i}") for i,q in enumerate(questions)]
        submit=st.form_submit_button("Submit interview",type="primary")
    if submit:
        if not notice: st.error("Please acknowledge the notice."); return
        if not any(a.strip() for a in answers): st.error("Answer at least one question."); return
        save_answers(link["id"],link["organization_id"],questions,answers); st.success("Responses submitted. Thank you.")
def render_interviews()->None:
    org=active_org_id(); st.title("Interview responses")
    with get_conn() as conn:
        links=conn.execute("""SELECT l.id,c.full_name candidate,j.title job,l.status,l.created_at,COUNT(r.id) answer_count FROM interview_links l JOIN candidates c ON c.id=l.candidate_id AND c.organization_id=l.organization_id JOIN jobs j ON j.id=l.job_id AND j.organization_id=l.organization_id LEFT JOIN interview_responses r ON r.interview_link_id=l.id AND r.organization_id=l.organization_id WHERE l.organization_id=? GROUP BY l.id ORDER BY l.id DESC""",(org,)).fetchall()
        answers=conn.execute("""SELECT c.full_name,j.title,r.question,r.answer,r.created_at FROM interview_responses r JOIN interview_links l ON l.id=r.interview_link_id AND l.organization_id=r.organization_id JOIN candidates c ON c.id=l.candidate_id AND c.organization_id=l.organization_id JOIN jobs j ON j.id=l.job_id AND j.organization_id=l.organization_id WHERE r.organization_id=? ORDER BY r.id DESC""",(org,)).fetchall()
        scores=conn.execute("""SELECT c.full_name,j.title,e.score,e.recommendation,e.evidence,e.created_at FROM evaluations e JOIN candidates c ON c.id=e.candidate_id AND c.organization_id=e.organization_id JOIN jobs j ON j.id=e.job_id AND j.organization_id=e.organization_id WHERE e.organization_id=? ORDER BY e.score DESC""",(org,)).fetchall()
    st.subheader("Invitation status")
    if links: st.dataframe(pd.DataFrame([dict(r) for r in links]),use_container_width=True,hide_index=True)
    else: st.info("No invitations yet.")
    st.subheader("Submitted answers")
    if answers: st.dataframe(pd.DataFrame([dict(r) for r in answers]),use_container_width=True,hide_index=True)
    else: st.info("No answers yet.")
    st.subheader("Baseline matching review")
    if scores: st.dataframe(pd.DataFrame([dict(r) for r in scores]),use_container_width=True,hide_index=True)
