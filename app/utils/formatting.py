def deduplicate_results(items: list[dict]) -> list[dict]:
    seen_urls = set()
    unique = []
    for item in items:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)
        elif not url:
            unique.append(item)
    return unique


def format_sources(items: list[dict]) -> str:
    if not items:
        return "No sources available."
    lines = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        source = item.get("source", "")
        date = item.get("date", "")
        date_str = f" ({date})" if date else ""
        lines.append(f"{i}. [{title}]({url}) — {source}{date_str}")
    return "\n".join(lines)


def format_findings_summary(findings: dict) -> str:
    if not findings:
        return "No findings available."

    parts = []

    notes = findings.get("notes", [])
    if notes:
        parts.append("**Key Facts:**")
        for note in notes:
            parts.append(f"- {note}")

    items = findings.get("items", [])
    if items:
        parts.append(f"\n**Sources ({len(items)}):**")
        parts.append(format_sources(items))

    return "\n".join(parts) if parts else "No findings available."


def format_confidence_badge(score: int) -> str:
    if score >= 8:
        return f"🟢 High Confidence ({score}/10)"
    elif score >= 6:
        return f"🟡 Moderate Confidence ({score}/10)"
    else:
        return f"🔴 Low Confidence ({score}/10)"


def format_report_table(headers: list[str], rows: list[list[str]]) -> str:
    """Generate a markdown table from headers and rows."""
    if not headers or not rows:
        return ""
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = []
    for row in rows:
        # Pad row to match header length
        padded = row + [""] * (len(headers) - len(row))
        body_lines.append("| " + " | ".join(padded[:len(headers)]) + " |")
    return "\n".join([header_line, separator] + body_lines)


def format_spellcheck_banner(spellcheck_result: dict) -> str:
    """Generate a user-facing banner for spell-check results."""
    if not spellcheck_result:
        return ""
    status = spellcheck_result.get("status", "no_correction")
    if status == "corrected":
        original = spellcheck_result.get("original", "")
        suggested = spellcheck_result.get("suggested", "")
        confidence = spellcheck_result.get("confidence", 0)
        return (
            f"🔤 **Auto-corrected:** \"{original}\" → **{suggested}** "
            f"(confidence: {confidence:.0%})"
        )
    elif status == "uncertain":
        original = spellcheck_result.get("original", "")
        suggested = spellcheck_result.get("suggested", "")
        return f"🤔 **Did you mean** \"{suggested}\" instead of \"{original}\"?"
    return ""
