"""
Clarity Agent — Query understanding, company resolution, and spell-check.
Returns structured JSON with metadata.
Detects ANY company in the world - not limited to a hardcoded list.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone

from app.config import get_llm
from app.state import AgentState
from app.utils.history import (
    resolve_company_name,
    get_recent_context,
    format_messages_for_prompt,
)
from app.utils.spellcheck import spellcheck_query, apply_correction
from app.utils.logger import log
from app.utils.retry import make_error_response

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "clarity.md"


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    return json.loads(text)


def _detect_company_in_query(query: str) -> str:
    """
    Simple heuristic to detect potential company names.
    Looks for capitalized words, quoted text, or business-related terms.
    Returns empty string if no obvious company found - LLM will handle it.
    Also filters out obvious gibberish/random text.
    """
    # Check for quoted company names
    quoted = re.findall(r'["\']([^"\']+)["\']', query)
    if quoted:
        candidate = quoted[0].strip()
        if _is_valid_company_name(candidate):
            return candidate
    
    # Look for business-related keywords that indicate a company name
    business_keywords = ['inc', 'corp', 'corporation', 'llc', 'ltd', 'limited', 
                        'company', 'solutions', 'technologies', 'tech', 'ai',
                        'systems', 'software', 'group', 'enterprises', 'industries']
    
    # Common words to skip
    skip_words = {'about', 'into', 'tell', 'research', 'deep', 'dive', 'the', 'a', 'an',
                  'me', 'what', 'info', 'on', 'for', 'of', 'in', 'at', 'to', 'from'}
    
    words = query.strip().split()
    
    # Check for multi-word company names with business keywords
    for i, word in enumerate(words):
        if word.lower() in business_keywords:
            # Look backwards for potential company name words (skip common words)
            company_words = []
            for j in range(i - 1, -1, -1):
                if words[j].lower() in skip_words:
                    break
                company_words.insert(0, words[j])
                if len(company_words) >= 3:  # Max 3 words before keyword
                    break
            
            # Add the keyword itself
            company_words.append(word)
            
            # Look forward for more business keywords
            for j in range(i + 1, min(i + 2, len(words))):
                if words[j].lower() in business_keywords:
                    company_words.append(words[j])
            
            if company_words:
                # Capitalize properly
                candidate = " ".join(w.capitalize() if w.lower() in business_keywords or w.islower() else w 
                               for w in company_words)
                if _is_valid_company_name(candidate):
                    return candidate
    
    # Look for consecutive capitalized words (potential company name)
    capitalized = []
    for i, word in enumerate(words):
        # Skip first word if it's capitalized (might be start of sentence)
        if i == 0 and word[0].isupper():
            continue
        # Collect capitalized words that aren't common words
        if word and word[0].isupper() and len(word) > 1:
            if word.lower() not in skip_words:
                capitalized.append(word)
        elif capitalized:
            # Break on first non-capitalized word
            break
    
    if capitalized:
        candidate = " ".join(capitalized)
        if _is_valid_company_name(candidate):
            return candidate
    
    # No obvious company found - return empty, let LLM handle it
    return ""


def _is_valid_company_name(name: str) -> bool:
    """
    Check if a string looks like a valid company name.
    Filters out obvious gibberish while accepting real company names.
    """
    if not name or len(name) < 2:
        return False
    
    # Remove spaces and special characters for analysis
    clean = re.sub(r'[^a-zA-Z]', '', name).lower()
    
    if len(clean) < 2:
        return False
    
    # Reject if ALL characters are the same (like "aaaa")
    if len(set(clean)) == 1:
        return False
    
    # Check for keyboard mashing patterns (consecutive keys)
    keyboard_rows = [
        'qwertyuiop',
        'asdfghjkl',
        'zxcvbnm'
    ]
    
    for row in keyboard_rows:
        # Check if 4+ consecutive characters from the same keyboard row
        for i in range(len(clean) - 3):
            substring = clean[i:i+4]
            if substring in row or substring in row[::-1]:
                return False
    
    # Check vowel ratio - real words have at least 15% vowels
    vowels = set('aeiou')
    vowel_count = sum(1 for c in clean if c in vowels)
    vowel_ratio = vowel_count / len(clean) if len(clean) > 0 else 0
    
    # "enjkdsnds" has 1 vowel out of 9 = 11% (too low)
    if vowel_ratio < 0.15 and len(clean) > 4:
        return False
    
    # Check for excessive consonant clusters
    consonant_streak = 0
    max_consonant_streak = 0
    
    for char in clean:
        if char not in vowels:
            consonant_streak += 1
            max_consonant_streak = max(max_consonant_streak, consonant_streak)
        else:
            consonant_streak = 0
    
    # "enjkdsnds" has 5 consecutive consonants (jkdsn)
    if max_consonant_streak > 4:
        return False
    
    # If it passes all checks, consider it valid
    return True


def clarity_node(state: AgentState) -> dict:
    messages = state.get("messages", [])
    user_query = state.get("user_query", "")
    existing_company = state.get("company_name", "")
    agent_outputs = state.get("agent_outputs", {})
    error_log = state.get("error_log", [])

    log("Clarity Agent", "INFO", f"Analyzing query: \"{user_query}\"")

    # ── Step 1: Spell-check (only for extremely obvious typos in major companies) ──
    sc_result = spellcheck_query(user_query)

    # Auto-correct ONLY with very high confidence (90%+) for major tech companies
    if sc_result["status"] == "corrected":
        log("Clarity Agent", "INFO",
            f"Auto-corrected \"{sc_result['original']}\" → \"{sc_result['suggested']}\" "
            f"(confidence: {sc_result['confidence']:.0%})")
        user_query = apply_correction(user_query, sc_result)
    
    # Note: We removed the "uncertain" interruption to trust user input more
    # The LLM and web search will validate if the company exists

    # ── Step 2: Company resolution ──
    query_company = _detect_company_in_query(user_query)

    if query_company and query_company.lower() != existing_company.lower():
        resolved = query_company
    elif existing_company:
        resolved = existing_company
    else:
        resolved = resolve_company_name(messages, user_query)
        if not resolved:
            resolved = query_company

    context_used = bool(existing_company and not query_company)

    # ── Step 3: LLM call ──
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    recent = get_recent_context(messages)
    context = format_messages_for_prompt(recent)

    user_message = (
        f"Conversation history:\n{context}\n\n"
        f"Latest user query: {user_query}\n\n"
        f"Previously resolved company name: {resolved if resolved else 'None'}"
    )

    llm = get_llm(temperature=0.1)

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ])
        result = _extract_json(response.content)
        log("Clarity Agent", "INFO",
            f"LLM result: status={result.get('clarity_status')}, "
            f"company={result.get('company_name', resolved)}")
    except Exception as exc:
        log("Clarity Agent", "ERROR", f"LLM error: {type(exc).__name__}: {exc}")
        error_log.append(make_error_response(exc, "Falling back to heuristic resolution"))
        if resolved:
            result = {
                "clarity_status": "clear",
                "company_name": resolved,
                "clarification_question": "",
            }
        else:
            result = {
                "clarity_status": "needs_clarification",
                "company_name": "",
                "clarification_question": "Could you specify which company you'd like me to research?",
            }

    status = result.get("clarity_status", "needs_clarification")
    company = result.get("company_name", resolved)
    log("Clarity Agent", "INFO", f"Final → status={status}, company={company}")

    # ── Build structured output ──
    clarity_output = {
        "agent": "clarity_agent",
        "clarity_status": status,
        "detected_company": company,
        "ambiguity_reason": (
            result.get("clarification_question", "") if status == "needs_clarification" else None
        ),
        "conversation_context_used": context_used,
        "spellcheck": sc_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    agent_outputs["clarity_agent"] = clarity_output

    return {
        "clarity_status": status,
        "company_name": company,
        "clarification_question": result.get("clarification_question", ""),
        "spellcheck_result": sc_result,
        "agent_outputs": agent_outputs,
        "error_log": error_log,
    }
