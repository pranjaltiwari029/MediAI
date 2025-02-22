# checking for diabetes with rag
import os
import faiss
import numpy as np
import pandas as pd
from flask import Flask, request, render_template, jsonify
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Load the diabetes dataset
df = pd.read_csv("diabetes.csv")

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text):
    return embedding_model.encode(text, convert_to_tensor=True).cpu().numpy()

# Convert dataset rows into knowledge base
data_texts = df.astype(str).apply(lambda row: " | ".join(row), axis=1).tolist()
embeddings = [embed_text(text) for text in data_texts]

# Build FAISS index
d = embeddings[0].shape[0]
index = faiss.IndexFlatL2(d)
index.add(np.array(embeddings))

# Load local LLM
qa_pipeline = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.1")

def retrieve_and_generate_answer(query):
    query_embedding = embed_text(query).reshape(1, -1)
    D, I = index.search(query_embedding, k=3)  
    retrieved_texts = "\n".join([data_texts[i] for i in I[0]])
    
    prompt = f"Based on the following medical records, answer the question:\n{retrieved_texts}\n\nQuestion: {query}\nAnswer:"
    response = qa_pipeline(prompt, max_length=200)[0]['generated_text']
    return response

# Flask App Setup
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    answer = retrieve_and_generate_answer(query)
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
