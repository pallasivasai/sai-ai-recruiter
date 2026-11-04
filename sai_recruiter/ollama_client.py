from __future__ import annotations
import os,requests
def _setting(name:str,default:str="")->str:
    try:
        import streamlit as st; value=st.secrets.get(name,default)
    except Exception: value=os.getenv(name,default)
    return str(value or default)
def ollama_generate(prompt:str,timeout:int=90)->str:
    base=_setting("OLLAMA_BASE_URL").rstrip("/"); model=_setting("OLLAMA_MODEL","qwen2.5:3b")
    if not base: raise RuntimeError("OLLAMA_BASE_URL is not configured.")
    response=requests.post(f"{base}/api/generate",json={"model":model,"prompt":prompt,"stream":False},timeout=timeout)
    response.raise_for_status(); return str(response.json().get("response","")).strip()
def draft_job_questions(job_title:str,job_description:str)->str:
    prompt=("Create 6 fair, job-related screening questions. Avoid age, religion, caste, disability, marital status and unrelated personal traits. Return numbered questions only.\n\n"+f"Role: {job_title}\nJob description:\n{job_description}")
    return ollama_generate(prompt)
