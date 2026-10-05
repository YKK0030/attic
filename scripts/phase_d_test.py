"""Offline Phase D tenant-isolation check."""
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
os.environ["ATTIC_DB"] = os.path.join(tempfile.gettempdir(), f"attic-phase-d-{uuid.uuid4().hex}.sqlite")
from attic_api import config, db
config.DB_PATH = os.environ["ATTIC_DB"]
db.DB_PATH = config.DB_PATH
from attic_api.core import audit, get_memory, recent_activity, recall, remember

db.init_db()
config.CURRENT_TENANT.set("tenant-a")
a = remember("same fact", "a", [], "shared")
config.CURRENT_TENANT.set("tenant-b")
b = remember("same fact", "b", [], "shared")
assert a["id"] != b["id"]
config.CURRENT_TENANT.set("tenant-a")
assert remember("event a", "a", [], "shared", idempotency_key="event-1")["skipped"] is False
config.CURRENT_TENANT.set("tenant-b")
assert remember("event b", "b", [], "shared", idempotency_key="event-1")["skipped"] is False
assert get_memory(a["id"]) is None
assert get_memory(b["id"])["tenant_id"] == "tenant-b"
assert not recall("same fact", 5, "shared") == [a]
assert audit(a["id"]) == []
config.CURRENT_TENANT.set("tenant-a")
assert recall("same fact", 5, "shared")
assert audit(a["id"])
assert recent_activity(10)
print("phase D ok")
