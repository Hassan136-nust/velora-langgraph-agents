"""
Spell-check / query correction for company names.
DISABLED by default - lets LLM and web search handle company validation.
Only catches extremely obvious typos in well-known companies.
"""

from rapidfuzz import fuzz, process
from datetime import datetime, timezone


# Minimal list of ONLY the most common tech giants for obvious typo detection
# This list should be very small to avoid false matches
KNOWN_COMPANIES = [
    "Google", "Amazon", "Microsoft", "Apple", "Meta", "Facebook",
    "Netflix", "Tesla", "OpenAI", "Anthropic"
]

# Build a lowercase → proper-case lookup
_COMPANY_MAP = {c.lower(): c for c in KNOWN_COMPANIES}


def spellcheck_query(query: str) -> dict:
    """
    Check the query for ONLY extremely obvious typos in major tech companies.
    Accepts most company names as-is to avoid false corrections.
    
    Returns:
        {
            "original": str,
            "suggested": str | None,
            "confidence": float (0-1),
            "status": "corrected" | "uncertain" | "no_correction"
        }
    """
    words = query.strip().split()
    best_match = None
    best_score = 0.0
    best_original = query

    company_names_lower = list(_COMPANY_MAP.keys())

    # Only check single words that are likely typos of major companies
    for word in words:
        # Skip very short words
        if len(word) <= 3:
            continue
        # Skip obvious stop words
        if word.lower() in {
            "the", "about", "tell", "what", "who", "how",
            "are", "was", "were", "and", "for",
            "their", "its", "them", "they", "company", "latest",
            "news", "revenue", "competitors", "competitor",
            "products", "services", "market", "stock", "price",
            "value", "growth", "profit", "loss", "share", "shares",
            "report", "analysis", "overview", "summary", "details",
            "information", "data", "update", "updates", "trends",
            "industry", "sector", "financial", "financials",
            "more", "any", "recent", "expand", "give", "show",
            "list", "compare", "versus", "between", "like",
            "also", "with", "from", "that", "this", "these",
            "those", "have", "had", "does", "did",
            "will", "would", "could", "should", "can",
            "been", "being", "into", "over", "under",
            "lawsuits", "lawsuit", "legal", "risks", "risk",
            "research", "find", "search", "look", "dive", "tell",
            "solutions", "technologies", "systems", "software",
            "corp", "inc", "llc", "ltd", "limited", "corporation"
        }:
            continue
        
        # Skip if word looks like a valid company name (has capitals, business terms, etc.)
        if _looks_like_company_name(word):
            continue

        # Use fuzzy matching only for potential typos
        result = process.extractOne(
            word.lower(),
            company_names_lower,
            scorer=fuzz.ratio,
        )
        
        if result:
            match_name, score, _ = result
            normalized = score / 100.0
            
            # Only consider high matches (80%+) to catch common typos
            # "goggle" -> "google" is 83% match
            if normalized > best_score and normalized >= 0.80:
                best_score = normalized
                best_match = _COMPANY_MAP[match_name]
                best_original = word

    # Exact match — no correction needed
    if best_match and best_original.lower() == best_match.lower():
        return {
            "original": best_original,
            "suggested": best_match,
            "confidence": 1.0,
            "status": "no_correction",
        }

    # Auto-correct with high confidence (80%+) for major companies
    # This catches common typos like "goggle" -> "Google" (83%), "Gogle" -> "Google", "Microsft" -> "Microsoft"
    if best_match and best_score >= 0.80:
        return {
            "original": best_original,
            "suggested": best_match,
            "confidence": round(best_score, 2),
            "status": "corrected",
        }

    # No meaningful match - accept the company name as-is
    return {
        "original": query,
        "suggested": None,
        "confidence": 0.0,
        "status": "no_correction",
    }


def _looks_like_company_name(word: str) -> bool:
    """
    Check if a word looks like it could be a company name.
    Returns True if it should be accepted as-is without spellcheck.
    Only skip spellcheck for words that are clearly proper company names.
    """
    # Contains numbers (like "3M", "7-Eleven") - likely a real company
    if any(c.isdigit() for c in word):
        return True
    
    # Has multiple capital letters (like "IBM", "HP") - likely acronym/company
    capital_count = sum(1 for c in word if c.isupper())
    if capital_count >= 2:
        return True
    
    # Very long words (8+ chars) are likely real company names, not typos
    if len(word) >= 8:
        return True
    
    # Otherwise, allow spellcheck to run
    return False


def apply_correction(query: str, spellcheck_result: dict) -> str:
    """Replace the misspelled token in the query with the corrected one."""
    if spellcheck_result["status"] == "corrected" and spellcheck_result["suggested"]:
        original = spellcheck_result["original"]
        suggested = spellcheck_result["suggested"]
        return query.replace(original, suggested, 1)
    return query
