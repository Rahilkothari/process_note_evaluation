import os
import chromadb
from chromadb.config import Settings
import json

class RAGService:
    def __init__(self):
        # Store ChromaDB persistently in the workspace
        db_path = os.path.join(os.getcwd(), "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # We will use a default collection for process notes
        self.collection = self.client.get_or_create_collection(
            name="process_notes_collection",
            metadata={"hnsw:space": "cosine"}
        )

    def ingest_section(self, note_id: int, team: str, section_id: str, content: str):
        """
        Ingest a single section into the vector database.
        Includes team metadata for strict partitioning.
        """
        if not content or not content.strip():
            return
            
        doc_id = f"note_{note_id}_sec_{section_id}"
        
        self.collection.upsert(
            documents=[content],
            metadatas=[{
                "team": team,
                "section_id": section_id,
                "note_id": note_id
            }],
            ids=[doc_id]
        )

    def get_team_context(self, team: str, section_id: str, query: str = "", limit: int = 2) -> list[str]:
        """
        Retrieve historical context for a specific section, STRICTLY filtered by team.
        """
        if not query:
            # If no query is provided, we can just fetch the most recent ones 
            # by doing a generic search or using a placeholder query.
            query = f"Process documentation for {section_id}"
            
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where={
                "$and": [
                    {"team": team},
                    {"section_id": section_id}
                ]
            }
        )
        
        # Extract documents from the results
        if results and results.get("documents") and len(results["documents"]) > 0:
            return results["documents"][0]
        
        return []

# Singleton instance
rag_service = RAGService()
