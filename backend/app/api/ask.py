import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import UserORM
from app.models.chat import ChatSessionORM, ChatMessageORM
from app.retrieval.graphrag_chain import ask
from app.graph.cypher_queries import get_subgraph_for_entity_ids

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    session_id: str
    message_id: str
    question: str
    answer: str
    findings: List[str]
    graph_path_explanation: str
    sources: List[dict]
    follow_up_suggestions: List[str]
    subgraph_node_ids: List[str]
    subgraph: Optional[dict] = None


@router.post("", response_model=AskResponse)
async def ask_question(
    req: AskRequest,
    user: UserORM = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get or create session
    session_id = req.session_id
    if session_id:
        result = await db.execute(
            select(ChatSessionORM).where(
                ChatSessionORM.id == session_id,
                ChatSessionORM.user_id == user.id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            session_id = None

    if not session_id:
        session = ChatSessionORM(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title=req.question[:60] + ("..." if len(req.question) > 60 else ""),
        )
        db.add(session)
        await db.flush()
        session_id = session.id

    # Load prior chat history for context
    history_result = await db.execute(
        select(ChatMessageORM)
        .where(ChatMessageORM.session_id == session_id)
        .order_by(ChatMessageORM.created_at)
        .limit(10)
    )
    history_messages = history_result.scalars().all()
    chat_history = [{"role": m.role, "content": m.content} for m in history_messages]

    # Save user message
    user_msg = ChatMessageORM(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=req.question,
    )
    db.add(user_msg)

    # Run GraphRAG
    result = await ask(req.question, chat_history)

    # Fetch subgraph for visualization
    subgraph = None
    node_ids = result.get("subgraph_node_ids", [])
    if node_ids:
        try:
            subgraph = await get_subgraph_for_entity_ids(node_ids)
        except Exception:
            subgraph = None

    # Save assistant message
    asst_msg = ChatMessageORM(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=result.get("answer", ""),
        structured_answer=json.dumps(result),
    )
    db.add(asst_msg)
    await db.commit()

    return AskResponse(
        session_id=session_id,
        message_id=asst_msg.id,
        question=req.question,
        answer=result.get("answer", ""),
        findings=result.get("findings", []),
        graph_path_explanation=result.get("graph_path_explanation", ""),
        sources=result.get("sources", []),
        follow_up_suggestions=result.get("follow_up_suggestions", []),
        subgraph_node_ids=node_ids,
        subgraph=subgraph,
    )
