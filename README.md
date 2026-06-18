# 🔍 Fact-Check Agent - Assessment

A "Truth Layer" web app: upload a PDF, and the agent extracts every checkable
claim (stats, dates, financial/technical figures), searches the live web to
verify each one, and reports it as **Verified**, **Inaccurate**, or **False**
-- along with the correct current fact and sources.

Built for the CogCulture Product Management Trainee assessment, Part 2.

## Live Demo

🚀 Try the deployed application here: [Live App Link](https://cog-culture-fast-check-agent.streamlit.app/)

## Demo Video

🎥 Watch the project demonstration: [Demo Video](https://drive.google.com/file/d/1FPuS63PUKxArSQMV_gpekWi3gsphEBE_/view?usp=sharing)


## How it works

```
PDF upload
   │
   ▼
1. Extract text ............... pdfplumber
   │
   ▼
2. Extract claims .............  Groq (Llama 3.3 70B) reads the text and
   │                             pulls out statistics, dates, financial and
   │                             technical figures as structured JSON.
   ▼
3. Search the live web ........  Tavily searches the web for each claim and
   │                             returns clean, structured evidence.
   ▼
4. Adjudicate a verdict ........ Groq (Llama 3.3 70B) compares the claim to
   │                             the search evidence and returns Verified /
   │                             Inaccurate / False + the correct fact +
   │                             sources.
   ▼
5. Report ....................... Streamlit UI: summary counts, a color-coded
                                   card per claim, and a downloadable JSON report.
```

Both APIs used are **free, no credit card required**:
- **[Groq](https://console.groq.com)** -- free-tier inference for Llama 3.3 70B (fast, supports JSON mode).
- **[Tavily](https://tavily.com)** -- 1,000 free search credits/month, purpose-built for AI agents.

## Project structure

```
fact-check-agent/
├── app.py                          # Streamlit UI + pipeline orchestration
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   ├── config.toml                 # theme
│   └── secrets.toml.example        # copy to secrets.toml, fill in your keys
└── utils/
    ├── __init__.py
    ├── config.py                   # API key loading + tunable settings
    ├── pdf_utils.py                # PDF -> text, chunking
    ├── groq_client.py              # Groq chat wrapper (JSON-mode + fallback parsing)
    ├── claim_extraction.py         # Step 2: extract claims
    ├── web_search.py               # Step 3: Tavily search
    └── fact_checker.py             # Step 4: verdict adjudication
```

## Setup (local)

**1. Clone and install**

```bash
git clone <your-repo-url>
cd fact-check-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Get free API keys**

| Provider | Free tier | Get a key |
|---|---|---|
| Groq | Generous daily request limit on Llama 3.3 70B, no card | [console.groq.com/keys](https://console.groq.com/keys) -- sign up, click "Create API Key" |
| Tavily | 1,000 search credits/month, no card | [app.tavily.com](https://app.tavily.com) -- sign up, copy the key from your dashboard |

**3. Add the keys locally**

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_..."
TAVILY_API_KEY = "tvly_..."
```

This file is already in `.gitignore` -- it will never be committed.

**4. Run it**

```bash
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`), upload a PDF, and click **Run Fact-Check**.

## Deploying to Streamlit Community Cloud

1. Push this project to a **public GitHub repo** (keep `.streamlit/secrets.toml` out of it -- only `secrets.toml.example` should be committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → pick your repo, branch (`main`), and main file path (`app.py`).
4. Before/after deploying, open **Settings → Secrets** on the app and paste:
   ```toml
   GROQ_API_KEY = "gsk_..."
   TAVILY_API_KEY = "tvly_..."
   ```
5. Click **Deploy**. You'll get a public URL like `https://your-app-name.streamlit.app`.

That URL is what you share as the "Deployed App Link" deliverable -- anyone can visit it and upload their own PDF, no setup required on their end.

## Usage

1. Open the app (locally or the deployed URL).
2. Upload a PDF containing factual claims (a one-pager, blog draft, pitch deck export, etc.).
3. Optionally adjust **Max claims to check** in the sidebar (default 15 -- keeps a single run comfortably inside both free tiers).
4. Click **Run Fact-Check** and watch the live progress (extracting → searching → verifying).
5. Read the report: summary counts at the top, then one card per claim with its verdict, explanation, the correct fact (if not Verified), and source links.
6. Click **Download full report (JSON)** to save the results.

## Notes & limitations

- **No OCR**: this app reads a PDF's embedded text layer (via `pdfplumber`). A pure scanned-image PDF with no text layer will return "couldn't extract any text." Adding OCR (e.g. `pytesseract`) would be a natural next step.
- **Claim cap**: each verified claim costs 1 Tavily search + 2 Groq calls, so the app caps how many claims it checks per run (adjustable in the sidebar, default 15) to stay inside free-tier rate limits on documents with many claims.
- **Verdicts are evidence-based, not omniscient**: the model is explicitly instructed to decide using only the live search results it's given, not its own training data, which is what makes it catch outdated stats that the model itself might otherwise have memorized as "true."
- **Sequential processing**: claims are verified one at a time (not in parallel) to stay well under both providers' requests-per-minute limits.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Streamlit | Fastest path to a clean, deployable UI for a file-upload + report workflow |
| LLM | Groq -- Llama 3.3 70B Versatile | Free tier, fast inference, native JSON mode for reliable structured output |
| Web search | Tavily | Built specifically for LLM/agent use cases; returns clean structured content instead of raw HTML |
| PDF parsing | pdfplumber | Reliable text extraction across most PDF layouts |
