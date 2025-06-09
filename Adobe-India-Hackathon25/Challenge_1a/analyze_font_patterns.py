#!/usr/bin/env python3
"""
Analyze font patterns in the PDF to understand the document structure
"""

import os
import fitz  # PyMuPDF
from process_pdfs import PDFProcessor
from collections import Counter

def analyze_font_patterns(pdf_path: str):
    """Analyze all font patterns in the PDF"""
    
    processor = PDFProcessor()
    spans = processor.extract_text_spans(pdf_path)
    
    print(f"=== FONT PATTERN ANALYSIS FOR: {os.path.basename(pdf_path)} ===")
    print(f"Total spans: {len(spans)}")
    print()
    
    # Group by font size and analyze
    size_groups = {}
    for span in spans:
        size = round(span.font_size, 1)
        if size not in size_groups:
            size_groups[size] = []
        size_groups[size].append(span)
    
    print("=== FONT SIZE DISTRIBUTION ===")
    print(f"{'Size':<8} {'Count':<8} {'Bold%':<8} {'Sample Text'}")
    print("-" * 80)
    
    for size in sorted(size_groups.keys(), reverse=True):
        spans_group = size_groups[size]
        bold_count = sum(1 for s in spans_group if s.is_bold)
        bold_pct = (bold_count / len(spans_group)) * 100
        
        # Get a representative sample text
        sample_text = spans_group[0].text[:50] + "..." if len(spans_group[0].text) > 50 else spans_group[0].text
        
        print(f"{size:<8.1f} {len(spans_group):<8} {bold_pct:<8.1f} {sample_text}")
    
    print()
    
    # Show the largest font sizes in detail
    print("=== LARGEST FONT SIZES (POTENTIAL TITLES) ===")
    largest_sizes = sorted(size_groups.keys(), reverse=True)[:5]
    
    for size in largest_sizes:
        spans_group = size_groups[size]
        print(f"\n--- Font Size {size} ({len(spans_group)} spans) ---")
        
        for i, span in enumerate(spans_group[:10]):  # Show first 10 of each size
            print(f"  {i+1}. '{span.text}' (page {span.page_num + 1}, bold: {span.is_bold})")
    
    print()
    
    # Analyze position patterns for largest fonts
    print("=== POSITION ANALYSIS FOR LARGE FONTS ===")
    doc = fitz.open(pdf_path)
    page_height = doc[0].rect.height if len(doc) > 0 else 800
    doc.close()
    
    # Get spans with font size > 20 (likely titles/headings)
    large_spans = [s for s in spans if s.font_size > 20]
    
    print(f"Large font spans (>20pt): {len(large_spans)}")
    for span in large_spans:
        relative_y = 1.0 - (span.bbox[1] / page_height)
        print(f"  '{span.text}' - Size: {span.font_size:.1f}, Y: {relative_y:.3f}, Bold: {span.is_bold}")

if __name__ == "__main__":
    pdf_path = "/Users/karandhillon/Adobe-1A/Adobe-India-Hackathon25/Challenge_1a/input/pdftest1.pdf"
    
    if os.path.exists(pdf_path):
        analyze_font_patterns(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")