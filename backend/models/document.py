# document.py - Auto-generated
"""
Document models for database and API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, JSON, func
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from models import Base

# SQLAlchemy Models
class Document(Base):
    """Document model for storing document information"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    doc_type = Column(String(100), nullable=True)  # e.g., PDF, HTML, etc.
    url = Column(String(500), nullable=True)
    file_path = Column(String(255), nullable=True)  # Local file path if applicable
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    source = relationship("Source", back_populates="documents")
    country = relationship("Country", back_populates="documents")
    topic = relationship("Topic", back_populates="documents")
    
# Pydantic Models for API
class DocumentBase(BaseModel):
    """Base document schema"""
    title: str
    url: Optional[str] = None
    doc_type: str
    country_id: int
    topic_id: int
    source_id: int

class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    file_path: Optional[str] = None

class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None

class DocumentRead(DocumentBase):
    """Schema for reading a document"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class DocumentDetailRead(DocumentRead):
    """Schema for reading a document with full details"""
    
    class Config:
        orm_mode = True

class DocumentSearchQuery(BaseModel):
    """Schema for document search queries"""
    query: str
    country_id: Optional[int] = None
    topic_id: Optional[int] = None
    limit: int = 10

class DocumentSearchResult(BaseModel):
    """Schema for document search results"""
    document: DocumentRead
    relevance_score: float
    matching_chunk: Optional[str] = None
    
    class Config:
        orm_mode = True