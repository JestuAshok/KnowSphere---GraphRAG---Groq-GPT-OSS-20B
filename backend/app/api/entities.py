from fastapi import APIRouter, HTTPException
from app.graph.cypher_queries import get_entity_detail

router = APIRouter(prefix="/entities", tags=["entities"])

VALID_TYPES = {"employee", "team", "project", "technology", "department", "customer", "document", "product"}


@router.get("/{entity_type}/{entity_id:path}")
async def entity_detail(entity_type: str, entity_id: str):
    """
    Generic entity detail endpoint.
    entity_id can be the entity's name or Neo4j elementId.
    """
    if entity_type.lower() not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Must be one of: {', '.join(VALID_TYPES)}"
        )
    result = await get_entity_detail(entity_type, entity_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"{entity_type.capitalize()} '{entity_id}' not found")
    return result
