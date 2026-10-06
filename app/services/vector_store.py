import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from app.config import settings
from chromadb.config import Settings

# Disable telemetry before initializing Chroma (works around posthog incompatibility)
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

# Initialize the embedding model (runs locally)
# This will download the model on first run
print("Loading embedding model...")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "legal_docs"   # <-- FIX: defined the missing constant
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(
    path=settings.VECTORSTORE_DIR,
    settings=Settings(anonymized_telemetry=False)  # <-- Add this
)


def get_or_create_collection():
    """Get existing collection or create a new one."""
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )


def embed_and_store_chunks(chunks_file_path: str):
    """Reads chunks.jsonl, generates embeddings, and stores in ChromaDB."""
    if not os.path.exists(chunks_file_path):
        raise FileNotFoundError(f"Chunks file not found: {chunks_file_path}")

    collection = get_or_create_collection()

    # Clear existing data to avoid duplicates if re-running
    existing_count = collection.count()
    if existing_count > 0:
        print(f"Collection already has {existing_count} items. Deleting existing collection to re-index...")
        chroma_client.delete_collection(COLLECTION_NAME)
        collection = get_or_create_collection()

    chunks = []
    with open(chunks_file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    print(f"Loaded {len(chunks)} chunks. Generating embeddings...")

    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        documents.append(chunk["text"])
        metadatas.append({
            "source": chunk.get("source", "unknown"),
            "section": chunk.get("section", "unknown"),
            "heading": chunk.get("heading", "unknown"),
            "doc_type": chunk.get("doc_type", "statute"),
            "jurisdiction": chunk.get("jurisdiction", "unknown"),
            "effective_date": chunk.get("effective_date", "unknown"),
        })
        ids.append(f"{chunk.get('source', 'doc')}_{i}")

    # Generate embeddings
    embeddings = embedding_model.encode(documents).tolist()

    # Add to ChromaDB
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Successfully stored {len(documents)} chunks in ChromaDB at {settings.VECTORSTORE_DIR}")
    return collection