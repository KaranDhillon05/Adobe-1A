#!/usr/bin/env python3
"""
Debug script to analyze why "Portable Document Format (PDF)" is being classified as H2 instead of H1
"""

import os
import json
import fitz  # PyMuPDF
from process_pdfs import PDFProcessor, TextSpan
from typing import List, Dict

def debug_heading_analysis(pdf_path: str, target_text: str = "Portable Document Format (PDF)"):
    """Analyze the scoring for a specific heading text in detail"""
    
    processor = PDFProcessor()
    
    # Extract text spans
    spans = processor.extract_text_spans(pdf_path)
    if not spans:
        print("No text spans extracted!")
        return
    
    # Find the target text span
    target_spans = [span for span in spans if target_text.lower() in span.text.lower()]
    
    if not target_spans:
        print(f"Target text '{target_text}' not found in PDF!")
        # Show what text was found instead
        print("Available text spans from first page:")
        first_page_spans = [s for s in spans if s.page_num == 0]
        for i, span in enumerate(first_page_spans[:20]):  # Show first 20
            print(f"  {i+1}: '{span.text}' (font_size: {span.font_size}, bold: {span.is_bold})")
        return
    
    # Analyze font statistics
    font_stats = processor.analyze_font_statistics(spans)
    
    # Get page height
    doc = fitz.open(pdf_path)
    page_height = doc[0].rect.height if len(doc) > 0 else 800
    doc.close()
    
    print(f"=== DEBUGGING HEADING ANALYSIS FOR: '{target_text}' ===")
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"Page height: {page_height}")
    print()
    
    print("=== FONT STATISTICS ===")
    print(f"Body font size: {font_stats['body_font_size']}")
    print(f"Heading threshold: {font_stats['heading_threshold']}")
    print(f"Font size histogram: {dict(list(font_stats['font_size_histogram'].items())[:10])}")  # Top 10
    print(f"Unique sizes (top 10): {font_stats['unique_sizes'][:10]}")
    print()
    
    print("=== SCORING WEIGHTS ===")
    for weight_name, weight_value in processor.scoring_weights.items():
        print(f"{weight_name}: {weight_value} ({weight_value*100}%)")
    print()
    
    print("=== DETAILED ANALYSIS FOR TARGET SPANS ===")
    for i, span in enumerate(target_spans):
        print(f"\n--- SPAN {i+1}: '{span.text}' ---")
        print(f"Font: {span.font_name}")
        print(f"Font size: {span.font_size}")
        print(f"Font flags: {span.font_flags}")
        print(f"Is bold: {span.is_bold}")
        print(f"Is italic: {span.is_italic}")
        print(f"BBox: {span.bbox}")
        print(f"Page: {span.page_num + 1}")
        
        # Calculate detailed scores
        score = analyze_detailed_score(span, font_stats, page_height, processor)
        level = processor.classify_heading_level(score)
        
        print(f"FINAL SCORE: {score:.3f}")
        print(f"CLASSIFICATION: {level}")
        print()

def analyze_detailed_score(span: TextSpan, font_stats: Dict, page_height: float, processor: PDFProcessor) -> float:
    """Analyze detailed scoring breakdown"""
    
    if len(span.text) < processor.min_heading_length:
        print(f"⚠️  Text too short (min length: {processor.min_heading_length})")
        return 0.0
    
    total_score = 0.0
    
    # 1. Font Size Score (40% weight)
    size_ratio = span.font_size / font_stats["body_font_size"]
    print(f"Font size ratio: {span.font_size} / {font_stats['body_font_size']} = {size_ratio:.3f}")
    
    if size_ratio >= processor.font_size_threshold:
        font_score = min(size_ratio / 2.0, 1.0)
        weighted_font_score = font_score * processor.scoring_weights['font_size']
        total_score += weighted_font_score
        print(f"✅ Font size score: {font_score:.3f} * {processor.scoring_weights['font_size']} = {weighted_font_score:.3f}")
    else:
        print(f"❌ Font size below threshold ({processor.font_size_threshold})")
    
    # 2. Formatting Score (30% weight)
    format_score = 0.0
    if span.is_bold:
        format_score += 0.6
        print(f"✅ Bold bonus: +0.6")
    else:
        print(f"❌ Not bold")
    
    if span.is_italic:
        format_score += 0.4
        print(f"✅ Italic bonus: +0.4")
    else:
        print(f"❌ Not italic")
    
    weighted_format_score = format_score * processor.scoring_weights['formatting']
    total_score += weighted_format_score
    print(f"Format score: {format_score:.3f} * {processor.scoring_weights['formatting']} = {weighted_format_score:.3f}")
    
    # 3. Position Score (20% weight)
    if page_height > 0:
        # Invert Y coordinate (PDF origin is bottom-left)
        relative_y = 1.0 - (span.bbox[1] / page_height)
        print(f"Position: y={span.bbox[1]}, page_height={page_height}, relative_y={relative_y:.3f}")
        
        if relative_y > 0.8:  # Top 20% of page
            position_score = 1.0
            print(f"✅ In top 20% of page")
        elif relative_y > 0.6:  # Top 40% of page
            position_score = 0.5
            print(f"⚠️  In top 40% of page")
        else:
            position_score = 0.1
            print(f"❌ Below top 40% of page")
        
        weighted_position_score = position_score * processor.scoring_weights['position']
        total_score += weighted_position_score
        print(f"Position score: {position_score:.3f} * {processor.scoring_weights['position']} = {weighted_position_score:.3f}")
    
    # 4. Content Pattern Score (10% weight)
    content_score = 0.0
    text = span.text.strip()
    
    # All caps text (but not too short)
    if text.isupper() and len(text) > 4:
        content_score += 0.5
        print(f"✅ All caps bonus: +0.5")
    else:
        print(f"❌ Not all caps or too short")
    
    # Numbered sections
    import re
    if re.match(r'^(\d+\.?)+\s+', text) or re.match(r'^(Chapter|Section)\s+\d+', text, re.IGNORECASE):
        content_score += 0.5
        print(f"✅ Numbered section bonus: +0.5")
    else:
        print(f"❌ No numbered section pattern")
    
    # Common heading words
    heading_word_found = False
    for word in processor.heading_keywords:
        if word in text.lower():
            content_score += 0.3
            print(f"✅ Heading keyword '{word}' found: +0.3")
            heading_word_found = True
            break
    
    if not heading_word_found:
        print(f"❌ No heading keywords found")
        print(f"   Available keywords: {processor.heading_keywords}")
    
    weighted_content_score = content_score * processor.scoring_weights['content']
    total_score += weighted_content_score
    print(f"Content score: {content_score:.3f} * {processor.scoring_weights['content']} = {weighted_content_score:.3f}")
    
    print(f"\nTOTAL SCORE: {total_score:.3f} (capped at 1.0)")
    return min(total_score, 1.0)

def compare_with_other_headings(pdf_path: str):
    """Compare scoring with other detected headings"""
    
    processor = PDFProcessor()
    spans = processor.extract_text_spans(pdf_path)
    font_stats = processor.analyze_font_statistics(spans)
    
    doc = fitz.open(pdf_path)
    page_height = doc[0].rect.height if len(doc) > 0 else 800
    doc.close()
    
    # Score all potential headings
    scored_spans = []
    for span in spans:
        score = processor.score_heading_candidate(span, font_stats, page_height)
        level = processor.classify_heading_level(score)
        if score > 0.3:  # Show anything with reasonable score
            scored_spans.append((span, score, level))
    
    # Sort by score descending
    scored_spans.sort(key=lambda x: x[1], reverse=True)
    
    print("\n=== COMPARISON WITH OTHER POTENTIAL HEADINGS ===")
    print(f"{'Score':<6} {'Level':<5} {'Font Size':<10} {'Bold':<5} {'Text'}")
    print("-" * 80)
    
    for span, score, level in scored_spans[:20]:  # Top 20
        text_preview = span.text[:50] + "..." if len(span.text) > 50 else span.text
        print(f"{score:<6.3f} {level or 'None':<5} {span.font_size:<10.1f} {span.is_bold:<5} {text_preview}")

if __name__ == "__main__":
    pdf_path = "/Users/karandhillon/Adobe-1A/Adobe-India-Hackathon25/Challenge_1a/input/pdftest1.pdf"
    
    if os.path.exists(pdf_path):
        debug_heading_analysis(pdf_path)
        compare_with_other_headings(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")