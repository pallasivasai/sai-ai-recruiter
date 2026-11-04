from __future__ import annotations

import os
import requests
import streamlit as st
from supabase import Client, create_client


def setting(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, os.environ.get(name, default)))
    except Exception:
        return os.environ.get(name, default)


def client_for(access_token: str | None = None, refresh_token: str | None = None) -> Client:
    url = setting("SUPABASE_URL")
    key = setting("SUPABASE_PUBLISHABLE_KEY") or setting("SUPABASE_ANON_KEY")
    if not url or not key:
        st.error("Add SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY to Streamlit Secrets.")
        st.stop()
    client = create_client(url, key)
    if access_token and refresh_token:
        client.auth.set_session(access_token, refresh_token)
    return client


def save_session(session) -> None:
    st.session_state["sb_access_token"] = session.access_token
    st.session_state["sb_refresh_token"] = session.refresh_token
    st.session_state["sb_user_id"] = session.user.id
    st.session_state["sb_email"] = session.user.email


def run() -> None:
    st.set_page_config(page_title="SAI AI Recruiter", page_icon="🎙️", layout="wide")
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
    .block-container{padding-top:2rem;max-width:1200px}
    </style>""", unsafe_allow_html=True)
    st.title("🎙️ SAI AI Recruiter")
    st.caption("Secure recruitment workspace · Supabase connected")

    access = st.session_state.get("sb_access_token")
    refresh = st.session_state.get("sb_refresh_token")
    if not access or not refresh:
        login, signup = st.tabs(["Sign in", "Create company account"])
        with login:
            with st.form("login_form"):
                email = st.text_input("Work email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                try:
                    auth = client_for().auth.sign_in_with_password({"email": email, "password": password})
                    save_session(auth.session)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Sign-in failed: {exc}")
        with signup:
            with st.form("signup_form"):
                name = st.text_input("Your name")
                company = st.text_input("Staffing company name")
                email = st.text_input("Work email", key="signup_email")
                password = st.text_input("Password (minimum 8 characters)", type="password", key="signup_password")
                submitted = st.form_submit_button("Create account", use_container_width=True)
            if submitted:
                if len(password) < 8 or len(company.strip()) < 2:
                    st.error("Enter a company name and a password of at least 8 characters.")
                else:
                    try:
                        auth = client_for().auth.sign_up({"email": email, "password": password,
                            "options": {"data": {"full_name": name}}})
                        if auth.session:
                            save_session(auth.session)
                            sb = client_for(auth.session.access_token, auth.session.refresh_token)
                            sb.rpc("create_organization", {"org_name": company.strip()}).execute()
                            st.success("Account and company created.")
                            st.rerun()
                        else:
                            st.success("Check your email to confirm your account, then sign in. After sign-in, create your company workspace.")
                    except Exception as exc:
                        st.error(f"Account creation failed: {exc}")
        return

    try:
        sb = client_for(access, refresh)
        user = sb.auth.get_user().user
    except Exception:
        st.session_state.pop("sb_access_token", None)
        st.session_state.pop("sb_refresh_token", None)
        st.warning("Your session expired. Please sign in again.")
        st.rerun()
        return

    memberships = sb.table("organization_members").select(
        "organization_id,role,organizations(id,name,slug)"
    ).eq("user_id", user.id).execute().data or []
    if not memberships:
        st.info("Your login is ready. Create your staffing company workspace to begin.")
        with st.form("create_org"):
            company = st.text_input("Company name")
            go = st.form_submit_button("Create workspace")
        if go and company.strip():
            try:
                sb.rpc("create_organization", {"org_name": company.strip()}).execute()
                st.rerun()
            except Exception as exc:
                st.error(f"Could not create workspace: {exc}")
        return

    choices = {m["organizations"]["name"]: m for m in memberships if m.get("organizations")}
    with st.sidebar:
        st.markdown("### SAI AI Recruiter")
        st.caption(user.email or "")
        selected_name = st.selectbox("Company workspace", list(choices))
        if st.button("Sign out", use_container_width=True):
            sb.auth.sign_out()
            for key in ("sb_access_token", "sb_refresh_token", "sb_user_id", "sb_email"):
                st.session_state.pop(key, None)
            st.rerun()
    membership = choices[selected_name]
    org_id = membership["organization_id"]
    role = membership["role"]
    st.subheader(selected_name)
    st.caption(f"Signed in as {role}")
    pages = st.tabs(["Overview", "Jobs", "Candidates", "Interview links"])
    jobs = sb.table("jobs").select("*").eq("organization_id", org_id).order("created_at", desc=True).execute().data or []
    candidates = sb.table("candidates").select("*").eq("organization_id", org_id).order("created_at", desc=True).execute().data or []
    sessions = sb.table("interview_sessions").select("id,status,channel,created_at").eq("organization_id", org_id).order("created_at", desc=True).limit(50).execute().data or []
    with pages[0]:
        a,b,c=st.columns(3)
        a.metric("Open jobs",sum(1 for j in jobs if j["status"]=="open"))
        b.metric("Candidates",len(candidates))
        c.metric("Interview sessions",len(sessions))
        st.markdown("#### Recent jobs")
        st.dataframe([{"Role":j["title"],"Location":j.get("location"),"Status":j["status"]} for j in jobs[:8]],use_container_width=True,hide_index=True)
    with pages[1]:
        st.markdown("#### Create job")
        with st.form("job_create"):
            title=st.text_input("Job title")
            location=st.text_input("Location")
            workplace=st.selectbox("Workplace",["Remote","Hybrid","On-site"])
            description=st.text_area("Job description")
            skills=st.text_input("Required skills (comma-separated)")
            create=st.form_submit_button("Save job")
        if create:
            if not title.strip() or not description.strip():
                st.error("Job title and description are required.")
            else:
                try:
                    sb.table("jobs").insert({"organization_id":org_id,"title":title.strip(),"location":location.strip(),
                        "workplace_type":workplace,"description":description.strip(),
                        "required_skills":[x.strip() for x in skills.split(",") if x.strip()],
                        "status":"open","created_by":user.id}).execute()
                    st.success("Job saved.")
                    st.rerun()
                except Exception as exc: st.error(f"Could not save job: {exc}")
        st.dataframe([{"Role":j["title"],"Location":j.get("location"),"Skills":", ".join(j.get("required_skills") or []),"Status":j["status"]} for j in jobs],use_container_width=True,hide_index=True)
    with pages[2]:
        st.markdown("#### Add candidate")
        with st.form("candidate_create"):
            full_name=st.text_input("Full name")
            email=st.text_input("Email")
            phone=st.text_input("Phone")
            city=st.text_input("Location")
            skill_text=st.text_input("Skills (comma-separated)")
            experience=st.number_input("Experience (years)",min_value=0.0,max_value=60.0,step=0.5)
            create=st.form_submit_button("Save candidate")
        if create:
            if not full_name.strip():
                st.error("Candidate name is required.")
            else:
                try:
                    sb.table("candidates").insert({"organization_id":org_id,"full_name":full_name.strip(),
                        "email":email.strip() or None,"phone":phone.strip() or None,"location":city.strip() or None,
                        "skills":[x.strip() for x in skill_text.split(",") if x.strip()],
                        "experience_years":experience,"created_by":user.id}).execute()
                    st.success("Candidate saved.")
                    st.rerun()
                except Exception as exc: st.error(f"Could not save candidate: {exc}")
        st.dataframe([{"Name":c["full_name"],"Email":c.get("email"),"Location":c.get("location"),"Experience":c.get("experience_years")} for c in candidates],use_container_width=True,hide_index=True)
    with pages[3]:
        st.markdown("#### Create candidate browser interview")
        if not jobs or not candidates:
            st.info("Add at least one job and one candidate first.")
        else:
            job_map={f'{j["title"]} · {j["id"][:8]}':j for j in jobs}
            candidate_map={f'{c["full_name"]} · {c["id"][:8]}':c for c in candidates}
            with st.form("invite_form"):
                chosen_job=st.selectbox("Job",list(job_map))
                chosen_candidate=st.selectbox("Candidate",list(candidate_map))
                days=st.number_input("Link validity (days)",min_value=1,max_value=30,value=7)
                send=st.form_submit_button("Generate interview link")
            if send:
                voice_url=setting("VOICE_SERVICE_URL").rstrip("/")
                internal=setting("VOICE_INTERNAL_API_KEY")
                if not voice_url or not internal:
                    st.error("Configure VOICE_SERVICE_URL and VOICE_INTERNAL_API_KEY in Streamlit Secrets.")
                else:
                    try:
                        response=requests.post(voice_url+"/api/invites",headers={"X-Internal-API-Key":internal},
                            json={"organization_id":org_id,"candidate_id":candidate_map[chosen_candidate]["id"],
                                  "job_id":job_map[chosen_job]["id"],"expires_in_hours":int(days*24)},timeout=20)
                        response.raise_for_status()
                        invite=response.json()
                        st.success("Interview link generated. Share it privately with the candidate.")
                        st.code(invite["url"])
                        st.caption(f"Expires: {invite['expires_at']}")
                    except Exception as exc: st.error(f"Could not create interview link: {exc}")
        st.markdown("#### Recent interview sessions")
        st.dataframe([{"Status":s["status"],"Channel":s["channel"],"Created":s["created_at"]} for s in sessions],use_container_width=True,hide_index=True)
