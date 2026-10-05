import os
import subprocess
from html.parser import HTMLParser
from urllib.request import Request, urlopen


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def clip(url: str) -> tuple[str, str]:
    request = Request(url, headers={"user-agent": "Attic/0.1"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
    parser = TextParser()
    parser.feed(html)
    return "\n".join(parser.parts), url


def transcribe(path: str) -> str:
    binary = os.getenv("WHISPER_BIN", "whisper-cli")
    result = subprocess.run([binary, path], check=True, capture_output=True, text=True)
    return result.stdout.strip()
