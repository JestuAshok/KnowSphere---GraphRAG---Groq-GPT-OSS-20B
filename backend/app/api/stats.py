from fastapi import APIRouter
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.document import DocumentORM
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["stats"])

_EMPTY_STATS = {
    "employees": 0, "projects": 0, "technologies": 0,
    "departments": 0, "customers": 0, "teams": 0, "documents": 0,
}


@router.get("/overview")
async def overview():
    """Live counts from Neo4j + SQLite document count."""
    try:
        from app.graph.cypher_queries import get_stats
        graph_stats = await get_stats()
    except Exception as e:
        logger.warning(f"Neo4j unavailable, returning zero stats: {e}")
        graph_stats = _EMPTY_STATS

    # Get document count from SQLite too (uploaded docs)
    async with AsyncSessionLocal() as db:
        doc_result = await db.execute(select(func.count(DocumentORM.id)))
        sqlite_docs = doc_result.scalar() or 0

    # Use whichever is higher
    doc_count = max(graph_stats.get("documents", 0), sqlite_docs)

    return {
        "employees": graph_stats.get("employees", 0),
        "projects": graph_stats.get("projects", 0),
        "technologies": graph_stats.get("technologies", 0),
        "departments": graph_stats.get("departments", 0),
        "customers": graph_stats.get("customers", 0),
        "teams": graph_stats.get("teams", 0),
        "documents": doc_count,
    }
