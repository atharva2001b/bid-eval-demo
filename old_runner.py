from rag_processor import process_queries
import os
import time
import sys
from pdf_processor import convert_pdf_to_text
from ollama_processor import OllamaProcessor


def get_demo_queries():
    """Returns a list of demo queries about AI."""
    return [
        "who is this contract from?",
        "what are the contact details of company?",
        "what are the clauses?",
        "overall summary"
    ]

def print_separator(char="-", length=80):
    """Print a separator line."""
    print(char * length)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
        
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    
    # Convert PDF to text
    text_file = convert_pdf_to_text(filename)
    print(text_file)
    
    # Get demo queries
    queries = get_demo_queries()
    print("\nDemo Queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    # Process queries and get answers
    print("\nInitializing RAG system and processing queries...")
    start_time = time.time()
    
    results = process_queries(text_file, queries)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Display results
    print(f"\nProcessing completed in {processing_time:.2f} seconds")
    print("\nResults:")
    print_separator("=")
    
    for i, (query, answer) in enumerate(zip(queries, results), 1):
        print(f"Query {i}: {query}")
        print("Answer:")
        print(answer)
        print_separator()

    # Initialize Ollama processor and generate bid evaluation
    print("\nGenerating bid evaluation report...")
    ollama = OllamaProcessor()
    evaluation_report = ollama.evaluate_bid(list(zip(queries, results)))
    
    # Display the evaluation report
    print("\nBid Evaluation Report:")
    print_separator("=")
    print(evaluation_report)
    return evaluation_report

if __name__ == "__main__":
    main()