import pandas as pd
import difflib
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import openai

# Load pre-trained model for embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

# Sample diabetes symptoms dataset
DATA = {
    "Symptom": [
        "Frequent urination", "Excessive thirst", "Unexplained weight loss",
        "Fatigue", "Blurred vision", "Slow healing wounds", "Tingling in hands/feet"
    ],
    "Diabetes Type": [
        "Type 1, Type 2, Gestational", "Type 1, Type 2", "Type 1",
        "Type 1, Type 2", "Type 1, Type 2, Gestational", "Type 2", "Type 2"
    ]
}

# Convert to DataFrame
diabetes_df = pd.DataFrame(DATA)

# Convert symptoms to embeddings
symptom_embeddings = model.encode(diabetes_df['Symptom'].tolist(), convert_to_numpy=True)

# Create FAISS index for vector similarity search
index = faiss.IndexFlatL2(symptom_embeddings.shape[1])
index.add(symptom_embeddings)

def retrieve_similar_symptoms(user_symptoms):
    """Retrieve closest symptoms from FAISS index."""
    user_embeddings = model.encode(user_symptoms, convert_to_numpy=True)
    _, indices = index.search(user_embeddings, k=3)  # Retrieve top 3 matches
    matched_symptoms = [diabetes_df.iloc[idx]['Symptom'] for idx in indices[0] if idx < len(diabetes_df)]
    return matched_symptoms

def generate_response(symptoms, diabetes_types):
    """Generate a response using GPT based on retrieved symptoms."""
    prompt = f"The user is experiencing {', '.join(symptoms)}. What types of diabetes might be associated with these symptoms?"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a medical assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

def check_diabetes():
    """Main function to get user input and suggest possible diabetes types using RAG."""
    print("Diabetes Symptom Checker (Not a substitute for professional advice)")
    user_input = input("Enter symptoms separated by commas: ")
    user_symptoms = [s.strip() for s in user_input.split(',')]
    
    matched_symptoms = retrieve_similar_symptoms(user_symptoms)
    possible_types = set()
    for symptom in matched_symptoms:
        types = diabetes_df[diabetes_df['Symptom'] == symptom]['Diabetes Type'].unique()
        for t in types:
            possible_types.update(t.split(", "))
    
    if possible_types:
        print("\nPossible diabetes type(s) based on symptoms:")
        for diabetes_type in possible_types:
            print(f"- {diabetes_type}")
        
        # Generate AI-based response
        gpt_response = generate_response(matched_symptoms, possible_types)
        print("\nAI-Generated Response:")
        print(gpt_response)
    else:
        print("No matching diabetes type found. Please consult a doctor.")
    
    print("\nDisclaimer: This tool is for informational purposes only. Consult a healthcare provider for medical advice.")

if __name__ == "__main__":
    check_diabetes()
