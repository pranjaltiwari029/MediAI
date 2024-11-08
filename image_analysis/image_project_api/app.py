from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import hashlib
from image_db import init_db, add_image_description, get_all_images, get_image_description
from transformers import pipeline
from PIL import Image

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

image_to_text = pipeline("image-to-text", model="Salesforce/blip-image-captioning-large")

@app.route('/uploads', methods=['POST'])
def upload_image():
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image'}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    image_hash = hashlib.md5(image.read()).hexdigest()
    image.seek(0)  # Reset file pointer to the beginning

    
    existing_description = get_image_description(image_hash)
    if existing_description:
        return jsonify({'description': existing_description}), 200

    
    image.save(file_path)

    
    img = Image.open(file_path)
    description = image_to_text(img)[0]['generated_text']

    
    add_image_description(image_hash, file_path, description)

    return jsonify({'description': description}), 200

@app.route('/images', methods=['GET'])
def get_images():
    
    images = get_all_images()
    return jsonify(images), 200

if __name__ == '__main__':
    
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)

