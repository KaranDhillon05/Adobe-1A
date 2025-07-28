#!/bin/bash
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
