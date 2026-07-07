# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in CodeMind AI, please report it
privately rather than opening a public issue. Contact the repository owner
directly via GitHub.

## Scope and local-first design

CodeMind AI is designed to run entirely locally:
- LLM inference happens via a local Ollama instance (no cloud API calls).
- Embeddings run on-device via sentence-transformers.
- The vector store (ChromaDB) and relational database (SQLite/Postgres) are
  both local by default.

Known considerations:
- **Test Generation** executes LLM-generated test code in a sandboxed
  subprocess against your own code (see `app/utils/test_sandbox.py`). This is
  intended for local, single-user use against code you trust - it is not
  hardened for multi-tenant or untrusted-input scenarios.
- **GitHub repo indexing** will clone remote repositories to a local temp
  directory. Only index repositories you trust.
- Do not expose this application's API directly to the public internet
  without adding authentication - it has no built-in auth layer, by design,
  for local single-user use.
EOF
echo "SECURITY.md created"
