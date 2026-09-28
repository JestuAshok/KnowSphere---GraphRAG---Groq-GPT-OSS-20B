import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.datasource import DataSourceORM

router = APIRouter(prefix="/datasources", tags=["datasources"])


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    config: Optional[dict] = None


@router.get("")
async def list_datasources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataSourceORM).order_by(DataSourceORM.name))
    sources = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "status": s.status,
            "last_sync": s.last_sync.isoformat() if s.last_sync else None,
        }
        for s in sources
    ]


@router.post("")
async def create_datasource(req: DataSourceCreate, db: AsyncSession = Depends(get_db)):
    ds = DataSourceORM(
        id=str(uuid.uuid4()),
        name=req.name,
        source_type=req.source_type,
        status="not_connected",
        config_json=json.dumps(req.config) if req.config else None,
    )
    db.add(ds)
    await db.commit()
    return {"id": ds.id, "status": "created"}


@router.post("/{source_id}/sync")
async def sync_datasource(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataSourceORM).where(DataSourceORM.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    # For the demo: file_upload is the only fully functional connector
    # Others update last_sync timestamp as a stub
    source.last_sync = datetime.utcnow()
    source.status = "connected"
    await db.commit()

    return {"status": "sync_triggered", "source_id": source_id, "source_type": source.source_type}
