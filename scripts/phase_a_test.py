"""Offline Phase A acceptance check."""
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

os.environ["ATTIC_DB"] = os.path.join(tempfile.gettempdir(), f"attic-phase-a-{uuid.uuid4().hex}.sqlite")
from attic_api import config, db
config.DB_PATH = os.environ["ATTIC_DB"]
db.DB_PATH = config.DB_PATH
from attic_api.core import audit, export_memories, get_memory, remember, supersede, update_memory

db.init_db()
first = remember("original fact", "test", ["a"], "test", actor="test", source_uri="unit://1")
assert get_memory(first["id"])["source_uri"] == "unit://1"
update_memory(first["id"], actor="test", content="updated fact", metadata={"kind": "demo"})
assert get_memory(first["id"])["content"] == "updated fact"
second = supersede(first["id"], {"content": "replacement", "source": "test", "tags": [], "namespace": "test"}, "test")
assert get_memory(first["id"])["status"] == "superseded"
assert get_memory(second["id"])["supersedes_id"] == first["id"]
assert [event["action"] for event in audit(first["id"])] == ["created", "updated", "updated", "superseded"]
assert len(export_memories("test")["memories"]) == 2
print("phase A ok")
