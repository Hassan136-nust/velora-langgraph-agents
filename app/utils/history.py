import re


def resolve_company_name(messages: list[dict], user_query: str) -> str:
    pronoun_patterns = [
        r"\btheir\b", r"\bthey\b", r"\bthem\b", r"\bthis company\b",
        r"\bthat company\b", r"\bthe company\b", r"\bits\b", r"\bit\b",
    ]

    has_pronoun = any(re.search(p, user_query.lower()) for p in pronoun_patterns)

    if not has_pronoun:
        return ""

    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            company_match = re.search(
                r"(?:about|regarding|for|on|researching|analyzing)\s+\*?\*?([A-Z][A-Za-z0-9\s&.'-]+?)(?:\*?\*?[\s,.:;!?])",
                content,
            )
            if company_match:
                return company_match.group(1).strip()

    return ""


def extract_user_intent(user_query: str) -> list[str]:
    query_lower = user_query.lower()
    intents = []

    intent_patterns = {
        "news": [r"\bnews\b", r"\blatest\b", r"\brecent\b", r"\bupdate", r"\bannounce"],
        "financials": [r"\brevenue\b", r"\bfunding\b", r"\bvaluation\b", r"\bfinancial", r"\bearnings\b", r"\bprofit", r"\bipo\b", r"\bstock\b"],
        "leadership": [r"\bceo\b", r"\bfounder\b", r"\bleader", r"\bexecutive", r"\bcto\b", r"\bcoo\b", r"\bmanagement\b"],
        "competitors": [r"\bcompetitor", r"\brival", r"\balternative", r"\bvs\b", r"\bcompare", r"\bcompetition\b"],
        "general": [r"\babout\b", r"\boverview\b", r"\bwhat is\b", r"\bwho is\b", r"\btell me\b", r"\bresearch\b"],
        "products": [r"\bproduct", r"\bservice", r"\boffering", r"\bplatform\b", r"\bsolution\b"],
    }

    for intent, patterns in intent_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                intents.append(intent)
                break

    if not intents:
        intents.append("general")

    return intents


def get_recent_context(messages: list[dict], window: int = 10) -> list[dict]:
    if len(messages) <= window:
        return messages
    return messages[-window:]


def format_messages_for_prompt(messages: list[dict]) -> str:
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
