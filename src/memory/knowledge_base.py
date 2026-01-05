"""ChromaDB integration for agent memory."""
import os
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings


class KnowledgeBase:
    """Knowledge base using ChromaDB for persistent storage."""

    def __init__(self, collection_name: str = "research_memory", persist_directory: str = "./data/chroma"):
        """Initialize the knowledge base.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data
        """
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a document in the knowledge base.

        Args:
            content: The content to store
            metadata: Optional metadata dictionary

        Returns:
            Document ID
        """
        from datetime import datetime
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        meta = metadata or {}
        meta["timestamp"] = datetime.now().isoformat()

        self.collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[meta]
        )
        return doc_id

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base.

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of search results with content and metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        documents = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                item = {
                    "content": doc,
                    "metadata": (
                        results["metadatas"][0][i]
                        if results.get("metadatas") and results["metadatas"][0]
                        else {}
                    )
                }
                if results.get("distances") and results["distances"][0]:
                    item["distance"] = results["distances"][0][i]
                    item["relevance"] = 1 - results["distances"][0][i]
                documents.append(item)

        return documents

    def clear(self) -> int:
        """Clear all documents from the knowledge base.

        Returns:
            Number of documents cleared
        """
        all_data = self.collection.get()
        all_ids = all_data.get("ids", [])
        if all_ids:
            self.collection.delete(ids=all_ids)
        return len(all_ids)

