"""
LLM-driven entity and relationship extraction from document text.
Uses Groq (OpenAI-compatible API) with structured JSON output.
"""
import json
import re
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()

ENTITY_TYPES = ["Employee", "Team", "Project", "Technology", "Department", "Customer", "Product"]
RELATIONSHIP_TYPES = ["MEMBER_OF", "DEPENDS_ON", "USES", "WORKS_ON", "PART_OF", "OWNS", "BELONGS_TO", "MENTIONED_IN"]

EXTRACTION_PROMPT = """You are an expert knowledge graph builder. Extract entities and relationships from the following enterprise document text.

Entity types to extract: Employee, Team, Project, Technology, Department, Customer, Product

Relationship types to use:
- MEMBER_OF: Employee is member of Team
- DEPENDS_ON: Project depends on Technology
- USES: Team uses Technology
- WORKS_ON: Employee works on Project
- PART_OF: Team is part of Department
- OWNS: Department/Team owns Project
- BELONGS_TO: Project belongs to Department
- MENTIONED_IN: Any entity mentioned in a Document

Return ONLY a valid JSON object (no markdown, no explanation) with this exact structure:
{
  "entities": [
    {"type": "Employee", "name": "Alice Smith", "properties": {"role": "Software Engineer", "email": "alice@company.com"}},
    {"type": "Team", "name": "Team A", "properties": {"description": "Core engineering team"}},
    {"type": "Technology", "name": "Technology X", "properties": {"description": "Cloud infrastructure platform"}},
    {"type": "Project", "name": "Project Phoenix", "properties": {"status": "active", "description": "..."}}
  ],
  "relationships": [
    {"from_type": "Employee", "from_name": "Alice Smith", "to_type": "Team", "to_name": "Team A", "rel_type": "MEMBER_OF"},
    {"from_type": "Team", "from_name": "Team A", "to_type": "Technology", "to_name": "Technology X", "rel_type": "USES"},
    {"from_type": "Project", "from_name": "Project Phoenix", "to_type": "Technology", "to_name": "Technology X", "rel_type": "DEPENDS_ON"}
  ]
}

Document text:
{text}
"""


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


async def extract_entities_and_relationships(text: str, max_chars: int = 4000) -> Dict[str, List]:
    """
    Run LLM entity/relationship extraction on document text.
    Truncates text to max_chars to stay within context limits.
    """
    truncated = text[:max_chars]
    prompt = EXTRACTION_PROMPT.format(text=truncated)

    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        result = json.loads(raw)
        return {
            "entities": result.get("entities", []),
            "relationships": result.get("relationships", []),
        }
    except json.JSONDecodeError:
        # Attempt partial recovery
        return {"entities": [], "relationships": []}
    except Exception as e:
        print(f"[EntityExtractor] Error: {e}")
        return {"entities": [], "relationships": []}


async def extract_question_entities(question: str) -> List[Dict[str, str]]:
    """Extract entity mentions from a user question for graph lookup."""
    prompt = f"""From this question, extract any organization entity mentions (Employee names, Team names, Project names, Technology names, Department names, Customer names).

Return ONLY a JSON array of objects with 'type' and 'name' fields. If none found, return [].

Question: {question}

Example output: [{{"type": "Team", "name": "Team A"}}, {{"type": "Technology", "name": "Technology X"}}]"""

    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except Exception:
        return []
