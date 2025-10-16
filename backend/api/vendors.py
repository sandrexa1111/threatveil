from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import time

router = APIRouter()


class Signal(BaseModel):
    signal_type: str
    severity_score: int = Field(ge=0, le=100)
    metadata: Dict[str, Any] = {}
    detected_at: float


class Vendor(BaseModel):
    id: str
    name: str
    domain: str
    industry_tag: str = "unknown"
    risk_score: int = 0
    reasons: List[str] = []
    signals: List[Signal] = []


# In-memory demo dataset
_VENDORS: Dict[str, Vendor] = {}


def _seed_demo_data():
    if _VENDORS:
        return
    now = time.time()
    demo = [
        Vendor(
            id="v1",
            name="Acme Corp",
            domain="acme.example",
            industry_tag="saas",
            signals=[
                Signal(signal_type="github", severity_score=70, metadata={"detail": "API key exposure"}, detected_at=now - 3600),
                Signal(signal_type="cert", severity_score=40, metadata={"detail": "cert churn"}, detected_at=now - 7200),
            ],
        ),
        Vendor(
            id="v2",
            name="Globex",
            domain="globex.example",
            industry_tag="fintech",
            signals=[
                Signal(signal_type="cve", severity_score=65, metadata={"detail": "OpenSSL CVE"}, detected_at=now - 10_000),
            ],
        ),
        Vendor(
            id="v3",
            name="Initech",
            domain="initech.example",
            industry_tag="infrastructure",
            signals=[
                Signal(signal_type="dns", severity_score=30, metadata={"detail": "subdomain churn"}, detected_at=now - 50_000),
            ],
        ),
    ]

    for v in demo:
        v.risk_score, v.reasons = _heuristic_risk(v.signals)
        _VENDORS[v.id] = v


def _heuristic_risk(signals: List[Signal]) -> (int, List[str]):
    score = 0
    reasons: List[str] = []
    for s in signals:
        # Weight types
        weight = 1.0
        if s.signal_type in ("github", "breach"):
            weight = 1.5
        elif s.signal_type in ("cve", "cert"):
            weight = 1.2
        # Recent signals weigh more (last 7 days)
        recency_boost = 1.2 if (time.time() - s.detected_at) < 7 * 24 * 3600 else 1.0
        contribution = int(min(100, s.severity_score * weight * recency_boost))
        score += contribution // 4  # normalize per-signal
        reasons.append(f"[{s.signal_type}] {s.metadata.get('detail', '')} (sev {s.severity_score})")

    score = max(0, min(100, score))
    # Keep top 3 reasons by implied severity
    reasons = reasons[:3]
    return score, reasons


@router.get("/api/v1/vendors", response_model=List[Vendor])
async def list_vendors():
    _seed_demo_data()
    return list(_VENDORS.values())


@router.get("/api/v1/vendors/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: str):
    _seed_demo_data()
    v = _VENDORS.get(vendor_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return v


