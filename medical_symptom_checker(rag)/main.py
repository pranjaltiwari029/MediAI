# medical symptom checker 

import os
import faiss
import numpy as np
import pandas as pd
from flask import Flask, request, render_template, jsonify
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Load datasets
datasets = {
    "diabetes": pd.read_csv("diabetes.csv"),
    "thyroid": pd.read_csv("Thyroid_Diff.csv"),
    "typhoid": pd.read_csv("Typhoid.csv")
}

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text):
    return embedding_model.encode(text, convert_to_tensor=True).cpu().numpy()

# Create FAISS index for each dataset
indexes = {}
data_texts = {}

for disease, df in datasets.items():
    texts = df.astype(str).apply(lambda row: " | ".join(row), axis=1).tolist()
    embeddings = [embed_text(text) for text in texts]
    d = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(d)
    index.add(np.array(embeddings))
    
    indexes[disease] = index
    data_texts[disease] = texts

# Load local LLM
qa_pipeline = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.1")

def retrieve_and_generate_answer(query, disease):
    if disease not in indexes:
        return "Invalid disease selection."
    
    query_embedding = embed_text(query).reshape(1, -1)
    D, I = indexes[disease].search(query_embedding, k=3)
    retrieved_texts = "\n".join([data_texts[disease][i] for i in I[0]])
    
    prompt = f"Based on the following medical records, answer the question:\n{retrieved_texts}\n\nQuestion: {query}\nAnswer:"
    response = qa_pipeline(prompt, max_length=200)[0]['generated_text']
    return response

# Flask App Setup
app = Flask(__name__)


@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    disease = request.form['disease']  # User selects disease (diabetes, thyroid, or typhoid)
    answer = retrieve_and_generate_answer(query, disease)
    return jsonify({'answer': answer,'disclaimer': "This is an AI-generated response . Please consult a medical professional for confirmation."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
