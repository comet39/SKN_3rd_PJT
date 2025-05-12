# metadata.py - Auto-generated
"""
Metadata API endpoints for countries, topics, and sources
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from config import settings
from models import get_db
from models.metadata import Country, Topic, Source, RequiredItem, FAQ

logger = logging.getLogger(__name__)

# Pydantic 모델 정의
class BaseModelWithTimestamp(BaseModel):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CountryBase(BaseModel):
    name: str
    code: str
    flag_url: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True

class CountryRead(CountryBase, BaseModelWithTimestamp):
    id: int

class TopicBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True

class TopicRead(TopicBase, BaseModelWithTimestamp):
    id: int

class SourceBase(BaseModel):
    name: str
    url: Optional[str] = None
    source_type: str
    description: Optional[str] = None

class SourceRead(SourceBase, BaseModelWithTimestamp):
    id: int

class RequiredItemBase(BaseModel):
    item: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: bool = True

class RequiredItemRead(RequiredItemBase, BaseModelWithTimestamp):
    id: int
    country_id: int

class FAQBase(BaseModel):
    question: str
    answer: str
    country_id: Optional[int] = None
    topic_id: Optional[int] = None
    is_featured: bool = False
    view_count: int = 0

class FAQRead(FAQBase, BaseModelWithTimestamp):
    id: int

class CountryWithItems(CountryRead):
    required_items: List[RequiredItemRead] = []

router = APIRouter()
# 국가 목록 조회
@router.get("/countries", response_model=List[CountryRead])
async def get_countries(db: Session = Depends(get_db)):
    """Get all countries"""
    from sqlalchemy import select
    from models.metadata import Country
    
    statement = select(Country).where(Country.enabled == True).order_by(Country.name)
    countries = db.execute(statement).scalars().all()
    
    return [
        CountryRead(
            id=country.id,
            name=country.name,
            code=country.code,
            enabled=country.enabled,
            created_at=country.created_at,
            updated_at=country.updated_at
        )
        for country in countries
    ]

# 국가 ID로 국가 조회
@router.get("/countries/{country_id}", response_model=CountryWithItems)
async def get_country(country_id: int, db: Session = Depends(get_db)):
    """Get a country by ID with required items"""
    from sqlalchemy import select
    from models.metadata import Country
    
    statement = select(Country).where(Country.id == country_id)
    country = db.execute(statement).scalar_one_or_none()
    
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")
    
    # Get required items
    required_items = [
        RequiredItemRead(
            id=item.id,
            country_id=item.country_id,
            item=item.item,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in country.required_items
    ]
    
    return CountryWithItems(
        id=country.id,
        name=country.name,
        code=country.code,
        enabled=country.enabled,
        created_at=country.created_at,
        updated_at=country.updated_at,
        required_items=required_items
    )

# 국가 코드로 국가 조회
@router.get("/countries/code/{country_code}", response_model=CountryWithItems)
async def get_country_by_code(country_code: str, db: Session = Depends(get_db)):
    """Get a country by code with required items"""
    from sqlalchemy import select
    from models.metadata import Country
    
    statement = select(Country).where(Country.code == country_code.upper())
    country = db.execute(statement).scalar_one_or_none()
    
    if not country:
        raise HTTPException(status_code=404, detail=f"Country with code {country_code} not found")
    
    # Get required items
    required_items = [
        RequiredItemRead(
            id=item.id,
            country_id=item.country_id,
            item=item.item,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in country.required_items
    ]
    
    return CountryWithItems(
        id=country.id,
        name=country.name,
        code=country.code,
        enabled=country.enabled,
        created_at=country.created_at,
        updated_at=country.updated_at,
        required_items=required_items
    )

# 토픽 목록 조회
@router.get("/topics", response_model=List[TopicRead])
async def get_topics(db: Session = Depends(get_db)):
    """Get all topics"""
    from sqlalchemy import select
    from models.metadata import Topic
    
    statement = select(Topic).where(Topic.enabled == True).order_by(Topic.name)
    topics = db.execute(statement).scalars().all()
    
    return [
        TopicRead(
            id=topic.id,
            name=topic.name,
            code=topic.code,
            enabled=topic.enabled,
            created_at=topic.created_at,
            updated_at=topic.updated_at
        )
        for topic in topics
    ]

# 토픽 ID로 토픽 조회
@router.get("/topics/{topic_id}", response_model=TopicRead)
async def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get a topic by ID"""
    from sqlalchemy import select
    from models.metadata import Topic
    
    statement = select(Topic).where(Topic.id == topic_id)
    topic = db.execute(statement).scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
    
    return TopicRead(
        id=topic.id,
        name=topic.name,
        code=topic.code,
        enabled=topic.enabled,
        created_at=topic.created_at,
        updated_at=topic.updated_at
    )

# 문서 소스 목록 조회
@router.get("/sources", response_model=List[SourceRead])
async def get_sources(db: Session = Depends(get_db)):
    """Get all document sources"""
    from sqlalchemy import select
    from models.metadata import Source
    
    statement = select(Source).order_by(Source.name)
    sources = db.execute(statement).scalars().all()
    
    return [
        SourceRead(
            id=source.id,
            name=source.name,
            url=source.url,
            source_type=source.source_type,
            created_at=source.created_at,
            updated_at=source.updated_at
        )
        for source in sources
    ]

# FAQ 목록 조회
@router.get("/faqs", response_model=List[FAQRead])
async def get_faqs(
    country_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get FAQs, optionally filtered by country and topic"""
    from sqlalchemy import select
    from models.metadata import FAQ
    
    query = select(FAQ)
    
    if country_id:
        query = query.where(FAQ.country_id == country_id)
    if topic_id:
        query = query.where(FAQ.topic_id == topic_id)
    
    # Limit results
    query = query.limit(limit)
    
    faqs = db.execute(query).scalars().all()
    
    return [
        FAQRead(
            id=faq.id,
            question=faq.question,
            answer=faq.answer,
            country_id=faq.country_id,
            topic_id=faq.topic_id,
            created_at=faq.created_at,
            updated_at=faq.updated_at
        )
        for faq in faqs
    ]

# 필수 항목 목록 조회
@router.get("/required-items", response_model=List[RequiredItemRead])
async def get_required_items(
    country_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get required items for a country"""
    from sqlalchemy import select
    from models.metadata import RequiredItem
    
    query = select(RequiredItem)
    
    if country_id:
        query = query.where(RequiredItem.country_id == country_id)
    
    items = db.execute(query).scalars().all()
    
    return [
        RequiredItemRead(
            id=item.id,
            country_id=item.country_id,
            item=item.item,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in items
    ]
