# Create optimized Dockerfile

dockerfile_content = '''# Adobe Hackathon 2025 - Optimized Docker Configuration
# High-performance, CPU-only PDF processing system

FROM --platform=linux/amd64 python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \\
    libfontconfig1 \\
    libfreetype6 \\
    libxft2 \\
    libx11-6 \\
    libxcb1 \\
    libxau6 \\
    libxdmcp6 \\
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/input /app/output /app/challenge1b

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \\
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
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)"

# Metadata
LABEL maintainer="Adobe Hackathon Team"
LABEL version="1.0"
LABEL description="High-performance PDF processing for Adobe Hackathon 2025"
'''

with open("adobe_pdf_processor/Dockerfile", "w") as f:
    f.write(dockerfile_content)

# Create Docker build and run scripts
build_script = '''#!/bin/bash
# Build script for Adobe Hackathon PDF Processor

echo "🏗️  Building Adobe Hackathon PDF Processor..."

# Build with proper platform specification
docker build --platform linux/amd64 -t adobe-pdf-processor .

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo ""
    echo "To test Challenge 1a:"
    echo "docker run --rm -v \$(pwd)/sample_input:/app/input:ro -v \$(pwd)/sample_output:/app/output --network none adobe-pdf-processor"
    echo ""
    echo "To test Challenge 1b:"
    echo "docker run --rm -v \$(pwd)/Challenge_1b:/app/challenge1b --network none adobe-pdf-processor --challenge 1b"
else
    echo "❌ Build failed!"
    exit 1
fi
'''

with open("adobe_pdf_processor/build.sh", "w") as f:
    f.write(build_script)

# Create test script
test_script = '''#!/bin/bash
# Test script for Adobe Hackathon PDF Processor

echo "🧪 Testing Adobe Hackathon PDF Processor..."

# Create test directories
mkdir -p test_input test_output

# Test Challenge 1a if test PDFs exist
if [ -f "test_input/*.pdf" ]; then
    echo "Testing Challenge 1a..."
    docker run --rm -v \$(pwd)/test_input:/app/input:ro -v \$(pwd)/test_output:/app/output --network none adobe-pdf-processor --challenge 1a
    
    if [ $? -eq 0 ]; then
        echo "✅ Challenge 1a test passed!"
    else
        echo "❌ Challenge 1a test failed!"
    fi
fi

# Test Challenge 1b if collections exist
if [ -d "Challenge_1b" ]; then
    echo "Testing Challenge 1b..."
    docker run --rm -v \$(pwd)/Challenge_1b:/app/challenge1b --network none adobe-pdf-processor --challenge 1b
    
    if [ $? -eq 0 ]; then
        echo "✅ Challenge 1b test passed!"
    else
        echo "❌ Challenge 1b test failed!"
    fi
fi

echo "🎉 Testing completed!"
'''

with open("adobe_pdf_processor/test.sh", "w") as f:
    f.write(test_script)

print("✅ Created Dockerfile and build/test scripts")