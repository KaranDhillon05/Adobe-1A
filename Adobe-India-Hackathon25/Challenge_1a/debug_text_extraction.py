#!/usr/bin/env python3
"""
Debug script to analyze text extraction issues causing garbled text
"""

import fitz
import sys
from collections import defaultdict

def debug_text_extraction(pdf_path):
    """Debug text extraction methods to identify duplication issues"""
    print(f"=== Debugging text extraction for {pdf_path} ===")
    
    doc = fitz.open(pdf_path)
    page = doc[0]  # Focus on first page
    
    print("\n1. RAW TEXT DICT EXTRACTION:")
    text_dict = page.get_text("dict")
    
    spans_found = []
    
    for block_idx, block in enumerate(text_dict.get("blocks", [])):
        if "lines" not in block:
            continue
            
        print(f"\nBlock {block_idx}: bbox={block.get('bbox', 'unknown')}")
        
        for line_idx, line in enumerate(block["lines"]):
            print(f"  Line {line_idx}: bbox={line.get('bbox', 'unknown')}")
            
            for span_idx, span in enumerate(line.get("spans", [])):
                text = span.get("text", "").strip()
                if text:
                    bbox = span.get("bbox", (0,0,0,0))
                    spans_found.append({
                        'text': text,
                        'bbox': bbox,
                        'font': span.get('font', ''),
                        'size': span.get('size', 0),
                        'flags': span.get('flags', 0)
                    })
                    
                    print(f"    Span {span_idx}: \"{text}\" | font={span.get('font', '')} | size={span.get('size', 0)} | bbox={bbox}")
    
    print(f"\nTotal spans found: {len(spans_found)}")
    
    # Check for overlaps
    print("\n2. CHECKING FOR OVERLAPPING SPANS:")
    overlaps = []
    for i, span1 in enumerate(spans_found):
        for j, span2 in enumerate(spans_found[i+1:], i+1):
            if spans_overlap(span1['bbox'], span2['bbox']):
                overlaps.append((i, j, span1, span2))
    
    if overlaps:
        print(f"Found {len(overlaps)} overlapping spans:")
        for i, j, span1, span2 in overlaps[:10]:  # Show first 10
            print(f"  Overlap {i},{j}: \"{span1['text']}\" vs \"{span2['text']}\"")
            print(f"    Bbox1: {span1['bbox']}")
            print(f"    Bbox2: {span2['bbox']}")
    else:
        print("No overlapping spans found")
    
    # Check current deduplication logic
    print("\n3. TESTING CURRENT DEDUPLICATION:")
    seen = {}
    duplicates = []
    
    for span in spans_found:
        key = (
            span['text'].strip().lower(),
            round(span['bbox'][0] / 10) * 10,
            round(span['bbox'][1] / 10) * 10,
            0  # page_num
        )
        
        if key in seen:
            duplicates.append((seen[key], span))
        else:
            seen[key] = span
    
    if duplicates:
        print(f"Found {len(duplicates)} potential duplicates with current logic:")
        for orig, dup in duplicates[:5]:
            print(f"  \"{orig['text']}\" vs \"{dup['text']}\"")
    else:
        print("No duplicates found with current logic")
    
    # Check specific problematic text
    print("\n4. SEARCHING FOR PROBLEMATIC TEXT:")
    problem_patterns = ['RFP', 'Request', 'Proposal', 'fquest', 'Prr']
    
    for pattern in problem_patterns:
        matching_spans = [s for s in spans_found if pattern.lower() in s['text'].lower()]
        if matching_spans:
            print(f"\nSpans containing '{pattern}':")
            for span in matching_spans:
                print(f"  \"{span['text']}\" | bbox={span['bbox']} | size={span['size']}")
    
    doc.close()

def spans_overlap(bbox1, bbox2, tolerance=2):
    """Check if two bounding boxes overlap (with tolerance)"""
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    # Check if there's any overlap
    return not (x1_max + tolerance < x2_min or 
                x2_max + tolerance < x1_min or 
                y1_max + tolerance < y2_min or 
                y2_max + tolerance < y1_min)

def debug_font_analysis(pdf_path):
    """Debug font analysis to understand why body text detection is failing"""
    print(f"\n=== Font Analysis Debug for {pdf_path} ===")
    
    doc = fitz.open(pdf_path)
    
    all_spans = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if len(text) >= 3:
                        all_spans.append({
                            'text': text,
                            'size': span.get('size', 0),
                            'font': span.get('font', ''),
                            'flags': span.get('flags', 0),
                            'page': page_num
                        })
    
    print(f"Total text spans: {len(all_spans)}")
    
    # Analyze font sizes
    size_counts = defaultdict(int)
    size_text_lengths = defaultdict(list)
    
    for span in all_spans:
        size = round(span['size'], 1)
        size_counts[size] += 1
        size_text_lengths[size].append(len(span['text']))
    
    print("\nFont size distribution:")
    for size in sorted(size_counts.keys(), reverse=True):
        avg_length = sum(size_text_lengths[size]) / len(size_text_lengths[size])
        print(f"  Size {size:6.1f}: {size_counts[size]:3d} spans, avg length {avg_length:5.1f}")
    
    # Find most common size for longer text
    weighted_sizes = {}
    for span in all_spans:
        size = span['size']
        weight = min(len(span['text']) / 10, 5)
        weighted_sizes[size] = weighted_sizes.get(size, 0) + weight
    
    if weighted_sizes:
        body_font_size = max(weighted_sizes.items(), key=lambda x: x[1])[0]
        print(f"\nDetected body font size: {body_font_size}")
        print(f"Heading threshold (1.2x): {body_font_size * 1.2}")
    
    doc.close()

if __name__ == "__main__":
    pdf_files = [
        "input/file01.pdf",
        "input/file02.pdf", 
        "input/file03.pdf"
    ]
    
    for pdf_file in pdf_files:
        try:
            debug_text_extraction(pdf_file)
            debug_font_analysis(pdf_file)
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")