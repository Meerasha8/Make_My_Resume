from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from dependencies import get_db
from models import DocumentEmbedding, User, _uuid_value


class DocumentEmbeddingCreate(BaseModel):
    source_table: str
    source_id: int
    content: str
    embedding: list[float]


class DocumentEmbeddingResponse(BaseModel):
    id: int
    user_uuid: str
    source_table: str
    source_id: int
    content: str
    embedding: list[float]


router = APIRouter(prefix="/document-embeddings", tags=["Document Embeddings"])


def _normalize_embedding(values: list[float]) -> list[float]:
    if not values:
        return [0.0] * 384
    if len(values) >= 384:
        return [float(value) for value in values[:384]]
    return [float(value) for value in values] + [0.0] * (384 - len(values))


def _serialize_document_embedding(item: DocumentEmbedding) -> DocumentEmbeddingResponse:
    return DocumentEmbeddingResponse(
        id=item.id,
        user_uuid=str(item.user_uuid),
        source_table=item.source_table,
        source_id=item.source_id,
        content=item.content,
        embedding=list(item.embedding) if item.embedding is not None else [],
    )


@router.post("/", response_model=DocumentEmbeddingResponse)
def create_document_embedding(
    payload: DocumentEmbeddingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_embedding = _normalize_embedding(payload.embedding)
    db_item = DocumentEmbedding(
        user_uuid=_uuid_value(current_user.user_uuid),
        source_table=payload.source_table,
        source_id=payload.source_id,
        content=payload.content,
        embedding=normalized_embedding,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _serialize_document_embedding(db_item)


@router.get("/", response_model=list[DocumentEmbeddingResponse])
def list_document_embeddings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(DocumentEmbedding)
        .where(DocumentEmbedding.user_uuid == _uuid_value(current_user.user_uuid))
        .order_by(DocumentEmbedding.id.desc())
    )
    items = db.scalars(statement).all()
    return [_serialize_document_embedding(item) for item in items]


@router.get("/{embedding_id}", response_model=DocumentEmbeddingResponse)
def get_document_embedding(
    embedding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(DocumentEmbedding)
        .filter(DocumentEmbedding.id == embedding_id)
        .filter(DocumentEmbedding.user_uuid == _uuid_value(current_user.user_uuid))
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Document embedding not found")
    return _serialize_document_embedding(item)


@router.put("/{embedding_id}", response_model=DocumentEmbeddingResponse)
def update_document_embedding(
    embedding_id: int,
    payload: DocumentEmbeddingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(DocumentEmbedding)
        .filter(DocumentEmbedding.id == embedding_id)
        .filter(DocumentEmbedding.user_uuid == _uuid_value(current_user.user_uuid))
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Document embedding not found")

    item.source_table = payload.source_table
    item.source_id = payload.source_id
    item.content = payload.content
    item.embedding = payload.embedding

    db.commit()
    db.refresh(item)
    return _serialize_document_embedding(item)


@router.delete("/{embedding_id}")
def delete_document_embedding(
    embedding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(DocumentEmbedding)
        .filter(DocumentEmbedding.id == embedding_id)
        .filter(DocumentEmbedding.user_uuid == _uuid_value(current_user.user_uuid))
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Document embedding not found")

    db.delete(item)
    db.commit()
    return {"message": "Document embedding deleted successfully"}
