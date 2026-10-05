import os
import json
from contextvars import ContextVar
from pathlib import Path

DB_PATH = Path(os.getenv("ATTIC_DB", "attic.db"))
API_KEY = os.getenv("ATTIC_API_KEY", "dev-key")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "attic_memories")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:0.5b-instruct")
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.45"))
MAX_REQUEST_BYTES = int(os.getenv("ATTIC_MAX_REQUEST_BYTES", "1048576"))
RATE_LIMIT = int(os.getenv("ATTIC_RATE_LIMIT", "120"))
RATE_WINDOW_SECONDS = int(os.getenv("ATTIC_RATE_WINDOW_SECONDS", "60"))
try:
    TENANT_KEYS = json.loads(os.getenv("ATTIC_TENANT_KEYS", "{}"))
except json.JSONDecodeError:
    TENANT_KEYS = {}
if not TENANT_KEYS:
    TENANT_KEYS = {API_KEY: "default"}
CURRENT_TENANT = ContextVar("attic_tenant", default="default")


def tenant_for_key(key: str | None) -> str | None:
    return TENANT_KEYS.get(key)
