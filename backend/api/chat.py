from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import time
import json
import hashlib

try:
    # Prefer official OpenAI SDK v1 style
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # will raise at runtime with clear error


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    model: str
    tokens_used: int
    cached: bool = False


router = APIRouter()


# Simple in-memory TTL cache for early cost control
_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = int(os.getenv("GPT_CACHE_TTL_SECONDS", "3600"))

# Optional Redis cache (preferred for efficiency)
_redis_client = None
try:
    import redis  # type: ignore

    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        _redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)
except Exception:
    _redis_client = None


def _get_openai_client():
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK not available. Please install 'openai' package.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def _cache_key(message: str) -> str:
    h = hashlib.md5(message.encode("utf-8")).hexdigest()
    return f"chat:{h}"


def _get_cached(message: str) -> Optional[Dict[str, Any]]:
    key = _cache_key(message)
    if _redis_client:
        cached = _redis_client.get(key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None
    # Fallback in-memory cache
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > _CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return entry["value"]


def _set_cached(message: str, value: Dict[str, Any]) -> None:
    key = _cache_key(message)
    if _redis_client:
        _redis_client.setex(key, _CACHE_TTL_SECONDS, json.dumps(value))
        return
    _CACHE[key] = {"ts": time.time(), "value": value}


SYSTEM_PROMPT = (
    "You are Veil, ThreatVeil's AI security analyst. Be concise, actionable, and professional. "
    "Cite concrete signals when possible, include 1-2 next steps, and avoid speculation."
)


def _select_model(message: str) -> str:
    if len(message) <= 80 and "?" in message:
        return os.getenv("OPENAI_MODEL_MINI", "gpt-4o-mini")
    return os.getenv("OPENAI_MODEL_FULL", "gpt-4o")


@router.post("/api/v2/chat/message", response_model=ChatResponse)
async def chat_message(req: ChatRequest):
    # Cache first
    cached = _get_cached(req.message)
    if cached:
        return ChatResponse(
            response=cached["content"],
            model=cached["model"],
            tokens_used=cached.get("tokens", 0),
            cached=True,
        )

    # Validate length and basic injection patterns
    if len(req.message) > 4000:
        raise HTTPException(status_code=400, detail="Message too long")

    try:
        client = _get_openai_client()
        model = _select_model(req.message)

        # Non-streamed minimal call to start
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.message},
            ],
            temperature=0.4,
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "500")),
        )

        content = response.choices[0].message.content or ""
        tokens_total = getattr(response.usage, "total_tokens", 0)

        # Basic cost estimate (update if pricing changes)
        # Inputs are unknown granularity here; use total as approximation
        model_used = response.model or model
        cost_usd = 0.0
        try:
            # Rough pricing based on context guide (per 1M tokens)
            if "gpt-4o-mini" in model_used:
                cost_usd = (tokens_total * (0.15 + 0.60) / 2.0) / 1_000_000.0
            else:
                cost_usd = (tokens_total * (2.50 + 10.00) / 2.0) / 1_000_000.0
        except Exception:
            cost_usd = 0.0

        # Cache result
        _set_cached(
            req.message,
            {
                "content": content,
                "model": model_used,
                "tokens": tokens_total,
                "cost_usd": round(cost_usd, 6),
            },
        )

        return ChatResponse(
            response=content,
            model=model_used,
            tokens_used=tokens_total,
            cached=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



