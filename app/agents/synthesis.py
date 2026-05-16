"""
Synthesis Agent — Final report generation with consulting-grade formatting.
Returns structured JSON metadata + beautiful markdown report.
"""

from pathlib import Path
from datetime import datetime, timezone

from app.config import get_llm, MAX_RETRY_ATTEMPTS
from app.state import AgentState
from app.utils.formatting import (
    format_findings_summary,
    format_confidence_badge,
    format_sources,
)
from app.utils.history import get_recent_context, format_messages_for_prompt
from app.utils.logger import log
from app.utils.retry import make_error_response

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "synthesis.md"


def synthesis_node(state: AgentState) -> dict:
    messages = state.get("messages", [])
    user_query = state.get("user_query", "")
    company_name = state.get("company_name", "")
    findings = state.get("research_findings", {})
    confidence = state.get("confidence_score", 0)
    attempts = state.get("attempts", 0)
    agent_outputs = state.get("agent_outputs", {})
    error_log = state.get("error_log", [])

    log("Synthesis Agent", "INFO",
        f"Generating report for \"{company_name}\" "
        f"(confidence: {confidence}/10, attempts: {attempts})")

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    recent = get_recent_context(messages)
    context = format_messages_for_prompt(recent)
    findings_text = format_findings_summary(findings)
    confidence_badge = format_confidence_badge(confidence)

    # Include warning if max retries exhausted with low confidence
    warning_section = ""
    if attempts >= MAX_RETRY_ATTEMPTS and confidence < 6:
        warning_section = (
            "\n\n> ⚠️ **WARNING:** This report was generated with partial data "
            f"after {attempts} research attempts. Some sections may be incomplete "
            "or based on limited sources. Please verify key findings independently."
        )
        log("Synthesis Agent", "WARNING",
            f"Max retries exhausted with low confidence ({confidence}/10) — adding warning")

    user_message = (
        f"Conversation history:\n{context}\n\n"
        f"Latest user query: {user_query}\n"
        f"Company: {company_name}\n"
        f"Confidence: {confidence_badge}\n"
        f"Research attempts: {attempts}\n\n"
        f"Research findings:\n{findings_text}"
    )

    llm = get_llm(temperature=0.3)

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ])
        final_answer = response.content.strip()
        if warning_section:
            final_answer += warning_section
        log("Synthesis Agent", "INFO", f"Generated report: {len(final_answer)} chars")
    except Exception as exc:
        log("Synthesis Agent", "ERROR", f"LLM error: {type(exc).__name__}: {exc}")
        error_log.append(make_error_response(exc, "Using raw findings as fallback report"))
        final_answer = _build_fallback_report(
            company_name, findings, confidence_badge, warning_section
        )

    # ── Build structured output ──
    synthesis_output = {
        "agent": "synthesis_agent",
        "report_title": f"{company_name} Business Research Report",
        "executive_summary": final_answer[:500] + "..." if len(final_answer) > 500 else final_answer,
        "final_confidence": confidence,
        "report_status": "completed" if confidence >= 6 else "completed_with_warnings",
        "research_attempts": attempts,
        "warning": warning_section.strip() if warning_section else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    agent_outputs["synthesis_agent"] = synthesis_output

    log("Synthesis Agent", "INFO", f"Report status: {synthesis_output['report_status']}")

    return {
        "final_answer": final_answer,
        "agent_outputs": agent_outputs,
        "error_log": error_log,
    }


def _build_fallback_report(
    company_name: str,
    findings: dict,
    confidence_badge: str,
    warning_section: str,
) -> str:
    """Build a basic report when the LLM fails."""
    notes = findings.get("notes", []) if findings else []
    items = findings.get("items", []) if findings else []

    parts = [f"# {company_name} Research Report\n"]

    if warning_section:
        parts.append(warning_section.strip())
        parts.append("")

    parts.append("## Executive Summary\n")
    parts.append(f"Research findings for {company_name} based on available data.\n")

    if notes:
        parts.append("## Key Findings\n")
        for note in notes:
            clean = note.strip()
            if len(clean) > 10:
                parts.append(f"- {clean}")

    if items:
        parts.append(f"\n## Sources\n")
        parts.append(format_sources(items))

    parts.append(f"\n## Confidence\n")
    parts.append(confidence_badge)

    return "\n".join(parts)
