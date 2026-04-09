# Use lightweight Python base image
FROM python:3.10-slim

# Install system packages including Tesseract OCR
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libportaudio2 \
    gcc \
    libc-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy entire project into container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Start the MediAI  backend
CMD ["python", "UI.py"]
