"""
All Cypher queries for Neo4j graph operations with automatic fallback to EmbeddedGraphStore.
Ensures KnowSphere runs seamlessly with or without Neo4j / Docker.
"""
from typing import Any, Dict, List, Optional
from app.graph.neo4j_driver import run_query, run_write_query, is_neo4j_available
from app.graph.embedded_graph import get_embedded_graph


# ─────────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────────

async def get_stats() -> Dict[str, int]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_stats()

    try:
        records = await run_query("""
            CALL apoc.meta.stats()
            YIELD labels
            RETURN labels
        """)
        if records:
            labels = records[0].get("labels", {})
            return {
                "employees": labels.get("Employee", 0),
                "projects": labels.get("Project", 0),
                "technologies": labels.get("Technology", 0),
                "departments": labels.get("Department", 0),
                "customers": labels.get("Customer", 0),
                "teams": labels.get("Team", 0),
                "documents": labels.get("Document", 0),
            }
        # Fallback: count individually
        result = {}
        for label in ["Employee", "Project", "Technology", "Department", "Customer", "Team", "Document"]:
            r = await run_query(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            result[label.lower() + "s"] = r[0]["cnt"] if r else 0
        return result
    except Exception:
        return get_embedded_graph().get_stats()


# ─────────────────────────────────────────────
#  GRAPH NODES & EDGES
# ─────────────────────────────────────────────

async def get_all_nodes(limit: int = 200, node_type: Optional[str] = None) -> Dict[str, List]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_all_nodes(limit=limit, node_type=node_type)

    try:
        if node_type and node_type != "All":
            node_query = f"""
                MATCH (n:{node_type})
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
                LIMIT $limit
            """
            rel_query = f"""
                MATCH (a:{node_type})-[r]-(b)
                RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS rel_type
                LIMIT $limit
            """
        else:
            node_query = """
                MATCH (n)
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
                LIMIT $limit
            """
            rel_query = """
                MATCH (a)-[r]->(b)
                RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS rel_type
                LIMIT $limit
            """
        nodes_raw = await run_query(node_query, {"limit": limit})
        rels_raw = await run_query(rel_query, {"limit": limit})

        nodes = []
        for n in nodes_raw:
            props = n.get("props", {})
            label = n["labels"][0] if n["labels"] else "Unknown"
            nodes.append({
                "id": n["id"],
                "label": props.get("name", props.get("title", n["id"])),
                "type": label,
                "properties": props,
            })

        edges = []
        for r in rels_raw:
            edges.append({
                "source": r["source"],
                "target": r["target"],
                "type": r["rel_type"],
            })

        return {"nodes": nodes, "edges": edges}
    except Exception:
        return get_embedded_graph().get_all_nodes(limit=limit, node_type=node_type)


async def get_node_by_id(node_id: str) -> Optional[Dict]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_node_by_id(node_id)

    try:
        records = await run_query("""
            MATCH (n)
            WHERE elementId(n) = $id
            OPTIONAL MATCH (n)-[r]-(neighbor)
            RETURN
                elementId(n) AS id,
                labels(n) AS labels,
                properties(n) AS props,
                collect({
                    rel_type: type(r),
                    direction: CASE WHEN startNode(r) = n THEN 'out' ELSE 'in' END,
                    neighbor_id: elementId(neighbor),
                    neighbor_label: labels(neighbor)[0],
                    neighbor_name: neighbor.name
                }) AS relationships
            LIMIT 1
        """, {"id": node_id})
        if not records:
            return get_embedded_graph().get_node_by_id(node_id)
        r = records[0]
        return {
            "id": r["id"],
            "type": r["labels"][0] if r["labels"] else "Unknown",
            "properties": r["props"],
            "relationships": [rel for rel in r["relationships"] if rel["rel_type"] is not None],
        }
    except Exception:
        return get_embedded_graph().get_node_by_id(node_id)


async def get_neighbors(node_id: str) -> Dict[str, List]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_neighbors(node_id)

    try:
        records = await run_query("""
            MATCH (n)-[r]-(neighbor)
            WHERE elementId(n) = $id
            RETURN
                elementId(neighbor) AS id,
                labels(neighbor) AS labels,
                properties(neighbor) AS props,
                type(r) AS rel_type,
                elementId(n) AS source_id
        """, {"id": node_id})

        nodes = []
        edges = []
        seen_ids = set()
        for rec in records:
            nid = rec["id"]
            props = rec.get("props", {})
            label = rec["labels"][0] if rec["labels"] else "Unknown"
            if nid not in seen_ids:
                nodes.append({
                    "id": nid,
                    "label": props.get("name", props.get("title", nid)),
                    "type": label,
                    "properties": props,
                })
                seen_ids.add(nid)
            edges.append({
                "source": rec["source_id"],
                "target": nid,
                "type": rec["rel_type"],
            })
        return {"nodes": nodes, "edges": edges}
    except Exception:
        return get_embedded_graph().get_neighbors(node_id)


async def get_path(from_id: str, to_id: str) -> Dict[str, List]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_path(from_id, to_id)

    try:
        records = await run_query("""
            MATCH path = shortestPath((a)-[*..10]-(b))
            WHERE elementId(a) = $from_id AND elementId(b) = $to_id
            RETURN [n IN nodes(path) | {
                id: elementId(n),
                label: n.name,
                type: labels(n)[0],
                props: properties(n)
            }] AS path_nodes,
            [r IN relationships(path) | {
                source: elementId(startNode(r)),
                target: elementId(endNode(r)),
                type: type(r)
            }] AS path_edges
            LIMIT 1
        """, {"from_id": from_id, "to_id": to_id})
        if not records:
            return get_embedded_graph().get_path(from_id, to_id)
        return {
            "nodes": records[0]["path_nodes"],
            "edges": records[0]["path_edges"],
        }
    except Exception:
        return get_embedded_graph().get_path(from_id, to_id)


async def get_subgraph_for_entity_ids(entity_ids: List[str]) -> Dict[str, List]:
    """Return the subgraph connecting a set of node elementIds."""
    if not await is_neo4j_available():
        return get_embedded_graph().get_subgraph_for_entity_ids(entity_ids)

    try:
        records = await run_query("""
            MATCH (n)
            WHERE elementId(n) IN $ids
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE elementId(m) IN $ids
            WITH n, r, m
            RETURN
                elementId(n) AS nid, labels(n) AS nlabels, properties(n) AS nprops,
                elementId(m) AS mid, labels(m) AS mlabels, properties(m) AS mprops,
                elementId(startNode(r)) AS rsrc, elementId(endNode(r)) AS rtgt, type(r) AS rtype
        """, {"ids": entity_ids})

        nodes = {}
        edges = []
        for rec in records:
            if rec["nid"] and rec["nid"] not in nodes:
                nl = rec["nlabels"][0] if rec["nlabels"] else "Unknown"
                np = rec["nprops"] or {}
                nodes[rec["nid"]] = {
                    "id": rec["nid"],
                    "label": np.get("name", np.get("title", rec["nid"])),
                    "type": nl,
                    "properties": np,
                }
            if rec["mid"] and rec["mid"] not in nodes:
                ml = rec["mlabels"][0] if rec["mlabels"] else "Unknown"
                mp = rec["mprops"] or {}
                nodes[rec["mid"]] = {
                    "id": rec["mid"],
                    "label": mp.get("name", mp.get("title", rec["mid"])),
                    "type": ml,
                    "properties": mp,
                }
            if rec["rtype"]:
                edges.append({"source": rec["rsrc"], "target": rec["rtgt"], "type": rec["rtype"]})

        return {"nodes": list(nodes.values()), "edges": edges}
    except Exception:
        return get_embedded_graph().get_subgraph_for_entity_ids(entity_ids)


# ─────────────────────────────────────────────
#  DEMO SCENARIO: Team → Technology → Project
# ─────────────────────────────────────────────

async def get_team_tech_projects(team_name: str) -> Dict[str, Any]:
    """Multi-hop: Team → USES → Technology ← DEPENDS_ON ← Project"""
    if not await is_neo4j_available():
        return get_embedded_graph().get_team_tech_projects(team_name)

    try:
        records = await run_query("""
            MATCH (team:Team {name: $team_name})-[:USES]->(tech:Technology)<-[:DEPENDS_ON]-(project:Project)
            RETURN
                team.name AS team_name,
                elementId(team) AS team_id,
                tech.name AS tech_name,
                elementId(tech) AS tech_id,
                project.name AS project_name,
                elementId(project) AS project_id,
                project.description AS project_description
            ORDER BY tech.name, project.name
        """, {"team_name": team_name})

        tech_records = await run_query("""
            MATCH (team:Team {name: $team_name})-[:USES]->(tech:Technology)
            RETURN tech.name AS tech_name, elementId(tech) AS tech_id
        """, {"team_name": team_name})

        return {
            "team_name": team_name,
            "technologies": tech_records,
            "affected_projects": records,
        }
    except Exception:
        return get_embedded_graph().get_team_tech_projects(team_name)


# ─────────────────────────────────────────────
#  INSIGHTS QUERIES
# ─────────────────────────────────────────────

async def get_projects_by_technology() -> List[Dict]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_projects_by_technology()

    try:
        return await run_query("""
            MATCH (tech:Technology)<-[:DEPENDS_ON]-(proj:Project)
            RETURN tech.name AS technology, count(proj) AS project_count
            ORDER BY project_count DESC
            LIMIT 10
        """)
    except Exception:
        return get_embedded_graph().get_projects_by_technology()


async def get_department_projects() -> List[Dict]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_department_projects()

    try:
        return await run_query("""
            MATCH (dept:Department)<-[:BELONGS_TO|PART_OF]-(proj:Project)
            RETURN dept.name AS department, count(proj) AS project_count
            ORDER BY project_count DESC
            UNION
            MATCH (dept:Department)<-[:BELONGS_TO]-(team:Team)-[:WORKS_ON]->(proj:Project)
            RETURN dept.name AS department, count(DISTINCT proj) AS project_count
            ORDER BY project_count DESC
            LIMIT 10
        """)
    except Exception:
        return get_embedded_graph().get_department_projects()


async def get_top_relationships() -> List[Dict]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_top_relationships()

    try:
        return await run_query("""
            MATCH ()-[r]->()
            RETURN type(r) AS relationship_type, count(r) AS count
            ORDER BY count DESC
            LIMIT 10
        """)
    except Exception:
        return get_embedded_graph().get_top_relationships()


# ─────────────────────────────────────────────
#  ENTITY DETAILS
# ─────────────────────────────────────────────

async def get_entity_detail(entity_type: str, name: str) -> Optional[Dict]:
    if not await is_neo4j_available():
        return get_embedded_graph().get_entity_detail(entity_type, name)

    try:
        label = entity_type.capitalize()
        records = await run_query(f"""
            MATCH (n:{label})
            WHERE n.name = $name OR elementId(n) = $name
            OPTIONAL MATCH (n)-[r]-(related)
            RETURN
                elementId(n) AS id,
                labels(n) AS labels,
                properties(n) AS props,
                collect({{
                    rel_type: type(r),
                    direction: CASE WHEN startNode(r) = n THEN 'out' ELSE 'in' END,
                    related_id: elementId(related),
                    related_type: labels(related)[0],
                    related_name: related.name
                }}) AS relationships
            LIMIT 1
        """, {"name": name})
        if not records:
            return get_embedded_graph().get_entity_detail(entity_type, name)
        r = records[0]
        return {
            "id": r["id"],
            "type": r["labels"][0] if r["labels"] else label,
            "properties": r["props"],
            "relationships": [rel for rel in r["relationships"] if rel["rel_type"] is not None],
        }
    except Exception:
        return get_embedded_graph().get_entity_detail(entity_type, name)


# ─────────────────────────────────────────────
#  WRITE / UPSERT
# ─────────────────────────────────────────────

async def upsert_entity(label: str, name: str, properties: Dict[str, Any]) -> str:
    """Create or update a node, return its ID."""
    embedded_id = get_embedded_graph().upsert_entity(label, name, properties)
    if await is_neo4j_available():
        try:
            props = {**properties, "name": name}
            records = await run_write_query(f"""
                MERGE (n:{label} {{name: $name}})
                SET n += $props
                RETURN elementId(n) AS id
            """, {"name": name, "props": props})
            return records[0]["id"] if records else embedded_id
        except Exception:
            pass
    return embedded_id


async def upsert_relationship(
    from_label: str, from_name: str,
    to_label: str, to_name: str,
    rel_type: str,
    properties: Optional[Dict[str, Any]] = None,
) -> bool:
    get_embedded_graph().upsert_relationship(from_label, from_name, to_label, to_name, rel_type, properties)
    if await is_neo4j_available():
        try:
            await run_write_query(f"""
                MATCH (a:{from_label} {{name: $from_name}})
                MATCH (b:{to_label} {{name: $to_name}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += $props
                RETURN r
            """, {"from_name": from_name, "to_name": to_name, "props": properties or {}})
        except Exception:
            pass
    return True


async def find_nodes_by_names(names: List[str]) -> List[Dict]:
    """Find nodes matching a list of names (for disambiguation)."""
    if not await is_neo4j_available():
        return get_embedded_graph().find_nodes_by_names(names)

    try:
        records = await run_query("""
            MATCH (n)
            WHERE n.name IN $names
            RETURN elementId(n) AS id, labels(n) AS labels, n.name AS name
        """, {"names": names})
        if not records:
            return get_embedded_graph().find_nodes_by_names(names)
        return records
    except Exception:
        return get_embedded_graph().find_nodes_by_names(names)
