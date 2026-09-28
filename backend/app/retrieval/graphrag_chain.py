"""
GraphRAG chain: orchestrates hybrid retrieval + LLM synthesis.
Produces structured, evidence-backed answers with subgraph data.
Includes in-memory query response caching for sub-millisecond repeated queries.
"""
import json
import re
import time
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI, OpenAIError
from app.core.config import get_settings
from app.retrieval.hybrid_retriever import retrieve, format_context_for_llm

settings = get_settings()

SYSTEM_PROMPT = """You are KnowSphere, an intelligent enterprise knowledge assistant powered by GraphRAG.
You answer questions by combining document retrieval and knowledge graph traversal.
Always provide structured, evidence-backed answers with citations to source documents and graph paths.
Be concise, precise, and professional."""

ANSWER_PROMPT = """Based on the retrieved context below, answer the user's question concisely.

{context}

Question: {question}

Provide your answer in this exact JSON format (no markdown fences, raw JSON only):
{{
  "findings": [
    "Finding 1: ...",
    "Finding 2: ...",
    "Finding 3: ..."
  ],
  "graph_path_explanation": "Plain English explanation of the graph traversal path used, e.g. 'Team A → Technology X/Y/Z → Project Phoenix/Nova/Atlas'",
  "answer_summary": "A concise 2-3 sentence summary directly answering the question",
  "sources": [
    {{"name": "document_name.docx", "relevance": "Why this source is relevant"}},
    {{"name": "Knowledge Graph: Team A → Technology", "relevance": "Graph path used"}}
  ],
  "follow_up_suggestions": [
    "What are the timelines for migrating away from Technology X?",
    "Which employees on Team A are critical to these projects?",
    "Are there alternative technologies that could replace Technology X?"
  ]
}}

If context is insufficient, still follow the format and explain what's missing in answer_summary."""

# In-memory query cache: {normalized_q: (result_dict, timestamp)}
_QUERY_CACHE: Dict[str, tuple] = {}
_QUERY_CACHE_TTL = 300.0  # 5 minutes


def _normalize_query_key(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=25.0,
    )


def clear_query_cache():
    """Clear query cache when data changes."""
    global _QUERY_CACHE
    _QUERY_CACHE.clear()


async def ask(
    question: str,
    chat_history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Main GraphRAG entry point.
    Returns: structured answer + subgraph data for visualization.
    """
    cache_key = _normalize_query_key(question)
    now = time.time()

    # If no conversational chat history, check fast in-memory query cache
    if not chat_history and cache_key in _QUERY_CACHE:
        cached_res, cached_time = _QUERY_CACHE[cache_key]
        if now - cached_time < _QUERY_CACHE_TTL:
            return cached_res

    # 1. Hybrid retrieval (concurrent vector + fast entity graph traversal)
    retrieval = await retrieve(question)
    context_text = format_context_for_llm(retrieval)

    # 2. Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chat_history:
        for msg in chat_history[-4:]:  # last 4 exchanges for context
            messages.append({"role": msg["role"], "content": msg["content"]})

    prompt = ANSWER_PROMPT.format(
        context=context_text if context_text else "No specific context retrieved. Answer from general knowledge.",
        question=question,
    )
    messages.append({"role": "user", "content": prompt})

    # 3. LLM call with compact max_tokens for high throughput
    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            max_tokens=650,
        )
    except OpenAIError as e:
        print(f"[GraphRAGChain] LLM request error: {e}")
        structured = {
            "findings": ["The LLM request failed. Check LLM_API_KEY and LLM_MODEL."],
            "graph_path_explanation": "Graph traversal was performed, but answer generation failed.",
            "answer_summary": "The answer service could not reach the configured language model.",
            "sources": [],
            "follow_up_suggestions": [],
        }
    else:
        try:
            raw = (response.choices[0].message.content or "").strip()
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            structured = json.loads(raw)
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            print(f"[GraphRAGChain] Parse error: {e}")
            structured = {
                "findings": ["The language model returned an invalid structured response. Please try again."],
                "graph_path_explanation": "Graph traversal was performed, but response parsing failed.",
                "answer_summary": "The language model response could not be read as structured data.",
                "sources": [],
                "follow_up_suggestions": [],
            }

    # 4. Enrich with subgraph data
    subgraph_node_ids = retrieval.get("subgraph_node_ids", [])

    # Add source docs from vector hits
    source_docs = list({c["doc_name"] for c in retrieval.get("vector_chunks", []) if "doc_name" in c})

    # Merge sources
    existing_source_names = {s["name"] for s in structured.get("sources", []) if "name" in s}
    for doc_name in source_docs:
        if doc_name not in existing_source_names:
            structured.setdefault("sources", []).append({
                "name": doc_name,
                "relevance": "Retrieved via semantic search",
            })

    result = {
        "answer": structured.get("answer_summary", ""),
        "findings": structured.get("findings", []),
        "graph_path_explanation": structured.get("graph_path_explanation", ""),
        "sources": structured.get("sources", []),
        "follow_up_suggestions": structured.get("follow_up_suggestions", []),
        "subgraph_node_ids": subgraph_node_ids,
        "question_entities": retrieval.get("question_entities", []),
        "graph_context_used": retrieval.get("graph_context", []),
    }

    # Save to query cache
    if not chat_history and result["answer"]:
        _QUERY_CACHE[cache_key] = (result, now)

    return result
