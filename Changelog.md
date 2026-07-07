# Changelog

## [1.0.0] - 2026-07-07

### Added
- Initial release: repository indexing, repo-aware chat, code explanation,
  code generation, bug detection, code review, unit test generation,
  documentation generation, and architecture/dependency analysis.
- FastAPI backend, LangGraph orchestration, ChromaDB vector store, local
  sentence-transformers embeddings, Ollama (phi3) for LLM inference.
- Single-page frontend with Mermaid.js diagram rendering.

### Reliability improvements
- **Bug Detection**: added deterministic AST-based static checks
  (`app/utils/static_bug_checks.py`) merged with LLM findings, tagged
  `[STATIC - guaranteed]` vs `[AI - review]`.
- **Code Review**: merged the same static checks in as a guaranteed baseline.
- **Test Generation**: generated tests are now actually executed in a
  sandboxed subprocess (`app/utils/test_sandbox.py`) against the original
  code, reporting real pass/fail results instead of trusting generated code.
- **Documentation**: added an AST-based logic-preservation check
  (`check_logic_preserved`) that flags when the model silently changes
  behavior while claiming to only add docstrings.
EOF
echo "CHANGELOG.md created"
