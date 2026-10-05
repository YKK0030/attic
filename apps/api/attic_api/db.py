import sqlite3
from contextlib import contextmanager

from .config import DB_PATH


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, namespace TEXT NOT NULL, source TEXT NOT NULL,
            source_type TEXT NOT NULL, content_hash TEXT NOT NULL,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            title TEXT, tags TEXT NOT NULL DEFAULT '[]',
            content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tenant_id, namespace, content_hash)
        );
        CREATE INDEX IF NOT EXISTS documents_namespace ON documents(namespace);
        CREATE TABLE IF NOT EXISTS connections (
            id TEXT PRIMARY KEY, namespace TEXT NOT NULL, document_a TEXT NOT NULL,
            document_b TEXT NOT NULL, score REAL NOT NULL,
            surfaced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            dismissed INTEGER NOT NULL DEFAULT 0,
            UNIQUE(namespace, document_a, document_b)
        );
        """)
        # Expand in place so existing local memories remain readable.
        columns = {row[1] for row in db.execute("PRAGMA table_info(documents)")}
        additions = {
            "memory_type": "TEXT NOT NULL DEFAULT 'document'",
            "source_uri": "TEXT",
            "agent_id": "TEXT",
            "user_id": "TEXT",
            "valid_from": "TEXT",
            "valid_until": "TEXT",
            "confidence": "REAL NOT NULL DEFAULT 1.0",
            "status": "TEXT NOT NULL DEFAULT 'active'",
            "supersedes_id": "TEXT",
            "approved_at": "TEXT",
            "metadata": "TEXT NOT NULL DEFAULT '{}'",
            "idempotency_key": "TEXT",
            "tenant_id": "TEXT NOT NULL DEFAULT 'default'",
        }
        for name, definition in additions.items():
            if name not in columns:
                db.execute(f"ALTER TABLE documents ADD COLUMN {name} {definition}")
        schema = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='documents'").fetchone()[0]
        if "UNIQUE(namespace, content_hash)" in schema:
            # ponytail: one transactional table swap; use a migration tool when PostgreSQL support lands.
            db.execute("DROP TABLE IF EXISTS documents_fts")
            db.executescript("""
            CREATE TABLE documents_new (
                id TEXT PRIMARY KEY, namespace TEXT NOT NULL, source TEXT NOT NULL,
                source_type TEXT NOT NULL, content_hash TEXT NOT NULL,
                tenant_id TEXT NOT NULL DEFAULT 'default', title TEXT,
                tags TEXT NOT NULL DEFAULT '[]', content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                memory_type TEXT NOT NULL DEFAULT 'document', source_uri TEXT,
                agent_id TEXT, user_id TEXT, valid_from TEXT, valid_until TEXT,
                confidence REAL NOT NULL DEFAULT 1.0, status TEXT NOT NULL DEFAULT 'active',
                supersedes_id TEXT, approved_at TEXT, metadata TEXT NOT NULL DEFAULT '{}',
                idempotency_key TEXT,
                UNIQUE(tenant_id, namespace, content_hash)
            );
            INSERT INTO documents_new SELECT id, namespace, source, source_type, content_hash,
                tenant_id, title, tags, content, created_at, updated_at, memory_type, source_uri,
                agent_id, user_id, valid_from, valid_until, confidence, status, supersedes_id,
                approved_at, metadata, idempotency_key FROM documents;
            DROP TABLE documents;
            ALTER TABLE documents_new RENAME TO documents;
            """)
        db.executescript("""
        CREATE INDEX IF NOT EXISTS documents_status ON documents(namespace, status);
        DROP INDEX IF EXISTS documents_idempotency;
        CREATE UNIQUE INDEX documents_idempotency ON documents(tenant_id, namespace, idempotency_key) WHERE idempotency_key IS NOT NULL;
        CREATE INDEX IF NOT EXISTS documents_tenant ON documents(tenant_id, namespace);
        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY, memory_id TEXT NOT NULL, action TEXT NOT NULL,
            actor TEXT NOT NULL, tenant_id TEXT NOT NULL DEFAULT 'default', metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS audit_memory ON audit_log(memory_id, created_at);
        """)
        audit_columns = {row[1] for row in db.execute("PRAGMA table_info(audit_log)")}
        if "tenant_id" not in audit_columns:
            db.execute("ALTER TABLE audit_log ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default'")
        try:
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(id UNINDEXED, content, source, tags)")
            db.execute("""CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(id, content, source, tags) VALUES (new.id, new.content, new.source, new.tags);
            END""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE OF content, source, tags ON documents BEGIN
                DELETE FROM documents_fts WHERE id = old.id;
                INSERT INTO documents_fts(id, content, source, tags) VALUES (new.id, new.content, new.source, new.tags);
            END""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents BEGIN
                DELETE FROM documents_fts WHERE id = old.id;
            END""")
            db.execute("INSERT INTO documents_fts(id, content, source, tags) SELECT id, content, source, tags FROM documents WHERE id NOT IN (SELECT id FROM documents_fts)")
        except sqlite3.OperationalError:
            # Some system SQLite builds omit FTS5; lexical fallback remains valid.
            pass
        db.execute("""CREATE TABLE IF NOT EXISTS index_metadata (
            namespace TEXT PRIMARY KEY, provider TEXT, model TEXT, dimension INTEGER,
            chunk_size INTEGER, chunk_overlap INTEGER, indexed_at TEXT
        )""")


@contextmanager
def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()
