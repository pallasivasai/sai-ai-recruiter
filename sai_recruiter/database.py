from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime,timezone
from typing import Iterator
from sai_recruiter.config import DB_PATH,DEFAULT_ORGANIZATION

def utc_now()->str:
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def get_conn()->Iterator[sqlite3.Connection]:
    conn=sqlite3.connect(DB_PATH,check_same_thread=False)
    conn.row_factory=sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db()->None:
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS organizations(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,organization_id INTEGER NOT NULL,title TEXT NOT NULL,department TEXT DEFAULT '',location TEXT DEFAULT '',employment_type TEXT DEFAULT 'Full-time',description TEXT NOT NULL,required_skills TEXT DEFAULT '',status TEXT NOT NULL DEFAULT 'Open',created_at TEXT NOT NULL,FOREIGN KEY(organization_id) REFERENCES organizations(id));
        CREATE TABLE IF NOT EXISTS candidates(id INTEGER PRIMARY KEY AUTOINCREMENT,organization_id INTEGER NOT NULL,full_name TEXT NOT NULL,email TEXT DEFAULT '',phone TEXT DEFAULT '',location TEXT DEFAULT '',skills TEXT DEFAULT '',experience_years REAL DEFAULT 0,resume_text TEXT DEFAULT '',resume_filename TEXT DEFAULT '',source TEXT DEFAULT 'Manual',consent_status TEXT NOT NULL DEFAULT 'Not recorded',created_at TEXT NOT NULL,FOREIGN KEY(organization_id) REFERENCES organizations(id));
        CREATE INDEX IF NOT EXISTS idx_candidates_org ON candidates(organization_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_org ON jobs(organization_id);
        CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY AUTOINCREMENT,organization_id INTEGER NOT NULL,job_id INTEGER NOT NULL,name TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'Draft',created_at TEXT NOT NULL,FOREIGN KEY(organization_id) REFERENCES organizations(id),FOREIGN KEY(job_id) REFERENCES jobs(id));
        CREATE TABLE IF NOT EXISTS interview_links(id INTEGER PRIMARY KEY AUTOINCREMENT,organization_id INTEGER NOT NULL,campaign_id INTEGER,candidate_id INTEGER NOT NULL,job_id INTEGER NOT NULL,token TEXT NOT NULL UNIQUE,status TEXT NOT NULL DEFAULT 'Invited',expires_at TEXT,created_at TEXT NOT NULL,FOREIGN KEY(organization_id) REFERENCES organizations(id),FOREIGN KEY(campaign_id) REFERENCES campaigns(id),FOREIGN KEY(candidate_id) REFERENCES candidates(id),FOREIGN KEY(job_id) REFERENCES jobs(id));
        CREATE TABLE IF NOT EXISTS interview_responses(id INTEGER PRIMARY KEY AUTOINCREMENT,organization_id INTEGER NOT NULL,interview_link_id INTEGER NOT NULL,question TEXT NOT NULL,answer TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(organization_id) REFERENCES organizations(id),FOREIGN KEY(interview_link_id) REFERENCES interview_links(id));
        CREATE TABLE IF NOT EXISTS evaluations(id INTEGER PRIMARY KEY AUTOINCREMENT,organization_id INTEGER NOT NULL,candidate_id INTEGER NOT NULL,job_id INTEGER NOT NULL,score REAL NOT NULL,evidence TEXT NOT NULL,recommendation TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(organization_id) REFERENCES organizations(id),FOREIGN KEY(candidate_id) REFERENCES candidates(id),FOREIGN KEY(job_id) REFERENCES jobs(id));
        CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,organization_id INTEGER NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,detail TEXT DEFAULT '',created_at TEXT NOT NULL,FOREIGN KEY(organization_id) REFERENCES organizations(id));
        """)
        conn.execute("INSERT OR IGNORE INTO organizations(name,created_at) VALUES(?,?)",(DEFAULT_ORGANIZATION,utc_now()))

def get_organizations():
    with get_conn() as conn: return conn.execute("SELECT * FROM organizations ORDER BY name").fetchall()

def get_or_create_organization(name:str)->int:
    cleaned=name.strip()[:100]
    if not cleaned: raise ValueError("Organization name is required.")
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO organizations(name,created_at) VALUES(?,?)",(cleaned,utc_now()))
        return int(conn.execute("SELECT id FROM organizations WHERE name=?",(cleaned,)).fetchone()["id"])

def log_event(org_id:int,action:str,detail:str="",actor:str="local-user")->None:
    with get_conn() as conn:
        conn.execute("INSERT INTO audit_logs(organization_id,actor,action,detail,created_at) VALUES(?,?,?,?,?)",(org_id,actor,action,detail[:500],utc_now()))

def seed_demo_data()->None:
    with get_conn() as conn:
        org_id=int(conn.execute("SELECT id FROM organizations WHERE name=?",(DEFAULT_ORGANIZATION,)).fetchone()["id"])
        if conn.execute("SELECT COUNT(*) n FROM jobs WHERE organization_id=?",(org_id,)).fetchone()["n"]==0:
            sample=[("Junior SQL Developer","Engineering","Remote - India","Full-time","Build SQL queries, reports, stored procedures and support database operations.","SQL, MySQL, PostgreSQL, Database, Excel"),("Python Developer Intern","Technology","Hybrid","Internship","Assist with Python APIs, data processing, debugging and automated tests.","Python, FastAPI, REST API, Git")]
            for row in sample: conn.execute("""INSERT INTO jobs(organization_id,title,department,location,employment_type,description,required_skills,status,created_at) VALUES(?,?,?,?,?,?,?,'Open',?)""",(org_id,*row,utc_now()))
        if conn.execute("SELECT COUNT(*) n FROM candidates WHERE organization_id=?",(org_id,)).fetchone()["n"]==0:
            demo=[("Ananya Reddy","ananya@example.com","9000000001","Hyderabad","SQL, MySQL, Excel, Python",1.0,"Hands-on projects with SQL, MySQL, Excel and Python."),("Rahul Varma","rahul@example.com","9000000002","Vijayawada","Python, FastAPI, REST API, Git",0.5,"Built Python API projects using FastAPI and Git."),("Meera Kumar","meera@example.com","9000000003","Remote","SQL, PostgreSQL, Power BI",2.0,"Experience with SQL, PostgreSQL and Power BI reporting.")]
            for row in demo: conn.execute("""INSERT INTO candidates(organization_id,full_name,email,phone,location,skills,experience_years,resume_text,source,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",(org_id,*row,"Demo",utc_now()))
