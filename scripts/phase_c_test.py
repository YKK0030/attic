"""Offline Phase C contract check."""
import os
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
os.environ["ATTIC_DB"] = os.path.join(tempfile.gettempdir(), f"attic-phase-c-{uuid.uuid4().hex}.sqlite")

from attic_api import config, db
config.DB_PATH = os.environ["ATTIC_DB"]
db.DB_PATH = config.DB_PATH
from attic_api.core import remember

db.init_db()
first = remember("Webhook fact", "test", [], "phase-c", idempotency_key="webhook:e-1")
second = remember("Changed replay payload", "test", [], "phase-c", idempotency_key="webhook:e-1")
assert first["skipped"] is False
assert second["skipped"] is True

main_source = Path(__file__).parents[1] / "apps/api/attic_api/main.py"
source = main_source.read_text()
for marker in ("/conversations", "/webhooks/memory", "/openai/tools", 'app.include_router(router, prefix="/v1")'):
    assert marker in source
print("phase C ok")
