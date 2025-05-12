# chat.py - Auto-generated
"""
Chat models for conversations, sessions, and messages
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from models import Base

# SQLAlchemy Models
class Conversation(Base):
    """Conversation model for database"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)  # Auto-generated or user-defined
    session_id = Column(String(100), nullable=False, index=True)  # Client session ID
    
    # Country and topic for this conversation
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    """Message model for database"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # For assistant messages, store context and sources used
    source_references = Column(JSON, nullable=True)  # Sources cited in response
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models for API
class MessageBase(BaseModel):
    """Base message schema"""
    role: Literal["user", "assistant", "system"]
    content: str

class MessageCreate(MessageBase):
    """Schema for creating a message"""
    references: Optional[List[Dict[str, Any]]] = None

class MessageRead(MessageBase):
    """Schema for reading a message"""
    id: int
    created_at: datetime
    references: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        orm_mode = True

class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: Optional[str] = None
    country_id: Optional[int] = None
    topic_id: Optional[int] = None

class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""
    session_id: str

class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    title: Optional[str] = None
    country_id: Optional[int] = None
    topic_id: Optional[int] = None
    active: Optional[bool] = None

class ConversationRead(ConversationBase):
    """Schema for reading a conversation"""
    id: int
    session_id: str
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ConversationDetailRead(ConversationRead):
    """Schema for reading a conversation with messages"""
    messages: List[MessageRead] = []
    
    class Config:
        orm_mode = True

class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str
    conversation_id: Optional[int] = None
    session_id: str = Field(..., description="Client session ID")
    country: Optional[str] = None
    topic: Optional[str] = None
    stream: bool = False
    model: Optional[str] = None

class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: MessageRead
    conversation_id: int
    references: Optional[List[Dict[str, Any]]] = None

class StreamingChatResponse(BaseModel):
    """Schema for streaming chat response chunks"""
    type: Literal["token", "reference", "end"]
    content: str
    references: Optional[List[Dict[str, Any]]] = None