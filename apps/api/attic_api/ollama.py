import json
from urllib.request import Request, urlopen

from .config import OLLAMA_EMBED_MODEL, OLLAMA_LLM_MODEL, OLLAMA_URL


def _post(path: str, payload: dict) -> dict:
    request = Request(
        f"{OLLAMA_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
    )
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def embed(text: str) -> list[float]:
    response = _post("/api/embed", {"model": OLLAMA_EMBED_MODEL, "input": text})
    return response["embeddings"][0]


def answer(question: str, context: str) -> str:
    prompt = (
        "Answer only from the context. If context does not contain the answer, say "
        "you do not know.\n\nContext:\n" + context + "\n\nQuestion: " + question
    )
    response = _post("/api/generate", {"model": OLLAMA_LLM_MODEL, "prompt": prompt, "stream": False})
    return response["response"].strip()
