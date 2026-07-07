"""
LangGraph state machine for repository-aware Q&A:

    retrieve -> generate -> critique -> (revise if needed, max 1 retry) -> END

This gives noticeably better answers than a single LLM call because the
critique step catches hallucinated file/function names or unsupported claims
before the answer reaches the user.
"""
import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from app.llm_service import llm
from app.rag import retrieve_context

logger = logging.getLogger("codemind.workflow")


class ChatState(TypedDict):
    query: str
    repo_id: Optional[str]
    context: str
    draft_answer: str
    critique: str
    needs_revision: bool
    final_answer: str
    revision_count: int


def _retrieve_node(state: ChatState) -> ChatState:
    context = retrieve_context(state["query"], state.get("repo_id"))
    state["context"] = context
    return state


def _generate_node(state: ChatState) -> ChatState:
    system = (
        "You are CodeMind AI, a repository-aware code assistant. Answer using "
        "ONLY the provided code context. Cite exact file paths and line ranges "
        "when referencing code. If the context doesn't contain the answer, say so "
        "explicitly instead of guessing."
    )
    user = f"Code context:\n{state['context']}\n\nQuestion: {state['query']}"
    state["draft_answer"] = llm.chat(system, user)
    return state


def _critique_node(state: ChatState) -> ChatState:
    if state["revision_count"] >= 1:
        # already revised once, don't loop forever
        state["needs_revision"] = False
        state["final_answer"] = state["draft_answer"]
        return state

    system = (
        "You are a strict reviewer. Check whether the DRAFT ANSWER is fully "
        "supported by the CODE CONTEXT and doesn't invent file names, functions, "
        "or behavior not present in the context. "
        'Respond with JSON: {"supported": true|false, "issues": "short description"}'
    )
    user = f"CODE CONTEXT:\n{state['context']}\n\nDRAFT ANSWER:\n{state['draft_answer']}"
    result = llm.chat_json(system, user)

    supported = result.get("supported", True)
    state["critique"] = result.get("issues", "")
    state["needs_revision"] = not supported
    if supported:
        state["final_answer"] = state["draft_answer"]
    return state


def _revise_node(state: ChatState) -> ChatState:
    system = (
        "You are CodeMind AI. Your previous answer had issues. Rewrite it to be "
        "strictly grounded in the code context, fixing the issues noted."
    )
    user = (
        f"Code context:\n{state['context']}\n\n"
        f"Original question: {state['query']}\n\n"
        f"Previous (flawed) answer:\n{state['draft_answer']}\n\n"
        f"Issues found: {state['critique']}\n\n"
        "Provide a corrected answer."
    )
    state["draft_answer"] = llm.chat(system, user)
    state["revision_count"] += 1
    return state


def _route_after_critique(state: ChatState) -> str:
    return "revise" if state["needs_revision"] else "end"


def build_chat_graph():
    graph = StateGraph(ChatState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("generate", _generate_node)
    graph.add_node("critique", _critique_node)
    graph.add_node("revise", _revise_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "critique")
    graph.add_conditional_edges(
        "critique", _route_after_critique, {"revise": "revise", "end": END}
    )
    graph.add_edge("revise", "critique")  # re-check after revising, but capped at 1 retry

    return graph.compile()


_chat_graph = build_chat_graph()


def run_repo_chat(query: str, repo_id: Optional[str] = None) -> dict:
    initial_state: ChatState = {
        "query": query,
        "repo_id": repo_id,
        "context": "",
        "draft_answer": "",
        "critique": "",
        "needs_revision": False,
        "final_answer": "",
        "revision_count": 0,
    }
    result = _chat_graph.invoke(initial_state)
    return {
        "answer": result.get("final_answer") or result.get("draft_answer"),
        "context_used": result["context"],
        "revised": result["revision_count"] > 0,
    }
