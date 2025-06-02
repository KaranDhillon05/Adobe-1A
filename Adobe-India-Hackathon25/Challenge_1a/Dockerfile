# Adobe Hackathon 2025 - ML-Enhanced Challenge 1a Docker Configuration
# Hybrid AI + algorithmic PDF processing system

FROM --platform=linux/amd64 python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing and ML models
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libfontconfig1 \
    libfreetype6 \
    libxft2 \
    libx11-6 \
    libxcb1 \
    libxau6 \
    libxdmcp6 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/input /app/output

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY process_pdfs_trained.py .
COPY models/ ./models/

# Make script executable
RUN chmod +x process_pdfs_trained.py

# Set Python path
ENV PYTHONPATH=/app

# Performance optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Use multiple CPU cores efficiently
ENV OPENBLAS_NUM_THREADS=8
ENV OMP_NUM_THREADS=8

# ML model optimizations (CPU-only for container compatibility)
ENV PYTORCH_DISABLE_CUDA=1
ENV TRANSFORMERS_OFFLINE=0
ENV TOKENIZERS_PARALLELISM=false

# Default command
CMD ["python", "process_pdfs_trained.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Metadata
LABEL maintainer="Adobe Hackathon Team - Angry Nerds"
LABEL version="4.0"
LABEL description="Enhanced ML-Hybrid PDF processing for Adobe Hackathon 2025 Challenge 1a - Trained Models Version"
LABEL models="Fine-tuned BERT + Enhanced Semantic Models with Statistical Analysis"
LABEL approach="Advanced hybrid: Statistical (70%) + Semantic (20%) + Fine-tuned BERT (10%)" 