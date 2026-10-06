from app.services.vector_store import get_or_create_collection, embedding_model
from typing import List, Dict, Any

def retrieve_relevant_chunks(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Embeds the query and retrieves the top_k most similar chunks."""
    collection = get_or_create_collection()
    
    if collection.count() == 0:
        return [{"error": "Vector store is empty. Please run the ingestion first."}]

    # Embed the query
    query_embedding = embedding_model.encode([query]).tolist()

    # Query ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # Format results
    retrieved_chunks = []
    for i in range(len(results["documents"][0])):
        retrieved_chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return retrieved_chunks