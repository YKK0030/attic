"""Offline Phase B retrieval acceptance check."""
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
os.environ["ATTIC_DB"] = os.path.join(tempfile.gettempdir(), f"attic-phase-b-{uuid.uuid4().hex}.sqlite")
from attic_api import config, db
config.DB_PATH = os.environ["ATTIC_DB"]
db.DB_PATH = config.DB_PATH
from attic_api.core import build_context, recall, reindex, remember

db.init_db()
remember("Python uses FastAPI for the Attic API", "api.md", ["code"], "bench", memory_type="fact", agent_id="agent-a")
remember("The garden needs water every morning", "home.md", ["home"], "bench", memory_type="fact", agent_id="agent-b")
remember("Python uses Flask for an unrelated old prototype", "old.md", ["old"], "other")

hits = recall("FastAPI Python", 5, "bench", mode="keyword", memory_type="fact", agent_id="agent-a")
assert hits and hits[0]["source"] == "api.md"
assert "keyword" in hits[0]["retrieval"]
context = build_context("FastAPI", "bench", max_chars=80)
assert context["chars"] <= 80
assert len(context["context"]) <= 80
assert context["sources"][0]["memory_id"] == hits[0]["id"]
assert reindex("bench", dry_run=True)["scanned"] == 2
print("phase B ok")
