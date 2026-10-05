import hashlib
import json
import re
import uuid
from datetime import datetime, timezone

from .config import CURRENT_TENANT
from .db import connect


def _tenant(tenant_id: str | None = None) -> str:
    return tenant_id or CURRENT_TENANT.get()


def chunks(text: str, size: int = 512, overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    return [" ".join(words[i:i + size]) for i in range(0, len(words), step)]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit(db, memory_id: str, action: str, actor: str, metadata: dict | None = None) -> None:
    db.execute("INSERT INTO audit_log(id,memory_id,action,actor,tenant_id,metadata) VALUES(?,?,?,?,?,?)",
               (uuid.uuid4().hex, memory_id, action, actor, _tenant(), json.dumps(metadata or {})))


def remember(content: str, source: str, tags: list[str], namespace: str,
             memory_type: str = "document", source_uri: str | None = None,
             agent_id: str | None = None, user_id: str | None = None,
             valid_from: str | None = None, valid_until: str | None = None,
             confidence: float = 1.0, status: str = "active",
             supersedes_id: str | None = None, actor: str = "system",
             metadata: dict | None = None, memory_id: str | None = None,
             idempotency_key: str | None = None, tenant_id: str | None = None) -> dict:
    tenant_id = _tenant(tenant_id)
    digest = hashlib.sha256(content.encode()).hexdigest()
    with connect() as db:
        old = db.execute(
            "SELECT id FROM documents WHERE tenant_id=? AND namespace=? AND content_hash=?",
            (tenant_id, namespace, digest),
        ).fetchone()
        if not old and idempotency_key:
            old = db.execute(
                "SELECT id FROM documents WHERE tenant_id=? AND namespace=? AND idempotency_key=?",
                (tenant_id, namespace, idempotency_key),
            ).fetchone()
        if old:
            return {"id": old["id"], "chunks": len(chunks(content)), "tags": tags, "skipped": True}
        doc_id = memory_id or uuid.uuid4().hex
        db.execute(
            """INSERT INTO documents
             (id,namespace,source,source_type,content_hash,tenant_id,tags,content,memory_type,
             source_uri,agent_id,user_id,valid_from,valid_until,confidence,status,
             supersedes_id,metadata,idempotency_key) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (doc_id, namespace, source, "api", digest, tenant_id, json.dumps(tags), content,
             memory_type, source_uri, agent_id, user_id, valid_from, valid_until,
             confidence, status, supersedes_id, json.dumps(metadata or {}), idempotency_key),
        )
        _audit(db, doc_id, "created", actor, {"source": source})
    pieces = chunks(content)
    vectors = 0
    try:
        from .vector import upsert
        vectors = upsert(doc_id, namespace, source, tags, pieces, metadata=metadata or {}, status=status, tenant_id=tenant_id)
    except Exception:
        pass
    return {"id": doc_id, "chunks": len(pieces), "vectors": vectors, "tags": tags, "skipped": False}


def _keyword_recall(query: str, namespace: str, limit: int, tag: str | None = None, tenant_id: str | None = None) -> list[dict]:
    tenant_id = _tenant(tenant_id)
    terms = re.findall(r"[\w-]+", query.lower())
    if not terms:
        return []
    match = " OR ".join(f'"{term.replace(chr(34), "")}"' for term in terms)
    with connect() as db:
        try:
            rows = db.execute("""SELECT d.* FROM documents_fts f JOIN documents d ON d.id=f.id
                WHERE documents_fts MATCH ? AND d.tenant_id=? AND d.namespace=? ORDER BY bm25(documents_fts) LIMIT ?""", (match, tenant_id, namespace, limit)).fetchall()
        except Exception:
            rows = db.execute("SELECT * FROM documents WHERE tenant_id=? AND namespace=?", (tenant_id, namespace)).fetchall()
    results = []
    for row in rows:
        if not _is_visible(row):
            continue
        tags = json.loads(row["tags"] or "[]")
        if tag and tag not in tags:
            continue
        words = set(re.findall(r"\w+", row["content"].lower()))
        score = len(set(terms) & words) / max(1, len(set(terms)))
        if score:
            results.append(_result(row, round(score, 3), ["keyword"]))
    return results


def _result(row, score: float, retrieval: list[str], chunk_index: int | None = None) -> dict:
    return {
        "id": row["id"], "content": row["content"], "source": row["source"],
        "source_uri": row["source_uri"], "namespace": row["namespace"],
        "score": score, "retrieval": retrieval, "chunk_index": chunk_index,
        "citation": {"memory_id": row["id"], "source": row["source"]},
        "status": row["status"], "tags": json.loads(row["tags"] or "[]"),
        "date": row["updated_at"],
    }


def recall(query: str, limit: int, namespace: str, tag: str | None = None,
           mode: str = "hybrid", memory_type: str | None = None,
           agent_id: str | None = None, user_id: str | None = None,
           valid_at: str | None = None, tenant_id: str | None = None) -> list[dict]:
    tenant_id = _tenant(tenant_id)
    candidate_limit = max(limit * 4, 20)
    keyword = _keyword_recall(query, namespace, candidate_limit, tag, tenant_id) if mode in {"keyword", "hybrid", "context", "timeline"} else []
    dense = []
    if mode in {"semantic", "hybrid", "context", "timeline"}:
        try:
            from .vector import search
            dense = search(query, namespace, candidate_limit, tag, tenant_id)
        except Exception:
            dense = []
    by_id = {}
    for rank, item in enumerate(keyword, 1):
        item["keyword_score"] = item["score"]
        item["rrf_score"] = 1 / (60 + rank)
        by_id[item["id"]] = item
    if dense:
        ids = {item["id"] for item in dense}
        with connect() as db:
            placeholders = ",".join("?" * len(ids))
            rows = {row["id"]: row for row in db.execute(f"SELECT * FROM documents WHERE tenant_id=? AND id IN ({placeholders})", (tenant_id, *ids))}
        for rank, item in enumerate(dense, 1):
            row = rows.get(item["id"])
            if not row or not _is_visible(row):
                continue
            current = by_id.get(item["id"]) or _result(row, item["score"], [])
            current["semantic_score"] = item["score"]
            current["rrf_score"] = current.get("rrf_score", 0) + 1 / (60 + rank)
            current["retrieval"] = sorted(set(current.get("retrieval", [])) | {"vector"})
            current["score"] = max(current.get("score", 0), item["score"])
            by_id[item["id"]] = current
    with connect() as db:
        rows = {row["id"]: row for row in db.execute("SELECT * FROM documents WHERE tenant_id=? AND namespace=?", (tenant_id, namespace))}
    filtered = []
    for item in by_id.values():
        row = rows.get(item["id"])
        if not row or not _is_visible(row):
            continue
        if memory_type and row["memory_type"] != memory_type:
            continue
        if agent_id and row["agent_id"] != agent_id:
            continue
        if user_id and row["user_id"] != user_id:
            continue
        if valid_at and not ((not row["valid_from"] or row["valid_from"] <= valid_at) and (not row["valid_until"] or row["valid_until"] > valid_at)):
            continue
        filtered.append(item)
    return _dedupe(sorted(filtered, key=lambda item: (item.get("rrf_score", 0), item["score"]), reverse=True), limit)


def _dedupe(results: list[dict], limit: int) -> list[dict]:
    seen_ids = set()
    unique = []
    for item in results:
        if item["id"] in seen_ids:
            continue
        item["retrieval"] = sorted(item.get("retrieval", []))
        unique.append(item)
        seen_ids.add(item["id"])
        if len(unique) >= limit:
            break
    return unique


def build_context(query: str, namespace: str = "default", limit: int = 5,
                  max_chars: int = 6000, **filters) -> dict:
    hits = recall(query, limit, namespace, mode="context", **filters)
    selected, blocks, used = [], [], 0
    for hit in hits:
        block = f"[{hit['source']} | memory:{hit['id']}]\n{hit['content']}"
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining]
        selected.append(hit)
        blocks.append(block)
        used += len(block)
    return {"query": query, "context": "\n\n".join(blocks), "sources": [h["citation"] | {"score": h["score"]} for h in selected], "hits": selected, "chars": used, "max_chars": max_chars}


def reindex(namespace: str | None = None, dry_run: bool = False) -> dict:
    tenant_id = _tenant()
    from .config import OLLAMA_EMBED_MODEL
    with connect() as db:
        query, args = "SELECT * FROM documents WHERE tenant_id=?", (tenant_id,)
        if namespace:
            query, args = query + " AND namespace=?", (tenant_id, namespace)
        rows = db.execute(query, args).fetchall()
    result = {"scanned": len(rows), "indexed": 0, "failed": 0, "dry_run": dry_run}
    if dry_run:
        return result
    try:
        from .vector import delete, upsert
        for row in rows:
            try:
                delete(row["id"])
                upsert(row["id"], row["namespace"], row["source"], json.loads(row["tags"]), chunks(row["content"]), json.loads(row["metadata"] or "{}"), row["status"], tenant_id)
                result["indexed"] += 1
            except Exception:
                result["failed"] += 1
    except Exception:
        result["failed"] = len(rows)
    now = _now()
    with connect() as db:
        scopes = {row["namespace"] for row in rows}
        for scope in scopes:
            db.execute("INSERT OR REPLACE INTO index_metadata(namespace,provider,model,dimension,chunk_size,chunk_overlap,indexed_at) VALUES(?,?,?,?,?,?,?)", (scope, "ollama", OLLAMA_EMBED_MODEL, None, 512, 50, now))
    return result


def forget(document_id: str, tenant_id: str | None = None) -> bool:
    tenant_id = _tenant(tenant_id)
    with connect() as db:
        found = db.execute("SELECT id FROM documents WHERE tenant_id=? AND id=?", (tenant_id, document_id)).fetchone()
        if not found:
            return False
        _audit(db, document_id, "deleted", "system")
        db.execute("DELETE FROM documents WHERE id=?", (document_id,))
    try:
        from .vector import delete
        delete(document_id)
    except Exception:
        pass
    return True


def _is_visible(row) -> bool:
    now = _now()
    return row["status"] == "active" and (not row["valid_from"] or row["valid_from"] <= now) and (not row["valid_until"] or row["valid_until"] > now)


def get_memory(document_id: str, tenant_id: str | None = None) -> dict | None:
    tenant_id = _tenant(tenant_id)
    with connect() as db:
        row = db.execute("SELECT * FROM documents WHERE tenant_id=? AND id=?", (tenant_id, document_id)).fetchone()
    return _row_dict(row) if row else None


def _row_dict(row) -> dict:
    item = dict(row)
    item["tags"] = json.loads(item["tags"] or "[]")
    item["metadata"] = json.loads(item.get("metadata") or "{}")
    return item


def update_memory(document_id: str, actor: str = "system", **changes) -> dict | None:
    tenant_id = _tenant(changes.pop("tenant_id", None))
    allowed = {"content", "source", "tags", "namespace", "memory_type", "source_uri", "agent_id", "user_id", "valid_from", "valid_until", "confidence", "status", "metadata"}
    changes = {key: value for key, value in changes.items() if key in allowed and value is not None}
    if not changes:
        return get_memory(document_id)
    with connect() as db:
        current = db.execute("SELECT * FROM documents WHERE tenant_id=? AND id=?", (tenant_id, document_id)).fetchone()
        if not current:
            return None
        if "content" in changes:
            changes["content_hash"] = hashlib.sha256(changes["content"].encode()).hexdigest()
        if "tags" in changes:
            changes["tags"] = json.dumps(changes["tags"])
        if "metadata" in changes:
            changes["metadata"] = json.dumps(changes["metadata"])
        changes["updated_at"] = _now()
        fields = ", ".join(f"{key}=?" for key in changes)
        db.execute(f"UPDATE documents SET {fields} WHERE id=?", (*changes.values(), document_id))
        _audit(db, document_id, "updated", actor, {"fields": list(changes)})
        updated = db.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
    if "content" in changes or "tags" in changes or "namespace" in changes:
        try:
            from .vector import delete, upsert
            delete(document_id)
            upsert(document_id, updated["namespace"], updated["source"], json.loads(updated["tags"]), chunks(updated["content"]), json.loads(updated["metadata"]), tenant_id=tenant_id)
        except Exception:
            pass
    return _row_dict(updated)


def set_status(document_id: str, status: str, actor: str) -> dict | None:
    return update_memory(document_id, status=status, actor=actor)


def supersede(document_id: str, replacement: dict, actor: str = "system") -> dict | None:
    old = get_memory(document_id)
    if not old:
        return None
    update_memory(document_id, status="superseded", actor=actor)
    with connect() as db:
        _audit(db, document_id, "superseded", actor, {"replacement": replacement.get("source")})
    replacement["supersedes_id"] = document_id
    replacement.setdefault("namespace", old["namespace"])
    return remember(actor=actor, tenant_id=_tenant(), **replacement)


def audit(document_id: str) -> list[dict]:
    tenant_id = _tenant()
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM audit_log WHERE tenant_id=? AND memory_id=? ORDER BY created_at", (tenant_id, document_id))]


def recent_activity(limit: int = 50) -> list[dict]:
    tenant_id = _tenant()
    limit = max(1, min(limit, 200))
    with connect() as db:
        rows = db.execute(
            "SELECT id, memory_id, action, actor, metadata, created_at FROM audit_log WHERE tenant_id=? ORDER BY created_at DESC, rowid DESC LIMIT ?",
            (tenant_id, limit),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item["metadata"] or "{}")
        result.append(item)
    return result


def export_memories(namespace: str | None = None) -> dict:
    tenant_id = _tenant()
    with connect() as db:
        query, args = "SELECT * FROM documents WHERE tenant_id=?", (tenant_id,)
        if namespace:
            query, args = query + " AND namespace=?", (tenant_id, namespace)
        memories = [_row_dict(row) for row in db.execute(query, args)]
        logs = [dict(row) for row in db.execute("SELECT * FROM audit_log ORDER BY created_at")]
    return {"version": 1, "memories": memories, "audit": logs}


def import_memories(bundle: dict, actor: str = "import") -> dict:
    tenant_id = _tenant()
    imported = 0
    for item in bundle.get("memories", []):
        item = dict(item)
        memory_id = item.pop("id", None)
        item.pop("created_at", None); item.pop("updated_at", None)
        item.pop("source_type", None); item.pop("title", None)
        remember(actor=actor, tenant_id=tenant_id, memory_id=memory_id, content=item.pop("content"), source=item.pop("source"), tags=item.pop("tags", []), **item)
        imported += 1
    return {"imported": imported}


def surface(namespace: str, limit: int = 10) -> list[dict]:
    tenant_id = _tenant()
    with connect() as db:
        rows = db.execute("SELECT id, source, content FROM documents WHERE tenant_id=? AND namespace=?", (tenant_id, namespace)).fetchall()
    # ponytail: O(n²) pair scan; use Qdrant nearest-neighbor pairs when corpus grows.
    pairs = []
    for index, left in enumerate(rows):
        left_words = set(re.findall(r"\w+", left["content"].lower()))
        for right in rows[index + 1:]:
            if left["source"] == right["source"]:
                continue
            right_words = set(re.findall(r"\w+", right["content"].lower()))
            score = len(left_words & right_words) / max(1, len(left_words | right_words))
            if score:
                pairs.append({"chunk_a": {"id": left["id"], "source": left["source"]}, "chunk_b": {"id": right["id"], "source": right["source"]}, "score": round(score, 3), "note": "Shared terms across different sources."})
    pairs = sorted(pairs, key=lambda item: item["score"], reverse=True)[:limit]
    with connect() as db:
        for pair in pairs:
            db.execute("INSERT OR REPLACE INTO connections(id,namespace,document_a,document_b,score) VALUES(?,?,?,?,?)", (uuid.uuid4().hex, namespace, pair["chunk_a"]["id"], pair["chunk_b"]["id"], pair["score"]))
    return pairs
