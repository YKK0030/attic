# Attic test cases

Run against a started API:

```sh
python3 scripts/smoke_test.py
```

The script checks:

1. Health endpoint returns `200` and `ok: true`.
2. Two memories write to SQLite and Qdrant.
3. SHA-256 deduplication skips the same content.
4. Semantic recall returns the marker memory.
5. Tag filtering returns only matching memories.
6. `/ask` returns grounded context and sources.
7. `/surface` returns a list.
8. Delete removes both SQLite and Qdrant memory records.

Manual UI checks:

- Open `http://localhost:4000`.
- Search a known phrase; results show source and score.
- Click `Ask`; answer shows retrieved sources.
- Click `refresh`; connections list updates.
- Search nonsense such as `akj`; empty state appears, API still returns `200`.

Expected log lines:

```text
GET / 200
GET /health 200
POST /memory 200
GET /recall?... 200
GET /ask?... 200
```
