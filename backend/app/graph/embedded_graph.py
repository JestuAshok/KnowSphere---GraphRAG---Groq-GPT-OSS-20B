"""
Embedded Graph Store using NetworkX with local JSON persistence.
Enables full GraphRAG traversal, visualization, and analytics without requiring Neo4j or Docker.
"""
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import networkx as nx

from app.core.config import get_settings, DATA_DIR

settings = get_settings()


class EmbeddedGraphStore:
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = DATA_DIR / "graph_store.json"
        
        self.graph = nx.MultiDiGraph()
        self.nodes_data: Dict[str, Dict[str, Any]] = {}
        self.edges_data: List[Dict[str, Any]] = []
        self._name_type_index: Dict[str, str] = {}  # key: f"{type.lower()}:{name.lower()}" -> id
        self.load()

    def _make_key(self, entity_type: str, name: str) -> str:
        return f"{entity_type.strip().lower()}:{name.strip().lower()}"

    def load(self):
        """Load graph from JSON file if it exists."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            
            self.graph.clear()
            self.nodes_data.clear()
            self.edges_data.clear()
            self._name_type_index.clear()

            for n in payload.get("nodes", []):
                nid = str(n["id"])
                name = n.get("properties", {}).get("name") or n.get("label") or nid
                ntype = n.get("type", "Unknown")
                props = n.get("properties", {})
                self.nodes_data[nid] = {
                    "id": nid,
                    "label": name,
                    "type": ntype,
                    "properties": props,
                }
                self.graph.add_node(nid, label=name, type=ntype, **props)
                self._name_type_index[self._make_key(ntype, name)] = nid
                self._name_type_index[f":{name.strip().lower()}"] = nid

            for e in payload.get("edges", []):
                eid = e.get("id") or str(uuid.uuid4())
                src = str(e["source"])
                tgt = str(e["target"])
                rel_type = e.get("type", "RELATED_TO")
                props = e.get("properties", {})
                edge_item = {
                    "id": eid,
                    "source": src,
                    "target": tgt,
                    "type": rel_type,
                    "properties": props,
                }
                self.edges_data.append(edge_item)
                self.graph.add_edge(src, tgt, key=eid, type=rel_type, **props)
        except Exception as err:
            print(f"[EmbeddedGraphStore] Load error: {err}")

    def save(self):
        """Save graph data to JSON file."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "nodes": list(self.nodes_data.values()),
                "edges": self.edges_data,
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as err:
            print(f"[EmbeddedGraphStore] Save error: {err}")

    def is_empty(self) -> bool:
        return len(self.nodes_data) == 0

    def clear(self):
        self.graph.clear()
        self.nodes_data.clear()
        self.edges_data.clear()
        self._name_type_index.clear()
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
            except Exception:
                pass

    def upsert_entity(self, label: str, name: str, properties: Dict[str, Any]) -> str:
        """Create or update a node and return its ID."""
        key = self._make_key(label, name)
        existing_id = self._name_type_index.get(key)

        props = {**properties, "name": name}
        if existing_id and existing_id in self.nodes_data:
            node_id = existing_id
            self.nodes_data[node_id]["properties"].update(props)
            self.nodes_data[node_id]["type"] = label
            self.nodes_data[node_id]["label"] = name
            nx.set_node_attributes(self.graph, {node_id: {"label": name, "type": label, **props}})
        else:
            clean_name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name).strip("_").lower()
            node_id = f"{label.lower()}_{clean_name}_{uuid.uuid4().hex[:6]}"
            node_data = {
                "id": node_id,
                "label": name,
                "type": label,
                "properties": props,
            }
            self.nodes_data[node_id] = node_data
            self.graph.add_node(node_id, label=name, type=label, **props)
            self._name_type_index[key] = node_id
            self._name_type_index[f":{name.strip().lower()}"] = node_id

        self.save()
        return node_id

    def upsert_relationship(
        self,
        from_label: str,
        from_name: str,
        to_label: str,
        to_name: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        from_id = self._name_type_index.get(self._make_key(from_label, from_name)) or self._name_type_index.get(f":{from_name.strip().lower()}")
        to_id = self._name_type_index.get(self._make_key(to_label, to_name)) or self._name_type_index.get(f":{to_name.strip().lower()}")

        if not from_id:
            from_id = self.upsert_entity(from_label, from_name, {})
        if not to_id:
            to_id = self.upsert_entity(to_label, to_name, {})

        props = properties or {}

        # Check if relationship already exists
        for e in self.edges_data:
            if e["source"] == from_id and e["target"] == to_id and e["type"] == rel_type:
                e["properties"].update(props)
                self.save()
                return True

        edge_id = f"rel_{uuid.uuid4().hex[:8]}"
        edge_data = {
            "id": edge_id,
            "source": from_id,
            "target": to_id,
            "type": rel_type,
            "properties": props,
        }
        self.edges_data.append(edge_data)
        self.graph.add_edge(from_id, to_id, key=edge_id, type=rel_type, **props)
        self.save()
        return True

    def get_stats(self) -> Dict[str, int]:
        counts = {
            "employees": 0,
            "projects": 0,
            "technologies": 0,
            "departments": 0,
            "customers": 0,
            "teams": 0,
            "documents": 0,
        }
        type_mapping = {
            "employee": "employees",
            "project": "projects",
            "technology": "technologies",
            "department": "departments",
            "customer": "customers",
            "team": "teams",
            "document": "documents",
        }
        for n in self.nodes_data.values():
            ntype = n.get("type", "").lower()
            key = type_mapping.get(ntype, f"{ntype}s")
            if key in counts:
                counts[key] += 1
        return counts

    def get_all_nodes(self, limit: int = 200, node_type: Optional[str] = None) -> Dict[str, List]:
        filtered_nodes = []
        for n in self.nodes_data.values():
            if node_type and node_type != "All":
                if n.get("type", "").lower() != node_type.lower():
                    continue
            filtered_nodes.append({
                "id": n["id"],
                "label": n.get("label") or n.get("properties", {}).get("name") or n["id"],
                "type": n.get("type", "Unknown"),
                "properties": n.get("properties", {}),
            })
            if len(filtered_nodes) >= limit:
                break

        node_ids = {n["id"] for n in filtered_nodes}
        filtered_edges = []
        for e in self.edges_data:
            if e["source"] in node_ids and e["target"] in node_ids:
                filtered_edges.append({
                    "source": e["source"],
                    "target": e["target"],
                    "type": e["type"],
                })
                if len(filtered_edges) >= limit:
                    break

        return {"nodes": filtered_nodes, "edges": filtered_edges}

    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        node = self.nodes_data.get(node_id)
        if not node:
            # Fallback search by name
            for n in self.nodes_data.values():
                if n.get("properties", {}).get("name") == node_id or n.get("label") == node_id:
                    node = n
                    node_id = n["id"]
                    break
        if not node:
            return None

        relationships = []
        for e in self.edges_data:
            if e["source"] == node_id:
                tgt = self.nodes_data.get(e["target"], {})
                relationships.append({
                    "rel_type": e["type"],
                    "direction": "out",
                    "neighbor_id": e["target"],
                    "neighbor_label": tgt.get("type", "Unknown"),
                    "neighbor_name": tgt.get("properties", {}).get("name") or tgt.get("label", ""),
                })
            elif e["target"] == node_id:
                src = self.nodes_data.get(e["source"], {})
                relationships.append({
                    "rel_type": e["type"],
                    "direction": "in",
                    "neighbor_id": e["source"],
                    "neighbor_label": src.get("type", "Unknown"),
                    "neighbor_name": src.get("properties", {}).get("name") or src.get("label", ""),
                })

        return {
            "id": node["id"],
            "type": node.get("type", "Unknown"),
            "properties": node.get("properties", {}),
            "relationships": relationships,
        }

    def get_neighbors(self, node_id: str) -> Dict[str, List]:
        target_node = self.nodes_data.get(node_id)
        if not target_node:
            for n in self.nodes_data.values():
                if n.get("properties", {}).get("name") == node_id or n.get("label") == node_id:
                    target_node = n
                    node_id = n["id"]
                    break
        if not target_node:
            return {"nodes": [], "edges": []}

        neighbor_ids = set()
        edges = []
        for e in self.edges_data:
            if e["source"] == node_id:
                neighbor_ids.add(e["target"])
                edges.append({"source": node_id, "target": e["target"], "type": e["type"]})
            elif e["target"] == node_id:
                neighbor_ids.add(e["source"])
                edges.append({"source": e["source"], "target": node_id, "type": e["type"]})

        nodes = []
        for nid in neighbor_ids:
            n = self.nodes_data.get(nid)
            if n:
                nodes.append({
                    "id": nid,
                    "label": n.get("label") or n.get("properties", {}).get("name") or nid,
                    "type": n.get("type", "Unknown"),
                    "properties": n.get("properties", {}),
                })

        return {"nodes": nodes, "edges": edges}

    def get_path(self, from_id: str, to_id: str) -> Dict[str, List]:
        # Support names or IDs
        if from_id not in self.nodes_data:
            for n in self.nodes_data.values():
                if n.get("properties", {}).get("name") == from_id or n.get("label") == from_id:
                    from_id = n["id"]
                    break
        if to_id not in self.nodes_data:
            for n in self.nodes_data.values():
                if n.get("properties", {}).get("name") == to_id or n.get("label") == to_id:
                    to_id = n["id"]
                    break

        if from_id not in self.graph or to_id not in self.graph:
            return {"nodes": [], "edges": []}

        try:
            undirected = self.graph.to_undirected()
            path = nx.shortest_path(undirected, source=from_id, target=to_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return {"nodes": [], "edges": []}

        path_nodes = []
        for nid in path:
            n = self.nodes_data.get(nid, {})
            path_nodes.append({
                "id": nid,
                "label": n.get("label") or n.get("properties", {}).get("name") or nid,
                "type": n.get("type", "Unknown"),
                "props": n.get("properties", {}),
            })

        path_edges = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            found = False
            for e in self.edges_data:
                if (e["source"] == u and e["target"] == v) or (e["source"] == v and e["target"] == u):
                    path_edges.append({
                        "source": e["source"],
                        "target": e["target"],
                        "type": e["type"],
                    })
                    found = True
                    break
            if not found:
                path_edges.append({"source": u, "target": v, "type": "CONNECTED_TO"})

        return {"nodes": path_nodes, "edges": path_edges}

    def get_subgraph_for_entity_ids(self, entity_ids: List[str]) -> Dict[str, List]:
        resolved_ids = set()
        for eid in entity_ids:
            if eid in self.nodes_data:
                resolved_ids.add(eid)
            else:
                for n in self.nodes_data.values():
                    if n.get("properties", {}).get("name") == eid or n.get("label") == eid:
                        resolved_ids.add(n["id"])
                        break

        nodes = []
        for nid in resolved_ids:
            n = self.nodes_data.get(nid)
            if n:
                nodes.append({
                    "id": nid,
                    "label": n.get("label") or n.get("properties", {}).get("name") or nid,
                    "type": n.get("type", "Unknown"),
                    "properties": n.get("properties", {}),
                })

        edges = []
        for e in self.edges_data:
            if e["source"] in resolved_ids and e["target"] in resolved_ids:
                edges.append({
                    "source": e["source"],
                    "target": e["target"],
                    "type": e["type"],
                })

        return {"nodes": nodes, "edges": edges}

    def get_team_tech_projects(self, team_name: str) -> Dict[str, Any]:
        """Multi-hop: Team -> USES -> Technology <- DEPENDS_ON <- Project"""
        team_id = self._name_type_index.get(self._make_key("Team", team_name)) or self._name_type_index.get(f":{team_name.strip().lower()}")
        if not team_id:
            for n in self.nodes_data.values():
                if n.get("type") == "Team" and (n.get("label", "").lower() == team_name.lower() or n.get("properties", {}).get("name", "").lower() == team_name.lower()):
                    team_id = n["id"]
                    break

        if not team_id:
            return {"team_name": team_name, "technologies": [], "affected_projects": []}

        # Find technologies used by team: (team)-[:USES]->(tech)
        used_techs: Dict[str, str] = {}  # tech_id -> tech_name
        for e in self.edges_data:
            if e["source"] == team_id and e["type"].upper() in ("USES", "USES_TECH"):
                tech_node = self.nodes_data.get(e["target"])
                if tech_node and tech_node.get("type") == "Technology":
                    t_name = tech_node.get("properties", {}).get("name") or tech_node.get("label")
                    used_techs[tech_node["id"]] = t_name

        tech_records = [{"tech_name": name, "tech_id": tid} for tid, name in used_techs.items()]

        # Find projects depending on these technologies: (project)-[:DEPENDS_ON]->(tech)
        affected_projects = []
        for e in self.edges_data:
            if e["target"] in used_techs and e["type"].upper() in ("DEPENDS_ON", "USES"):
                proj_node = self.nodes_data.get(e["source"])
                if proj_node and proj_node.get("type") == "Project":
                    p_name = proj_node.get("properties", {}).get("name") or proj_node.get("label")
                    p_desc = proj_node.get("properties", {}).get("description", "")
                    tech_id = e["target"]
                    affected_projects.append({
                        "team_name": team_name,
                        "team_id": team_id,
                        "tech_name": used_techs[tech_id],
                        "tech_id": tech_id,
                        "project_name": p_name,
                        "project_id": proj_node["id"],
                        "project_description": p_desc,
                    })

        affected_projects.sort(key=lambda x: (x["tech_name"], x["project_name"]))

        return {
            "team_name": team_name,
            "technologies": tech_records,
            "affected_projects": affected_projects,
        }

    def get_projects_by_technology(self) -> List[Dict]:
        counts: Dict[str, int] = {}
        for e in self.edges_data:
            if e["type"].upper() in ("DEPENDS_ON", "USES"):
                tech = self.nodes_data.get(e["target"])
                proj = self.nodes_data.get(e["source"])
                if tech and tech.get("type") == "Technology" and proj and proj.get("type") == "Project":
                    t_name = tech.get("properties", {}).get("name") or tech.get("label")
                    counts[t_name] = counts.get(t_name, 0) + 1

        sorted_techs = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{"technology": k, "project_count": v} for k, v in sorted_techs]

    def get_department_projects(self) -> List[Dict]:
        dept_proj_map: Dict[str, set] = {}
        for n in self.nodes_data.values():
            if n.get("type") == "Department":
                d_name = n.get("properties", {}).get("name") or n.get("label")
                dept_proj_map.setdefault(d_name, set())

        # Check projects with direct department property or edges
        for n in self.nodes_data.values():
            if n.get("type") == "Project":
                p_name = n.get("properties", {}).get("name") or n.get("label")
                dept = n.get("properties", {}).get("department")
                if dept:
                    dept_proj_map.setdefault(dept, set()).add(p_name)

        # Check edges: (project)-[:BELONGS_TO|PART_OF]->(department)
        for e in self.edges_data:
            if e["type"].upper() in ("BELONGS_TO", "PART_OF", "OWNED_BY"):
                proj = self.nodes_data.get(e["source"])
                dept = self.nodes_data.get(e["target"])
                if proj and proj.get("type") == "Project" and dept and dept.get("type") == "Department":
                    d_name = dept.get("properties", {}).get("name") or dept.get("label")
                    p_name = proj.get("properties", {}).get("name") or proj.get("label")
                    dept_proj_map.setdefault(d_name, set()).add(p_name)

        res = [{"department": k, "project_count": len(v)} for k, v in dept_proj_map.items() if len(v) > 0]
        res.sort(key=lambda x: x["project_count"], reverse=True)
        return res[:10]

    def get_top_relationships(self) -> List[Dict]:
        counts: Dict[str, int] = {}
        for e in self.edges_data:
            rel = e.get("type", "RELATED_TO")
            counts[rel] = counts.get(rel, 0) + 1
        sorted_rels = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{"relationship_type": k, "count": v} for k, v in sorted_rels]

    def get_entity_detail(self, entity_type: str, name: str) -> Optional[Dict]:
        label = entity_type.capitalize()
        target = None
        for n in self.nodes_data.values():
            n_name = n.get("properties", {}).get("name") or n.get("label")
            if (n["id"] == name or (n_name and n_name.lower() == name.lower())) and (n.get("type", "").lower() == entity_type.lower()):
                target = n
                break
        if not target:
            # Try without type constraint
            for n in self.nodes_data.values():
                n_name = n.get("properties", {}).get("name") or n.get("label")
                if n["id"] == name or (n_name and n_name.lower() == name.lower()):
                    target = n
                    break
        if not target:
            return None

        node_id = target["id"]
        relationships = []
        for e in self.edges_data:
            if e["source"] == node_id:
                tgt = self.nodes_data.get(e["target"], {})
                relationships.append({
                    "rel_type": e["type"],
                    "direction": "out",
                    "related_id": e["target"],
                    "related_type": tgt.get("type", "Unknown"),
                    "related_name": tgt.get("properties", {}).get("name") or tgt.get("label", ""),
                })
            elif e["target"] == node_id:
                src = self.nodes_data.get(e["source"], {})
                relationships.append({
                    "rel_type": e["type"],
                    "direction": "in",
                    "related_id": e["source"],
                    "related_type": src.get("type", "Unknown"),
                    "related_name": src.get("properties", {}).get("name") or src.get("label", ""),
                })

        return {
            "id": target["id"],
            "type": target.get("type", label),
            "properties": target.get("properties", {}),
            "relationships": relationships,
        }

    def find_nodes_by_names(self, names: List[str]) -> List[Dict]:
        name_lower_set = {n.strip().lower() for n in names}
        res = []
        for n in self.nodes_data.values():
            n_name = n.get("properties", {}).get("name") or n.get("label", "")
            if n_name.lower() in name_lower_set:
                res.append({
                    "id": n["id"],
                    "labels": [n.get("type", "Unknown")],
                    "name": n_name,
                })
        return res

    def get_all_node_names(self) -> List[Dict]:
        res = []
        for n in self.nodes_data.values():
            n_name = n.get("properties", {}).get("name") or n.get("label")
            if n_name:
                res.append({
                    "id": n["id"],
                    "type": n.get("type", "Unknown"),
                    "name": n_name,
                })
        return res


# Global singleton instance
_embedded_store: Optional[EmbeddedGraphStore] = None


def get_embedded_graph() -> EmbeddedGraphStore:
    global _embedded_store
    if _embedded_store is None:
        _embedded_store = EmbeddedGraphStore()
    return _embedded_store
