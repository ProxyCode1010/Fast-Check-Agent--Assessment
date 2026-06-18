"""Central configuration: API keys and tunable settings.

API keys are read from Streamlit secrets first (the right place for them on
Streamlit Community Cloud), then from environment variables (handy for local
scripts/tests run outside `streamlit run`).
"""
import os

try:
    import streamlit as st
    _STREAMLIT_AVAILABLE = True
except Exception:  # pragma: no cover - streamlit always present in this app
    _STREAMLIT_AVAILABLE = False


def get_secret(key: str, default: str = "") -> str:
    """Look up a config value: Streamlit secrets, then env vars, then default."""
    if _STREAMLIT_AVAILABLE:
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            # st.secrets raises if no secrets.toml exists at all (e.g. fresh
            # local checkout) -- that's fine, just fall through to env vars.
            pass
    return os.environ.get(key, default)


# --- API keys -----------------------------------------------------------
GROQ_API_KEY = get_secret("GROQ_API_KEY")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")

# --- Models ---------------------------------------------------------------
# llama-3.3-70b-versatile is free on Groq, supports JSON mode, and is strong
# enough for both claim extraction and evidence-based verdicts.
# See: https://console.groq.com/docs/models
EXTRACTION_MODEL = get_secret("EXTRACTION_MODEL", "llama-3.3-70b-versatile")
VERIFICATION_MODEL = get_secret("VERIFICATION_MODEL", "llama-3.3-70b-versatile")

# --- Pipeline tuning --------------------------------------------------------
# Caps how many claims get verified per run. Each verified claim costs
# 1 Tavily search credit + 2 Groq calls, so this keeps a single run
# comfortably inside both free tiers (Tavily: 1,000 credits/mo;
# Groq: ~1,000 RPD on the 70B model).
MAX_CLAIMS_DEFAULT = 15
MAX_CLAIMS_LIMIT = 30

TAVILY_MAX_RESULTS = 5
TAVILY_SEARCH_DEPTH = "advanced"

# Document text is chunked before claim extraction so very long PDFs don't
# blow past a single completion's context window.
CHUNK_MAX_CHARS = 12000
