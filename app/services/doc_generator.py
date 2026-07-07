"""Automated documentation generation: docstrings for a snippet, or a full
Markdown reference doc for an indexed file."""
from app.llm_service import llm
from app.rag import retrieve_context


def generate_docstrings(code: str, language: str = "python") -> str:
    system = (
        "You are CodeMind AI. Add complete, standard-style docstrings/comments "
        "(e.g. Google-style for Python, JSDoc for JS/TS) to every function and "
        "class in the given code. Return the FULL code with docstrings inserted, "
        "in a single fenced code block. Do not change logic."
    )
    user = f"Language: {language}\n\nCode:\n```{language}\n{code}\n```"
    return llm.chat(system, user, temperature=0.1)


def generate_file_documentation(repo_id: str, file_path: str) -> str:
    context = retrieve_context(f"all functions and classes in {file_path}", repo_id=repo_id, top_k=12)
    system = (
        "You are CodeMind AI's documentation engine. Produce a clear Markdown "
        "reference document for the target file: overview, list of "
        "functions/classes with signatures and descriptions, parameters, return "
        "values, and usage examples where sensible. Base everything strictly on "
        "the provided code chunks."
    )
    user = f"Target file: {file_path}\n\nCode chunks:\n{context}"
    return llm.chat(system, user, temperature=0.1)
