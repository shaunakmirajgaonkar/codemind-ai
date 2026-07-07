"""Unit test generation. Defaults to pytest for Python; picks a sensible
framework for other languages (jest for JS/TS, JUnit for Java, etc.)."""
from typing import Optional

from app.llm_service import llm
from app.rag import retrieve_context

FRAMEWORK_BY_LANGUAGE = {
    "python": "pytest", "javascript": "jest", "typescript": "jest",
    "java": "JUnit 5", "go": "the built-in testing package",
    "rust": "the built-in #[test] framework", "csharp": "xUnit",
    "ruby": "RSpec", "php": "PHPUnit",
}


def generate_tests_for_snippet(code: str, language: str = "python") -> str:
    framework = FRAMEWORK_BY_LANGUAGE.get(language, "an idiomatic test framework for that language")
    system = (
        f"You are CodeMind AI. Write thorough unit tests using {framework}. "
        "Cover: happy path, edge cases, invalid input, and boundary conditions. "
        "Use mocks/stubs for external dependencies (DB, network, filesystem). "
        "Return only the test code in a single fenced code block."
    )
    user = f"Language: {language}\n\nCode to test:\n```{language}\n{code}\n```"
    return llm.chat(system, user, temperature=0.2)


def generate_tests_for_repo_file(repo_id: str, file_path: str, language: str = "python") -> str:
    framework = FRAMEWORK_BY_LANGUAGE.get(language, "an idiomatic test framework for that language")
    context = retrieve_context(f"functions and classes in {file_path}", repo_id=repo_id, top_k=10)
    system = (
        f"You are CodeMind AI. Write thorough unit tests using {framework} for "
        f"the functions/classes defined in {file_path}, based strictly on the "
        "provided code context. Cover happy path, edge cases, and error handling. "
        "Return only the test code in a single fenced code block, with correct imports."
    )
    user = f"Target file: {file_path}\n\nCode context:\n{context}"
    return llm.chat(system, user, temperature=0.2)
