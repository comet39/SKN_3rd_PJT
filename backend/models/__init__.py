"""
Model initialization
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

# Create SQLAlchemy engine and session factory
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# This will hold all models to avoid circular imports
_models_initialized = False
_models = {}

def init_models():
    """Initialize all models to ensure they're registered with SQLAlchemy"""
    global _models_initialized, _models
    
    if _models_initialized:
        return _models
    
    # Import models here to avoid circular imports
    from .metadata import Country, Topic, Source, RequiredItem, FAQ
    from .document import Document
    
    # Store models in a dictionary
    _models.update({
        'Country': Country,
        'Topic': Topic,
        'Source': Source,
        'RequiredItem': RequiredItem,
        'FAQ': FAQ,
        'Document': Document
    })
    
    _models_initialized = True
    return _models

# Initialize models when this module is imported
models = init_models()

# Make models available at package level
Base = Base
SessionLocal = SessionLocal

# Add all models to __all__
__all__ = ['Base', 'SessionLocal', 'get_db'] + list(models.keys())

# Dependency to get DB session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()