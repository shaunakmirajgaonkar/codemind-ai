"""
Central configuration. All values are loaded from environment variables / .env
so the whole platform can run 100% locally with zero cloud dependencies.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ollama (local LLM inference)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    OLLAMA_STREAM: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./storage/codemind.db"

    # Vector store
    CHROMA_PERSIST_DIR: str = "./storage/chroma_db"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Repo indexing
    MAX_FILE_SIZE_KB: int = 500
    CHUNK_MAX_LINES: int = 120
    CHUNK_OVERLAP_LINES: int = 15

    # GitHub
    GITHUB_TOKEN: str = ""

    # Misc
    APP_NAME: str = "CodeMind AI"
    APP_VERSION: str = "1.0.0"


settings = Settings()
