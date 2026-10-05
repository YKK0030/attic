from pathlib import Path

from ..core import remember
from .parsers import read


def files(path: Path):
    allowed = {".md", ".txt", ".pdf"}
    paths = [path] if path.is_file() else sorted(path.rglob("*"))
    return (item for item in paths if item.is_file() and item.suffix.lower() in allowed)


def run(path: Path, namespace: str = "default") -> list[dict]:
    return [remember(read(item), str(item), [], namespace) for item in files(path)]
