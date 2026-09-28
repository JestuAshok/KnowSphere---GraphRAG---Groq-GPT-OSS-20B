import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import UserORM
from app.models.chat import ChatSessionORM, ChatMessageORM

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history")
async def chat_history(
    user: UserORM = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    result = await db.execute(
        select(ChatSessionORM)
        .where(ChatSessionORM.user_id == user.id)
        .order_by(desc(ChatSessionORM.updated_at))
        .limit(limit)
    )
    sessions = result.scalars().all()

    output = []
    for s in sessions:
        # Get the first user message (the question)
        first_msg = await db.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == s.id, ChatMessageORM.role == "user")
            .order_by(ChatMessageORM.created_at)
            .limit(1)
        )
        first = first_msg.scalar_one_or_none()
        output.append({
            "session_id": s.id,
            "title": s.title,
            "question": first.content if first else s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat() if s.updated_at else s.created_at.isoformat(),
        })
    return output


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user: UserORM = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sess_result = await db.execute(
        select(ChatSessionORM).where(
            ChatSessionORM.id == session_id,
            ChatSessionORM.user_id == user.id,
        )
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs_result = await db.execute(
        select(ChatMessageORM)
        .where(ChatMessageORM.session_id == session_id)
        .order_by(ChatMessageORM.created_at)
    )
    messages = msgs_result.scalars().all()

    return {
        "session_id": session_id,
        "title": session.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "structured_answer": json.loads(m.structured_answer) if m.structured_answer else None,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }
