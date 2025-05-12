# session.py - Auto-generated
"""
Session management API endpoints
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from config import settings
from models import get_db
from models.chat import ConversationRead, ConversationDetailRead

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_info(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get session information including conversations"""
    from sqlalchemy import select
    from models.chat import Conversation
    
    # Get all conversations for this session
    statement = select(Conversation).where(
        Conversation.session_id == session_id
    ).order_by(Conversation.created_at.desc())
    
    conversations = db.execute(statement).scalars().all()
    
    # If no conversations, create a new one
    if not conversations:
        return {
            "session_id": session_id,
            "is_new": True,
            "conversations": [],
            "active_conversation_id": None
        }
    
    # Format conversations
    formatted_conversations = []
    active_conversation_id = None
    
    for conversation in conversations:
        formatted_conversations.append({
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "active": conversation.active,
            "country_id": conversation.country_id,
            "topic_id": conversation.topic_id
        })
        
        # Set active conversation (the most recent active one)
        if conversation.active and active_conversation_id is None:
            active_conversation_id = conversation.id
    
    return {
        "session_id": session_id,
        "is_new": False,
        "conversations": formatted_conversations,
        "active_conversation_id": active_conversation_id
    }

@router.post("/{session_id}/new", response_model=ConversationRead)
async def create_new_session_conversation(
    session_id: str,
    country_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    title: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new conversation in the session"""
    from models.chat import Conversation
    
    # Create default title if not provided
    if not title:
        title = f"Conversation {uuid.uuid4().hex[:6]}"
    
    # Create new conversation
    conversation = Conversation(
        session_id=session_id,
        title=title,
        country_id=country_id,
        topic_id=topic_id,
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return ConversationRead(
        id=conversation.id,
        title=conversation.title,
        session_id=conversation.session_id,
        country_id=conversation.country_id,
        topic_id=conversation.topic_id,
        active=conversation.active,
        metadata=conversation.metadata,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )

@router.post("/{session_id}/end", response_model=Dict[str, Any])
async def end_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """End all active conversations in a session"""
    from sqlalchemy import select, update
    from models.chat import Conversation
    
    # Update all active conversations to inactive
    statement = (
        update(Conversation)
        .where(Conversation.session_id == session_id)
    )
    
    db.execute(statement)
    db.commit()
    
    return {
        "session_id": session_id,
        "status": "ended"
    }

@router.get("/{session_id}/conversations", response_model=List[ConversationRead])
async def get_session_conversations(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get all conversations for a session"""
    from sqlalchemy import select
    from models.chat import Conversation
    
    statement = select(Conversation).where(
        Conversation.session_id == session_id
    ).order_by(Conversation.created_at.desc())
    
    conversations = db.execute(statement).scalars().all()
    
    return [
        ConversationRead(
            id=conversation.id,
            title=conversation.title,
            session_id=conversation.session_id,
            country_id=conversation.country_id,
            topic_id=conversation.topic_id,
            active=conversation.active,
            metadata=conversation.metadata,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        for conversation in conversations
    ]

@router.get("/{session_id}/active", response_model=Optional[ConversationDetailRead])
async def get_active_conversation(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get the active conversation for a session"""
    from sqlalchemy import select
    from models.chat import Conversation
    
    statement = select(Conversation).where(
        Conversation.session_id == session_id
    ).order_by(Conversation.created_at.desc())
    
    conversation = db.execute(statement).scalar_one_or_none()
    
    if not conversation:
        return None
    
    # Get messages for this conversation
    messages = []
    for message in conversation.messages:
        messages.append({
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at
        })
    
    return ConversationDetailRead(
        id=conversation.id,
        title=conversation.title,
        session_id=conversation.session_id,
        country_id=conversation.country_id,
        topic_id=conversation.topic_id,
        active=conversation.active,
        metadata=conversation.metadata,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages
    )

@router.post("/{session_id}/update", response_model=Dict[str, Any])
async def update_session_preferences(
    session_id: str,
    country_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update preferences for the active conversation in a session"""
    from sqlalchemy import select, update
    from models.chat import Conversation
    
    # Get active conversation
    statement = select(Conversation).where(
        Conversation.session_id == session_id
    ).order_by(Conversation.created_at.desc())
    
    conversation = db.execute(statement).scalar_one_or_none()
    
    if not conversation:
        # Create new conversation if none exists
        return await create_new_session_conversation(
            session_id=session_id,
            country_id=country_id,
            topic_id=topic_id,
            db=db
        )
    
    # Update conversation
    update_values = {}
    if country_id is not None:
        update_values["country_id"] = country_id
    if topic_id is not None:
        update_values["topic_id"] = topic_id
    
    if update_values:
        conversation_id = conversation.id
        statement = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(**update_values)
        )
        
        db.execute(statement)
        db.commit()
    
    # Get updated conversation
    statement = select(Conversation).where(Conversation.id == conversation.id)
    updated_conversation = db.execute(statement).scalar_one()
    
    return {
        "session_id": session_id,
        "conversation_id": updated_conversation.id,
        "country_id": updated_conversation.country_id,
        "topic_id": updated_conversation.topic_id,
        "status": "updated"
    }