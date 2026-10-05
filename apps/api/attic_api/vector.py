import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from .config import QDRANT_COLLECTION, QDRANT_URL
from .providers import embed

client = QdrantClient(url=QDRANT_URL)


def delete(document_id: str) -> None:
    client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))])
        ),
    )


def _ensure_collection(vector_size: int) -> None:
    if not client.collection_exists(QDRANT_COLLECTION):
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )


def upsert(document_id: str, namespace: str, source: str, tags: list[str], pieces: list[str], metadata: dict | None = None, status: str = "active", tenant_id: str = "default") -> int:
    vectors = [embed(piece) for piece in pieces]
    if not vectors:
        return 0
    _ensure_collection(len(vectors[0]))
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"attic:{document_id}:{index}")),
                vector=vector,
                payload={"document_id": document_id, "namespace": namespace, "tenant_id": tenant_id, "source": source, "tags": tags, "content": piece, "metadata": metadata or {}, "status": status},
            )
            for index, (piece, vector) in enumerate(zip(pieces, vectors))
        ],
    )
    return len(vectors)


def search(query: str, namespace: str, limit: int, tag: str | None = None, tenant_id: str = "default") -> list[dict]:
    filters = [models.FieldCondition(key="namespace", match=models.MatchValue(value=namespace))]
    if tenant_id != "default":
        filters.append(models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id)))
    if tag:
        filters.append(models.FieldCondition(key="tags", match=models.MatchValue(value=tag)))
    result = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=embed(query),
        query_filter=models.Filter(must=filters),
        limit=limit,
        with_payload=True,
    )
    return [
        {"id": point.payload["document_id"], "content": point.payload["content"], "source": point.payload["source"], "score": round(point.score, 3)}
        for point in result.points
    ]
