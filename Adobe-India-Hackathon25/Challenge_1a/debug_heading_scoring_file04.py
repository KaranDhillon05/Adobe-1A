#!/usr/bin/env python3
"""
Debug Script for Heading Scoring Analysis on file04.pdf
This shows why "Mission Statement", "Goals", and "Pathway Options" are not being classified as headings.
"""

import sys
import json
from pathlib import Path
from process_pdfs import PDFProcessor, TextSpan
import fitz

class HeadingScoreDebugger:
    def __init__(self):
        self.processor = PDFProcessor()
        self.target_texts = [
            "Mission Statement:",
            "Goals:",
            "PATHWAY OPTIONS",
            "DISTINCTION PATHWAY", 
            "REGULAR PATHWAY",
            "Parsippany -Troy Hills STEM Pathways"
        ]

    def debug_heading_scoring(self, pdf_path: str):
        """Debug the heading scoring process in detail"""
        print("="*80)
        print("HEADING SCORING DEBUG ANALYSIS FOR FILE04.PDF")
        print("="*80)
        print(f"Analyzing: {pdf_path}")
        print()

        if not Path(pdf_path).exists():
            print(f"❌ Error: File {pdf_path} not found!")
            return

        try:
            # Extract all text spans
            spans = self.processor.extract_text_spans(pdf_path)
            print(f"📊 Total spans extracted: {len(spans)}")
            
            # Analyze font statistics
            font_stats = self.processor.analyze_font_statistics(spans)
            print(f"📈 Font Statistics:")
            print(f"   Body font size: {font_stats['body_font_size']}")
            print(f"   Heading threshold: {font_stats['heading_threshold']}")
            print(f"   Font size histogram: {font_stats['font_size_histogram']}")
            print(f"   Unique sizes: {font_stats['unique_sizes']}")
            print()

            # Get page height for position scoring
            doc = fitz.open(pdf_path)
            page_height = doc[0].rect.height if len(doc) > 0 else 800
            doc.close()
            print(f"📏 Page height: {page_height}")
            print()

            # Filter potential heading spans
            potential_headings = [
                span for span in spans 
                if (span.font_size >= font_stats["heading_threshold"] or 
                    span.is_bold or 
                    len(span.text.strip()) > 10)
            ]
            print(f"🎯 Potential heading spans: {len(potential_headings)}")
            print()

            # Focus on target texts
            target_spans = []
            for span in potential_headings:
                for target in self.target_texts:
                    if target.lower() in span.text.lower():
                        target_spans.append(span)
                        break

            print("🔍 DETAILED SCORING ANALYSIS FOR TARGET TEXTS")
            print("="*80)

            for i, span in enumerate(target_spans):
                print(f"\n📝 SPAN {i+1}: '{span.text}'")
                print(f"   Font: {span.font_name}")
                print(f"   Size: {span.font_size}")
                print(f"   Bold: {span.is_bold}")
                print(f"   Italic: {span.is_italic}")
                print(f"   BBox: {span.bbox}")
                print(f"   Page: {span.page_num}")
                
                # Calculate detailed score breakdown
                score = self.debug_score_calculation(span, font_stats, page_height)
                level = self.processor.classify_heading_level(score)
                
                print(f"   📊 FINAL SCORE: {score:.3f}")
                print(f"   📋 CLASSIFICATION: {level if level else 'NOT A HEADING'}")
                
                # Show if it passes filters
                is_filtered = self.processor._is_definitely_not_heading(span.text)
                print(f"   🚫 FILTERED OUT: {is_filtered}")
                
                print("-" * 60)

            # Show all spans that made it through to final headings
            print("\n✅ SPANS THAT BECAME HEADINGS")
            print("="*60)
            
            # Run the actual heading detection to see what passes
            final_headings = self.processor.detect_headings(pdf_path)
            print(f"Final headings detected: {len(final_headings)}")
            
            for heading in final_headings:
                print(f"   {heading['level']}: {heading['text']} (page {heading['page']})")
                
                # Find the original span for this heading
                matching_spans = [s for s in spans if s.text.strip().lower() == heading['text'].lower()]
                if matching_spans:
                    span = matching_spans[0]
                    score = self.processor.score_heading_candidate(span, font_stats, page_height)
                    print(f"      Score: {score:.3f}, Size: {span.font_size}, Bold: {span.is_bold}")

        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()

    def debug_score_calculation(self, span: TextSpan, font_stats: dict, page_height: float) -> float:
        """Debug version of score calculation with detailed breakdown"""
        print(f"   🧮 SCORE BREAKDOWN:")
        
        if len(span.text) < self.processor.min_heading_length:
            print(f"      ❌ Text too short (< {self.processor.min_heading_length} chars)")
            return 0.0

        text = span.text.strip()
        
        # Check if filtered out
        if self.processor._is_definitely_not_heading(text):
            print(f"      ❌ Filtered out by _is_definitely_not_heading")
            return 0.0

        score = 0.0
        
        # 1. Font Size Score (35% weight)
        size_ratio = span.font_size / font_stats["body_font_size"]
        print(f"      📏 Size ratio: {size_ratio:.3f} ({span.font_size} / {font_stats['body_font_size']})")
        
        if size_ratio >= self.processor.font_size_threshold:
            font_score = min(size_ratio / 2.0, 1.0)
            weighted_font_score = font_score * 0.35
            score += weighted_font_score
            print(f"         Font score: {font_score:.3f} * 0.35 = {weighted_font_score:.3f}")
        else:
            print(f"         Font score: 0 (below threshold {self.processor.font_size_threshold})")

        # 2. Formatting Score (25% weight)
        format_score = 0.0
        if span.is_bold:
            format_score += 0.6
            print(f"         Bold bonus: +0.6")
        if span.is_italic:
            format_score += 0.4
            print(f"         Italic bonus: +0.4")
        
        # Special case for very large fonts
        if size_ratio >= 2.0 and format_score == 0.0:
            format_score = 0.6
            print(f"         Large font bonus: +0.6")
        
        weighted_format_score = format_score * 0.25
        score += weighted_format_score
        print(f"         Format score: {format_score:.3f} * 0.25 = {weighted_format_score:.3f}")

        # 3. Structural Context Score (25% weight)
        structural_score = self.processor._evaluate_structural_context(text, span, page_height)
        weighted_structural_score = structural_score * 0.25
        score += weighted_structural_score
        print(f"         Structural score: {structural_score:.3f} * 0.25 = {weighted_structural_score:.3f}")

        # 4. Position Score (10% weight)
        if page_height > 0:
            relative_y = 1.0 - (span.bbox[1] / page_height)
            if relative_y > 0.8:
                position_score = 1.0
            elif relative_y > 0.6:
                position_score = 0.5
            else:
                position_score = 0.1
            
            weighted_position_score = position_score * 0.10
            score += weighted_position_score
            print(f"         Position: y={relative_y:.3f}, score={position_score:.3f} * 0.10 = {weighted_position_score:.3f}")

        # 5. Content Pattern Score (5% weight)
        content_score = 0.0
        
        # Check for various patterns
        import re
        if re.match(r'^[A-Z]\.\s+[A-Z]', text) or re.match(r'^\d+\.\s+[A-Z]', text):
            content_score += 0.8
            print(f"         Numbered heading pattern: +0.8")
        elif re.match(r'^(Chapter|Section|Part)\s+\d+', text, re.IGNORECASE):
            content_score += 0.7
            print(f"         Chapter/Section pattern: +0.7")
        
        # Section keywords
        section_keywords = [
            'preconditions', 'document properties', 'accessibility', 'objects', 'miscellaneous',
            'mission statement', 'goals', 'pathway options', 'regular pathway', 'distinction pathway',
            'requirements', 'objectives', 'overview', 'introduction', 'conclusion', 'summary'
        ]
        
        text_lower = text.lower()
        matching_keywords = [kw for kw in section_keywords if kw in text_lower]
        if matching_keywords:
            content_score += 0.6
            print(f"         Section keywords ({matching_keywords}): +0.6")
        
        weighted_content_score = content_score * 0.05
        score += weighted_content_score
        print(f"         Content score: {content_score:.3f} * 0.05 = {weighted_content_score:.3f}")

        final_score = min(score, 1.0)
        print(f"      🎯 TOTAL SCORE: {final_score:.3f}")
        
        return final_score

def main():
    """Main function to run the debug analysis"""
    pdf_path = "/Users/karandhillon/Adobe-1A/Adobe-India-Hackathon25/Challenge_1a/input/file04.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    debugger = HeadingScoreDebugger()
    debugger.debug_heading_scoring(pdf_path)

if __name__ == "__main__":
    main()