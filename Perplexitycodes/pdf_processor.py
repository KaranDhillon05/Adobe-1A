"""
Adobe Hackathon 2025 - Core PDF Processing Engine
High-performance PDF processing with advanced heading detection and semantic analysis
"""

import fitz  # PyMuPDF - fastest PDF processing library
import numpy as np
import json
import re
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
import logging

@dataclass
class TextSpan:
    """Represents a text span with formatting and position information"""
    text: str
    font_name: str
    font_size: float
    font_flags: int  # Bold, italic flags
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_num: int

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

class PDFProcessor:
    """High-performance PDF processor with advanced heading detection"""

    def __init__(self, font_size_threshold: float = 1.2, min_heading_length: int = 3):
        self.font_size_threshold = font_size_threshold
        self.min_heading_length = min_heading_length
        self.logger = logging.getLogger(__name__)

        # Heading pattern weights for multi-factor scoring
        self.scoring_weights = {
            'font_size': 0.4,    # Larger fonts = higher heading level
            'formatting': 0.3,   # Bold/italic formatting
            'position': 0.2,     # Page position (top = higher)
            'content': 0.1       # Capitalization, numbering patterns
        }

    def extract_text_spans(self, pdf_path: str) -> List[TextSpan]:
        """Extract all text spans with formatting information in single pass"""
        spans = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                # Single-pass extraction for maximum performance
                text_dict = page.get_text("dict")

                for block in text_dict.get("blocks", []):
                    if "lines" not in block:  # Skip image blocks
                        continue

                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if not text or len(text) < 2:
                                continue

                            spans.append(TextSpan(
                                text=text,
                                font_name=span.get("font", ""),
                                font_size=span.get("size", 0),
                                font_flags=span.get("flags", 0),
                                bbox=span.get("bbox", (0, 0, 0, 0)),
                                page_num=page_num
                            ))

            doc.close()
            return spans

        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            return []

    def analyze_font_statistics(self, spans: List[TextSpan]) -> Dict[str, Any]:
        """Analyze font patterns to identify body text and potential headings"""
        if not spans:
            return {"body_font_size": 12, "font_size_histogram": {}}

        # Build font size histogram
        font_sizes = [span.font_size for span in spans if span.font_size > 0]
        size_counter = Counter(font_sizes)

        # Body text is the most common font size
        body_font_size = size_counter.most_common(1)[0][0] if size_counter else 12

        # Heading candidates are fonts larger than body * threshold
        heading_threshold = body_font_size * self.font_size_threshold

        return {
            "body_font_size": body_font_size,
            "heading_threshold": heading_threshold,
            "font_size_histogram": dict(size_counter),
            "unique_sizes": sorted(set(font_sizes), reverse=True)
        }

    def score_heading_candidate(self, span: TextSpan, font_stats: Dict[str, Any], 
                              page_height: float) -> float:
        """Multi-factor scoring for heading detection"""
        if len(span.text) < self.min_heading_length:
            return 0.0

        score = 0.0

        # 1. Font Size Score (40% weight)
        size_ratio = span.font_size / font_stats["body_font_size"]
        if size_ratio >= self.font_size_threshold:
            font_score = min(size_ratio / 2.0, 1.0)  # Cap at 1.0
            score += font_score * self.scoring_weights['font_size']

        # 2. Formatting Score (30% weight)
        format_score = 0.0
        if span.is_bold:
            format_score += 0.6
        if span.is_italic:
            format_score += 0.4
        score += format_score * self.scoring_weights['formatting']

        # 3. Position Score (20% weight) - Higher on page = higher score
        if page_height > 0:
            # Invert Y coordinate (PDF origin is bottom-left)
            relative_y = 1.0 - (span.bbox[1] / page_height)
            if relative_y > 0.8:  # Top 20% of page
                position_score = 1.0
            elif relative_y > 0.6:  # Top 40% of page
                position_score = 0.5
            else:
                position_score = 0.1
            score += position_score * self.scoring_weights['position']

        # 4. Content Pattern Score (10% weight)
        content_score = 0.0
        text = span.text.strip()

        # All caps text (but not too short)
        if text.isupper() and len(text) > 4:
            content_score += 0.5

        # Numbered sections (1.1, Chapter 1, etc.)
        if re.match(r'^(\d+\.?)+\s+', text) or re.match(r'^(Chapter|Section)\s+\d+', text, re.IGNORECASE):
            content_score += 0.5

        # Common heading words
        heading_words = ['introduction', 'conclusion', 'abstract', 'overview', 'summary', 'background']
        if any(word in text.lower() for word in heading_words):
            content_score += 0.3

        score += content_score * self.scoring_weights['content']

        return min(score, 1.0)  # Cap at 1.0

    def classify_heading_level(self, score: float) -> Optional[str]:
        """Classify heading level based on composite score"""
        if score >= 0.8:
            return "H1"
        elif score >= 0.6:
            return "H2" 
        elif score >= 0.4:
            return "H3"
        else:
            return None  # Not a heading

    def detect_title(self, pdf_path: str, spans: List[TextSpan]) -> str:
        """Detect document title using multiple strategies"""
        try:
            # Strategy 1: Check PDF metadata
            doc = fitz.open(pdf_path)
            metadata_title = doc.metadata.get("title", "").strip()
            doc.close()

            if metadata_title and len(metadata_title) > 3:
                return metadata_title

            # Strategy 2: Find largest text in top 20% of first page
            first_page_spans = [s for s in spans if s.page_num == 0]
            if not first_page_spans:
                return "Untitled Document"

            # Get page dimensions
            doc = fitz.open(pdf_path)
            page = doc[0]
            page_height = page.rect.height
            doc.close()

            # Find spans in top 20% of page
            top_20_percent = page_height * 0.8  # PDF coordinates are bottom-up
            top_spans = [s for s in first_page_spans if s.bbox[1] >= top_20_percent]

            if top_spans:
                # Get the largest font in the top area
                largest_span = max(top_spans, key=lambda x: x.font_size)
                return largest_span.text.strip()

            # Strategy 3: Use filename as fallback
            filename = os.path.basename(pdf_path)
            return os.path.splitext(filename)[0]

        except Exception as e:
            self.logger.error(f"Error detecting title: {e}")
            return "Untitled Document"

    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """Extract structured outline from PDF with high accuracy"""
        try:
            # Extract all text spans in single pass
            spans = self.extract_text_spans(pdf_path)
            if not spans:
                return {"title": "Empty Document", "outline": []}

            # Analyze font patterns
            font_stats = self.analyze_font_statistics(spans)

            # Get page height for position scoring
            doc = fitz.open(pdf_path)
            page_height = doc[0].rect.height if len(doc) > 0 else 800
            doc.close()

            # Score and classify headings
            outline = []
            for span in spans:
                score = self.score_heading_candidate(span, font_stats, page_height)
                level = self.classify_heading_level(score)

                if level:
                    outline.append({
                        "level": level,
                        "text": span.text.strip(),
                        "page": span.page_num + 1  # Convert to 1-indexed
                    })

            # Detect document title
            title = self.detect_title(pdf_path, spans)

            return {
                "title": title,
                "outline": outline
            }

        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {e}")
            return {"title": "Error Processing", "outline": []}
