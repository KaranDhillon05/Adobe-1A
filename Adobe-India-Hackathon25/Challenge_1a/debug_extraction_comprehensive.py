#!/usr/bin/env python3
"""
Comprehensive debug script to identify PDF processing issues
"""

import fitz
import sys
from pathlib import Path
from collections import defaultdict, Counter
from process_pdfs import PDFProcessor, TextSpan
import json

def debug_pdf_extraction(pdf_path):
    """Debug PDF extraction comprehensively"""
    print(f"\n{'='*60}")
    print(f"DEBUGGING: {pdf_path}")
    print(f"{'='*60}")
    
    doc = fitz.open(pdf_path)
    print(f"📄 Total pages: {len(doc)}")
    
    processor = PDFProcessor()
    
    # 1. Test basic text extraction
    all_text_spans = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n--- PAGE {page_num + 1} ---")
        
        # Extract spans for this page
        page_spans = processor._extract_clean_text_spans(page, page_num)
        print(f"Spans extracted from page {page_num + 1}: {len(page_spans)}")
        
        # Show first few spans
        for i, span in enumerate(page_spans[:10]):
            print(f"  {i+1}. '{span.text}' (size: {span.font_size}, bold: {span.is_bold})")
        
        all_text_spans.extend(page_spans)
    
    doc.close()
    
    print(f"\n📊 TOTAL SPANS EXTRACTED: {len(all_text_spans)}")
    
    # 2. Test font analysis
    font_stats = processor.analyze_font_statistics(all_text_spans)
    print(f"\n🔤 FONT ANALYSIS:")
    print(f"  Body font size: {font_stats['body_font_size']}")
    print(f"  Heading threshold: {font_stats['heading_threshold']}")
    print(f"  Font size histogram: {dict(list(font_stats['font_size_histogram'].items())[:10])}")
    
    # 3. Test heading detection
    potential_headings = []
    for span in all_text_spans:
        text = span.text.strip()
        if (span.font_size >= font_stats["heading_threshold"] or
            (span.is_bold and span.font_size >= font_stats["body_font_size"] * 0.9) or
            processor._looks_like_heading_content(text)):
            potential_headings.append(span)
    
    print(f"\n📋 POTENTIAL HEADINGS: {len(potential_headings)}")
    
    for i, span in enumerate(potential_headings[:20]):  # Show first 20
        score = processor.score_heading_candidate(span, font_stats, 800)
        level = processor.classify_heading_level(score, span, font_stats)
        print(f"  {i+1}. Page {span.page_num+1}: '{span.text}' (score: {score:.3f}, level: {level})")
        print(f"      Font: {span.font_size}, Bold: {span.is_bold}, Size ratio: {span.font_size/font_stats['body_font_size']:.2f}")
    
    # 4. Show the final result
    result = processor.process_pdf(pdf_path)
    print(f"\n📝 FINAL RESULT:")
    print(f"  Title: {result['title']}")
    print(f"  Headings found: {len(result['outline'])}")
    for heading in result['outline']:
        print(f"    {heading['level']}: {heading['text']} (page {heading['page']})")

def main():
    """Test specific problematic files"""
    test_files = [
        "input/file02.pdf",  # 12 pages, only 2 headings found
        "input/pdftest1.pdf",  # 25 pages, only 16 headings found
    ]
    
    for pdf_file in test_files:
        if Path(pdf_file).exists():
            debug_pdf_extraction(pdf_file)
        else:
            print(f"File not found: {pdf_file}")

if __name__ == "__main__":
    main()