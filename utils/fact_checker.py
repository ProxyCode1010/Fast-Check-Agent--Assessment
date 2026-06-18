"""Verification of individual claims against live web search evidence."""
from . import config
from .groq_client import chat_json
from .web_search import search_claim

VERIFICATION_SYSTEM_PROMPT = """You are a meticulous, evidence-driven fact-checker.

You are given a CLAIM pulled from a marketing/business document, plus a set
of LIVE WEB SEARCH RESULTS gathered just now. Decide a verdict using ONLY
the evidence provided -- do not rely on prior knowledge if it conflicts
with more recent evidence in the results.

- "Verified": the search evidence confirms the claim is currently accurate.
- "Inaccurate": the claim is in the right ballpark / was once true, but the
  evidence shows a different current figure, an outdated date, or stale data.
- "False": the evidence directly contradicts the claim, or there is no
  credible evidence anywhere in the results supporting it.

Respond with ONLY a single JSON object, no commentary, no Markdown fences:
{
  "verdict": "Verified | Inaccurate | False",
  "confidence": "High | Medium | Low",
  "explanation": "<1-2 sentence reasoning citing what the evidence shows>",
  "correct_fact": "<the accurate, current fact/figure, or 'N/A' if Verified>",
  "source_urls": ["<url1>", "<url2>"]
}"""


def verify_claim(claim: dict, model: str = None) -> dict:
    """Search the web for one claim, then ask the LLM to adjudicate a verdict.

    Returns the original claim dict merged with verdict/evidence fields.
    Failures (search or LLM error) are captured into the result as an
    "Unverified" verdict instead of raising, so one bad claim doesn't stop
    the whole batch.
    """
    model = model or config.VERIFICATION_MODEL
    result = dict(claim)

    try:
        evidence = search_claim(claim["claim"])
    except Exception as exc:
        result.update(
            verdict="Unverified",
            confidence="Low",
            explanation=f"Web search failed: {exc}",
            correct_fact="N/A",
            source_urls=[],
        )
        return result

    sources_block = "\n\n".join(
        f"[{i + 1}] {s['title']} ({s['url']})\n{s['content']}"
        for i, s in enumerate(evidence["sources"])
    ) or "No search results were returned."

    user_prompt = (
        f"CLAIM:\n{claim['claim']}\n\n"
        f"TAVILY QUICK ANSWER:\n{evidence['tavily_answer'] or 'None provided'}\n\n"
        f"SEARCH RESULTS:\n{sources_block}"
    )

    try:
        verdict_data = chat_json(VERIFICATION_SYSTEM_PROMPT, user_prompt, model=model)
    except Exception as exc:
        result.update(
            verdict="Unverified",
            confidence="Low",
            explanation=f"Verification model failed: {exc}",
            correct_fact="N/A",
            source_urls=[s["url"] for s in evidence["sources"]],
        )
        return result

    fallback_urls = [s["url"] for s in evidence["sources"]]
    result.update(
        verdict=verdict_data.get("verdict", "Unverified"),
        confidence=verdict_data.get("confidence", "Low"),
        explanation=verdict_data.get("explanation", ""),
        correct_fact=verdict_data.get("correct_fact", "N/A"),
        source_urls=verdict_data.get("source_urls") or fallback_urls,
    )
    return result


def verify_claims(claims: list, model: str = None, progress_callback=None) -> list:
    """Verify a list of claims sequentially, reporting progress via callback.

    progress_callback(done, total, claim_text) is called after each claim.
    Sequential (not parallel) on purpose: it keeps requests-per-minute well
    under the free-tier limits for both Groq and Tavily.
    """
    results = []
    total = len(claims)
    for i, claim in enumerate(claims, start=1):
        results.append(verify_claim(claim, model=model))
        if progress_callback:
            progress_callback(i, total, claim.get("claim", ""))
    return results
