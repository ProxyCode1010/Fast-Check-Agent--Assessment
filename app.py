"""Fact-Check Agent — Streamlit app.

Upload a PDF; the app extracts verifiable claims, checks each one against
live web search results, and reports it as Verified / Inaccurate / False.

Pipeline: PDF -> text (pdfplumber) -> claim extraction (Groq/Llama)
          -> live web search (Tavily) -> verdict (Groq/Llama) -> report
"""
import json

import streamlit as st

from utils import config
from utils.claim_extraction import extract_claims
from utils.fact_checker import verify_claims
from utils.pdf_utils import extract_text_from_pdf

st.set_page_config(page_title="Fact-Check Agent", page_icon="🔍", layout="wide")

VERDICT_STYLE = {
    "Verified": ("✅", "#1a7f37", "#dafbe1"),
    "Inaccurate": ("⚠️", "#9a6700", "#fff8c5"),
    "False": ("❌", "#cf222e", "#ffebe9"),
    "Unverified": ("❔", "#57606a", "#f6f8fa"),
}


def render_claim_card(item: dict) -> None:
    icon, color, bg = VERDICT_STYLE.get(item.get("verdict"), VERDICT_STYLE["Unverified"])
    with st.container(border=True):
        st.markdown(
            f"<span style='background:{bg};color:{color};padding:2px 10px;"
            f"border-radius:12px;font-weight:600;font-size:0.85rem'>"
            f"{icon} {item.get('verdict', 'Unverified')} · "
            f"{item.get('confidence', '')} confidence</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Claim:** {item.get('claim', '')}")
        st.caption(f"Category: {item.get('category', 'other')}")
        if item.get("explanation"):
            st.write(item["explanation"])
        if item.get("verdict") != "Verified" and item.get("correct_fact", "N/A") not in ("N/A", ""):
            st.info(f"**Correct fact:** {item['correct_fact']}")
        urls = item.get("source_urls") or []
        if urls:
            links = " · ".join(
                f"[{u.split('/')[2] if '//' in u else u}]({u})" for u in urls
            )
            st.markdown(f"**Sources:** {links}")


def check_api_keys() -> bool:
    missing = [
        name
        for name, value in [("GROQ_API_KEY", config.GROQ_API_KEY), ("TAVILY_API_KEY", config.TAVILY_API_KEY)]
        if not value
    ]
    if missing:
        st.error(
            "Missing API key(s): **" + ", ".join(missing) + "**.\n\n"
            "Add them to `.streamlit/secrets.toml` locally, or to "
            "**Settings → Secrets** on Streamlit Community Cloud, then rerun the app. "
            "Both Groq and Tavily offer free API keys -- see the README for sign-up links."
        )
        return False
    return True


def run_pipeline(uploaded_file, max_claims: int) -> None:
    with st.status("Reading PDF…", expanded=True) as status:
        text = extract_text_from_pdf(uploaded_file.read())
        if not text.strip():
            status.update(label="Couldn't extract any text from this PDF.", state="error")
            st.error(
                "This PDF appears to be empty, image-only, or scanned without a text "
                "layer. This app reads embedded text and does not perform OCR."
            )
            return
        st.write(f"Extracted {len(text):,} characters of text.")

        status.update(label="Extracting verifiable claims with Llama 3.3 70B…")
        claims = extract_claims(text, max_claims=max_claims)
        if not claims:
            status.update(label="No verifiable claims found.", state="complete")
            st.warning("No statistics, dates, or figures worth checking were found in this document.")
            return
        st.write(f"Found {len(claims)} claims to verify (capped at {max_claims}).")

        status.update(label="Verifying claims against live web data…")
        progress_bar = st.progress(0.0)
        progress_text = st.empty()

        def on_progress(done, total, claim_text):
            progress_bar.progress(done / total)
            progress_text.caption(f"({done}/{total}) Checking: {claim_text[:90]}")

        results = verify_claims(claims, progress_callback=on_progress)
        status.update(label="Done!", state="complete")

    st.session_state["results"] = results


def render_results(results: list) -> None:
    st.divider()
    st.subheader("Report")

    counts = {"Verified": 0, "Inaccurate": 0, "False": 0, "Unverified": 0}
    for r in results:
        verdict = r.get("verdict", "Unverified")
        counts[verdict] = counts.get(verdict, 0) + 1

    cols = st.columns(4)
    cols[0].metric("✅ Verified", counts["Verified"])
    cols[1].metric("⚠️ Inaccurate", counts["Inaccurate"])
    cols[2].metric("❌ False", counts["False"])
    cols[3].metric("❔ Unverified", counts["Unverified"])

    st.write("")
    for item in results:
        render_claim_card(item)

    st.download_button(
        "Download full report (JSON)",
        data=json.dumps(results, indent=2),
        file_name="fact_check_report.json",
        mime="application/json",
    )


def main() -> None:
    st.title("🔍 Fact-Check Agent")
    st.write(
        "Upload a PDF (a marketing one-pager, blog draft, pitch deck export, etc.) "
        "and this agent extracts verifiable claims, checks each one against live "
        "web data, and flags anything outdated, wrong, or unsupported -- with the "
        "correct current fact and sources."
    )

    if not check_api_keys():
        st.stop()

    with st.sidebar:
        st.header("Settings")
        max_claims = st.slider(
            "Max claims to check",
            min_value=5,
            max_value=config.MAX_CLAIMS_LIMIT,
            value=config.MAX_CLAIMS_DEFAULT,
        )
        st.caption(
            "Capped to stay comfortably inside the free Groq/Tavily tiers. "
            "Each claim costs 1 web search + 2 LLM calls."
        )
        st.divider()
        st.caption(
            "Powered by **Groq** (Llama 3.3 70B) for claim extraction and "
            "verdict reasoning, and **Tavily** for live web search."
        )

    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    run_clicked = st.button("Run Fact-Check", type="primary", disabled=uploaded is None)

    if run_clicked:
        run_pipeline(uploaded, max_claims)

    if "results" in st.session_state:
        render_results(st.session_state["results"])


if __name__ == "__main__":
    main()
