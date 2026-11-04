# Architecture

## Current starter
Streamlit is the recruiter-facing UI. SQLite is only for prototype data. Matching is a transparent skill/keyword baseline, not a performance prediction or automated hiring decision. Candidate invitation tokens are random and have a seven-day expiry timestamp; production needs durable storage, access controls and rate limits.

## Target production design
- UI: Streamlit initially; React may replace it for richer UX.
- API: FastAPI for authenticated APIs, candidate links and background jobs.
- Database: PostgreSQL with row-level security and tenant-aware foreign keys.
- Files: private S3-compatible storage, malware scanning and expiring signed URLs.
- Jobs: Redis + Celery/RQ for parsing, AI and notifications.
- LLM: privately hosted Ollama for structured extraction/question drafting, validated for quality and latency.
- Voice: separate FastAPI WebSocket/WebRTC gateway; streaming STT, turn orchestration, LLM and TTS.
- Monitoring: structured logs, request IDs, error monitoring, usage limits and health checks.

## Browser voice flow (future phase)
1. Recruiter creates a job and campaign.
2. Candidate receives an expiring HTTPS link and reads the AI interview notice.
3. Candidate grants microphone permission.
4. Browser audio streams over WebRTC or secure WebSocket to the voice gateway.
5. Streaming STT transcribes speech; the orchestrator selects relevant follow-ups; LLM drafts response; TTS streams it back.
6. Store transcript and structured answers with model/version and notice records.
7. Show explainable job-related evidence to recruiter for human review.

A Streamlit text form or audio upload is not a low-latency full-duplex voice interview.

## Multi-tenancy
Every tenant-owned row must include organization_id. Enforce membership in backend services, not a UI selector. Use PostgreSQL RLS as defense in depth and tenant-aware constraints. Candidate data stays separate per organization unless sharing is explicitly authorized and lawful.

## Fairness and privacy
Do not infer or score protected characteristics or unrelated personal information. Keep evidence tied to job criteria, test for bias, support accommodations, disclose AI assistance and preserve human review/override. Minimize candidate data, give a clear notice, retain only as needed, support applicable access/correction/deletion rights, encrypt sensitive data and avoid recording audio by default.
