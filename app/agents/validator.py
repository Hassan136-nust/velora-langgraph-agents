"""
Validator Agent — Research quality assessment and retry gating.
Returns structured JSON with quality_score, missing_information, and feedback.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone

from app.config import get_llm
from app.state import AgentState
from app.utils.formatting import format_findings_summary
from app.utils.logger import log
from app.utils.retry import make_error_response

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "validator.md"


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    return json.loads(text)


def validator_node(state: AgentState) -> dict:
    user_query = state.get("user_query", "")
    company_name = state.get("company_name", "")
    findings = state.get("research_findings", {})
    confidence = state.get("confidence_score", 0)
    attempts = state.get("attempts", 0)
    agent_outputs = state.get("agent_outputs", {})
    error_log = state.get("error_log", [])

    log("Validator Agent", "INFO",
        f"Validating research for \"{company_name}\" "
        f"(confidence: {confidence}/10, attempt: {attempts})")

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    findings_summary = format_findings_summary(findings)

    user_message = (
        f"User query: {user_query}\n"
        f"Company: {company_name}\n"
        f"Confidence score: {confidence}/10\n"
        f"Attempt number: {attempts}\n\n"
        f"Research findings:\n{findings_summary}"
    )

    llm = get_llm(temperature=0.1)

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ])
        result = _extract_json(response.content)
        log("Validator Agent", "INFO",
            f"Result: {result.get('validation_result')} | "
            f"Quality: {result.get('quality_score', 'N/A')}/10")
    except Exception as exc:
        log("Validator Agent", "ERROR", f"LLM error: {type(exc).__name__}: {exc}")
        error_log.append(make_error_response(exc, "Falling back to confidence-based validation"))
        if confidence >= 5 or attempts >= 3:
            result = {
                "validation_result": "sufficient",
                "validation_notes": "",
                "quality_score": confidence,
                "missing_information": [],
                "feedback": "Validated via confidence fallback",
            }
        else:
            result = {
                "validation_result": "insufficient",
                "validation_notes": "Broaden search queries and look for more recent sources.",
                "quality_score": max(confidence - 1, 1),
                "missing_information": ["Additional sources needed"],
                "feedback": "Need more reliable sources",
            }

    validation_result = result.get("validation_result", "sufficient")
    if validation_result == "insufficient":
        log("Validator Agent", "WARNING",
            f"Research insufficient — looping back to Research Agent (attempt {attempts})")
    else:
        log("Validator Agent", "INFO", "Research validated as sufficient — proceeding to synthesis")

    # ── Build structured output ──
    validator_output = {
        "agent": "validator_agent",
        "validation_result": validation_result,
        "missing_information": result.get("missing_information", []),
        "quality_score": int(result.get("quality_score", confidence)),
        "feedback": result.get("feedback", ""),
        "attempts": attempts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    agent_outputs["validator_agent"] = validator_output

    return {
        "validation_result": validation_result,
        "validation_notes": result.get("validation_notes", ""),
        "agent_outputs": agent_outputs,
        "error_log": error_log,
    }
