from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from supabase import Client, create_client

APP_DIR = Path(__file__).parent
app = FastAPI(title="SAI AI Recruiter Voice Gateway", version="0.1.0")
_supabase: Client | None = None


def db() -> Client:
    global _supabase
    if _supabase is None:
        url = os.environ.get("SUPABASE_URL", "").strip()
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")
        _supabase = create_client(url, key)
    return _supabase


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def load_session(token: str) -> dict[str, Any]:
    if not token or len(token) < 24:
        raise HTTPException(status_code=404, detail="Interview link is invalid or expired")
    response = (
        db().table("interview_sessions")
        .select("id,organization_id,candidate_id,job_id,status,invite_expires_at,recording_enabled")
        .eq("invite_token_hash", token_hash(token))
        .limit(1).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Interview link is invalid or expired")
    session = response.data[0]
    if session["status"] not in ("invited", "ready", "in_progress"):
        raise HTTPException(status_code=410, detail="This interview is no longer available")
    expiry = session.get("invite_expires_at")
    if expiry and datetime.fromisoformat(expiry.replace("Z", "+00:00")) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This interview link has expired")
    return session


def job_context(session: dict[str, Any]) -> str:
    result = (db().table("jobs").select("title,description,required_skills")
              .eq("organization_id", session["organization_id"])
              .eq("id", session["job_id"]).limit(1).execute())
    if not result.data:
        return "Role details are unavailable."
    job = result.data[0]
    return f"Role: {job['title']}\nDescription: {job['description']}\nRequired skills: {', '.join(job.get('required_skills') or [])}"


class InviteRequest(BaseModel):
    organization_id: str
    candidate_id: str
    job_id: str
    expires_in_hours: int = Field(default=168, ge=1, le=720)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sai-ai-recruiter-voice"}


@app.post("/api/invites")
def create_invite(payload: InviteRequest, x_internal_api_key: str | None = Header(default=None, alias="X-Internal-API-Key")) -> dict[str, str]:
    expected = os.environ.get("VOICE_INTERNAL_API_KEY", "")
    if not expected or not x_internal_api_key or not secrets.compare_digest(expected, x_internal_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    raw_token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc).timestamp() + payload.expires_in_hours * 3600
    expires_at = datetime.fromtimestamp(expiry, timezone.utc).isoformat()
    row = {
        "organization_id": payload.organization_id,
        "candidate_id": payload.candidate_id,
        "job_id": payload.job_id,
        "status": "invited",
        "channel": "browser_voice",
        "invite_token_hash": token_hash(raw_token),
        "invite_expires_at": expires_at,
        "recording_enabled": False,
    }
    created = db().table("interview_sessions").insert(row).execute()
    if not created.data:
        raise HTTPException(status_code=500, detail="Could not create interview session")
    base = os.environ.get("CANDIDATE_INTERVIEW_BASE_URL", "").rstrip("/")
    return {"interview_id": created.data[0]["id"], "token": raw_token,
            "url": f"{base}/?token={raw_token}" if base else f"/?token={raw_token}",
            "expires_at": expires_at}


def ask_ollama(prompt: str, context: str) -> str:
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
    system = (
        "You are SAI AI Recruiter, a fair and professional job interviewer. "
        "Ask one job-related question at a time. Do not infer protected traits or "
        "make hiring decisions. Evaluate only role-related evidence. Keep replies concise. "
        "If the candidate has answered, acknowledge briefly and ask the next relevant question. "
        "Never ask for passwords, bank details, government ID numbers, or unrelated sensitive data."
    )
    try:
        response = requests.post(
            f"{base}/api/chat",
            json={"model": model, "stream": False, "messages": [
                {"role": "system", "content": system + "\n\nJob context:\n" + context},
                {"role": "user", "content": prompt},
            ]},
            timeout=90,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"AI model is unavailable: {exc}") from exc


@app.get("/", response_class=HTMLResponse)
def candidate_page() -> str:
    return (APP_DIR / "candidate.html").read_text(encoding="utf-8")


@app.get("/api/interview/{token}")
def interview_info(token: str) -> dict[str, str]:
    session = load_session(token)
    return {"status": session["status"], "channel": "browser_voice"}

@app.post("/api/interview/{token}/notice")
def acknowledge_notice(token: str) -> dict[str, str]:
    session = load_session(token)
    db().table("interview_sessions").update({
        "candidate_notice_version": "v1",
        "candidate_notice_accepted_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", session["id"]).execute()
    return {"status": "acknowledged"}


@app.websocket("/ws/interview/{token}")
async def interview_socket(websocket: WebSocket, token: str) -> None:
    await websocket.accept()
    try:
        session = load_session(token)
        context = job_context(session)
        await websocket.send_json({"type": "ready", "message": "Welcome. Please introduce yourself and tell me briefly about your experience."})
        while True:
            message = await websocket.receive_json()
            if message.get("type") != "candidate_text":
                continue
            text = str(message.get("text", "")).strip()[:6000]
            if not text:
                continue
            if session["status"] != "in_progress":
                db().table("interview_sessions").update({
                    "status": "in_progress", "started_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", session["id"]).execute()
                session["status"] = "in_progress"
            previous = (db().table("interview_messages").select("sequence_no")
                        .eq("interview_session_id", session["id"])
                        .order("sequence_no", desc=True).limit(1).execute()).data
            seq = (previous[0]["sequence_no"] if previous else 0) + 1
            db().table("interview_messages").insert({
                "organization_id": session["organization_id"], "interview_session_id": session["id"],
                "speaker": "candidate", "content": text, "sequence_no": seq,
            }).execute()
            answer = ask_ollama(text, context)
            db().table("interview_messages").insert({
                "organization_id": session["organization_id"], "interview_session_id": session["id"],
                "speaker": "assistant", "content": answer, "sequence_no": seq + 1,
            }).execute()
            await websocket.send_json({"type": "assistant_text", "message": answer})
    except WebSocketDisconnect:
        return
    except HTTPException as exc:
        await websocket.send_json({"type": "error", "message": exc.detail})
        await websocket.close(code=1008)
    except Exception:
        await websocket.send_json({"type": "error", "message": "The interview service encountered an error. Please try again later."})
        await websocket.close(code=1011)
