"""
Entity disambiguation: resolve name variants to canonical Neo4j / embedded graph nodes.
Uses cached exact matches first, falling back to cached embedding similarity.
"""
import re
import time
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from app.retrieval.embedder import embed_texts
from app.graph.cypher_queries import find_nodes_by_names
from app.graph.neo4j_driver import run_query, is_neo4j_available
from app.graph.embedded_graph import get_embedded_graph

# In-memory cache for node metadata and candidate embeddings
_NODES_CACHE: List[Dict[str, Any]] = []
_NODES_CACHE_TIME: float = 0.0
_NODES_CACHE_TTL: float = 60.0  # seconds

_CANDIDATE_EMBEDDINGS: Dict[str, np.ndarray] = {}  # node id -> embedding vector


async def get_all_node_names(force_refresh: bool = False) -> List[Dict]:
    """Fetch all node names with in-memory TTL caching."""
    global _NODES_CACHE, _NODES_CACHE_TIME
    now = time.time()
    if not force_refresh and _NODES_CACHE and (now - _NODES_CACHE_TIME < _NODES_CACHE_TTL):
        return _NODES_CACHE

    nodes = []
    if not await is_neo4j_available():
        nodes = get_embedded_graph().get_all_node_names()
    else:
        try:
            nodes = await run_query("""
                MATCH (n)
                WHERE n.name IS NOT NULL
                RETURN elementId(n) AS id, labels(n)[0] AS type, n.name AS name
                LIMIT 5000
            """)
        except Exception:
            nodes = get_embedded_graph().get_all_node_names()

    _NODES_CACHE = nodes
    _NODES_CACHE_TIME = now
    return _NODES_CACHE


def invalidate_node_cache():
    """Clear cached nodes on graph updates."""
    global _NODES_CACHE, _NODES_CACHE_TIME, _CANDIDATE_EMBEDDINGS
    _NODES_CACHE = []
    _NODES_CACHE_TIME = 0.0
    _CANDIDATE_EMBEDDINGS = {}


def normalize_name(name: str) -> str:
    """Simple normalization: lowercase, strip, collapse whitespace."""
    return re.sub(r"\s+", " ", name.strip().lower())


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two unit vectors."""
    return float(np.dot(a, b))


async def disambiguate_entity(
    name: str,
    entity_type: Optional[str] = None,
    threshold: float = 0.85,
    all_nodes: Optional[List[Dict]] = None,
) -> Optional[Dict]:
    """
    Try to match `name` to an existing graph node.
    Returns the matched node dict or None if no close match.
    """
    if all_nodes is None:
        all_nodes = await get_all_node_names()
    if not all_nodes:
        return None

    # Filter by type if provided
    if entity_type:
        candidates = [n for n in all_nodes if n.get("type", "").lower() == entity_type.lower()]
    else:
        candidates = all_nodes

    if not candidates:
        return None

    # 1. Exact & normalized match (instant O(1)-like lookup)
    norm_query = normalize_name(name)
    for node in candidates:
        if normalize_name(node["name"]) == norm_query:
            return node

    # 2. Substring match for compound names (e.g. "Phoenix" -> "Project Phoenix")
    for node in candidates:
        norm_node = normalize_name(node["name"])
        if norm_query in norm_node or norm_node in norm_query:
            # Check length ratio to avoid false positives on tiny words
            if len(norm_query) >= 3 and len(norm_node) >= 3:
                return node

    # 3. Embedding similarity match (only embed single query text, reuse cached candidate embeddings)
    global _CANDIDATE_EMBEDDINGS
    try:
        # Precompute missing candidate embeddings in bulk
        missing = [c for c in candidates if c["id"] not in _CANDIDATE_EMBEDDINGS]
        if missing:
            missing_names = [m["name"] for m in missing]
            new_embs = embed_texts(missing_names)
            for m, emb in zip(missing, new_embs):
                _CANDIDATE_EMBEDDINGS[m["id"]] = emb

        query_emb = embed_texts([name])[0]
        best_score = -1.0
        best_node = None
        for node in candidates:
            emb = _CANDIDATE_EMBEDDINGS.get(node["id"])
            if emb is not None:
                score = cosine_similarity(query_emb, emb)
                if score > best_score:
                    best_score = score
                    best_node = node

        if best_score >= threshold:
            return best_node
    except Exception as e:
        print(f"[Disambiguator] Embedding match error: {e}")

    return None


async def disambiguate_entities(
    entities: List[Dict],
    threshold: float = 0.85,
) -> List[Dict]:
    """
    Disambiguate a list of extracted entities using single cached node list.
    Adds 'canonical_name' and 'neo4j_id' fields if matched.
    """
    if not entities:
        return []

    all_nodes = await get_all_node_names()
    result = []
    for entity in entities:
        name = entity.get("name", "")
        etype = entity.get("type")
        matched = await disambiguate_entity(name, etype, threshold, all_nodes=all_nodes)
        enriched = dict(entity)
        if matched:
            enriched["canonical_name"] = matched["name"]
            enriched["neo4j_id"] = matched["id"]
            enriched["matched"] = True
            enriched["type"] = matched.get("type", etype)
        else:
            enriched["canonical_name"] = name
            enriched["matched"] = False
        result.append(enriched)
    return result
