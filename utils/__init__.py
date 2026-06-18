"""Fact-Check Agent — core pipeline package.

Modules:
    config           Settings + API key loading (Streamlit secrets / env vars)
    pdf_utils         PDF -> text extraction and chunking
    groq_client       Thin wrapper around the Groq chat completions API
    claim_extraction  LLM step: pull verifiable claims out of document text
    web_search        Live web search via Tavily
    fact_checker      LLM step: adjudicate a verdict using search evidence
"""
