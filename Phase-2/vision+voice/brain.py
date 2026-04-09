# step 1:setup groq api key |  
import os
# GROQ_API_KEY=os.environ.get("GROQ_API_KEY")

# step 2: convert image to requiredformat
import base64

# image_path="images/acne.jpg"
def encode_image(image_path): 
    image_file=open(image_path,"rb")
    return base64.b64encode(image_file.read()).decode('utf-8')

# \ step 3 : setup Multimodal LLM
from groq import Groq
# if not GROQ_API_KEY:
#     raise ValueError("GROQ_API_KEY is not set. Please provide your API key.")

# query="Is there something wrong with my face?"
# model="llama-3.2-90b-vision-preview"
def analyze_image_with_query(query,model,encoded_image):
    
    client=Groq(api_key=GROQ_API_KEY)

    messages=[
        {
            "role":"user",
            "content":[
                {
                "type":"text",
                "text":query
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":f"data:image/jpeg;base64,{encoded_image}",
                    },
                },
            ],
        }]
    chat_completion=client.chat.completions.create(
        messages=messages,
        model=model
    )
    return chat_completion.choices[0].message.content