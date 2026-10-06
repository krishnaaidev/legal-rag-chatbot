import os
from app.services.vector_store import embed_and_store_chunks
from app.config import settings

if __name__ == "__main__":
    chunks_file = os.path.join(settings.PROCESSED_DATA_DIR, "chunks.jsonl")
    print(f"Building vector store from {chunks_file}...")
    
    embed_and_store_chunks(chunks_file)
    
    print("\nVector store build complete!")