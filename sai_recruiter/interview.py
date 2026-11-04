from __future__ import annotations
import secrets
from datetime import datetime,timedelta,timezone
from urllib.parse import quote
from sai_recruiter.database import get_conn,utc_now
def create_interview_link(org_id:int,campaign_id:int|None,candidate_id:int,job:dict,base_url:str)->str:
    token=secrets.token_urlsafe(24); expires=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()
    with get_conn() as conn: conn.execute("""INSERT INTO interview_links(organization_id,campaign_id,candidate_id,job_id,token,status,expires_at,created_at) VALUES(?,?,?,?,?,'Invited',?,?)""",(org_id,campaign_id,candidate_id,job["id"],token,expires,utc_now()))
    return f"{base_url.rstrip('/')}/?interview={quote(token)}"
def get_interview_by_token(token:str):
    with get_conn() as conn: return conn.execute("""SELECT l.*,c.full_name,c.email,j.title,j.description,j.required_skills FROM interview_links l JOIN candidates c ON c.id=l.candidate_id AND c.organization_id=l.organization_id JOIN jobs j ON j.id=l.job_id AND j.organization_id=l.organization_id WHERE l.token=?""",(token,)).fetchone()
def save_answers(link_id:int,org_id:int,questions:list[str],answers:list[str])->None:
    with get_conn() as conn:
        for q,a in zip(questions,answers):
            if a.strip(): conn.execute("INSERT INTO interview_responses(organization_id,interview_link_id,question,answer,created_at) VALUES(?,?,?,?,?)",(org_id,link_id,q,a.strip(),utc_now()))
        conn.execute("UPDATE interview_links SET status='Completed' WHERE id=? AND organization_id=?",(link_id,org_id))
