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

2. Run server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Test endpoint
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
- Introduce heuristic risk engine and seeded demo data
- Enable SSE streaming
- Add proper Redis cache and pgvector for RAG



