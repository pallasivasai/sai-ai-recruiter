# SAI AI Recruiter

AI-assisted recruitment workspace for staffing teams. This first release is a Streamlit-hostable foundation for jobs, candidate intake, resume/JD matching, browser interview invitations, and recruiter review.

> **Voice status:** This starter includes a candidate interview-link workflow and structured text responses. It does not yet provide production real-time two-way voice streaming. A low-latency voice engine needs a persistent WebSocket/WebRTC service; Streamlit Community Cloud is suitable for the recruiter UI/orchestration layer.

## Included
- Streamlit recruiter dashboard
- Organization-scoped prototype workspace
- Job creation and JD management
- Candidate manual entry and CSV import
- PDF/DOCX/TXT resume text extraction
- Explainable skills/keyword matching baseline
- Candidate interview links and response capture
- Optional Ollama question drafting
- SQLite demo database and audit events

## Deploy on Streamlit Community Cloud
1. Open https://streamlit.io/cloud and sign in with GitHub.
2. Create an app from `pallasivasai/sai-ai-recruiter`, branch `main`, entrypoint `app.py`.
3. Deploy. Use Streamlit Cloud secrets only for optional configuration.
4. Test using demo candidates before connecting real candidate data.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Hosting and production notes
- Streamlit Cloud local files are not durable production storage. SQLite is for demos only. Use managed PostgreSQL and private object storage before handling real candidate records.
- Ollama must run on a separately reachable server; Streamlit Cloud does not bundle local models. Keep it private and authenticated.
- Full-duplex browser voice requires a separate persistent FastAPI WebSocket/WebRTC service. Browser microphone access requires HTTPS and candidate permission.
- Do not commit credentials, resumes, recordings or personal candidate data.
- Provide clear candidate notice, appropriate lawful basis/consent, retention controls and opt-out/deletion workflows.

## Security status
This is an early-stage prototype, not a production-secure multi-tenant SaaS. The organization selector is not an authorization boundary. Before onboarding companies, implement verified authentication, server-side tenant membership checks, PostgreSQL row-level security, tenant-safe constraints, encrypted storage, backups, monitoring and security tests.

## Roadmap
1. Streamlit UI, jobs and candidate intake
2. Authentication and secure tenant isolation
3. Resume parsing and evidence-based matching
4. Browser interview workflow
5. Separate real-time voice service (WebRTC/WebSocket + STT + LLM + TTS)
6. Analytics, billing and production hardening

No license has been selected; all rights reserved by default.
