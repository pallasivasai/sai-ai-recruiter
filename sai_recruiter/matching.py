from __future__ import annotations
import re
STOPWORDS={"and","the","for","with","you","are","will","have","has","this","that","from","your","our","not","but","job","role","work","years","year","candidate","experience","required","preferred","using","use","ability","knowledge","skills","skill","good","strong","team"}
def tokens(text:str)->set[str]:
    words=re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{1,}",(text or "").lower())
    return {w for w in words if w not in STOPWORDS}
def evaluate_candidate(job:dict,candidate:dict)->dict:
    required=[s.strip().lower() for s in (job.get("required_skills") or "").split(",") if s.strip()]
    profile=" ".join([candidate.get("skills") or "",candidate.get("resume_text") or ""]).lower()
    matched=[s for s in required if s in profile]; missing=[s for s in required if s not in profile]
    job_terms=tokens((job.get("description") or "")+" "+(job.get("title") or "")); overlap=job_terms & tokens(profile)
    term_ratio=len(overlap)/max(1,len(job_terms)); skill_ratio=len(matched)/max(1,len(required))
    score=round(min(100,75*skill_ratio+25*min(1,term_ratio*2)),1)
    recommendation="Strong match — recruiter review" if score>=75 else "Potential match — review gaps" if score>=45 else "Low evidence match — review manually"
    return {"score":score,"recommendation":recommendation,"evidence":{"matched_skills":matched,"missing_skills":missing,"overlapping_job_terms":sorted(overlap)[:20],"note":"Keyword evidence only; not a validated prediction of job performance."}}
def generate_screening_questions(job:dict)->list[str]:
    skills=[s.strip() for s in (job.get("required_skills") or "").split(",") if s.strip()]
    qs=[f"Could you briefly describe your relevant experience for the {job.get('title','position')} role?","Tell me about a recent project where you used a relevant technology for this role.","What was a difficult problem you faced, and how did you solve it?"]
    qs.extend([f"Can you describe a practical task you have completed using {s}?" for s in skills[:3]])
    qs.append("What is your availability and preferred work arrangement?")
    return qs
