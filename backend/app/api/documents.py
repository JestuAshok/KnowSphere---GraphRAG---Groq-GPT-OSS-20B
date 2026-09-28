import os
import uuid
import json
import aiofiles
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.auth import get_current_user
from app.core.database import get_db, AsyncSessionLocal
from app.core.config import get_settings
from app.models.user import UserORM
from app.models.document import DocumentORM
from app.models.activity import ActivityLogORM
from app.retrieval.ingestion_pipeline import ingest_document

settings = get_settings()
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf", ".xlsx", ".xls", ".csv"}


async def _log_activity(event_type: str, description: str, entity_type: str, entity_name: str):
    async with AsyncSessionLocal() as db:
        log = ActivityLogORM(
            id=str(uuid.uuid4()),
            event_type=event_type,
            description=description,
            entity_type=entity_type,
            entity_name=entity_name,
        )
        db.add(log)
        await db.commit()


async def _process_document(doc_id: str, file_path: str, doc_name: str, mime_type: str):
    """Background task: run full ingestion pipeline."""
    try:
        result = await ingest_document(
            file_path=file_path,
            doc_id=doc_id,
            doc_name=doc_name,
            mime_type=mime_type,
            log_activity_fn=_log_activity,
        )
        # Update document record
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(DocumentORM).where(DocumentORM.id == doc_id))
            doc = res.scalar_one_or_none()
            if doc:
                doc.content = result.get("text", "")[:50000]  # cap at 50k chars
                doc.entities_json = json.dumps(result.get("entities", []))
                doc.status = "done"
                doc.processed_at = datetime.utcnow()
                doc.neo4j_node_id = result.get("neo4j_doc_id", "")
                await db.commit()
    except Exception as e:
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(DocumentORM).where(DocumentORM.id == doc_id))
            doc = res.scalar_one_or_none()
            if doc:
                doc.status = "error"
                await db.commit()
        print(f"[Documents] Ingestion error for {doc_id}: {e}")


@router.get("")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(DocumentORM).order_by(desc(DocumentORM.created_at)).limit(limit)
    )
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.original_name,
            "file_size": d.file_size,
            "status": d.status,
            "created_at": d.created_at.isoformat(),
            "processed_at": d.processed_at.isoformat() if d.processed_at else None,
        }
        for d in docs
    ]


@router.get("/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentORM).where(DocumentORM.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    entities = json.loads(doc.entities_json) if doc.entities_json else []

    return {
        "id": doc.id,
        "filename": doc.original_name,
        "file_size": doc.file_size,
        "content": doc.content or "",
        "entities": entities,
        "status": doc.status,
        "created_at": doc.created_at.isoformat(),
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
    }


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: UserORM = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save file to disk
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}{ext}"
    os.makedirs(settings.uploads_path, exist_ok=True)
    file_path = os.path.join(settings.uploads_path, safe_name)

    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create DB record
    doc = DocumentORM(
        id=doc_id,
        filename=safe_name,
        original_name=file.filename,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status="processing",
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.commit()

    # Queue ingestion pipeline as background task
    background_tasks.add_task(
        _process_document,
        doc_id=doc_id,
        file_path=file_path,
        doc_name=file.filename,
        mime_type=file.content_type or "",
    )

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Document uploaded and queued for ingestion",
    }
