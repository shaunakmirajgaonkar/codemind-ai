"""Static-analysis-flavored bug detection using the LLM against retrieved
context, returning structured JSON findings (severity, line, description, fix)."""
from typing import Optional

from app.llm_service import llm
from app.rag import retrieve_context

BUG_SYSTEM_PROMPT = """You are CodeMind AI's bug detection engine. Analyze the
given code for:
- Logic errors and off-by-one mistakes
- Null/None handling issues
- Resource leaks (unclosed files, connections)
- Race conditions / concurrency issues
- Security issues (injection, unsafe deserialization, hardcoded secrets)
- Exception handling gaps

Respond as JSON: {"findings": [{"severity": "critical|high|medium|low",
"line_hint": "approximate line or function name", "issue": "description",
"suggested_fix": "concrete fix"}]}. If no issues found, return {"findings": []}.
"""


def detect_bugs_in_snippet(code: str, language: str = "python") -> dict:
    user = f"Language: {language}\n\nCode:\n```{language}\n{code}\n```"
    return llm.chat_json(BUG_SYSTEM_PROMPT, user)


def detect_bugs_in_repo_file(repo_id: str, file_path: str) -> dict:
    context = retrieve_context(f"code in {file_path}", repo_id=repo_id, top_k=10)
    user = f"Target file: {file_path}\n\nCode chunks:\n{context}"
    return llm.chat_json(BUG_SYSTEM_PROMPT, user)
