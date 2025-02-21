from transformers import pipeline

def generate_answer(query, retrieved_text):
    generator = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct", device_map="auto")
    prompt = f"Use the following information to answer the question:\n\n{retrieved_text}\n\nQuestion: {query}\nAnswer:"
    response = generator(prompt, max_length=150, do_sample=True)
    return response[0]['generated_text']
