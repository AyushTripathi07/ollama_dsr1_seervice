# Use an official Python runtime as the base image
FROM python:3.10-slim

# Set environment variables
ENV OLLAMA_MODEL=deepseek-r1:1.5b

# Install required dependencies
RUN apt-get update && apt-get install -y \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Install pip dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy the application files
WORKDIR /app
COPY . /app

# Expose the necessary ports
EXPOSE 5000 11434

# Start Ollama server in the background and ensure it stays running
CMD (ollama serve &) && \
    sleep 5 && \
    ollama pull $OLLAMA_MODEL && \
    gunicorn --bind 0.0.0.0:5000 app:app