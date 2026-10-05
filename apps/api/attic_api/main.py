from pathlib import Path
import json
import logging
import threading
import time
import uuid

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .config import API_KEY, CURRENT_TENANT, MAX_REQUEST_BYTES, RATE_LIMIT, RATE_WINDOW_SECONDS, RAG_MIN_SCORE, tenant_for_key
from .core import audit, build_context, export_memories, forget, get_memory, import_memories, recall, remember, reindex, set_status, supersede, surface, update_memory
from .db import connect, init_db
from .jobs import start as start_jobs
from .jobs import stop as stop_jobs
from .providers import answer

app = FastAPI(title="Attic", version="0.1.0")
router = APIRouter()
_rate_lock = threading.Lock()
_rate_windows: dict[str, tuple[float, int]] = {}
logger = logging.getLogger("attic")
_here = Path(__file__).resolve()
_web_candidates = [_here.parent.parent / "web"]
if len(_here.parents) > 3:
    _web_candidates.append(_here.parents[3] / "web")
WEB = next((path for path in _web_candidates if path.exists()), _web_candidates[0])


class Memory(BaseModel):
    content: str = Field(min_length=1)
    source: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    namespace: str = "default"
    memory_type: str = "document"
    source_uri: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    status: str = "active"
    metadata: dict = Field(default_factory=dict)


class MemoryPatch(BaseModel):
    content: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    namespace: str | None = None
    memory_type: str | None = None
    source_uri: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: str | None = None
    metadata: dict | None = None


class ImportBundle(BaseModel):
    memories: list[dict] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    id: str | None = None
    role: str = Field(min_length=1)
    content: str = Field(min_length=1)


class Conversation(BaseModel):
    conversation_id: str = Field(min_length=1)
    messages: list[ConversationMessage] = Field(min_length=1)
    namespace: str = "default"
    source: str = "conversation"
    tags: list[str] = Field(default_factory=list)


class WebhookMemory(BaseModel):
    event_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    namespace: str = "default"
    metadata: dict = Field(default_factory=dict)


class ToolExecution(BaseModel):
    name: str = Field(min_length=1)
    arguments: dict = Field(default_factory=dict)


def check_key(key: str | None) -> str:
    tenant = tenant_for_key(key)
    if tenant is None:
        raise HTTPException(status_code=401, detail="invalid x-attic-key")
    CURRENT_TENANT.set(tenant)
    return tenant


@app.middleware("http")
async def safety_middleware(request: Request, call_next):
    size = request.headers.get("content-length")
    if size and size.isdigit() and int(size) > MAX_REQUEST_BYTES:
        return JSONResponse({"detail": "request body too large"}, status_code=413)
    key = request.headers.get("x-attic-key")
    tenant = tenant_for_key(key)
    if tenant:
        now = time.monotonic()
        with _rate_lock:
            started, count = _rate_windows.get(key, (now, 0))
            if now - started >= RATE_WINDOW_SECONDS:
                started, count = now, 0
            if count >= RATE_LIMIT:
                return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
            _rate_windows[key] = (started, count + 1)
        CURRENT_TENANT.set(tenant)
    response = await call_next(request)
    if tenant:
        with connect() as db:
            db.execute(
                "INSERT INTO audit_log(id,memory_id,action,actor,tenant_id,metadata) VALUES(?,?,?,?,?,?)",
                (uuid.uuid4().hex, f"request:{uuid.uuid4().hex}", "access", "api", tenant,
                 json.dumps({"method": request.method, "path": request.url.path, "status": response.status_code})),
            )
    return response


@app.on_event("startup")
def startup():
    init_db()
    start_jobs()


@app.on_event("shutdown")
def shutdown():
    stop_jobs()


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB / "index.html")


@app.get("/app.css", include_in_schema=False)
def css():
    return FileResponse(WEB / "app.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def js():
    return FileResponse(WEB / "app.js", media_type="text/javascript")


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return FileResponse(WEB / "favicon.svg", media_type="image/svg+xml")


@app.get("/favicon.ico", include_in_schema=False)
def favicon_ico():
    return FileResponse(WEB / "favicon.svg", media_type="image/svg+xml")


@router.get("/health")
def health(x_attic_key: str | None = Header(default=None)):
    tenant = check_key(x_attic_key)
    with connect() as db:
        count = db.execute("SELECT COUNT(*) FROM documents WHERE tenant_id=?", (tenant,)).fetchone()[0]
        namespaces = [row[0] for row in db.execute("SELECT DISTINCT namespace FROM documents WHERE tenant_id=? ORDER BY namespace", (tenant,))]
        tags = {}
        for row in db.execute("SELECT tags FROM documents WHERE tenant_id=?", (tenant,)):
            for tag in json.loads(row[0]):
                tags[tag] = tags.get(tag, 0) + 1
    return {"ok": True, "memories": count, "namespaces": namespaces, "top_tags": sorted(tags, key=tags.get, reverse=True)[:10]}


@router.post("/memory")
def create_memory(memory: Memory, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    return remember(**memory.model_dump())


@router.get("/recall")
def search(
    q: str = Query(min_length=1), limit: int = Query(default=5, ge=1, le=100),
    tag: str | None = None, namespace: str = "default", mode: str = Query(default="hybrid", pattern="^(semantic|keyword|hybrid|context|timeline)$"),
    memory_type: str | None = None, agent_id: str | None = None, user_id: str | None = None, valid_at: str | None = None,
    x_attic_key: str | None = Header(default=None),
):
    check_key(x_attic_key)
    return recall(q, limit, namespace, tag, mode, memory_type, agent_id, user_id, valid_at)


@router.get("/ask")
def ask(
    q: str = Query(min_length=1), namespace: str = "default",
    x_attic_key: str | None = Header(default=None),
):
    check_key(x_attic_key)
    results = recall(q, 5, namespace, mode="context")
    context = [item for item in results if item["score"] >= RAG_MIN_SCORE]
    if not context:
        return {"answer": "nothing relevant found", "sources": [], "had_context": False}
    try:
        response = answer(q, "\n\n".join(f"[{item['source']} | memory:{item['id']}] {item['content']}" for item in context))
    except Exception as error:
        logger.exception("RAG generation failed")
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {error}") from error
    return {"answer": response, "sources": [item["citation"] | {"score": item["score"]} for item in context], "had_context": True}


@router.get("/context")
def context(
    q: str = Query(min_length=1), namespace: str = "default", limit: int = Query(default=5, ge=1, le=100),
    max_chars: int = Query(default=6000, ge=100, le=100000), tag: str | None = None,
    memory_type: str | None = None, agent_id: str | None = None, user_id: str | None = None, valid_at: str | None = None,
    x_attic_key: str | None = Header(default=None),
):
    check_key(x_attic_key)
    return build_context(q, namespace, limit, max_chars, tag=tag, memory_type=memory_type, agent_id=agent_id, user_id=user_id, valid_at=valid_at)


@router.post("/reindex")
def reindex_memories(namespace: str | None = None, dry_run: bool = False, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    return reindex(namespace, dry_run)


@router.get("/surface")
def connections(namespace: str = "default", limit: int = Query(default=10, ge=1, le=100), x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    return surface(namespace, limit)


@router.delete("/memory/{memory_id}")
def delete_memory(memory_id: str, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    if not forget(memory_id):
        raise HTTPException(status_code=404, detail="memory not found")
    return {"deleted": memory_id}


@router.get("/memory/{memory_id}")
def read_memory(memory_id: str, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    item = get_memory(memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="memory not found")
    return item


@router.patch("/memory/{memory_id}")
def patch_memory(memory_id: str, patch: MemoryPatch, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    item = update_memory(memory_id, actor="api", **patch.model_dump(exclude_none=True))
    if not item:
        raise HTTPException(status_code=404, detail="memory not found")
    return item


@router.post("/memory/{memory_id}/approve")
def approve_memory(memory_id: str, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    item = set_status(memory_id, "active", "api")
    if not item:
        raise HTTPException(status_code=404, detail="memory not found")
    return item


@router.post("/memory/{memory_id}/reject")
def reject_memory(memory_id: str, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    item = set_status(memory_id, "rejected", "api")
    if not item:
        raise HTTPException(status_code=404, detail="memory not found")
    return item


@router.post("/memory/{memory_id}/supersede")
def supersede_memory(memory_id: str, replacement: Memory, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    item = supersede(memory_id, replacement.model_dump(), "api")
    if not item:
        raise HTTPException(status_code=404, detail="memory not found")
    return item


@router.get("/memory/{memory_id}/audit")
def memory_audit(memory_id: str, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    if not get_memory(memory_id) and not audit(memory_id):
        raise HTTPException(status_code=404, detail="memory not found")
    return audit(memory_id)


@router.get("/export")
def export(namespace: str | None = None, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    return export_memories(namespace)


@router.post("/import")
def import_bundle(bundle: ImportBundle, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    return import_memories(bundle.model_dump(), "api")


@router.post("/conversations")
def ingest_conversation(conversation: Conversation, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    memories = []
    for index, message in enumerate(conversation.messages):
        message_id = message.id or str(index)
        memories.append(remember(
            content=f"{message.role}: {message.content}",
            source=conversation.source,
            tags=conversation.tags,
            namespace=conversation.namespace,
            memory_type="conversation",
            source_uri=f"conversation:{conversation.conversation_id}",
            metadata={"conversation_id": conversation.conversation_id, "message_id": message_id, "role": message.role},
            idempotency_key=f"conversation:{conversation.conversation_id}:{message_id}",
            actor="conversation",
        ))
    return {"conversation_id": conversation.conversation_id, "memories": memories}


@router.post("/webhooks/memory")
def ingest_webhook(event: WebhookMemory, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    metadata = {**event.metadata, "event_id": event.event_id}
    return remember(
        content=event.content,
        source=event.source,
        tags=event.tags,
        namespace=event.namespace,
        metadata=metadata,
        idempotency_key=f"webhook:{event.event_id}",
        actor="webhook",
    )


def _openai_tools() -> list[dict]:
    return [{
        "type": "function",
        "function": {
            "name": "attic_remember",
            "description": "Store durable evidence in Attic.",
            "parameters": {"type": "object", "required": ["content", "source"], "properties": {
                "content": {"type": "string"}, "source": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "namespace": {"type": "string"},
            }},
        },
    }, {
        "type": "function",
        "function": {
            "name": "attic_recall",
            "description": "Retrieve cited evidence from Attic.",
            "parameters": {"type": "object", "required": ["query"], "properties": {
                "query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "namespace": {"type": "string"},
            }},
        },
    }]


@router.get("/openai/tools")
def openai_tools(x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    return {"tools": _openai_tools()}


@router.post("/openai/tools/execute")
def execute_openai_tool(call: ToolExecution, x_attic_key: str | None = Header(default=None)):
    check_key(x_attic_key)
    args = call.arguments
    if call.name == "attic_remember":
        required = {"content", "source"}
        if not required <= args.keys():
            raise HTTPException(status_code=422, detail="attic_remember requires content and source")
        return remember(content=args["content"], source=args["source"], tags=args.get("tags", []), namespace=args.get("namespace", "default"), actor="tool")
    if call.name == "attic_recall":
        if "query" not in args:
            raise HTTPException(status_code=422, detail="attic_recall requires query")
        return recall(args["query"], args.get("limit", 5), args.get("namespace", "default"))
    raise HTTPException(status_code=404, detail="unknown Attic tool")


app.include_router(router)
app.include_router(router, prefix="/v1")
