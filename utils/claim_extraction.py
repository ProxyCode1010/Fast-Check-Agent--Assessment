"""LLM-based extraction of verifiable claims from document text."""
from . import config
from .groq_client import chat_json
from .pdf_utils import chunk_text

EXTRACTION_SYSTEM_PROMPT = """You are a meticulous fact-checking analyst.

Read the marketing/business document text the user provides and pull out
every VERIFIABLE factual claim: statistics, percentages, growth figures,
dates, financial numbers, market sizes, technical specifications, or
comparisons to named competitors/products.

Ignore opinions, vague marketing language, and anything with no checkable
number, date, or named fact behind it (e.g. "industry-leading", "best in
class" are NOT claims; "40% of Fortune 500 companies use our product" IS).

Respond with ONLY a single JSON object, no commentary, no Markdown fences:
{
  "claims": [
    {
      "claim": "<the claim restated as one standalone, checkable sentence>",
      "category": "statistic | date | financial | technical | other",
      "source_snippet": "<the exact original sentence/phrase it came from>"
    }
  ]
}

If there are no verifiable claims in this text, return {"claims": []}."""


def extract_claims(document_text: str, model: str = None, max_claims: int = None) -> list:
    """Extract a deduplicated list of claim dicts from the full document text.

    Long documents are processed chunk by chunk (one LLM call per chunk) and
    the results are merged and deduplicated, since a single completion has
    a limited context window.
    """
    model = model or config.EXTRACTION_MODEL
    chunks = chunk_text(document_text)

    all_claims = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        result = chat_json(EXTRACTION_SYSTEM_PROMPT, chunk, model=model)
        chunk_claims = result.get("claims", []) if isinstance(result, dict) else []
        all_claims.extend(c for c in chunk_claims if isinstance(c, dict) and c.get("claim"))

    # Deduplicate near-identical claims (exact match, case-insensitive)
    seen = set()
    deduped = []
    for claim in all_claims:
        key = claim["claim"].strip().lower()
        if key not in seen:
            seen.add(key)
            deduped.append(claim)

    if max_claims:
        deduped = deduped[:max_claims]

    for i, claim in enumerate(deduped, start=1):
        claim["id"] = f"C{i}"

    return deduped
