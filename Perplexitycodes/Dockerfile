# Adobe Hackathon 2025 - Optimized Docker Configuration
# High-performance, CPU-only PDF processing system

FROM --platform=linux/amd64 python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    libfontconfig1 \
    libfreetype6 \
    libxft2 \
    libx11-6 \
    libxcb1 \
    libxau6 \
    libxdmcp6 \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/input /app/output /app/challenge1b

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data (required for semantic analysis)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

# Copy application code
COPY . .

# Make main script executable
RUN chmod +x main.py

# Set Python path
ENV PYTHONPATH=/app

# Performance optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Use multiple CPU cores efficiently
ENV OPENBLAS_NUM_THREADS=8
ENV OMP_NUM_THREADS=8

# Default command (auto-detects challenge mode)
CMD ["python", "main.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Metadata
LABEL maintainer="Adobe Hackathon Team"
LABEL version="1.0"
LABEL description="High-performance PDF processing for Adobe Hackathon 2025"
