"""Natural-language -> code generation, optionally grounded in an indexed
repo so generated code matches existing conventions (naming, imports, style)."""
from typing import Optional

from app.llm_service import llm
from app.rag import retrieve_context


def generate_code(
    instruction: str, language: str = "python", repo_id: Optional[str] = None
) -> str:
    context_block = ""
    if repo_id:
        context = retrieve_context(instruction, repo_id=repo_id, top_k=6)
        context_block = (
            f"\n\nExisting codebase conventions to follow (naming, imports, style):\n{context}"
        )

    system = (
        "You are CodeMind AI, an expert software engineer. Generate clean, "
        "production-quality code that follows best practices for the given "
        "language. Include necessary imports. Add brief inline comments only "
        "where logic is non-obvious. Output only the code, in a single fenced "
        "code block, no extra prose before or after."
    )
    user = f"Language: {language}\n\nInstruction: {instruction}{context_block}"
    return llm.chat(system, user, temperature=0.3)
