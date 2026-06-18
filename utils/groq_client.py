"""Thin wrapper around the Groq chat completions API.

Groq's hosted Llama models support OpenAI-style JSON mode
(response_format={"type": "json_object"}), which is far more reliable than
asking the model nicely and hoping it skips the Markdown code fence. This
module uses JSON mode when available and falls back to fence-stripping +
regex extraction if a model/response ever doesn't cooperate.
"""
import json
import re

from groq import Groq

from . import config

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to .streamlit/secrets.toml "
                "locally, or to your app's Secrets in Streamlit Community Cloud."
            )
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def chat_json(system_prompt: str, user_prompt: str, model: str, temperature: float = 0.1):
    """Call the chat completion API and return the parsed JSON response.

    The system prompt MUST instruct the model to return a single JSON
    object (Groq's JSON mode requires a top-level object, not a bare array
    -- so list-producing prompts should ask for e.g. {"claims": [...]}).
    """
    client = get_client()

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass  # fall through to the no-JSON-mode retry below
    except Exception as exc:
        # response_format unsupported by this model, or another API error.
        # Retry once without it before giving up.
        if "response_format" not in str(exc).lower():
            raise

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content
    cleaned = _strip_code_fence(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise
