import operator
from typing import TypedDict, Optional, Any, Annotated
from pydantic import BaseModel, Field


class ResearchItem(BaseModel):
    title: str = ""
    snippet: str = ""
    url: str = ""
    source: str = ""
    date: str = ""


class ResearchFindings(BaseModel):
    items: list[ResearchItem] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def _merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dicts, with right overwriting left for conflicting keys."""
    merged = dict(left) if left else {}
    if right:
        merged.update(right)
    return merged


def _merge_lists(left: list, right: list) -> list:
    """Concatenate two lists."""
    result = list(left) if left else []
    if right:
        result.extend(right)
    return result


class AgentState(TypedDict, total=False):
    # Core
    messages: list[dict]
    user_query: str
    company_name: str

    # Clarity
    clarity_status: str
    clarification_question: str

    # Spell-check
    spellcheck_result: Optional[dict]

    # Research
    research_findings: Optional[dict]
    confidence_score: int

    # Validation
    validation_result: str
    validation_notes: str
    attempts: int

    # Synthesis
    final_answer: str

    # Structured per-agent JSON outputs — MERGED across agents
    agent_outputs: Annotated[dict[str, Any], _merge_dicts]

    # Logs — CONCATENATED across agents
    agent_logs: Annotated[list[dict], _merge_lists]

    # Errors — CONCATENATED across agents
    error_log: Annotated[list[dict], _merge_lists]
