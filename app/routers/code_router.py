from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GeneratedArtifact
from app.services import (
    code_explainer, bug_detector, code_generator,
    doc_generator, test_generator, code_reviewer,
)

router = APIRouter(prefix="/api/code", tags=["code-intelligence"])


class SnippetRequest(BaseModel):
    code: str
    language: str = "python"


class RepoFileRequest(BaseModel):
    repo_id: str
    file_path: str
    language: str = "python"


class GenerateRequest(BaseModel):
    instruction: str
    language: str = "python"
    repo_id: Optional[str] = None


# ---------------- Explain ----------------
@router.post("/explain")
def explain(payload: SnippetRequest):
    return {"explanation": code_explainer.explain_snippet(payload.code, payload.language)}


@router.post("/explain/file")
def explain_file(payload: RepoFileRequest):
    return {"explanation": code_explainer.explain_file_in_repo(payload.repo_id, payload.file_path)}


# ---------------- Generate ----------------
@router.post("/generate")
def generate(payload: GenerateRequest):
    return {"code": code_generator.generate_code(payload.instruction, payload.language, payload.repo_id)}


# ---------------- Bug detection ----------------
@router.post("/bugs")
def find_bugs(payload: SnippetRequest):
    return bug_detector.detect_bugs_in_snippet(payload.code, payload.language)


@router.post("/bugs/file")
def find_bugs_in_file(payload: RepoFileRequest):
    return bug_detector.detect_bugs_in_repo_file(payload.repo_id, payload.file_path)


# ---------------- Review ----------------
@router.post("/review")
def review(payload: SnippetRequest, db: Session = Depends(get_db)):
    result = code_reviewer.review_snippet(payload.code, payload.language)
    db.add(GeneratedArtifact(artifact_type="review", content=str(result)))
    db.commit()
    return result


@router.post("/review/file")
def review_file(payload: RepoFileRequest, db: Session = Depends(get_db)):
    result = code_reviewer.review_repo_file(payload.repo_id, payload.file_path)
    db.add(GeneratedArtifact(
        repository_id=payload.repo_id, artifact_type="review",
        target_file=payload.file_path, content=str(result),
    ))
    db.commit()
    return result


# ---------------- Tests ----------------
@router.post("/tests")
def generate_tests(payload: SnippetRequest, db: Session = Depends(get_db)):
    result = test_generator.generate_tests_for_snippet(payload.code, payload.language)
    db.add(GeneratedArtifact(artifact_type="test", content=result))
    db.commit()
    return {"tests": result}


@router.post("/tests/file")
def generate_tests_file(payload: RepoFileRequest, db: Session = Depends(get_db)):
    result = test_generator.generate_tests_for_repo_file(payload.repo_id, payload.file_path, payload.language)
    db.add(GeneratedArtifact(
        repository_id=payload.repo_id, artifact_type="test",
        target_file=payload.file_path, content=result,
    ))
    db.commit()
    return {"tests": result}


# ---------------- Docs ----------------
@router.post("/docs")
def generate_docs(payload: SnippetRequest):
    return {"documented_code": doc_generator.generate_docstrings(payload.code, payload.language)}


@router.post("/docs/file")
def generate_docs_file(payload: RepoFileRequest, db: Session = Depends(get_db)):
    result = doc_generator.generate_file_documentation(payload.repo_id, payload.file_path)
    db.add(GeneratedArtifact(
        repository_id=payload.repo_id, artifact_type="doc",
        target_file=payload.file_path, content=result,
    ))
    db.commit()
    return {"documentation": result}
