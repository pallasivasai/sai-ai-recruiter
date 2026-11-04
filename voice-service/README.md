# SAI AI Recruiter Voice Gateway (MVP)

FastAPI service for candidate browser interviews. It validates one-time/expiring interview tokens, stores transcript messages in Supabase, and asks a private Ollama model for the next role-related question.

## Run locally

```bash
cd voice-service
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
# Set environment variables from .env.example in your shell
uvicorn main:app --reload --port 8000
```

The candidate page is at `http://localhost:8000/?token=...`.

## Required server environment

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` — server only; never expose to browser or commit it
- `VOICE_INTERNAL_API_KEY` — protects the invite-creation endpoint
- `OLLAMA_BASE_URL` and `OLLAMA_MODEL`
- `CANDIDATE_INTERVIEW_BASE_URL` — public HTTPS URL of this service

Create an interview invite from a trusted recruiter backend:

```http
POST /api/invites
X-Internal-API-Key: <VOICE_INTERNAL_API_KEY>
Content-Type: application/json

{"organization_id":"...","candidate_id":"...","job_id":"...","expires_in_hours":168}
```

The response contains a raw candidate token and URL. Only its SHA-256 hash is stored in the database. Send the raw URL to the candidate privately.

## Speech and privacy limitations

This MVP uses the browser Web Speech API for speech recognition and browser speech synthesis for spoken replies. Browser support and speech processing providers vary; this is not a fully self-hosted speech pipeline. The app does not upload or persist raw microphone audio. Transcript text is sent to this service, passed to the configured Ollama endpoint, and saved to `interview_messages`.

For a strict open-source, self-hosted speech pipeline, replace browser speech recognition/synthesis with a separately deployed streaming Whisper/faster-whisper + Piper service. Keep candidate notice, retention, access controls and deletion workflows in place before production use.

This is an MVP, not a production hiring decision system. Recruiters must review evidence and make hiring decisions; AI output must not automatically reject candidates.
