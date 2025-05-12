# db.py - Auto-generated
"""
Vector database interface using ChromaDB
"""
import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions

from config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector database for document embeddings using ChromaDB"""
    
    def __init__(self, collection_name: str = "documents"):
        """Initialize the vector store with ChromaDB"""
        self.collection_name = collection_name
        self.db_path = settings.VECTOR_DB_PATH
        
        # Ensure directory exists
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Setup OpenAI embeddings
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.EMBEDDING_MODEL
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Connected to existing collection: {collection_name}")
        except Exception as e:
            logger.info(f"Creating new collection: {collection_name}")
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
    
    def add_texts(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]], 
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add texts and their metadata to the vector store
        
        Args:
            texts: List of text chunks to embed
            metadatas: List of metadata for each text chunk
            ids: Optional list of IDs for each chunk, generated if not provided
        
        Returns:
            List of IDs for the added chunks
        """
        if ids is None:
            # Generate UUIDs for each chunk
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Add to collection
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(texts)} documents to collection {self.collection_name}")
        return ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector store
        
        Args:
            query: Query text
            k: Number of results to return
            filter_dict: Optional dictionary for filtering results
        
        Returns:
            List of dictionaries with text, metadata, and score
        """
        # Convert query to embedding using the OpenAI model
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filter_dict
        )
        
        # Format results
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        result_list = []
        for i in range(len(documents)):
            result_list.append({
                "content": documents[i],
                "metadata": metadatas[i],
                "score": 1.0 - distances[i],  # Convert distance to similarity score
                "id": ids[i]
            })
        
        return result_list
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete documents by IDs
        
        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from collection {self.collection_name}")
    
    def update(
        self, 
        ids: List[str], 
        texts: List[str], 
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        Update documents by IDs
        
        Args:
            ids: List of document IDs to update
            texts: New text content
            metadatas: New metadata
        """
        # Delete and re-add, as ChromaDB update is equivalent to delete + add
        self.delete(ids)
        self.add_texts(texts, metadatas, ids)
        logger.info(f"Updated {len(ids)} documents in collection {self.collection_name}")
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID
        
        Args:
            id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            result = self.collection.get(ids=[id])
            
            if not result["documents"]:
                return None
            
            return {
                "content": result["documents"][0],
                "metadata": result["metadatas"][0],
                "id": id
            }
        except Exception as e:
            logger.error(f"Error getting document by ID {id}: {e}")
            return None
    
    def get_by_metadata(
        self, 
        metadata_filter: Dict[str, Any], 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get documents by metadata filter
        
        Args:
            metadata_filter: Filter criteria
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        try:
            results = self.collection.get(
                where=metadata_filter,
                limit=limit
            )
            
            documents = []
            for i in range(len(results["documents"])):
                documents.append({
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "id": results["ids"][i]
                })
            
            return documents
        except Exception as e:
            logger.error(f"Error getting documents by metadata: {e}")
            return []
    
    def hybrid_search(
        self, 
        query: str, 
        filter_dict: Optional[Dict[str, Any]] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (combination of vector and keyword)
        
        Args:
            query: Query text
            filter_dict: Optional dictionary for filtering results
            k: Number of results to return
            
        Returns:
            List of search results
        """
        # Currently, ChromaDB doesn't have built-in hybrid search,
        # so we perform vector search and then re-rank based on keyword matching
        
        # Get more results than needed for re-ranking
        vector_results = self.similarity_search(query, k=k*2, filter_dict=filter_dict)
        
        # Simple re-ranking by keyword matching score
        keywords = query.lower().split()
        for result in vector_results:
            content = result["content"].lower()
            
            # Calculate keyword match score
            keyword_score = 0
            for keyword in keywords:
                if keyword in content:
                    keyword_score += 1
            
            # Normalize keyword score
            if keywords:
                keyword_score /= len(keywords)
            
            # Combine scores (weighted average)
            vector_score = result["score"]
            combined_score = (vector_score * 0.7) + (keyword_score * 0.3)
            
            result["score"] = combined_score
        
        # Sort by combined score and limit to k results
        vector_results.sort(key=lambda x: x["score"], reverse=True)
        return vector_results[:k]