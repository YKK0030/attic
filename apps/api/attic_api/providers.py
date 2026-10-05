import json
import os
from urllib.request import Request, urlopen

from .ollama import answer as ollama_answer
from .ollama import embed as ollama_embed


def _post(url: str, payload: dict, headers: dict) -> dict:
    request = Request(url, data=json.dumps(payload).encode(), headers={"content-type": "application/json", **headers})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def embed(text: str) -> list[float]:
    provider = os.getenv("EMBED_PROVIDER", "ollama")
    if provider == "ollama":
        return ollama_embed(text)
    if provider == "openai":
        result = _post("https://api.openai.com/v1/embeddings", {"model": os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"), "input": text}, {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
        return result["data"][0]["embedding"]
    if provider == "voyage":
        result = _post("https://api.voyageai.com/v1/embeddings", {"model": os.getenv("VOYAGE_EMBED_MODEL", "voyage-3-lite"), "input": [text]}, {"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}"})
        return result["data"][0]["embedding"]
    raise ValueError(f"unsupported EMBED_PROVIDER: {provider}")


def answer(question: str, context: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        return ollama_answer(question, context)
    prompt = "Answer only from context. Say you do not know when context lacks the answer.\n\nContext:\n" + context + "\n\nQuestion: " + question
    if provider == "openai":
        result = _post("https://api.openai.com/v1/chat/completions", {"model": os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"), "messages": [{"role": "user", "content": prompt}]}, {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
        return result["choices"][0]["message"]["content"].strip()
    if provider == "claude":
        result = _post("https://api.anthropic.com/v1/messages", {"model": os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest"), "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]}, {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
        return result["content"][0]["text"].strip()
    raise ValueError(f"unsupported LLM_PROVIDER: {provider}")
