import json
import time

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Repository, IndexedFile
from app.repo_indexer import index_repository, reindex_repository

router = APIRouter(prefix="/api/repos", tags=["repositories"])


class IndexRepoRequest(BaseModel):
    name: str
    source: str  # local path or git URL (https://github.com/user/repo.git)


@router.post("")
def index_repo(payload: IndexRepoRequest, db: Session = Depends(get_db)):
    start = time.time()
    try:
        repo = index_repository(db, payload.name, payload.source)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to index repository: {e}")

    return {
        "id": repo.id,
        "name": repo.name,
        "total_files": repo.total_files,
        "total_chunks": repo.total_chunks,
        "language_summary": json.loads(repo.language_summary or "{}"),
        "duration_seconds": round(time.time() - start, 2),
    }


@router.get("")
def list_repos(db: Session = Depends(get_db)):
    repos = db.query(Repository).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "source_path": r.source_path,
            "total_files": r.total_files,
            "total_chunks": r.total_chunks,
            "language_summary": json.loads(r.language_summary or "{}"),
            "indexed_at": r.indexed_at.isoformat() if r.indexed_at else None,
        }
        for r in repos
    ]


@router.get("/{repo_id}")
def get_repo(repo_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    files = db.query(IndexedFile).filter(IndexedFile.repository_id == repo_id).all()
    return {
        "id": repo.id,
        "name": repo.name,
        "local_clone_path": repo.local_clone_path,
        "total_files": repo.total_files,
        "total_chunks": repo.total_chunks,
        "language_summary": json.loads(repo.language_summary or "{}"),
        "files": [
            {"file_path": f.file_path, "language": f.language, "num_lines": f.num_lines,
             "num_chunks": f.num_chunks}
            for f in files
        ],
    }


@router.post("/{repo_id}/reindex")
def reindex_repo(repo_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    updated = reindex_repository(db, repo)
    return {"id": updated.id, "total_files": updated.total_files, "total_chunks": updated.total_chunks}


@router.delete("/{repo_id}")
def delete_repo(repo_id: str, db: Session = Depends(get_db)):
    from app.vector_store import delete_repo_chunks
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    delete_repo_chunks(repo_id)
    db.query(IndexedFile).filter(IndexedFile.repository_id == repo_id).delete()
    db.delete(repo)
    db.commit()
    return {"deleted": True}
