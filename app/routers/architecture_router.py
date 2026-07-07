import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Repository
from app.services.architecture_analyzer import analyze_architecture

router = APIRouter(prefix="/api/architecture", tags=["architecture"])


@router.get("/{repo_id}")
def get_architecture(repo_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if not repo.local_clone_path:
        raise HTTPException(status_code=400, detail="Repository has no local path on disk")

    language_summary = json.loads(repo.language_summary or "{}")
    return analyze_architecture(repo.local_clone_path, language_summary)
