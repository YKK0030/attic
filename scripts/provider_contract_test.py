import os

from api.attic_api import providers


def fake_post(url, payload, headers):
    if "embeddings" in url:
        return {"data": [{"embedding": [0.1, 0.2]}]}
    if "anthropic" in url:
        return {"content": [{"text": "claude answer"}]}
    return {"choices": [{"message": {"content": "openai answer"}}]}


providers._post = fake_post
os.environ["OPENAI_API_KEY"] = "test"
os.environ["VOYAGE_API_KEY"] = "test"
os.environ["ANTHROPIC_API_KEY"] = "test"

os.environ["EMBED_PROVIDER"] = "openai"
assert providers.embed("x") == [0.1, 0.2]
os.environ["EMBED_PROVIDER"] = "voyage"
assert providers.embed("x") == [0.1, 0.2]
os.environ["LLM_PROVIDER"] = "openai"
assert providers.answer("q", "c") == "openai answer"
os.environ["LLM_PROVIDER"] = "claude"
assert providers.answer("q", "c") == "claude answer"
print("provider contract self-check: ok")
