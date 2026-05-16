"""
Research Agent — Web search, data gathering, and structured findings.
Returns structured JSON with metadata.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone

from app.config import get_llm
from app.state import AgentState
from app.tools.tavily_search import search_tavily
from app.utils.formatting import deduplicate_results
from app.utils.history import extract_user_intent
from app.utils.logger import log
from app.utils.retry import make_error_response

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "research.md"

QUERY_TEMPLATES = {
    "news": "{company} latest news developments",
    "financials": "{company} revenue funding valuation financial results",
    "leadership": "{company} CEO founder leadership team background",
    "competitors": "{company} competitors alternatives market comparison",
    "general": "{company} company overview business model",
    "products": "{company} products services platform offerings",
}


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    return json.loads(text)


def _build_search_queries(company: str, intents: list[str], validation_notes: str) -> list[str]:
    queries = []
    for intent in intents:
        template = QUERY_TEMPLATES.get(intent, QUERY_TEMPLATES["general"])
        queries.append(template.format(company=company))

    if "general" not in intents:
        queries.append(QUERY_TEMPLATES["general"].format(company=company))

    if validation_notes:
        queries.append(f"{company} {validation_notes}")

    return queries[:6]


def research_node(state: AgentState) -> dict:
    user_query = state.get("user_query", "")
    company_name = state.get("company_name", "")
    validation_notes = state.get("validation_notes", "")
    attempts = state.get("attempts", 0) + 1
    agent_outputs = state.get("agent_outputs", {})
    error_log = state.get("error_log", [])

    log("Research Agent", "INFO",
        f"Starting research for \"{company_name}\" (attempt {attempts})")

    intents = extract_user_intent(user_query)
    queries = _build_search_queries(company_name, intents, validation_notes)

    log("Research Agent", "INFO", f"Intents: {intents} | Queries: {len(queries)}")

    # ── Search phase ──
    all_results = []
    api_status = "success"
    sources_used = set()

    for query in queries:
        results = search_tavily(query)
        if results:
            all_results.extend(results)
            for r in results:
                src = r.get("source", "")
                if src:
                    sources_used.add(src)
        else:
            api_status = "partial"

    unique_results = deduplicate_results(all_results)
    log("Research Agent", "INFO", f"Found {len(unique_results)} unique results from {len(sources_used)} sources")

    if not unique_results:
        api_status = "no_results"
        log("Research Agent", "WARNING", "No search results found")

    # ── LLM analysis phase ──
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    results_text = "\n\n".join([
        f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\n"
        f"Source: {r.get('source', '')}\nDate: {r.get('date', '')}\n"
        f"Snippet: {r.get('snippet', '')}"
        for r in unique_results
    ]) if unique_results else "No search results found."

    user_message = (
        f"User query: {user_query}\n"
        f"Company: {company_name}\n"
        f"User intent categories: {', '.join(intents)}\n"
        f"Validation notes from previous attempt: {validation_notes or 'N/A (first attempt)'}\n"
        f"Attempt number: {attempts}\n\n"
        f"Search results:\n{results_text}"
    )

    llm = get_llm(temperature=0.2)
    key_findings = []
    research_summary = ""

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ])
        result = _extract_json(response.content)
        notes = result.get("notes", [])
        key_findings = result.get("key_findings", notes)
        research_summary = result.get("research_summary", "")
        confidence = int(result.get("confidence_score", 3))
        log("Research Agent", "INFO", f"LLM confidence: {confidence}/10 | Findings: {len(notes)}")
    except Exception as exc:
        log("Research Agent", "ERROR", f"LLM error: {type(exc).__name__}: {exc}")
        error_log.append(make_error_response(exc, "Using raw search snippets as fallback"))
        notes = [r.get("snippet", "")[:200] for r in unique_results[:5] if r.get("snippet")]
        key_findings = notes
        confidence = min(len(unique_results), 5)
        api_status = "llm_fallback"

    findings = {
        "items": unique_results,
        "notes": notes,
    }

    # ── Build structured output ──
    research_output = {
        "agent": "research_agent",
        "research_summary": research_summary or "; ".join(notes[:3]) if notes else "Limited data available",
        "sources_used": sorted(sources_used),
        "key_findings": key_findings[:10],
        "confidence_score": confidence,
        "search_attempt": attempts,
        "api_status": api_status,
        "total_results": len(unique_results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    agent_outputs["research_agent"] = research_output

    return {
        "research_findings": findings,
        "confidence_score": confidence,
        "attempts": attempts,
        "agent_outputs": agent_outputs,
        "error_log": error_log,
    }
