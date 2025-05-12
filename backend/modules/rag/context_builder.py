"""
사용자 질문에 대해 벡터 검색을 통해 관련 문서들을 불러와 LLM에 입력할 context 문자열을 구성
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import tiktoken

from config import settings
from modules.vector_db.db import VectorStore

logger = logging.getLogger(__name__)

class ContextBuilder:
    """Builds context for LLM from retrieved documents"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize the context builder
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store or VectorStore()
        
        # Initialize tokenizer for token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # For OpenAI models
    
    def build_context(
        self, 
        query: str, 
        country: Optional[str] = None, 
        topic: Optional[str] = None,
        max_tokens: int = 3000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build context for a query
        
        Args:
            query: User query
            country: Optional country filter
            topic: Optional topic filter
            max_tokens: Maximum tokens for context
            
        Returns:
            Tuple of (context string, reference info list)
        """
        # Prepare filter for vector search
        filter_dict = {}
        if country:
            filter_dict["country"] = country
        if topic:
            filter_dict["topic"] = topic
        
        # Perform hybrid search
        search_results = self.vector_store.hybrid_search(
            query=query,
            filter_dict=filter_dict,
            k=settings.TOP_K_RESULTS
        )
        
        # Build context within token limit
        context_parts = []
        used_tokens = 0
        references = []
        
        for result in search_results:
            content = result["content"]
            metadata = result["metadata"]
            
            # Count tokens in this chunk
            tokens = len(self.tokenizer.encode(content))
            
            # Check if adding this would exceed the limit
            if used_tokens + tokens <= max_tokens:
                context_parts.append(content)
                used_tokens += tokens
                
                # Add to references (for citation)
                ref_info = {
                    "chunk_id": result["id"],
                    "document_id": metadata.get("document_id"),
                    "title": metadata.get("title", "Untitled Document"),
                    "source": metadata.get("source", "Unknown Source"),
                    "url": metadata.get("url", ""),
                    "source_type": metadata.get("source_type", "DOCUMENT")
                }
                references.append(ref_info)
            else:
                # If we've already got at least 2 chunks, stop
                if len(context_parts) >= 2:
                    break
                
                # Otherwise try to fit a truncated version of this chunk
                truncated_content = self._truncate_to_fit(
                    content, max_tokens - used_tokens
                )
                context_parts.append(truncated_content)
                used_tokens += len(self.tokenizer.encode(truncated_content))
                
                # Add truncated reference
                ref_info = {
                    "chunk_id": result["id"],
                    "document_id": metadata.get("document_id"),
                    "title": metadata.get("title", "Untitled Document"),
                    "source": metadata.get("source", "Unknown Source"),
                    "url": metadata.get("url", ""),
                    "source_type": metadata.get("source_type", "DOCUMENT"),
                    "truncated": True
                }
                references.append(ref_info)
                break
        
        # Join context parts with separators
        context = "\n\n---\n\n".join(context_parts)
        
        # If no context found, provide a message
        if not context:
            context = "No relevant information found."
        
        logger.info(f"Built context with {used_tokens} tokens from {len(references)} chunks")
        return context, references
    
    def _truncate_to_fit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated text
        """
        # If already fits, return as is
        current_tokens = len(self.tokenizer.encode(text))
        if current_tokens <= max_tokens:
            return text
        
        # Split into sentences
        sentences = text.split(". ")
        result = []
        current_len = 0
        
        for sentence in sentences:
            sentence_len = len(self.tokenizer.encode(sentence + ". "))
            
            if current_len + sentence_len <= max_tokens:
                result.append(sentence)
                current_len += sentence_len
            else:
                break
        
        # Join sentences back together
        truncated_text = ". ".join(result)
        if not truncated_text.endswith("."):
            truncated_text += "."
        
        return truncated_text