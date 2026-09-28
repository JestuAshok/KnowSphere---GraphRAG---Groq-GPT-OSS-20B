from typing import Optional, List
from fastapi import APIRouter, Query
from app.graph.cypher_queries import (
    get_all_nodes,
    get_node_by_id,
    get_neighbors,
    get_path,
    get_subgraph_for_entity_ids,
)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/nodes")
async def graph_nodes(
    limit: int = Query(200, le=500),
    node_type: Optional[str] = Query(None, alias="type"),
):
    """All nodes + edges, optionally filtered by type."""
    try:
        return await get_all_nodes(limit=limit, node_type=node_type)
    except Exception:
        from app.graph.demo_data import nodes
        return nodes(node_type)


@router.get("/node/{node_id:path}")
async def graph_node(node_id: str):
    """Node detail with all relationships."""
    node = await get_node_by_id(node_id)
    if not node:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/neighbors/{node_id:path}")
async def graph_neighbors(node_id: str):
    """Expand a node: return its immediate neighbors."""
    return await get_neighbors(node_id)


@router.get("/path")
async def graph_path(
    from_id: str = Query(..., alias="from"),
    to_id: str = Query(..., alias="to"),
):
    """Shortest path between two nodes."""
    return await get_path(from_id, to_id)


@router.get("/subgraph")
async def graph_subgraph(entity_ids: str = Query(...)):
    """
    Return subgraph for a comma-separated list of node elementIds.
    Used by the frontend to visualize a GraphRAG answer's graph context.
    """
    ids = [i.strip() for i in entity_ids.split(",") if i.strip()]
    if not ids:
        return {"nodes": [], "edges": []}
    return await get_subgraph_for_entity_ids(ids)
