# Streamlit Community Cloud deployment

1. Sign in at https://streamlit.io/cloud.
2. Create app from repository `pallasivasai/sai-ai-recruiter`.
3. Branch: `main`; main file: `app.py`.
4. Deploy and test using demo candidates.

## Limitations
- Streamlit Cloud local files are not durable storage. SQLite/uploads may not survive restarts or redeploys; use managed PostgreSQL and private object storage for real candidate data.
- Streamlit Cloud does not provide persistent low-latency bidirectional audio transport. Host the voice gateway separately where persistent WebSocket/WebRTC connections are supported.
- Candidate links currently collect typed responses, not live voice.
- Secrets belong in Streamlit Cloud Advanced settings or an untracked local secrets file, never in Git.

Optional secrets: OLLAMA_BASE_URL and OLLAMA_MODEL. DATABASE_URL is reserved for a future PostgreSQL adapter and is not wired into this starter.
