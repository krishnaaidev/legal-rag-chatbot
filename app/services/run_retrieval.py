from app.services.retriever import retrieve_relevant_chunks

if __name__ == "__main__":
    test_queries = [
        "What is the penalty for an offence?",
        "What does the Act say about the Court?",
        "Who has the power to make rules?"
    ]

    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"QUERY: {query}")
        print(f"{'='*50}")
        
        results = retrieve_relevant_chunks(query, top_k=2)
        
        for i, res in enumerate(results):
            if "error" in res:
                print(res["error"])
                break
                
            print(f"\n--- Result {i+1} (Distance: {res['distance']:.4f}) ---")
            print(f"Source: {res['metadata']['source']}")
            print(f"Section: {res['metadata']['section']}")
            print(f"Heading: {res['metadata']['heading']}")
            print(f"Text snippet: {res['text'][:150]}...")