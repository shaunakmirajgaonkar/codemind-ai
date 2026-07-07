import time
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.graph_workflow import run_repo_chat
from app.models import QueryHistory

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    repo_id: Optional[str] = None


@router.post("")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    start = time.time()
    result = run_repo_chat(payload.query, payload.repo_id)
    latency_ms = (time.time() - start) * 1000

    history = QueryHistory(
        repository_id=payload.repo_id,
        query_type="chat",
        prompt=payload.query,
        response=result["answer"],
        latency_ms=latency_ms,
    )
    db.add(history)
    db.commit()

    return {
        "answer": result["answer"],
        "revised": result["revised"],
        "latency_ms": round(latency_ms, 1),
    }


@router.get("/history")
def get_history(repo_id: Optional[str] = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(QueryHistory)
    if repo_id:
        q = q.filter(QueryHistory.repository_id == repo_id)
    rows = q.order_by(QueryHistory.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "query_type": r.query_type, "prompt": r.prompt,
            "response": r.response, "latency_ms": r.latency_ms,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
