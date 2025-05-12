# helpers.py - Auto-generated
"""
Helper functions for the application
"""
import os
import re
import uuid
from typing import Dict, Any, List, Optional, Union

def generate_unique_id() -> str:
    """Generate a unique ID for documents, chunks, etc."""
    return str(uuid.uuid4())

def normalize_language_code(language_code: str) -> str:
    """Normalize language code to standard format (e.g., 'en-US' -> 'en')"""
    # Just take the first part for simplicity (e.g., 'en-US' -> 'en')
    normalized = language_code.split('-')[0].lower()
    return normalized

def detect_language(text: str) -> str:
    """Detect language of the given text"""
    try:
        # Use langdetect if available
        from langdetect import detect
        return detect(text)
    except ImportError:
        # Fallback to basic heuristic (Korean vs English vs Others)
        # Check for Korean characters (Hangul)
        if re.search(r'[\uac00-\ud7a3]', text):
            return 'ko'
        # Assume English if mostly ASCII
        if re.search(r'^[a-zA-Z0-9\s\.,;:!\?"\'()\[\]\-_]+$', text):
            return 'en'
        # Default
        return 'en'
    except Exception:
        # Default to English if detection fails
        return 'en'
