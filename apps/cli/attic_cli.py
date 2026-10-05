import argparse
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import os

from api.attic_api.integrations import clip, transcribe
from api.attic_api.ingestion.parsers import read


def call(base: str, method: str, path: str, data: dict | None = None):
    body = json.dumps(data).encode() if data else None
    req = Request(base + path, data=body, method=method, headers={"x-attic-key": "dev-key", "Content-Type": "application/json"})
    with urlopen(req) as response:
        return json.load(response)


parser = argparse.ArgumentParser(prog="attic")
parser.add_argument("--url", default="http://localhost:4000")
sub = parser.add_subparsers(dest="command", required=True)
ingest = sub.add_parser("ingest")
ingest.add_argument("path", type=Path)
ingest.add_argument("--namespace", default="default")
ingest.add_argument("--tag", action="append", default=[])
search = sub.add_parser("search")
search.add_argument("query")
search.add_argument("--namespace", default="default")
search.add_argument("--tag")
search.add_argument("--limit", type=int, default=5)
ask = sub.add_parser("ask")
ask.add_argument("question")
forget = sub.add_parser("forget")
forget.add_argument("memory_id")
sub.add_parser("status")
clip_command = sub.add_parser("clip")
clip_command.add_argument("clip_url")
voice = sub.add_parser("voice")
voice.add_argument("path", type=Path)
sub.add_parser("notion")
args = parser.parse_args()

if args.command == "ingest":
    for file in ([args.path] if args.path.is_file() else args.path.rglob("*")):
        if file.is_file() and file.suffix.lower() in {".md", ".txt", ".pdf"}:
            print(json.dumps(call(args.url, "POST", "/memory", {"content": read(file), "source": str(file), "tags": args.tag, "namespace": args.namespace})))
elif args.command == "search":
    query = quote(args.query)
    params = f"q={query}&namespace={quote(args.namespace)}&limit={args.limit}"
    if args.tag:
        params += "&tag=" + quote(args.tag)
    print(json.dumps(call(args.url, "GET", "/recall?" + params)))
elif args.command == "ask":
    print(json.dumps(call(args.url, "GET", "/ask?q=" + quote(args.question))))
elif args.command == "forget":
    print(json.dumps(call(args.url, "DELETE", "/memory/" + quote(args.memory_id))))
elif args.command == "clip":
    content, source = clip(args.clip_url)
    print(json.dumps(call(args.url, "POST", "/memory", {"content": content, "source": source})))
elif args.command == "voice":
    content = transcribe(str(args.path))
    print(json.dumps(call(args.url, "POST", "/memory", {"content": content, "source": str(args.path), "tags": ["voice"]})))
elif args.command == "notion":
    token = os.environ["NOTION_TOKEN"]
    database = os.environ["NOTION_DATABASE_ID"]
    request = Request(f"https://api.notion.com/v1/databases/{database}/query", method="POST", headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28", "content-type": "application/json"}, data=b"{}")
    with urlopen(request) as response:
        pages = json.load(response)["results"]
    for page in pages:
        title = page.get("properties", {}).get("title", {}).get("title", [])
        name = "".join(item.get("plain_text", "") for item in title)
        if name:
            print(json.dumps(call(args.url, "POST", "/memory", {"content": name, "source": f"notion:{page['id']}", "tags": ["notion"]})))
else:
    print(json.dumps(call(args.url, "GET", "/health")))
