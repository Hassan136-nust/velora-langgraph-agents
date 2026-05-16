"""
LangGraph pipeline — builds and runs the multi-agent research workflow.
"""

from langgraph.graph import StateGraph, END

from app.state import AgentState
from app.config import CONFIDENCE_THRESHOLD, MAX_RETRY_ATTEMPTS
from app.agents.clarity import clarity_node
from app.agents.research import research_node
from app.agents.validator import validator_node
from app.agents.synthesis import synthesis_node
from app.utils.logger import log, clear_logs, get_logs


def route_after_clarity(state: AgentState) -> str:
    if state.get("clarity_status") == "needs_clarification":
        log("Router", "INFO", "Clarity → END (needs clarification)")
        return "interrupt"
    log("Router", "INFO", "Clarity → Research Agent")
    return "research"


def route_after_research(state: AgentState) -> str:
    confidence = state.get("confidence_score", 0)
    if confidence >= CONFIDENCE_THRESHOLD:
        log("Router", "INFO",
            f"Research → Synthesis (confidence {confidence} ≥ {CONFIDENCE_THRESHOLD})")
        return "synthesis"
    log("Router", "INFO",
        f"Research → Validator (confidence {confidence} < {CONFIDENCE_THRESHOLD})")
    return "validator"


def route_after_validator(state: AgentState) -> str:
    validation = state.get("validation_result", "sufficient")
    attempts = state.get("attempts", 0)
    if validation == "insufficient" and attempts < MAX_RETRY_ATTEMPTS:
        log("Router", "INFO",
            f"Validator → Research (insufficient, attempt {attempts}/{MAX_RETRY_ATTEMPTS})")
        return "research"
    if validation == "insufficient":
        log("Router", "WARNING",
            f"Validator → Synthesis (max retries exhausted at attempt {attempts})")
    else:
        log("Router", "INFO", "Validator → Synthesis (sufficient)")
    return "synthesis"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("clarity", clarity_node)
    graph.add_node("research", research_node)
    graph.add_node("validator", validator_node)
    graph.add_node("synthesis", synthesis_node)

    graph.set_entry_point("clarity")

    graph.add_conditional_edges(
        "clarity",
        route_after_clarity,
        {
            "research": "research",
            "interrupt": END,
        },
    )

    graph.add_conditional_edges(
        "research",
        route_after_research,
        {
            "synthesis": "synthesis",
            "validator": "validator",
        },
    )

    graph.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "research": "research",
            "synthesis": "synthesis",
        },
    )

    graph.add_edge("synthesis", END)

    return graph.compile()


def run_graph(
    user_query: str,
    messages: list[dict],
    company_name: str = "",
) -> dict:
    """Execute the full pipeline and return the final state."""
    clear_logs()

    graph = build_graph()

    initial_state: AgentState = {
        "messages": messages,
        "user_query": user_query,
        "company_name": company_name,
        "clarity_status": "",
        "clarification_question": "",
        "spellcheck_result": None,
        "research_findings": None,
        "confidence_score": 0,
        "validation_result": "",
        "validation_notes": "",
        "attempts": 0,
        "final_answer": "",
        "agent_outputs": {},
        "agent_logs": [],
        "error_log": [],
    }

    result = graph.invoke(initial_state)
    # Attach final logs to the result
    result["agent_logs"] = get_logs()
    return result
