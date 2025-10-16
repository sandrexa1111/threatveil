# ThreatVeil Sentinel - MVP Bootstrap

Quick start for the minimal backend chat endpoint.

## Prerequisites
- Python 3.11+
- Node 18+ (frontend will be added next)

## Backend (FastAPI) - Chat Endpoint
1. Create environment
```bash
cd backend
python -m venv .venv
. .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env   # Fill in OPENAI_API_KEY
```

2. (Optional) Start Redis for caching
```bash
docker run -p 6379:6379 -d redis:7
```

3. Run server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Test endpoint
```bash
curl -X POST http://localhost:8000/api/v2/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"What are the top vendor risks this week?"}'
```

Expected JSON:
```json
{
  "response": "...",
  "model": "gpt-4o-mini",
  "tokens_used": 123,
  "cached": false
}
```

## Next Steps
- Add lightweight frontend chat widget
- Heuristic risk engine with seeded demo data (done)
- Enable SSE streaming
- Add proper Redis cache and pgvector for RAG
## Demo Data & Heuristic Risk
Two endpoints are available:
```bash
GET  /api/v1/vendors             # list seeded vendors with risk_score and reasons
GET  /api/v1/vendors/{vendor_id} # single vendor details
```
Risk is computed from signals by type, severity, and recency; responses include top reasons for Veil to cite.


## Environment variables
Backend `.env`:
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL_MINI=gpt-4o-mini
OPENAI_MODEL_FULL=gpt-4o
OPENAI_MAX_TOKENS=500
GPT_CACHE_TTL_SECONDS=3600
# Optional Redis
REDIS_URL=redis://localhost:6379/0
```



