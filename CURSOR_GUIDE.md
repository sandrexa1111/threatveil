# ThreatVeil Sentinel - Master Development Prompt for Cursor

## Project Context

You are helping build **ThreatVeil Sentinel**, an AI-native cybersecurity vendor risk intelligence platform. This is a solo-founder MVP focused on speed, cost-efficiency, and future scalability.

---

## Core Mission

Build a platform that:
1. **Predicts vendor compromise** using public threat signals and ML models
2. **Provides conversational AI security analysis** via "Veil AI" (GPT-powered chatbot)
3. **Visualizes global threats** on an interactive 3D globe
4. **Delivers plain-English remediation** that SMBs and startups can actually use
5. **Offers developer API wrapper** for embedding threat intelligence in other products

---

## Tech Stack

### Frontend
- **Framework:** Next.js 14+ (App Router) with TypeScript
- **Styling:** Tailwind CSS
- **State:** React hooks (useState, useContext) + TanStack Query for server state
- **Map Viz:** Globe.gl (three.js) for 3D globe OR Mapbox GL for 2D
- **UI Components:** shadcn/ui for consistent design system
- **Chat UI:** Custom with SSE streaming support

### Backend
- **Framework:** FastAPI (Python 3.11+) with async/await
- **Database:** PostgreSQL 15+ with SQLAlchemy ORM
- **Vector Store:** Pinecone (for RAG) or pgvector extension
- **Cache:** Redis for sessions and response caching
- **Message Queue:** Celery with Redis broker (for background jobs)
- **Auth:** Clerk or Supabase Auth
- **API Docs:** Auto-generated with FastAPI (OpenAPI/Swagger)

### AI/ML
- **LLM:** OpenAI GPT-4o and GPT-4o-mini (tiered selection)
- **ML Models:** LightGBM/XGBoost for risk prediction
- **Embeddings:** OpenAI text-embedding-3-small
- **NLP:** HuggingFace transformers for signal classification

### Infrastructure
- **Hosting:** Vercel (frontend) + Render/Railway (backend)
- **Storage:** AWS S3 for raw feeds
- **Monitoring:** Sentry (errors) + simple cost dashboard
- **CI/CD:** GitHub Actions

---

## Code Style & Standards

### General Principles
- **Write production-ready code from day 1** - no "TODO: implement later" stubs
- **Prioritize readability over cleverness** - clear > compact
- **Error handling is mandatory** - every external API call must have try/catch
- **Type everything** - TypeScript in frontend, type hints in Python
- **Document WHY not WHAT** - comments explain decisions, not syntax

### Python (Backend)
```python
# Good patterns to follow:

# 1. Async by default for I/O operations
async def fetch_signals(vendor_id: str) -> List[Signal]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/signals/{vendor_id}")
        return [Signal(**item) for item in response.json()]

# 2. Pydantic models for validation
from pydantic import BaseModel, Field

class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    domain: str = Field(..., regex=r'^[a-z0-9\-\.]+$')
    industry: Optional[str] = None

# 3. Dependency injection for database sessions
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db)
) -> Vendor:
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    return result.scalar_one_or_none()

# 4. Structured logging
import structlog
logger = structlog.get_logger()

logger.info("vendor_created", vendor_id=vendor.id, domain=vendor.domain)
```

### TypeScript (Frontend)
```typescript
// Good patterns to follow:

// 1. Explicit types for props
interface VendorCardProps {
  vendor: {
    id: string;
    name: string;
    riskScore: number;
  };
  onSelect: (id: string) => void;
}

// 2. Custom hooks for reusable logic
function useVendorRisk(vendorId: string) {
  return useQuery({
    queryKey: ['vendor-risk', vendorId],
    queryFn: () => fetchVendorRisk(vendorId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// 3. Server actions for mutations (Next.js 14+)
'use server';

export async function createVendor(formData: FormData) {
  const name = formData.get('name') as string;
  // Validate, then API call
  return await apiClient.post('/vendors', { name });
}

// 4. Error boundaries for resilience
'use client';

export default function ErrorBoundary({ error }: { error: Error }) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded">
      <h2>Something went wrong</h2>
      <pre>{error.message}</pre>
    </div>
  );
}
```

---

## Architecture Patterns

### 1. Separation of Concerns

```
frontend/
├── app/                    # Next.js app router
│   ├── (auth)/            # Auth-protected routes
│   ├── (marketing)/       # Public pages
│   └── api/               # API routes (thin layer)
├── components/
│   ├── ui/                # shadcn/ui primitives
│   ├── features/          # Feature-specific components
│   │   ├── chat/         # Veil AI chat components
│   │   ├── globe/        # Threat globe visualization
│   │   └── vendors/      # Vendor management
│   └── layouts/          # Page layouts
├── lib/
│   ├── api-client.ts     # Axios/fetch wrapper
│   ├── hooks/            # Custom React hooks
│   └── utils/            # Helper functions
└── types/                # TypeScript types

backend/
├── api/
│   ├── routes/           # FastAPI routers
│   │   ├── vendors.py
│   │   ├── chat.py
│   │   └── signals.py
│   ├── deps.py           # Dependency injection
│   └── middleware.py     # Auth, CORS, etc.
├── core/
│   ├── config.py         # Settings management
│   ├── security.py       # Auth logic
│   └── database.py       # DB connection
├── models/               # SQLAlchemy models
├── schemas/              # Pydantic schemas
├── services/             # Business logic layer
│   ├── gpt_service.py    # GPT wrapper logic
│   ├── ingestion/        # Feed parsers
│   └── ml/               # ML model inference
├── tasks/                # Celery background tasks
└── tests/                # Pytest tests
```

### 2. Service Layer Pattern

Keep routes thin, put logic in services:

```python
# ❌ BAD - logic in route
@router.post("/vendors")
async def create_vendor(vendor: VendorCreate, db: AsyncSession = Depends(get_db)):
    # 50 lines of business logic here...
    
# ✅ GOOD - logic in service
@router.post("/vendors")
async def create_vendor(
    vendor: VendorCreate, 
    db: AsyncSession = Depends(get_db)
):
    return await vendor_service.create(db, vendor)

# services/vendor_service.py
async def create(db: AsyncSession, vendor_data: VendorCreate) -> Vendor:
    # All business logic here
    # Can be tested independently
    # Can be reused in other routes or tasks
```

### 3. GPT Wrapper Architecture

```python
# services/gpt_service.py

class GPTService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.cache = RedisCache()
        
    async def chat(
        self, 
        message: str,
        session_id: str,
        tools: Optional[List[dict]] = None
    ) -> ChatResponse:
        # 1. Check cache
        cache_key = self._cache_key(message, session_id)
        if cached := await self.cache.get(cache_key):
            return ChatResponse(**cached, cached=True)
        
        # 2. Build context (RAG)
        context = await self._build_context(message)
        
        # 3. Get conversation history
        history = await self._get_history(session_id)
        
        # 4. Call GPT
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": f"{context}\n\n{message}"}
        ]
        
        response = await self.client.chat.completions.create(
            model=self._select_model(message),
            messages=messages,
            tools=tools,
            stream=False
        )
        
        # 5. Handle tool calls if needed
        if response.choices[0].message.tool_calls:
            response = await self._handle_tool_calls(
                response, messages
            )
        
        # 6. Cache response
        result = ChatResponse(
            content=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            model=response.model
        )
        await self.cache.set(cache_key, result.dict(), ttl=3600)
        
        # 7. Store in history
        await self._save_to_history(session_id, message, result.content)
        
        return result
    
    def _select_model(self, message: str) -> str:
        """Select GPT-4o-mini for simple queries, GPT-4o for complex"""
        if len(message) < 50 and '?' in message:
            return "gpt-4o-mini"
        return "gpt-4o"
    
    async def _build_context(self, query: str) -> str:
        """RAG: retrieve relevant signals/vendors"""
        # Implement vector search here
        pass
```

---

## Critical Implementation Rules

### 🚨 Security Rules (NEVER violate these)

1. **Never log sensitive data** - API keys, passwords, PII
2. **Always validate user input** - Pydantic schemas, Zod validation
3. **Rate limit all endpoints** - Use slowapi or custom middleware
4. **Sanitize GPT inputs** - Remove potential prompt injections
5. **Never trust GPT outputs** - Filter for SQL, code execution attempts
6. **Use parameterized queries** - Never string concatenation for SQL
7. **Hash API keys in database** - Store hash + prefix only
8. **Implement CORS properly** - Whitelist specific origins
9. **Use environment variables** - Never hardcode secrets
10. **Validate file uploads** - Check type, size, scan for malware

### 💰 Cost Optimization Rules

1. **Cache aggressively** - 40%+ hit rate target for GPT responses
2. **Use GPT-4o-mini by default** - Only use GPT-4o for complex queries
3. **Implement request deduplication** - Same query within 1min = cached
4. **Set token limits** - Max 500 tokens output unless explicitly needed
5. **Lazy load data** - Only fetch what's visible on screen
6. **Debounce search inputs** - Wait 300ms before API calls
7. **Use streaming for long responses** - Can cancel early
8. **Batch database queries** - Use DataLoader pattern
9. **Monitor costs in real-time** - Alert when daily spend > $50
10. **Set up spending limits** - OpenAI dashboard + internal caps

### 🎯 UX Rules

1. **Time to first token < 500ms** - Perceived instant response
2. **Show loading states** - Skeleton screens, spinners
3. **Optimistic updates** - Update UI before API confirms
4. **Error messages must be actionable** - "Retry" button, clear next steps
5. **Empty states guide users** - Show examples, suggest actions
6. **Infinite scroll for lists** - Not pagination (better mobile UX)
7. **Real-time updates** - Use SSE or WebSockets for live data
8. **Keyboard shortcuts** - Power users should never need mouse
9. **Mobile-first design** - 60% of users will be on mobile
10. **Accessibility matters** - ARIA labels, keyboard navigation

---

## MVP Phase 1 - First 2 Weeks (Prioritized Tasks)

### Week 1: Foundation

**Day 1-2: Project Setup**
```bash
# Initialize repos
npx create-next-app@latest threatveil-frontend --typescript --tailwind --app
mkdir threatveil-backend && cd threatveil-backend
poetry init && poetry add fastapi uvicorn sqlalchemy psycopg2-binary

# Setup database
docker-compose up -d postgres redis
alembic init migrations
```

**Tasks:**
- [ ] Setup Next.js with TypeScript, Tailwind, shadcn/ui
- [ ] Setup FastAPI with SQLAlchemy, Alembic migrations
- [ ] Create database schema (vendors, signals, predictions, chat_sessions tables)
- [ ] Implement authentication (Clerk or Supabase)
- [ ] Setup environment variables and secrets management
- [ ] Create basic API client wrapper (frontend)
- [ ] Setup Sentry for error tracking

**Day 3-4: Core Data Models & API**
- [ ] Implement Vendor CRUD endpoints (POST, GET, PUT, DELETE)
- [ ] Create vendor CSV upload endpoint with validation
- [ ] Build signal ingestion service (NVD, OTX parsers)
- [ ] Create background job for daily feed updates (Celery)
- [ ] Setup Redis caching layer
- [ ] Write tests for critical paths (vendor creation, signal ingestion)

**Day 5-7: Frontend Dashboard**
- [ ] Build vendor list page with search/filter
- [ ] Create vendor detail page with signal timeline
- [ ] Implement basic risk score display (heuristic-based initially)
- [ ] Add loading states and error boundaries
- [ ] Create responsive navigation layout
- [ ] Build settings page for API keys and preferences

### Week 2: GPT Integration & Chat

**Day 8-9: GPT Service Foundation**
- [ ] Implement GPT service class with OpenAI SDK
- [ ] Create system prompt for Veil AI persona
- [ ] Build chat API endpoints (POST /chat/sessions, POST /chat/messages)
- [ ] Implement conversation history storage (PostgreSQL)
- [ ] Add response caching layer (Redis)
- [ ] Create cost tracking (log tokens per request)

**Day 10-11: Chat UI**
- [ ] Build chat widget component (collapsible, bottom-right)
- [ ] Implement SSE streaming for real-time responses
- [ ] Add typing indicator and loading states
- [ ] Create message list with user/assistant styling
- [ ] Add thumbs up/down feedback buttons
- [ ] Implement session management (persist across page loads)

**Day 12-13: Function Calling & RAG**
- [ ] Implement 3 function tools: query_vendor, get_signals, run_prediction
- [ ] Build RAG pipeline (vector embeddings for signals)
- [ ] Create context builder (inject relevant data into GPT)
- [ ] Test tool calling flow end-to-end
- [ ] Add error handling for tool failures

**Day 14: Polish & Demo Prep**
- [ ] Create demo dataset (10 vendors with signals)
- [ ] Write 5 pre-canned demo conversations
- [ ] Setup monitoring dashboard (costs, usage, errors)
- [ ] Deploy to staging environment
- [ ] Record demo video showing key features
- [ ] Prepare pilot outreach email list

---

## Common Patterns & Code Snippets

### Pattern 1: Authenticated API Routes (Next.js)

```typescript
// app/api/vendors/route.ts
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';

export async function GET() {
  const { userId } = auth();
  
  if (!userId) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }
  
  try {
    const vendors = await apiClient.get('/vendors', {
      headers: { 'X-User-ID': userId }
    });
    
    return NextResponse.json(vendors.data);
  } catch (error) {
    console.error('Failed to fetch vendors:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Pattern 2: Server-Side Streaming (FastAPI)

```python
# api/routes/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(message: ChatMessage, user_id: str = Depends(get_user_id)):
    async def generate():
        stream = await gpt_service.chat_stream(
            message=message.content,
            session_id=message.session_id,
            user_id=user_id
        )
        
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### Pattern 3: React Query for Server State

```typescript
// lib/hooks/useVendors.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useVendors() {
  return useQuery({
    queryKey: ['vendors'],
    queryFn: () => apiClient.get('/vendors').then(r => r.data),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreateVendor() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (vendor: VendorCreate) => 
      apiClient.post('/vendors', vendor),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
    },
  });
}

// Usage in component:
function VendorList() {
  const { data: vendors, isLoading } = useVendors();
  const createVendor = useCreateVendor();
  
  if (isLoading) return <Skeleton />;
  
  return (
    <div>
      {vendors.map(v => <VendorCard key={v.id} vendor={v} />)}
      <button onClick={() => createVendor.mutate({ name: 'New' })}>
        Add Vendor
      </button>
    </div>
  );
}
```

### Pattern 4: Background Jobs (Celery)

```python
# tasks/ingestion.py
from celery import shared_task
import structlog

logger = structlog.get_logger()

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def ingest_nvd_feed(self):
    """Fetch and process NVD CVE feed"""
    logger.info("Starting NVD ingestion")
    
    try:
        # Fetch feed
        raw_data = nvd_client.fetch_recent()
        
        # Parse and store
        signals = [parse_cve(item) for item in raw_data]
        
        async with get_db() as db:
            for signal in signals:
                await signal_service.create_or_update(db, signal)
        
        logger.info(
            "NVD ingestion complete",
            signals_processed=len(signals)
        )
        
    except Exception as e:
        logger.error("NVD ingestion failed", error=str(e))
        raise

# Schedule in celery beat
# celerybeat_schedule = {
#     'ingest-nvd-daily': {
#         'task': 'tasks.ingestion.ingest_nvd_feed',
#         'schedule': crontab(hour=2, minute=0),  # 2 AM daily
#     },
# }
```

---

## Testing Strategy

### What to Test

**Backend (Pytest):**
- [ ] All API endpoints (happy path + error cases)
- [ ] GPT service (mock OpenAI responses)
- [ ] Vendor service business logic
- [ ] Signal parsing (feed ingestion)
- [ ] Authentication and authorization
- [ ] Rate limiting

**Frontend (Jest + React Testing Library):**
- [ ] Critical user flows (create vendor, send chat message)
- [ ] Form validation
- [ ] Error states
- [ ] Loading states

### Test Structure

```python
# tests/test_vendors.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_vendor(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/vendors",
        json={"name": "Test Corp", "domain": "test.com"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Corp"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_vendor_duplicate_domain(client: AsyncClient, auth_headers):
    # Create first vendor
    await client.post("/api/v1/vendors", json={"domain": "test.com"}, headers=auth_headers)
    
    # Try duplicate
    response = await client.post(
        "/api/v1/vendors",
        json={"domain": "test.com"},
        headers=auth_headers
    )
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()
```

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/threatveil

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...

# Auth (Clerk example)
CLERK_SECRET_KEY=sk_test_...

# External APIs
NVD_API_KEY=...
SHODAN_API_KEY=...

# App Config
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# Monitoring
SENTRY_DSN=https://...

# Costs
DAILY_SPEND_LIMIT_USD=50
ALERT_EMAIL=you@example.com
```

### Frontend (.env.local)

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Analytics (optional)
NEXT_PUBLIC_POSTHOG_KEY=...
```

---

## Deployment Checklist

### Before First Deploy

- [ ] All secrets moved to environment variables
- [ ] Database migrations tested and documented
- [ ] API rate limiting enabled
- [ ] CORS configured for production domain
- [ ] Sentry error tracking configured
- [ ] Health check endpoints implemented (`/health`, `/ready`)
- [ ] Database connection pooling configured
- [ ] Redis cache expiration policies set
- [ ] OpenAI spending limits set in dashboard
- [ ] Backup strategy for database (automated daily)
- [ ] SSL certificates configured (Let's Encrypt)
- [ ] CDN setup for static assets (Vercel/Cloudflare)

### Post-Deploy Monitoring

- [ ] Setup uptime monitoring (UptimeRobot, Better Uptime)
- [ ] Configure Slack alerts for errors (Sentry → Slack)
- [ ] Daily cost report (OpenAI + infrastructure)
- [ ] Weekly performance review (p95 latency, error rates)

---

## When You Get Stuck

### Debugging Checklist

1. **Check the logs** - Sentry, CloudWatch, or `docker logs`
2. **Verify environment variables** - Are they set correctly?
3. **Test API endpoint directly** - Use curl or Postman
4. **Check database state** - Is data actually saved?
5. **Reproduce in minimal example** - Isolate the problem
6. **Check external service status** - Is OpenAI/DB having issues?
7. **Review recent changes** - Git diff since it last worked
8. **Ask for help** - Paste error + context into Claude/GPT

### Common Issues & Fixes

**Issue:** "OpenAI API key not found"
- **Fix:** Check `.env` file, restart server after changes

**Issue:** "Database connection failed"
- **Fix:** Ensure Postgres is running: `docker-compose ps`

**Issue:** "CORS error in browser"
- **Fix:** Add frontend URL to CORS_ORIGINS in backend

**Issue:** "Chat responses are slow (>5s)"
- **Fix:** Check OpenAI status, reduce context size, use GPT-4o-mini

**Issue:** "Redis connection timeout"
- **Fix:** Check Redis is running, verify REDIS_URL

---

## Success Criteria for MVP

### Week 2 Demo Must Have:

- [ ] User can sign up and log in
- [ ] User can add vendor via CSV or manual entry
- [ ] User can see vendor list with risk scores
- [ ] User can click vendor to see detail page with signals
- [ ] User can open chat and ask "What's my biggest risk?"
- [ ] Veil AI responds with relevant answer in <3 seconds
- [ ] User can see conversation history
- [ ] Admin can view cost dashboard (tokens used, $$ spent)

### Quality Gates:

- [ ] All critical paths have tests (>60% coverage)
- [ ] No console errors in browser
- [ ] No Python exceptions in logs during demo
- [ ] Mobile responsive (test on iPhone and Android)
- [ ] Loads in <3 seconds on 3G connection

---

## Final Notes for Cursor

- **When I ask you to implement a feature, always:**
  1. Confirm you understand the requirement
  2. Show me the file structure you'll create/modify
  3. Implement with full error handling and types
  4. Add basic tests if it's critical logic
  5. Update this document if you discover better patterns

- **Prioritize in this order:**
  1. Security (never compromise)
  2. Functionality (does it work?)
  3. User experience (is it pleasant to use?)
  4. Performance (is it fast enough?)
  5. Code elegance (is it maintainable?)

- **Always consider:**
  - Mobile users (60% of traffic)
  - Cost implications (every GPT call costs money)
  - Error states (what if API fails?)
  - Loading states (what does user see while waiting?)

- **Never:**
  - Hardcode secrets
  - Skip input validation
  - Ignore errors silently
  - Commit `.env` files
  - Use `any` type in TypeScript
  - Write SQL strings by concatenation

---

**Let's build something great! Start with Week 1, Day 1 tasks and work through systematically. Ask questions when anything is unclear. 🚀**