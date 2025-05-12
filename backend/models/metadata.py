"""
Metadata models for the application
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship

from . import Base

class Country(Base):
    """Country model"""
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), unique=True, index=True)
    flag_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships will be set up after all models are defined
    required_items = relationship("RequiredItem", back_populates="country", cascade="all, delete-orphan")
    faqs = relationship("FAQ", back_populates="country")
    documents = relationship("Document", back_populates="country")

class Topic(Base):
    """Topic model for categorizing FAQs"""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships will be set up after all models are defined
    faqs = relationship("FAQ", back_populates="topic")
    documents = relationship("Document", back_populates="topic")

class Source(Base):
    """Source model for document sources"""
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=True)
    source_type = Column(String(50), nullable=False)  # e.g., GOVERNMENT, EMBASSY, etc.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships will be set up after all models are defined
    documents = relationship("Document", back_populates="source")

class RequiredItem(Base):
    """Required items for each country"""
    __tablename__ = "required_items"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    item = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # e.g., DOCUMENTS, VISA, etc.
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships will be set up after all models are defined
    country = relationship("Country", back_populates="required_items")

class FAQ(Base):
    """Frequently Asked Questions"""
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships will be set up after all models are defined
    country = relationship("Country", back_populates="faqs")
    topic = relationship("Topic", back_populates="faqs")

# Set up relationships after all models are defined
# 관계 설정 (중복 제거)
def setup_relationships():
    """Set up all relationships between models"""
    Country.required_items = relationship("RequiredItem", back_populates="country", cascade="all, delete-orphan")
    Country.faqs = relationship("FAQ", back_populates="country")
    Country.documents = relationship("Document", back_populates="country")

    Topic.faqs = relationship("FAQ", back_populates="topic")
    Topic.documents = relationship("Document", back_populates="topic")

    Source.documents = relationship("Document", back_populates="source")

    RequiredItem.country = relationship("Country", back_populates="required_items")

    FAQ.country = relationship("Country", back_populates="faqs")
    FAQ.topic = relationship("Topic", back_populates="faqs")

# 관계 설정 실행
setup_relationships()