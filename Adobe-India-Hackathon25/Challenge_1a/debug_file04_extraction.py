#!/usr/bin/env python3
"""
Comprehensive Debug Script for file04.pdf Text Extraction
This script analyzes why "Mission Statement", "Goals", and "Pathway Options" are not being detected.
"""

import sys
import json
import fitz  # PyMuPDF
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import re

@dataclass
class DetailedTextSpan:
    """Enhanced text span with detailed analysis information"""
    text: str
    font_name: str
    font_size: float
    font_flags: int
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_num: int
    color: Optional[Tuple[float, float, float]] = None
    extraction_method: str = "unknown"
    
    @property
    def is_bold(self) -> bool:
        return bool(self.font_flags & 2**4)
    
    @property
    def is_italic(self) -> bool:
        return bool(self.font_flags & 2**1)
    
    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]
    
    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]

class PDF04Debugger:
    def __init__(self):
        self.target_texts = [
            "mission statement",
            "goals", 
            "pathway options",
            "distinction pathway",
            "regular pathway",
            "parsippany",
            "stem pathways"
        ]
    
    def debug_file04(self, pdf_path: str):
        """Comprehensive debugging analysis for file04.pdf"""
        print("="*80)
        print("FILE04.PDF EXTRACTION DEBUG ANALYSIS")
        print("="*80)
        print(f"Analyzing: {pdf_path}")
        print()
        
        if not Path(pdf_path).exists():
            print(f"❌ Error: File {pdf_path} not found!")
            return
        
        try:
            doc = fitz.open(pdf_path)
            print(f"📄 Document Info:")
            print(f"   Pages: {len(doc)}")
            print(f"   Metadata: {doc.metadata}")
            print()
            
            # Analyze each extraction method
            all_spans = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                print(f"🔍 ANALYZING PAGE {page_num + 1}")
                print("-" * 60)
                
                # Method 1: Table detection
                print("METHOD 1: Table Detection")
                table_spans = self.extract_table_text_debug(page, page_num)
                all_spans.extend(table_spans)
                self.print_method_results("Table", table_spans)
                print()
                
                # Method 2: Layout-aware extraction
                print("METHOD 2: Layout-Aware Extraction")
                layout_spans = self.extract_layout_aware_debug(page, page_num)
                all_spans.extend(layout_spans)
                self.print_method_results("Layout-Aware", layout_spans)
                print()
                
                # Method 3: Standard extraction
                print("METHOD 3: Standard Extraction")
                standard_spans = self.extract_standard_debug(page, page_num)
                all_spans.extend(standard_spans)
                self.print_method_results("Standard", standard_spans)
                print()
                
                # Method 4: Raw text blocks analysis
                print("METHOD 4: Raw Text Blocks Analysis")
                raw_spans = self.extract_raw_blocks_debug(page, page_num)
                all_spans.extend(raw_spans)
                self.print_method_results("Raw Blocks", raw_spans)
                print()
                
                # Method 5: Drawing objects and annotations
                print("METHOD 5: Drawing Objects & Annotations")
                self.analyze_drawings_and_annotations(page, page_num)
                print()
                
                print("=" * 60)
                print()
            
            doc.close()
            
            # Overall analysis
            self.analyze_all_spans(all_spans)
            
            # Search for target texts
            self.search_target_texts(all_spans)
            
            # Font and formatting analysis
            self.analyze_fonts_and_formatting(all_spans)
            
            # Spatial analysis
            self.analyze_spatial_distribution(all_spans)
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
    
    def extract_table_text_debug(self, page, page_num: int) -> List[DetailedTextSpan]:
        """Debug version of table text extraction"""
        spans = []
        try:
            tables = page.find_tables()
            print(f"   Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                print(f"   Table {i+1}: bbox={table.bbox}")
                table_data = table.extract()
                
                if table_data:
                    print(f"   Table data ({len(table_data)} rows):")
                    for row_idx, row in enumerate(table_data[:3]):  # Show first 3 rows
                        print(f"     Row {row_idx}: {row}")
                    
                    # Process table headers
                    first_row = table_data[0] if table_data else []
                    for j, cell in enumerate(first_row):
                        if cell and len(str(cell).strip()) > 2:
                            bbox = table.bbox
                            cell_bbox = (
                                bbox[0] + (bbox[2] - bbox[0]) * j / len(first_row),
                                bbox[1],
                                bbox[0] + (bbox[2] - bbox[0]) * (j + 1) / len(first_row),
                                bbox[1] + 20
                            )
                            
                            spans.append(DetailedTextSpan(
                                text=str(cell).strip(),
                                font_name="table-header",
                                font_size=12.0,
                                font_flags=16,
                                bbox=cell_bbox,
                                page_num=page_num,
                                extraction_method="table"
                            ))
        except Exception as e:
            print(f"   Table extraction error: {e}")
        
        return spans
    
    def extract_layout_aware_debug(self, page, page_num: int) -> List[DetailedTextSpan]:
        """Debug version of layout-aware extraction"""
        spans = []
        try:
            blocks = page.get_text("dict")
            print(f"   Found {len(blocks.get('blocks', []))} blocks")
            
            # Analyze blocks
            for block_idx, block in enumerate(blocks.get("blocks", [])):
                if "lines" not in block:
                    continue
                
                bbox = block.get("bbox", (0, 0, 0, 0))
                print(f"   Block {block_idx}: bbox={bbox}")
                
                for line_idx, line in enumerate(block.get("lines", [])):
                    for span_idx, span in enumerate(line.get("spans", [])):
                        text = span.get("text", "").strip()
                        if text and len(text) >= 3:
                            color = span.get("color", None)
                            
                            detailed_span = DetailedTextSpan(
                                text=text,
                                font_name=span.get("font", ""),
                                font_size=span.get("size", 0),
                                font_flags=span.get("flags", 0),
                                bbox=span.get("bbox", (0, 0, 0, 0)),
                                page_num=page_num,
                                color=color,
                                extraction_method="layout-aware"
                            )
                            spans.append(detailed_span)
                            
                            # Print details for interesting text
                            if any(target in text.lower() for target in self.target_texts):
                                print(f"     *** FOUND TARGET: {text}")
                                print(f"         Font: {span.get('font', 'N/A')}, Size: {span.get('size', 'N/A')}")
                                print(f"         Flags: {span.get('flags', 'N/A')}, Color: {color}")
                                print(f"         BBox: {span.get('bbox', 'N/A')}")
        
        except Exception as e:
            print(f"   Layout-aware extraction error: {e}")
        
        return spans
    
    def extract_standard_debug(self, page, page_num: int) -> List[DetailedTextSpan]:
        """Debug version of standard text extraction"""
        spans = []
        try:
            text_dict = page.get_text("dict")
            block_count = len(text_dict.get("blocks", []))
            print(f"   Processing {block_count} blocks with standard method")
            
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text or len(text) < 3:
                            continue
                        
                        color = span.get("color", None)
                        detailed_span = DetailedTextSpan(
                            text=text,
                            font_name=span.get("font", ""),
                            font_size=span.get("size", 0),
                            font_flags=span.get("flags", 0),
                            bbox=span.get("bbox", (0, 0, 0, 0)),
                            page_num=page_num,
                            color=color,
                            extraction_method="standard"
                        )
                        spans.append(detailed_span)
        
        except Exception as e:
            print(f"   Standard extraction error: {e}")
        
        return spans
    
    def extract_raw_blocks_debug(self, page, page_num: int) -> List[DetailedTextSpan]:
        """Extract raw text blocks for deep analysis"""
        spans = []
        try:
            # Try different text extraction modes
            modes = ["text", "html", "dict", "rawdict", "xml"]
            
            for mode in modes:
                try:
                    if mode == "text":
                        text = page.get_text("text")
                        if text.strip():
                            print(f"   Text mode extracted {len(text)} characters")
                            # Look for target texts in plain text
                            for target in self.target_texts:
                                if target in text.lower():
                                    print(f"     *** Found '{target}' in text mode!")
                    
                    elif mode == "dict" or mode == "rawdict":
                        data = page.get_text(mode)
                        if isinstance(data, dict):
                            blocks = data.get("blocks", [])
                            print(f"   {mode.capitalize()} mode: {len(blocks)} blocks")
                            
                            for block in blocks:
                                if block.get("type") == 0 and "lines" in block:  # Text block
                                    for line in block["lines"]:
                                        for span in line.get("spans", []):
                                            text = span.get("text", "").strip()
                                            if text and len(text) >= 2:
                                                detailed_span = DetailedTextSpan(
                                                    text=text,
                                                    font_name=span.get("font", ""),
                                                    font_size=span.get("size", 0),
                                                    font_flags=span.get("flags", 0),
                                                    bbox=span.get("bbox", (0, 0, 0, 0)),
                                                    page_num=page_num,
                                                    color=span.get("color", None),
                                                    extraction_method=f"raw-{mode}"
                                                )
                                                spans.append(detailed_span)
                    
                    elif mode == "xml":
                        xml_data = page.get_text("xml")
                        if xml_data:
                            print(f"   XML mode extracted {len(xml_data)} characters")
                            # Search for target texts in XML
                            for target in self.target_texts:
                                if target in xml_data.lower():
                                    print(f"     *** Found '{target}' in XML mode!")
                                    # Extract context around the target
                                    import re
                                    pattern = rf'.{{0,50}}{re.escape(target)}.{{0,50}}'
                                    matches = re.findall(pattern, xml_data, re.IGNORECASE)
                                    for match in matches[:3]:  # Show first 3 matches
                                        print(f"       Context: {match}")
                
                except Exception as e:
                    print(f"   Error with {mode} mode: {e}")
        
        except Exception as e:
            print(f"   Raw blocks extraction error: {e}")
        
        return spans
    
    def analyze_drawings_and_annotations(self, page, page_num: int):
        """Analyze drawings, annotations, and other objects that might contain text"""
        try:
            # Check for annotations
            annotations = page.annots()
            if annotations:
                print(f"   Found annotations on page {page_num + 1}")
                for annot in annotations:
                    content = annot.info.get("content", "")
                    if content:
                        print(f"     Annotation content: {content}")
            
            # Check for images that might contain text
            images = page.get_images()
            if images:
                print(f"   Found {len(images)} images")
                # Images might contain text as graphics - this would require OCR
            
            # Check for vector graphics and paths
            drawings = page.get_drawings()
            if drawings:
                print(f"   Found {len(drawings)} drawing objects")
                # Vector graphics might contain text elements
            
            # Check for widgets (form fields)
            widgets = page.widgets()
            if widgets:
                print(f"   Found {len(widgets)} widgets/form fields")
                for widget in widgets:
                    if hasattr(widget, 'field_value') and widget.field_value:
                        print(f"     Widget value: {widget.field_value}")
        
        except Exception as e:
            print(f"   Error analyzing drawings/annotations: {e}")
    
    def print_method_results(self, method_name: str, spans: List[DetailedTextSpan]):
        """Print results from an extraction method"""
        print(f"   {method_name} extracted {len(spans)} text spans")
        
        # Show target text matches
        target_matches = []
        for span in spans:
            for target in self.target_texts:
                if target in span.text.lower():
                    target_matches.append((target, span))
        
        if target_matches:
            print(f"   *** Found {len(target_matches)} target matches:")
            for target, span in target_matches:
                print(f"     '{target}' -> '{span.text}' (size: {span.font_size}, bold: {span.is_bold})")
        
        # Show sample spans
        if spans:
            print(f"   Sample spans (first 3):")
            for i, span in enumerate(spans[:3]):
                print(f"     {i+1}. '{span.text}' (font: {span.font_name}, size: {span.font_size})")
    
    def analyze_all_spans(self, spans: List[DetailedTextSpan]):
        """Analyze all extracted spans comprehensively"""
        print("📊 COMPREHENSIVE SPAN ANALYSIS")
        print("=" * 60)
        
        print(f"Total spans extracted: {len(spans)}")
        
        # Group by extraction method
        by_method = defaultdict(list)
        for span in spans:
            by_method[span.extraction_method].append(span)
        
        print("\nSpans by extraction method:")
        for method, method_spans in by_method.items():
            print(f"  {method}: {len(method_spans)} spans")
        
        # Unique texts
        unique_texts = set(span.text.lower().strip() for span in spans)
        print(f"\nUnique text fragments: {len(unique_texts)}")
        
        # Font analysis
        fonts = Counter(span.font_name for span in spans if span.font_name)
        print(f"\nFonts used ({len(fonts)} unique):")
        for font, count in fonts.most_common(5):
            print(f"  {font}: {count} spans")
        
        # Size analysis
        sizes = Counter(span.font_size for span in spans if span.font_size > 0)
        print(f"\nFont sizes ({len(sizes)} unique):")
        for size, count in sorted(sizes.items(), reverse=True)[:10]:
            print(f"  {size}pt: {count} spans")
        
        print()
    
    def search_target_texts(self, spans: List[DetailedTextSpan]):
        """Search for target texts and analyze why they might not be detected"""
        print("🎯 TARGET TEXT SEARCH ANALYSIS")
        print("=" * 60)
        
        for target in self.target_texts:
            print(f"\nSearching for: '{target}'")
            
            # Exact matches
            exact_matches = [span for span in spans if target == span.text.lower().strip()]
            print(f"  Exact matches: {len(exact_matches)}")
            
            # Partial matches
            partial_matches = [span for span in spans if target in span.text.lower()]
            print(f"  Partial matches: {len(partial_matches)}")
            
            if partial_matches:
                print("  Partial match details:")
                for span in partial_matches[:5]:  # Show first 5
                    print(f"    '{span.text}' (method: {span.extraction_method}, size: {span.font_size})")
            
            # Fuzzy matches (words contained)
            target_words = target.split()
            fuzzy_matches = []
            for span in spans:
                span_words = span.text.lower().split()
                if any(word in span_words for word in target_words):
                    fuzzy_matches.append(span)
            
            print(f"  Fuzzy matches (contains words): {len(fuzzy_matches)}")
            if fuzzy_matches and not partial_matches:  # Only show if no partial matches
                print("  Fuzzy match details:")
                for span in fuzzy_matches[:3]:
                    print(f"    '{span.text}' (method: {span.extraction_method})")
    
    def analyze_fonts_and_formatting(self, spans: List[DetailedTextSpan]):
        """Analyze font patterns and formatting that might affect detection"""
        print("🎨 FONT AND FORMATTING ANALYSIS")
        print("=" * 60)
        
        # Bold text analysis
        bold_spans = [span for span in spans if span.is_bold]
        print(f"Bold text spans: {len(bold_spans)}")
        if bold_spans:
            print("Sample bold texts:")
            for span in bold_spans[:5]:
                print(f"  '{span.text}' (size: {span.font_size})")
        
        # Large text analysis
        size_threshold = 12.0  # Typical body text size
        large_spans = [span for span in spans if span.font_size > size_threshold]
        print(f"\nLarge text spans (>{size_threshold}pt): {len(large_spans)}")
        if large_spans:
            print("Sample large texts:")
            for span in sorted(large_spans, key=lambda x: x.font_size, reverse=True)[:5]:
                print(f"  '{span.text}' (size: {span.font_size}pt)")
        
        # Color analysis
        colored_spans = [span for span in spans if span.color is not None]
        print(f"\nColored text spans: {len(colored_spans)}")
        if colored_spans:
            colors = Counter(span.color for span in colored_spans)
            print("Colors used:")
            for color, count in colors.most_common(5):
                print(f"  {color}: {count} spans")
        
        print()
    
    def analyze_spatial_distribution(self, spans: List[DetailedTextSpan]):
        """Analyze spatial distribution of text spans"""
        print("📍 SPATIAL DISTRIBUTION ANALYSIS")
        print("=" * 60)
        
        if not spans:
            print("No spans to analyze")
            return
        
        # Page distribution
        by_page = defaultdict(list)
        for span in spans:
            by_page[span.page_num].append(span)
        
        print("Distribution by page:")
        for page_num in sorted(by_page.keys()):
            page_spans = by_page[page_num]
            print(f"  Page {page_num + 1}: {len(page_spans)} spans")
            
            # Find spans in different regions of the page
            top_spans = [s for s in page_spans if s.bbox[1] > 700]  # Top region
            middle_spans = [s for s in page_spans if 300 < s.bbox[1] <= 700]  # Middle
            bottom_spans = [s for s in page_spans if s.bbox[1] <= 300]  # Bottom
            
            print(f"    Top region: {len(top_spans)} spans")
            print(f"    Middle region: {len(middle_spans)} spans")
            print(f"    Bottom region: {len(bottom_spans)} spans")
            
            # Show interesting spans in each region
            for region_name, region_spans in [("Top", top_spans), ("Middle", middle_spans), ("Bottom", bottom_spans)]:
                target_spans = [s for s in region_spans if any(target in s.text.lower() for target in self.target_texts)]
                if target_spans:
                    print(f"    {region_name} region target texts:")
                    for span in target_spans:
                        print(f"      '{span.text}' at {span.bbox}")
        
        print()

def main():
    """Main function to run the debug analysis"""
    pdf_path = "/Users/karandhillon/Adobe-1A/Adobe-India-Hackathon25/Challenge_1a/input/file04.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    debugger = PDF04Debugger()
    debugger.debug_file04(pdf_path)

if __name__ == "__main__":
    main()