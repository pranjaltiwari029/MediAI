from sentence_transformers import SentenceTransformer

def get_embedding(text):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(text).tolist()
