from database import add_documents, retrieve_document
from rag import generate_answer

def main():
    # Sample documents to add to the vector database
    documents = [
        "ChromaDB is an open-source vector database for AI applications.",
        "Sentence-transformers allow you to convert text into embeddings.",
        "Retrieval-Augmented Generation (RAG) combines search with language models."
    ]
    
    # Add documents to the database
    add_documents(documents)
    
    # Query the system
    query = "How does RAG work?"
    retrieved_text = retrieve_document(query)
    
    # Generate the final response using a local LLM
    answer = generate_answer(query, retrieved_text)
    print("\nFinal Answer:", answer)

if __name__ == "__main__":
    main()
