"""Plain-language explanation of a code snippet or a whole indexed file."""
from typing import Optional

from app.llm_service import llm
from app.rag import retrieve_context


def explain_snippet(code: str, language: str = "python") -> str:
    system = (
        "You are CodeMind AI, an expert code explainer. Explain what the given "
        "code does, its inputs/outputs, edge cases, and any non-obvious logic. "
        "Use clear, concise language suitable for a developer onboarding to this codebase."
    )
    user = f"Language: {language}\n\nCode:\n```{language}\n{code}\n```\n\nExplain this code."
    return llm.chat(system, user)


def explain_file_in_repo(repo_id: str, file_path: str) -> str:
    context = retrieve_context(f"contents and purpose of {file_path}", repo_id=repo_id, top_k=10)
    system = (
        "You are CodeMind AI. Explain the purpose, structure, and key logic of the "
        "target file using the retrieved code chunks. Mention how it likely fits "
        "into the broader codebase if that's inferable from imports/names."
    )
    user = f"Target file: {file_path}\n\nRetrieved chunks:\n{context}\n\nExplain this file."
    return llm.chat(system, user)
