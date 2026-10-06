from app.services.generator import generate_legal_answer

if __name__ == "__main__":
    test_queries = [
        "What is the penalty for an offence?",
        "Can a public servant be punished for acting in good faith?",
        "What is the capital of France?" # Out of scope query to test hallucination guard
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"QUESTION: {query}")
        print(f"{'='*60}")
        
        result = generate_legal_answer(query)
        
        print(f"\nANSWER:\n{result['answer']}")
        
        if result['sources']:
            print("\nSOURCES CITED:")
            for s in result['sources']:
                print(f"- {s['source']}, Section {s['section']} (Distance: {s['distance']})")