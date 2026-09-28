"""
Hybrid retriever: merges FAISS semantic search with Neo4j / embedded graph traversal.
Optimized for high-speed concurrent execution and sub-millisecond entity matching.
"""
import asyncio
import re
from typing import List, Dict, Any, Optional
from app.retrieval.embedder import search_similar
from app.retrieval.entity_extractor import extract_question_entities
from app.retrieval.disambiguator import disambiguate_entities, get_all_node_names
from app.graph.cypher_queries import (
    get_neighbors,
    get_node_by_id,
    get_team_tech_projects,
    find_nodes_by_names,
)
from app.graph.neo4j_driver import run_query


async def fast_extract_entities(question: str) -> List[Dict[str, Any]]:
    """
    Sub-millisecond direct matcher:
    Scans the question against known graph node names using boundary matching.
    """
    try:
        nodes = await get_all_node_names()
    except Exception:
        return []

    q_lower = question.lower()
    matches = []
    seen_ids = set()

    # Sort longer names first so "Project Phoenix" matches before "Phoenix"
    sorted_nodes = sorted(nodes, key=lambda n: len(n.get("name", "")), reverse=True)
    for n in sorted_nodes:
        name = n.get("name", "").strip()
        if not name or len(name) < 2:
            continue
        # Use word-boundary matching for names
        pattern = r"(?<!\w)" + re.escape(name.lower()) + r"(?!\w)"
        if re.search(pattern, q_lower):
            node_id = n.get("id")
            if node_id not in seen_ids:
                seen_ids.add(node_id)
                matches.append({
                    "type": n.get("type", "Entity"),
                    "name": name,
                    "canonical_name": name,
                    "neo4j_id": node_id,
                    "matched": True,
                })

    return matches


async def retrieve(question: str, k_vector: int = 5, k_graph: int = 3) -> Dict[str, Any]:
    """
    Hybrid retrieval combining:
    1. FAISS semantic search → top-k document chunks (run in worker thread)
    2. Fast entity extraction (with fallback to LLM entity extraction)
    3. Concurrent Graph traversal for matched entities
    """
    # ── 1. Run FAISS search & Entity detection concurrently ───────
    async def _run_vector_search():
        return await asyncio.to_thread(search_similar, question, k_vector)

    async def _run_entity_detection():
        # First try sub-millisecond direct match against known graph nodes
        direct_matches = await fast_extract_entities(question)
        if direct_matches:
            return direct_matches

        # Fallback to LLM entity extraction if no direct matches in question
        try:
            raw_entities = await extract_question_entities(question)
            return await disambiguate_entities(raw_entities)
        except Exception as e:
            print(f"[HybridRetriever] Entity extraction fallback note: {e}")
            return []

    # Execute vector search and entity detection simultaneously
    vector_hits, disambiguated = await asyncio.gather(
        _run_vector_search(),
        _run_entity_detection(),
    )

    matched = [e for e in disambiguated if e.get("matched")]

    # ── 2. Concurrent Graph traversal for matched entities ────────
    graph_context = []
    subgraph_node_ids = set()

    team_entities = [e for e in matched if e.get("type") == "Team"]
    other_entities = [e for e in matched if e.get("type") != "Team"][:k_graph]

    # Tasks for multi-hop team traversals
    team_tasks = []
    for te in team_entities:
        team_name = te.get("canonical_name", te.get("name"))
        team_tasks.append((team_name, get_team_tech_projects(team_name)))

    # Tasks for node detail lookups
    node_tasks = []
    for entity in other_entities:
        neo4j_id = entity.get("neo4j_id")
        if neo4j_id:
            subgraph_node_ids.add(neo4j_id)
            node_tasks.append((entity, get_node_by_id(neo4j_id)))

    # Run team traversals in parallel
    if team_tasks:
        team_results = await asyncio.gather(*[t[1] for t in team_tasks], return_exceptions=True)
        for (team_name, _), traversal in zip(team_tasks, team_results):
            if isinstance(traversal, dict) and traversal.get("affected_projects"):
                graph_context.append({
                    "type": "multi_hop_traversal",
                    "team": team_name,
                    "path": f"{team_name} → USES → Technology → DEPENDS_ON ← Project",
                    "technologies": traversal.get("technologies", []),
                    "affected_projects": traversal.get("affected_projects", []),
                })
                for proj in traversal.get("affected_projects", []):
                    if proj.get("team_id"): subgraph_node_ids.add(proj["team_id"])
                    if proj.get("tech_id"): subgraph_node_ids.add(proj["tech_id"])
                    if proj.get("project_id"): subgraph_node_ids.add(proj["project_id"])

    # Run node lookups in parallel
    if node_tasks:
        node_results = await asyncio.gather(*[t[1] for t in node_tasks], return_exceptions=True)
        for (entity, _), node_detail in zip(node_tasks, node_results):
            if isinstance(node_detail, dict) and node_detail:
                graph_context.append({
                    "type": "node_detail",
                    "entity": entity.get("canonical_name"),
                    "entity_type": node_detail.get("type"),
                    "properties": node_detail.get("properties", {}),
                    "relationships": node_detail.get("relationships", []),
                })
                for rel in (node_detail.get("relationships") or [])[:5]:
                    if rel.get("neighbor_id"):
                        subgraph_node_ids.add(rel["neighbor_id"])

    return {
        "vector_chunks": vector_hits,
        "graph_context": graph_context,
        "question_entities": disambiguated,
        "subgraph_node_ids": list(subgraph_node_ids),
    }


def format_context_for_llm(retrieval_result: Dict[str, Any]) -> str:
    """Format retrieved context into a prompt-friendly string."""
    lines = []

    # Vector chunks
    chunks = retrieval_result.get("vector_chunks", [])
    if chunks:
        lines.append("## Relevant Document Excerpts")
        for i, chunk in enumerate(chunks, 1):
            lines.append(f"\n[Source {i}: {chunk.get('doc_name', 'Unknown')}]")
            lines.append(chunk.get("text", ""))

    # Graph traversal results
    graph = retrieval_result.get("graph_context", [])
    if graph:
        lines.append("\n## Knowledge Graph Context")
        for ctx in graph:
            if ctx["type"] == "multi_hop_traversal":
                lines.append(f"\nMulti-hop path: {ctx['path']}")
                lines.append(f"Team: {ctx['team']}")
                techs = [t["tech_name"] for t in ctx["technologies"]]
                lines.append(f"Technologies used: {', '.join(techs)}")
                lines.append("Affected Projects:")
                for proj in ctx["affected_projects"]:
                    lines.append(f"  - {proj['project_name']} (uses {proj['tech_name']})")
                    if proj.get("project_description"):
                        lines.append(f"    Description: {proj['project_description']}")
            elif ctx["type"] == "node_detail":
                lines.append(f"\nEntity: {ctx['entity']} ({ctx['entity_type']})")
                rels = ctx.get("relationships", [])
                for rel in rels[:8]:
                    direction = "→" if rel.get("direction") == "out" else "←"
                    lines.append(f"  {direction} [{rel['rel_type']}] {rel.get('neighbor_name', '')} ({rel.get('neighbor_label', '')})")

    return "\n".join(lines)
