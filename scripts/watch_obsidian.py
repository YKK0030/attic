import os
import time
from pathlib import Path

from api.attic_api.ingestion.pipeline import run

vault = Path(os.environ.get("OBSIDIAN_VAULT", "./notes"))
namespace = os.environ.get("ATTIC_NAMESPACE", "obsidian")
seen = {}
print(f"Watching {vault} in namespace {namespace}")
while True:
    for file in vault.rglob("*"):
        if file.is_file() and file.suffix.lower() in {".md", ".txt", ".pdf"}:
            modified = file.stat().st_mtime_ns
            if seen.get(file) != modified:
                run(file, namespace)
                seen[file] = modified
    time.sleep(float(os.environ.get("OBSIDIAN_POLL_SECONDS", "10")))
