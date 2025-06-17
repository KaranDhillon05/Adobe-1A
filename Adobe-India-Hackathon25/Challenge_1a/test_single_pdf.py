#!/usr/bin/env python3
"""
Single PDF Test Script for Adobe Hackathon Solution
Usage: python3 test_single_pdf.py path/to/your/file.pdf
"""

import sys
import json
from pathlib import Path
from process_pdfs import PDFProcessor
import time

def test_single_pdf(pdf_path):
    """Test a single PDF file"""
    if not Path(pdf_path).exists():
        print(f"Error: File {pdf_path} not found!")
        return
    
    print(f"Testing PDF: {pdf_path}")
    print("-" * 50)
    
    # Initialize processor
    processor = PDFProcessor()
    
    # Process PDF
    start_time = time.time()
    try:
        result = processor.process_pdf(str(pdf_path))
        processing_time = time.time() - start_time
        
        # Display results
        print(f"✅ Processing completed in {processing_time:.3f} seconds")
        print(f"📄 Title: {result['title']}")
        print(f"📋 Found {len(result['outline'])} headings")
        print()
        
        # Show outline
        print("Document Outline:")
        print("=" * 50)
        for i, heading in enumerate(result['outline'], 1):
            level = heading['level']
            text = heading['text']
            page = heading['page']
            indent = "  " * (int(level[1]) - 1) if level.startswith('H') else ""
            print(f"{indent}{level}: {text} (page {page})")
        
        print()
        print("JSON Output:")
        print("=" * 50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Save output
        output_file = Path(pdf_path).stem + "_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_single_pdf.py path/to/your/file.pdf")
        print("Example: python3 test_single_pdf.py input/file01.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_single_pdf(pdf_path)