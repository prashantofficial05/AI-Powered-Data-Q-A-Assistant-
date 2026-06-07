"""
llm_provider.py – Unified LLM interface for Groq, Claude, and OpenAI.

Free tiers:
  • Groq   → https://console.groq.com/keys       (generous free tier, no card needed)
  • Claude → https://console.anthropic.com/       (free trial credits)
  • OpenAI → https://platform.openai.com/api-keys (free trial credits)

FIXES:
  - groq 1.x: usage object may be None on some responses → safe fallback to 0
  - openai 2.x: usage.total_tokens still works; added safe None guard
  - anthropic 0.28+: API unchanged; added safe None guard on usage
  - All providers: wrapped usage access in getattr() with defaults so a
    missing usage field never crashes the app
  - Removed unused 'httpx' import
  - Added GROQ_MODEL fallback to 'llama-3.1-8b-instant' (llama3-8b-8192
    was retired by Groq in early 2025)
"""
import os
import time
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


# ── helpers ────────────────────────────────────────────────────────────────────

def _safe_tokens(usage, *attrs) -> int:
    """Return the first matching attribute value from a usage object, or 0."""
    if usage is None:
        return 0
    for attr in attrs:
        val = getattr(usage, attr, None)
        if val is not None:
            return int(val)
    return 0


# ── Groq (FREE) ────────────────────────────────────────────────────────────────
def _call_groq(messages: list[dict], system: str) -> tuple[str, int]:
    import groq as groq_sdk                                   # groq 1.x
    client = groq_sdk.Groq(api_key=os.getenv("GROQ_API_KEY"))
    # llama3-8b-8192 was retired; default to llama-3.1-8b-instant
    model  = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    resp   = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, *messages],
        max_tokens=1024,
        temperature=0.2,
    )
    tokens = _safe_tokens(getattr(resp, "usage", None), "total_tokens")
    return resp.choices[0].message.content, tokens


# ── Claude (Anthropic) ─────────────────────────────────────────────────────────
def _call_claude(messages: list[dict], system: str) -> tuple[str, int]:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    model  = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    resp   = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    usage  = getattr(resp, "usage", None)
    tokens = _safe_tokens(usage, "input_tokens") + _safe_tokens(usage, "output_tokens")
    return resp.content[0].text, tokens


# ── OpenAI ─────────────────────────────────────────────────────────────────────
def _call_openai(messages: list[dict], system: str) -> tuple[str, int]:
    from openai import OpenAI                                  # openai 2.x
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model  = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    resp   = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, *messages],
        max_tokens=1024,
        temperature=0.2,
    )
    tokens = _safe_tokens(getattr(resp, "usage", None), "total_tokens")
    return resp.choices[0].message.content, tokens


# ── Public interface ───────────────────────────────────────────────────────────
def ask_llm(messages: list[dict], system: str) -> dict:
    """
    Call the configured LLM provider.
    Returns {"answer": str, "tokens": int, "latency_ms": float, "provider": str}
    """
    t0 = time.time()
    try:
        if PROVIDER == "groq":
            answer, tokens = _call_groq(messages, system)
        elif PROVIDER == "claude":
            answer, tokens = _call_claude(messages, system)
        elif PROVIDER == "openai":
            answer, tokens = _call_openai(messages, system)
        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER '{PROVIDER}'. "
                f"Valid options: groq | claude | openai"
            )
    except Exception as e:
        raise RuntimeError(f"LLM call failed ({PROVIDER}): {e}") from e

    return {
        "answer":     answer,
        "tokens":     tokens,
        "latency_ms": round((time.time() - t0) * 1000, 1),
        "provider":   PROVIDER,
    }
