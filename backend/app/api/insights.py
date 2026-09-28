from fastapi import APIRouter
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.cypher_queries import (
    get_projects_by_technology,
    get_department_projects,
    get_top_relationships,
)
from app.core.database import AsyncSessionLocal
from app.models.activity import ActivityLogORM

router = APIRouter(tags=["insights"])

insights_router = APIRouter(prefix="/insights")
activity_router = APIRouter(prefix="/activity")


@insights_router.get("/projects-by-technology")
async def projects_by_technology():
    try:
        data = await get_projects_by_technology()
    except Exception:
        from app.graph.demo_data import projects_by_technology
        data = projects_by_technology()
    return [{"technology": r["technology"], "project_count": r["project_count"]} for r in data]


@insights_router.get("/department-projects")
async def department_projects():
    try:
        data = await get_department_projects()
    except Exception:
        from app.graph.demo_data import department_projects
        data = department_projects()
    # Aggregate by department (query may return duplicates from UNION)
    dept_map = {}
    for r in data:
        dept = r.get("department")
        cnt = r.get("project_count", 0)
        if dept:
            dept_map[dept] = dept_map.get(dept, 0) + cnt
    return [{"department": k, "project_count": v} for k, v in dept_map.items()]


@insights_router.get("/top-relationships")
async def top_relationships():
    try:
        data = await get_top_relationships()
    except Exception:
        from app.graph.demo_data import top_relationships
        data = top_relationships()
    return [{"relationship_type": r["relationship_type"], "count": r["count"]} for r in data]


@activity_router.get("/recent")
async def recent_activity(limit: int = 20):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ActivityLogORM).order_by(desc(ActivityLogORM.created_at)).limit(limit)
        )
        logs = result.scalars().all()
        return [
            {
                "id": l.id,
                "event_type": l.event_type,
                "description": l.description,
                "entity_type": l.entity_type,
                "entity_name": l.entity_name,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]


router.include_router(insights_router)
router.include_router(activity_router)
