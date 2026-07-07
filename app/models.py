"""
SQLAlchemy ORM models: repositories, indexed files, chat/query history,
and generated artifacts (reviews, tests, docs) so past work is retrievable.
"""
import datetime
import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    source_path = Column(String, nullable=False)  # local path or git URL
    local_clone_path = Column(String, nullable=True)
    language_summary = Column(Text, nullable=True)  # JSON string {lang: file_count}
    total_files = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    indexed_at = Column(DateTime, default=datetime.datetime.utcnow)

    files = relationship("IndexedFile", back_populates="repository", cascade="all, delete-orphan")


class IndexedFile(Base):
    __tablename__ = "indexed_files"

    id = Column(String, primary_key=True, default=gen_id)
    repository_id = Column(String, ForeignKey("repositories.id"))
    file_path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    num_lines = Column(Integer, default=0)
    num_chunks = Column(Integer, default=0)

    repository = relationship("Repository", back_populates="files")


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(String, primary_key=True, default=gen_id)
    repository_id = Column(String, nullable=True)
    query_type = Column(String)  # chat | explain | review | tests | docs | bugs | arch
    prompt = Column(Text)
    response = Column(Text)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class GeneratedArtifact(Base):
    __tablename__ = "generated_artifacts"

    id = Column(String, primary_key=True, default=gen_id)
    repository_id = Column(String, nullable=True)
    artifact_type = Column(String)  # test | doc | review
    target_file = Column(String, nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
