#!/bin/bash
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
