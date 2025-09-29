from __future__ import annotations

import os
import time
from typing import Dict, Any, Optional, List

import requests


class OllamaClient:
    """Minimal client for interacting with a local Ollama server.

    Default endpoint: http://localhost:11434
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, timeout: float = 60.0) -> None:
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3:latest")
        self.timeout = timeout

    def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return (data.get("response") or "").strip()
        except Exception:
            return ""


class GeminiClient:
    """Client for Google Generative Language (Gemini) API.

    Docs: https://ai.google.dev/api/rest/v1beta/models.generateContent
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.timeout = timeout

    def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        if not self.api_key:
            return ""
        base = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
        url = f"{base.rstrip('/')}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # Extract first candidate text
            candidates: List[Dict[str, Any]] = data.get("candidates") or []
            if not candidates:
                return ""
            parts = ((candidates[0].get("content") or {}).get("parts") or [])
            texts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
            return ("\n".join(texts)).strip()
        except Exception:
            return ""


def get_default_llm_provider() -> str:
    """Return provider per env with fallbacks.

    LLM_PROVIDER can be: gemini | ollama | openai_compat
    If not set: prefer gemini if key exists, else ollama.
    """
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if provider in {"gemini", "ollama", "openai_compat"}:
        return provider
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    return "ollama"


class OpenAICompatClient:
    """Client for OpenAI-compatible HTTP APIs (e.g., vLLM, llama.cpp server).

    Expects env:
      OPENAI_COMPAT_BASE_URL (e.g., http://localhost:8001/v1)
      OPENAI_COMPAT_API_KEY (optional)
      OPENAI_COMPAT_MODEL   (e.g., llama-3-8b-instruct)
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 60.0) -> None:
        self.base_url = base_url or os.getenv("OPENAI_COMPAT_BASE_URL", "http://localhost:8001/v1")
        self.api_key = api_key or os.getenv("OPENAI_COMPAT_API_KEY")
        self.model = model or os.getenv("OPENAI_COMPAT_MODEL", "llama-3-8b-instruct")
        self.timeout = timeout

    def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                return ""
            msg = choices[0].get("message") or {}
            return (msg.get("content") or "").strip()
        except Exception:
            return ""


def concise_reasoning_for_verdict(verdict: str, claim_text: str, evidence_titles: list[str]) -> str:
    """Create a compact prompt and request a concise reasoning from the LLM.

    This helper uses a short instruction to keep latency low.
    """
    titles_text = "; ".join(evidence_titles[:5]) if evidence_titles else "(no evidence titles)"
    instruction = (
        "You are a careful fact-checking assistant. \n"
        "Given a claim, a tentative verdict, and a list of evidence titles, write a single-sentence reasoning "
        "(<= 40 words) that justifies the verdict conservatively. Avoid hallucinations; do not cite unknown data."
    )
    prompt = (
        f"{instruction}\n\n"
        f"Claim: {claim_text}\n"
        f"Verdict: {verdict}\n"
        f"Evidence Titles: {titles_text}\n\n"
        f"One-sentence reasoning:"
    )

    provider = get_default_llm_provider()
    if provider == "gemini":
        client = GeminiClient()
    elif provider == "openai_compat":
        client = OpenAICompatClient()
    else:
        client = OllamaClient()
    output = client.generate(prompt)
    # Ensure single-line, trimmed output
    return " ".join(output.split())[:300]


def preliminary_reasoning_for_claim(claim_text: str, evidence_titles: list[str]) -> str:
    """Generate a brief, neutral reasoning about a claim using evidence titles only.

    Used during verification to compare reasoning embeddings with evidence.
    """
    titles_text = "; ".join(evidence_titles[:5]) if evidence_titles else "(no evidence titles)"
    instruction = (
        "You are a careful analyst. \n"
        "Given a claim and a list of evidence titles, write a neutral, one-sentence summary (<= 30 words) "
        "capturing the main justification that could be supported by these titles. Avoid any unsupported details."
    )
    prompt = (
        f"{instruction}\n\n"
        f"Claim: {claim_text}\n"
        f"Evidence Titles: {titles_text}\n\n"
        f"One-sentence neutral reasoning:"
    )
    provider = get_default_llm_provider()
    if provider == "gemini":
        client = GeminiClient()
    elif provider == "openai_compat":
        client = OpenAICompatClient()
    else:
        client = OllamaClient()
    output = client.generate(prompt)
    return " ".join(output.split())[:240]


