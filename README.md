# CodeMind AI — Local Code Intelligence Platform

A fully local, offline-capable AI code intelligence platform: repository-aware
Q&A, code explanation, generation, bug detection, automated code review, unit
test generation, documentation generation, and architecture/dependency
analysis. No external API calls, no API keys required for the AI features —
everything runs on your machine.

## Stack
- **API**: FastAPI
- **LLM**: Ollama (`phi3` by default) — local inference
- **Orchestration**: LangGraph (retrieve → generate → self-critique → revise)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`) — local, on-device
- **Vector DB**: ChromaDB (persisted to local disk)
- **Relational DB**: SQLite by default, Postgres-ready via Docker Compose
- **Repo parsing**: GitPython + Python `ast` (AST-aware chunking, real dependency graphs)
- **Frontend**: single-page HTML/JS (no build step), Mermaid.js for diagrams

## 1. Prerequisites (macOS)

```bash
# Ollama for local LLM inference
brew install ollama
ollama serve &          # leave running in a separate terminal / tab
ollama pull phi3         # ~2.3GB, one-time download

# Python 3.11 recommended
python3 --version
```

## 2. Setup

```bash
cd codemind_ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env defaults already point at localhost Ollama + local SQLite + local Chroma —
# no editing needed to run locally.
```

## 3. Run

```bash
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

If port 8000 is already in use (common on Mac):
```bash
lsof -ti:8000 | xargs kill -9
```

## 4. Using the platform

1. **Repositories tab** → index a repo by local path (e.g.
   `/Users/you/code/medextract`) or a Git URL
   (`https://github.com/shaunakmirajgaonkar/your-repo.git`). This clones
   (if needed), AST-chunks every file, embeds locally, and stores vectors in
   ChromaDB.
2. **Repo Chat** → ask natural-language questions about the indexed repo.
   Answers are grounded in retrieved code and pass through a LangGraph
   self-critique step before being shown to you.
3. **Explain / Generate / Bug Detection / Review / Tests / Docs** → paste any
   snippet directly, no indexing required. Generate Code can optionally use
   an indexed repo's conventions.
4. **Architecture** → builds a real dependency graph from `ast` import
   parsing (deterministic, not LLM-guessed), renders it as a Mermaid diagram,
   flags circular dependencies, and adds an LLM narrative summary on top of
   the real graph data.

## 5. Optional: Postgres via Docker

```bash
docker compose up -d postgres
# then set in .env:
# DATABASE_URL=postgresql://codemind:codemind@localhost:5432/codemind
```

Or run the whole stack in Docker (Ollama still runs natively on the host for
Metal acceleration):
```bash
docker compose up --build
```

## Project layout

```
codemind_ai/
├── app/
│   ├── main.py                 # FastAPI app + router wiring
│   ├── config.py               # env-based settings
│   ├── database.py             # SQLAlchemy session/engine
│   ├── models.py                # ORM models
│   ├── llm_service.py           # Ollama wrapper (stream=False)
│   ├── embeddings.py            # local sentence-transformers embeddings
│   ├── vector_store.py          # ChromaDB wrapper
│   ├── rag.py                   # shared retrieval helper
│   ├── graph_workflow.py        # LangGraph retrieve→generate→critique→revise
│   ├── repo_indexer.py          # clone/walk/chunk/index a repository
│   ├── utils/chunking.py        # AST-aware Python chunking + line fallback
│   ├── services/                # one module per feature
│   │   ├── code_explainer.py
│   │   ├── code_generator.py
│   │   ├── bug_detector.py
│   │   ├── code_reviewer.py
│   │   ├── test_generator.py
│   │   ├── doc_generator.py
│   │   └── architecture_analyzer.py   # ast + networkx dependency graph
│   └── routers/                 # FastAPI endpoints per feature
├── frontend/index.html          # single-page UI
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Notes on "100% local"

- **LLM inference**: Ollama, runs entirely on-device.
- **Embeddings**: sentence-transformers, runs entirely on-device (no OpenAI/API calls).
- **Vector store**: ChromaDB persisted to `./storage/chroma_db` on disk.
- **Relational DB**: SQLite file on disk by default.
- **GitHub integration**: only touches the network if you index a **remote**
  Git URL (to clone it) — indexing a local path never leaves your machine.

## Extending

- Swap `OLLAMA_MODEL` in `.env` to any pulled Ollama model (e.g. `llama3.1`,
  `codellama`, `deepseek-coder`) — no code changes needed.
- Add a new language to `EXT_LANGUAGE_MAP` in `app/utils/chunking.py` to get
  proper language tagging for retrieval/citations.
- Add a new feature by creating `app/services/your_feature.py` +
  a route in `app/routers/`.
