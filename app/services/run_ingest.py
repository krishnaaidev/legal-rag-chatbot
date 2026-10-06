from app.services.ingest import process_all_documents


if __name__ == "__main__":
    chunks = process_all_documents()

    if chunks:
        print("\n--- CHUNK PREVIEW (first 3) ---")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n[Chunk {i+1}]")
            print(f"Source:    {chunk['source']}")
            print(f"Section:   {chunk['section']}")
            print(f"Jurisdiction: {chunk.get('jurisdiction')}")
            print(f"Effective:    {chunk.get('effective_date')}")
            print(f"Heading:   {chunk['heading'][:80]}")
            print(f"Preview:   {chunk['text'][:150]}...")