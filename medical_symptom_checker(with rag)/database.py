import chromadb
from sentence_transformers import SentenceTransformer

# Initialize ChromaDB client
db_client = chromadb.PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="documents")

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def add_documents(docs):
    embeddings = embedding_model.encode(docs).tolist()
    for i, doc in enumerate(docs):
        collection.add(ids=[str(i)], documents=[doc], embeddings=[embeddings[i]])

def retrieve_document(query):
    query_embedding = embedding_model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=1)
    return results["documents"][0][0] if results["documents"] else "No relevant document found."
