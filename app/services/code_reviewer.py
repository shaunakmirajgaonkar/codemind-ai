"""Automated code review: readability, maintainability, performance, security,
and adherence to language idioms — returns structured, actionable feedback."""
from app.llm_service import llm
from app.rag import retrieve_context

REVIEW_SYSTEM_PROMPT = """You are CodeMind AI performing a senior engineer's
code review. Assess: correctness, readability, maintainability, performance,
security, and idiomatic style for the language. Be specific and actionable,
not generic.

Respond as JSON:
{
  "overall_score": 0-100,
  "summary": "2-3 sentence overview",
  "strengths": ["..."],
  "issues": [{"category": "readability|performance|security|correctness|style",
              "severity": "high|medium|low", "comment": "...", "suggestion": "..."}]
}
"""


def review_snippet(code: str, language: str = "python") -> dict:
    user = f"Language: {language}\n\nCode:\n```{language}\n{code}\n```"
    return llm.chat_json(REVIEW_SYSTEM_PROMPT, user)


def review_repo_file(repo_id: str, file_path: str) -> dict:
    context = retrieve_context(f"code in {file_path}", repo_id=repo_id, top_k=10)
    user = f"Target file: {file_path}\n\nCode context:\n{context}"
    return llm.chat_json(REVIEW_SYSTEM_PROMPT, user)
