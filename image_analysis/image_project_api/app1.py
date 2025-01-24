from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import hashlib
from image_db import init_db, add_image_description, get_all_images, get_image_description
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the processor and model for BLIP-2
processor = Blip2Processor.from_pretrained("Salesforce/blip2-flan-t5-xxl")
model = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-flan-t5-xxl")

# Define additional prompts for more detailed image analysis
prompts = [
    "Describe the overall setting of the image.",
    "What objects are present in the image?",
    "Describe any activities happening in the image.",
    "What emotions or moods are depicted?",
]

@app.route('/uploads', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image'}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Generate a hash for image deduplication
    image_hash = hashlib.md5(image.read()).hexdigest()
    image.seek(0)  # Reset file pointer to the beginning

    # Check if the image has already been analyzed
    existing_description = get_image_description(image_hash)
    if existing_description:
        return jsonify({'description': existing_description}), 200

    # Save the image
    image.save(file_path)

    # Perform detailed analysis with BLIP-2 model
    img = Image.open(file_path)

    detailed_description = {}
    for prompt in prompts:
        # Prepare the inputs for the model
        inputs = processor(images=img, text=prompt, return_tensors="pt")

        # Generate the answer using BLIP-2
        outputs = model.generate(**inputs)
        
        # Decode the output and store it
        description = processor.decode(outputs[0], skip_special_tokens=True)
        detailed_description[prompt] = description

    # Combine the detailed description into one text for storing
    combined_description = "\n".join([f"{prompt}: {desc}" for prompt, desc in detailed_description.items()])

    # Save description to the database
    add_image_description(image_hash, file_path, combined_description)

    return jsonify({'description': detailed_description}), 200

@app.route('/images', methods=['GET'])
def get_images():
    images = get_all_images()
    return jsonify(images), 200

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
