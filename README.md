# SAI AI Recruiter

AI-assisted recruitment workspace for staffing teams. This repository contains a Supabase-backed recruiter workspace and a separate browser voice-interview gateway MVP.

## Current components

- **Recruiter dashboard:** Streamlit (`app.py`). With Supabase secrets configured, it opens the cloud workspace with email/password sign-in, company workspaces, job and candidate management, and interview-link creation. Without cloud secrets, the earlier SQLite demo remains available.
- **Database:** Supabase PostgreSQL with organization membership, tenant-scoped RLS, jobs, candidates, applications, interview sessions, transcript messages and evaluations.
- **Voice gateway:** FastAPI in `voice-service/`. It validates expiring interview tokens, talks to Ollama, and stores transcript messages in Supabase.
- **Candidate page:** Browser microphone interview with speech recognition and spoken responses.

## Configure the recruiter dashboard

Add these values to Streamlit Community Cloud → App → Settings → Secrets:

```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "YOUR_SUPABASE_PUBLISHABLE_KEY"
VOICE_SERVICE_URL = "https://YOUR_VOICE_SERVICE_HOST"
VOICE_INTERNAL_API_KEY = "A_LONG_RANDOM_SHARED_SECRET"
```

Use the publishable key with Supabase Auth and RLS. Never put a Supabase service-role/secret key in the Streamlit dashboard or browser.

## Deploy the voice gateway separately

Deploy `voice-service/` as a Docker web service on a host that supports persistent WebSockets. Configure these server-side environment variables:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (server-only)
- `VOICE_INTERNAL_API_KEY` (same value as the Streamlit secret)
- `CANDIDATE_INTERVIEW_BASE_URL` (public HTTPS URL of the voice service)
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL` (default: `qwen2.5:3b`)

The voice service needs network access to the Ollama endpoint. A local Ollama process on a personal PC is not reachable from a cloud host unless you deliberately configure secure private networking. Do not expose Ollama publicly without authentication and network restrictions.

See [voice-service/README.md](voice-service/README.md) for local setup and deployment details.

## Speech and privacy notes

The current voice MVP uses the browser Web Speech API for speech recognition and browser speech synthesis for spoken replies. Browser support and speech processing providers vary; this is not yet a fully self-hosted speech pipeline. Raw microphone audio is not uploaded or stored by this app. Spoken answers are converted to text, sent to the voice service, processed by the configured Ollama model, and saved as interview transcript messages.

A strict open-source speech deployment can replace browser speech recognition/synthesis with a self-hosted streaming faster-whisper + Piper pipeline. Candidate notice acknowledgement is required before an interview starts. Recording is off by default.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For the legacy SQLite demo, no Supabase secrets are needed. For the cloud workspace, configure the Supabase values above. For the voice service, follow its own README.

## Production checklist

This is an MVP, not a production hiring platform. Before real candidate onboarding:
- Review and test tenant isolation and all RLS policies with separate company accounts.
- Configure email verification, password reset, rate limits, backups and monitoring.
- Set candidate notice, retention, deletion and data-subject request processes for the jurisdictions where you operate.
- Add robust interview completion, retry, abuse prevention and token revocation workflows.
- Keep AI recommendations explainable and role-related; recruiters must make final decisions.
- Do not commit credentials, resumes, recordings or candidate personal data.

No license has been selected; all rights reserved by default.