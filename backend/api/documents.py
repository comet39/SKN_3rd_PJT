# documents.py - Auto-generated
"""
Document API endpoints for document search and management
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
import os
import json
from datetime import datetime

from config import settings
from models import get_db
from models.document import DocumentRead, DocumentDetailRead, DocumentSearchQuery, DocumentSearchResult
from modules.vector_db.db import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize vector store
vector_store = VectorStore()

# 국가/토픽 기준 필터링 조회
@router.get("/{country_id}/{topic_id}", response_model=List[DocumentRead])
async def get_documents_by_country_topic(
    country_id: int,
    topic_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get documents filtered by country and topic"""
    from sqlalchemy import select
    from models.document import Document
    
    query = (
        select(Document)
        .where(Document.country_id == country_id)
        .where(Document.topic_id == topic_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    
    documents = db.execute(query).scalars().all()
    
    return [
        DocumentRead(
            id=doc.id,
            title=doc.title,
            url=doc.url,
            doc_type=doc.doc_type,
            country_id=doc.country_id,
            topic_id=doc.topic_id,
            source_id=doc.source_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in documents
    ]

# 문서 ID로 문서 조회
@router.get("/{document_id}", response_model=DocumentDetailRead)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific document with content"""
    from sqlalchemy import select
    from models.document import Document
    
    query = select(Document).where(Document.id == document_id)
    document = db.execute(query).scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    return DocumentDetailRead(
        id=document.id,
        title=document.title,
        url=document.url,
        doc_type=document.doc_type,
        country_id=document.country_id,
        topic_id=document.topic_id,
        source_id=document.source_id,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


# Vector + 메타 필터 기반 하이브리드 검색
@router.post("/search", response_model=List[DocumentSearchResult])
async def search_documents(
    query: DocumentSearchQuery,
    db: Session = Depends(get_db)
):
    """Search documents using vector search"""
    # Prepare filter
    filter_dict = {}
    if query.country_id:
        filter_dict["metadata.country_id"] = query.country_id
    if query.topic_id:
        filter_dict["metadata.topic_id"] = query.topic_id
    
    # Perform search
    search_results = vector_store.hybrid_search(
        query=query.query,
        filter_dict=filter_dict,
        k=query.limit
    )
    
    # Format results
    results = []
    for result in search_results:
        # Get document info
        document_id = result["metadata"].get("document_id")
        if not document_id:
            continue
        
        # Get the document from the database
        try:
            from sqlalchemy import select
            from models.document import Document
            
            statement = select(Document).where(Document.id == document_id)
            document = db.execute(statement).scalar_one_or_none()
            
            if document:
                results.append(
                    DocumentSearchResult(
                        document=DocumentRead(
                            id=document.id,
                            title=document.title,
                            url=document.url,
                            doc_type=document.doc_type,
                            country_id=document.country_id,
                            topic_id=document.topic_id,
                            source_id=document.source_id,
                            created_at=document.created_at,
                            updated_at=document.updated_at,
                        ),
                        relevance_score=result["score"],
                        matching_chunk=result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"]
                    )
                )
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
    
    return results
