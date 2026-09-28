"""
Full document ingestion pipeline:
1. Extract text from file
2. Chunk text
3. Embed chunks → FAISS
4. LLM entity/relationship extraction
5. Write entities/relationships to Neo4j
6. Log activity
"""
import os
import re
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import get_settings
from app.retrieval.embedder import add_documents
from app.retrieval.entity_extractor import extract_entities_and_relationships
from app.retrieval.disambiguator import disambiguate_entities
from app.graph.cypher_queries import upsert_entity, upsert_relationship
from app.graph.neo4j_driver import run_write_query

settings = get_settings()

CHUNK_SIZE = 512  # characters (approx 128 tokens)
CHUNK_OVERLAP = 64


# ─────────────────────────────────────────────
#  TEXT EXTRACTION
# ─────────────────────────────────────────────

def extract_text_from_file(file_path: str, mime_type: str = "") -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    try:
        if suffix == ".txt" or suffix == ".md":
            return path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".docx":
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        elif suffix == ".pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix in (".xlsx", ".xls"):
            import openpyxl
            wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
            lines = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = "\t".join(str(c) for c in row if c is not None)
                    if row_text.strip():
                        lines.append(row_text)
            return "\n".join(lines)
        else:
            # Attempt plain text
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"[Ingestion] Text extraction error for {path}: {e}")
        return ""


# ─────────────────────────────────────────────
#  CHUNKING
# ─────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return [c for c in chunks if c.strip()]


# ─────────────────────────────────────────────
#  MAIN PIPELINE
# ─────────────────────────────────────────────

async def ingest_document(
    file_path: str,
    doc_id: str,
    doc_name: str,
    mime_type: str = "",
    log_activity_fn=None,
) -> Dict[str, Any]:
    """
    Full ingestion pipeline for a single document.
    Returns: {"entities": [...], "relationships": [...], "chunks_added": int, "neo4j_doc_id": str}
    """
    # 1. Extract text
    text = extract_text_from_file(file_path, mime_type)
    if not text.strip():
        return {"entities": [], "relationships": [], "chunks_added": 0, "neo4j_doc_id": "", "text": ""}

    # 2. Chunk
    chunks = chunk_text(text)

    # 3. Add to FAISS
    faiss_chunks = [
        {
            "text": chunk,
            "doc_id": doc_id,
            "doc_name": doc_name,
            "chunk_idx": i,
        }
        for i, chunk in enumerate(chunks)
    ]
    add_documents(faiss_chunks)

    # 4. Entity + relationship extraction (on first 4000 chars of full text)
    extraction = await extract_entities_and_relationships(text)
    entities = extraction.get("entities", [])
    relationships = extraction.get("relationships", [])

    # 5. Disambiguate entities
    disambiguated = await disambiguate_entities(entities)

    # 6. Write Document node to Neo4j
    neo4j_doc_id = await upsert_entity("Document", doc_name, {
        "doc_id": doc_id,
        "filename": doc_name,
        "ingested_at": datetime.utcnow().isoformat(),
    })

    # 7. Upsert entities and their MENTIONED_IN relationships
    for entity in disambiguated:
        canonical_name = entity.get("canonical_name", entity.get("name", ""))
        label = entity.get("type", "Entity")
        props = entity.get("properties", {})
        if canonical_name:
            await upsert_entity(label, canonical_name, props)
            # Link to document
            await upsert_relationship(
                label, canonical_name,
                "Document", doc_name,
                "MENTIONED_IN"
            )

    # 8. Upsert relationships
    for rel in relationships:
        from_name = rel.get("from_name", "")
        to_name = rel.get("to_name", "")
        from_type = rel.get("from_type", "Entity")
        to_type = rel.get("to_type", "Entity")
        rel_type = rel.get("rel_type", "RELATED_TO")
        if from_name and to_name:
            try:
                await upsert_relationship(from_type, from_name, to_type, to_name, rel_type)
            except Exception as e:
                print(f"[Ingestion] Relationship upsert error: {e}")

    # 9. Log activity
    if log_activity_fn:
        await log_activity_fn(
            event_type="document_ingested",
            description=f"Document '{doc_name}' ingested: {len(disambiguated)} entities, {len(relationships)} relationships extracted",
            entity_type="Document",
            entity_name=doc_name,
        )
        for ent in disambiguated[:5]:  # log first 5 new entities
            if not ent.get("matched"):
                await log_activity_fn(
                    event_type="entity_detected",
                    description=f"New {ent['type']} entity detected: {ent.get('canonical_name', ent['name'])}",
                    entity_type=ent["type"],
                    entity_name=ent.get("canonical_name", ent["name"]),
                )

    return {
        "entities": disambiguated,
        "relationships": relationships,
        "chunks_added": len(faiss_chunks),
        "neo4j_doc_id": neo4j_doc_id,
        "text": text,
    }
