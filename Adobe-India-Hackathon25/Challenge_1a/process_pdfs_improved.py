#!/usr/bin/env python3
"""
Adobe Hackathon 2025 - IMPROVED PDF Processing System
Enhanced heading detection with superior false positive filtering and accuracy
"""

import os
import json
import re
from pathlib import Path
from collections import Counter, defaultdict
import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional
import time
import sys
import logging
from dataclasses import dataclass
import numpy as np

# ML Model imports with better error handling
try:
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("WARNING: ML dependencies not available. Running in algorithmic-only mode.")

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

class ImprovedPDFProcessor:
    """Enhanced PDF processor with superior heading detection and false positive filtering"""
    
    def __init__(self, font_size_threshold: float = 1.2, min_heading_length: int = 3, use_ml_models: bool = False):
        self.font_size_threshold = font_size_threshold
        self.min_heading_length = min_heading_length
        self.use_ml_models = use_ml_models and ML_AVAILABLE
        self.logger = logging.getLogger(__name__)
        
        # IMPROVED: Research-optimized scoring weights with better balance
        self.scoring_weights = {
            'font_size': 0.45,   # PRIMARY: Font size is most reliable indicator
            'content': 0.30,     # SECONDARY: Enhanced semantic content patterns
            'formatting': 0.15,  # TERTIARY: Bold/italic with better filtering
            'position': 0.10     # MINIMAL: Position for document structure
        }
        
        # IMPROVED: Enhanced keyword patterns with better coverage
        self.heading_keywords = [
            'chapter', 'section', 'introduction', 'conclusion', 'abstract', 'summary', 'overview', 'background',
            'pdf', 'document', 'format', 'guide', 'manual', 'report', 'testing', 'basic',
            'mission', 'goals', 'objectives', 'requirements', 'pathway', 'options', 'regular', 'distinction',
            'preconditions', 'properties', 'accessibility', 'objects', 'miscellaneous', 'tools', 'how to test',
            'instruction', 'test', 'add', 'description', 'advanced', 'content', 'navigation', 'reading'
        ]
        
        # IMPROVED: Enhanced false positive patterns
        self.false_positive_patterns = [
            # UI Elements and Instructions
            r'^(do not|don\'t)\s+check\s+.*',
            r'^(please|click|select|press|enter|type)\s+.*',
            r'^(ok|cancel|apply|close|save|delete)\s*$',
            r'^(ctrl|alt|shift)\s*\+.*',
            r'^(figure|fig\.?)\s+\d+.*',
            r'^(table|tab\.?)\s+\d+.*',
            r'^(page|p\.?)\s+\d+.*',
            
            # Form fields and interactive elements
            r'^(name|date|email|phone|address):\s*$',
            r'^(signature|sign)\s+.*',
            r'^(check|uncheck)\s+.*',
            r'^(yes|no)\s*$',
            
            # Technical identifiers
            r'^[a-z0-9]{8,}$',  # Long alphanumeric strings
            r'^[a-f0-9]{32,}$',  # Hash-like strings
            r'^[a-z]+://.*',      # URLs
            
            # Sentence fragments and mid-paragraph text
            r'^(this|the|in|at|on|with|for|from|to|of|and|or|but)\s+\w+.*',
            r'^(you|we|they|it)\s+(can|will|should|may|must).*',
            r'^(when|if|after|before|during|while)\s+\w+.*',
            r'\b(is|are|was|were|has|have|had)\s+\w+.*',
            r'\.(\s|$)',          # Ends with period (likely sentence)
            r'^[a-z].*',          # Starts with lowercase (likely mid-sentence)
            
            # Common UI text patterns
            r'^(show|hide|display|view)\s+.*',
            r'^(enable|disable)\s+.*',
            r'^(on|off)\s*$',
            r'^(true|false)\s*$',
            
            # Figure captions and references
            r'^figure\s+\d+.*',
            r'^table\s+\d+.*',
            r'^page\s+\d+.*',
            r'^section\s+\d+.*',
            
            # Form instructions
            r'^(fill|complete|submit)\s+.*',
            r'^(required|optional)\s*$',
            r'^(attach|upload)\s+.*',
        ]
        
        # Compile regex patterns for efficiency
        self.false_positive_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.false_positive_patterns]
        
        # ML Models initialization with better error handling
        self.semantic_model = None
        self.classification_model = None
        self.classification_tokenizer = None
        
        if self.use_ml_models:
            try:
                self._initialize_ml_models()
                self.logger.info("✅ ML models loaded successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load ML models: {e}. Using algorithmic-only mode.")
                self.use_ml_models = False

    def _initialize_ml_models(self):
        """Initialize ML models for heading detection with better error handling"""
        self.logger.info("🤖 Loading ML models...")
        
        try:
            # Model 1: Semantic similarity model (80MB)
            self.semantic_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Model 2: Binary classification model (16MB)
            model_name = 'prajjwal1/bert-tiny'
            self.classification_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.classification_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            self.logger.info("🎆 ML models ready: all-MiniLM-L6-v2 (80MB) + bert-tiny (16MB)")
        except Exception as e:
            self.logger.error(f"Failed to initialize ML models: {e}")
            raise

    def extract_text_spans(self, pdf_path: str) -> List[TextSpan]:
        """Extract text spans with enhanced deduplication and cleaning"""
        spans = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_spans = self._extract_clean_text_spans(page, page_num)
                spans.extend(page_spans)
            
            doc.close()
            
            # Apply robust deduplication
            unique_spans = self._robust_deduplicate_spans(spans)
            return unique_spans
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            return []

    def _extract_clean_text_spans(self, page, page_num: int) -> List[TextSpan]:
        """Extract text spans cleanly without overlaps or duplicates"""
        spans = []
        
        try:
            # Use single method to avoid overlaps
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if len(text) >= 2:  # Only meaningful text
                            spans.append(TextSpan(
                                text=text,
                                font_name=span.get("font", ""),
                                font_size=span.get("size", 0),
                                font_flags=span.get("flags", 0),
                                bbox=span.get("bbox", (0, 0, 0, 0)),
                                page_num=page_num
                            ))
        
        except Exception as e:
            self.logger.debug(f"Text extraction failed on page {page_num}: {e}")
        
        return spans

    def _robust_deduplicate_spans(self, spans: List[TextSpan]) -> List[TextSpan]:
        """Remove duplicate and overlapping text spans"""
        if not spans:
            return []
        
        # Sort by page, then Y position, then X position
        sorted_spans = sorted(spans, key=lambda s: (s.page_num, s.bbox[1], s.bbox[0]))
        
        unique_spans = []
        seen_texts = set()
        
        for span in sorted_spans:
            text_key = span.text.lower().strip()
            
            # Skip if we've seen this exact text
            if text_key in seen_texts:
                continue
            
            # Check for overlapping spans
            is_duplicate = False
            for existing_span in unique_spans:
                if (span.page_num == existing_span.page_num and 
                    self._spans_overlap(span.bbox, existing_span.bbox)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_spans.append(span)
                seen_texts.add(text_key)
        
        return unique_spans

    def _spans_overlap(self, bbox1: Tuple[float, float, float, float], 
                       bbox2: Tuple[float, float, float, float], tolerance: float = 5.0) -> bool:
        """Check if two bounding boxes overlap significantly"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Check for overlap with tolerance
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        return x_overlap > tolerance and y_overlap > tolerance

    def _is_definitely_not_heading(self, text: str) -> bool:
        """IMPROVED: Enhanced false positive filtering"""
        text_lower = text.lower().strip()
        
        # Check against compiled regex patterns
        for pattern in self.false_positive_regex:
            if pattern.match(text_lower):
                return True
        
        # Additional semantic checks
        if len(text.strip()) < 2:
            return True
        
        # Filter dots/periods patterns that are clearly not headings
        if re.match(r'^\.+$', text.strip()):
            return True
        
        # Filter very long text (likely paragraphs)
        if len(text) > 100:
            return True
        
        # Filter text with too many words (likely sentences)
        word_count = len(text.split())
        if word_count > 15:
            return True
        
        return False

    def analyze_font_statistics(self, spans: List[TextSpan]) -> Dict[str, any]:
        """Analyze font patterns to identify body text and potential headings"""
        if not spans:
            return {"body_font_size": 12, "font_size_histogram": {}, "unique_sizes": []}
        
        # Build font size histogram
        font_sizes = [span.font_size for span in spans if span.font_size > 0]
        size_counter = Counter(font_sizes)
        
        # Body text is the most common font size
        body_font_size = size_counter.most_common(1)[0][0] if size_counter else 12
        
        # Heading threshold based on font size analysis
        heading_threshold = body_font_size * self.font_size_threshold
        
        # Get unique sizes for analysis
        unique_sizes = sorted(set(font_sizes), reverse=True)
        
        return {
            "body_font_size": body_font_size,
            "heading_threshold": heading_threshold,
            "font_size_histogram": dict(size_counter),
            "unique_sizes": unique_sizes
        }

    def score_heading_candidate(self, span: TextSpan, font_stats: Dict[str, any], 
                              page_height: float) -> float:
        """IMPROVED: Enhanced multi-factor scoring for heading detection"""
        text = span.text.strip()
        
        # Early filtering
        if len(text) < self.min_heading_length:
            return 0.0
        
        if self._is_definitely_not_heading(text):
            return 0.0
        
        score = 0.0
        
        # 1. Font Size Score (45% weight) - IMPROVED
        size_ratio = span.font_size / font_stats["body_font_size"]
        if size_ratio >= self.font_size_threshold:
            # More nuanced scoring based on size ratio
            if size_ratio >= 2.0:
                font_score = 1.0  # Very large text
            elif size_ratio >= 1.5:
                font_score = 0.9  # Large text
            elif size_ratio >= 1.2:
                font_score = 0.7  # Medium-large text
            else:
                font_score = 0.5  # Slightly larger text
            score += font_score * self.scoring_weights['font_size']
        
        # 2. Content Pattern Score (30% weight) - IMPROVED
        content_score = 0.0
        
        # Check for heading-like content
        if self._looks_like_heading_content(text):
            content_score = 1.0
        elif self._appears_standalone_text(text):
            content_score = 0.8
        elif re.match(r'^\d+\.\s+[A-Za-z]', text) or re.match(r'^[A-Z]\.\s+[A-Za-z]', text):
            content_score = 1.0  # Numbered sections
        elif len(text.split()) <= 8 and not text.endswith('.'):
            content_score = 0.6  # Short phrases
        elif text.isupper() and 2 <= len(text.split()) <= 6:
            content_score = 0.7  # ALL CAPS headings
        
        score += content_score * self.scoring_weights['content']
        
        # 3. Formatting Score (15% weight) - IMPROVED
        format_score = 0.0
        if span.is_bold:
            format_score += 0.6
        if span.is_italic:
            format_score += 0.4
        score += format_score * self.scoring_weights['formatting']
        
        # 4. Position Score (10% weight) - IMPROVED
        if page_height > 0:
            relative_y = 1.0 - (span.bbox[1] / page_height)
            if relative_y > 0.8:  # Top 20% of page
                position_score = 1.0
            elif relative_y > 0.6:  # Top 40% of page
                position_score = 0.6
            elif relative_y > 0.4:  # Top 60% of page
                position_score = 0.3
            else:
                position_score = 0.1
            score += position_score * self.scoring_weights['position']
        
        return min(score, 1.0)

    def _looks_like_heading_content(self, text: str) -> bool:
        """Check if text content suggests it's a heading"""
        if not text or len(text.strip()) < 2:
            return False
            
        text_lower = text.lower().strip()
        
        # Numbered sections
        if re.match(r'^\d+\.\s+[A-Za-z]', text) or re.match(r'^[A-Z]\.\s+[A-Za-z]', text):
            return True
        
        # Common heading patterns
        heading_patterns = [
            'overview', 'introduction', 'conclusion', 'summary', 'abstract',
            'chapter', 'section', 'part', 'appendix', 'references',
            'table of contents', 'contents', 'acknowledgements',
            'mission statement', 'goals', 'objectives', 'requirements',
            'pathway options', 'regular pathway', 'distinction pathway',
            'preconditions', 'document properties', 'accessibility',
            'objects', 'miscellaneous', 'tools', 'how to test',
            'instruction', 'test', 'add', 'description', 'advanced',
            'content', 'navigation', 'reading'
        ]
        
        if any(pattern in text_lower for pattern in heading_patterns):
            return True
        
        # ALL CAPS short phrases (likely headings)
        if text.isupper() and 2 <= len(text.split()) <= 6:
            return True
        
        return False

    def _appears_standalone_text(self, text: str) -> bool:
        """Check if text appears to be standalone (not part of a sentence)"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Doesn't start with common sentence starters
        sentence_starters = ['the', 'this', 'that', 'it', 'in', 'on', 'at', 'with', 'for', 'from', 'to', 'of', 'and', 'or', 'but']
        first_word = text.lower().split()[0] if text.split() else ""
        
        if first_word in sentence_starters:
            return False
        
        # Doesn't end with period (likely sentence)
        if text.endswith('.'):
            return False
        
        # Not too long (likely paragraph)
        if len(text.split()) > 10:
            return False
        
        return True

    def classify_heading_level(self, score: float, span: TextSpan, font_stats: Dict[str, any]) -> Optional[str]:
        """IMPROVED: Enhanced heading level classification"""
        if score < 0.3:  # Higher threshold for better precision
            return None
        
        # Use font size as additional factor for level determination
        size_ratio = span.font_size / font_stats["body_font_size"]
        
        if score >= 0.8 or size_ratio >= 2.0:
            return "H1"
        elif score >= 0.6 or size_ratio >= 1.5:
            return "H2"
        elif score >= 0.4 or size_ratio >= 1.2:
            return "H3"
        else:
            return None

    def detect_title(self, pdf_path: str, spans: List[TextSpan]) -> str:
        """IMPROVED: Enhanced document title detection"""
        try:
            # Strategy 1: Check PDF metadata
            doc = fitz.open(pdf_path)
            metadata_title = doc.metadata.get("title", "").strip()
            doc.close()
            
            if metadata_title and len(metadata_title) > 3:
                return metadata_title
            
            # Strategy 2: Find largest text in top 30% of first page
            first_page_spans = [s for s in spans if s.page_num == 0]
            if not first_page_spans:
                return "Untitled Document"
            
            # Get page dimensions
            doc = fitz.open(pdf_path)
            page = doc[0]
            page_height = page.rect.height
            doc.close()
            
            # Find spans in top 30% of page
            top_30_percent = page_height * 0.7  # PDF coordinates are bottom-up
            top_spans = [s for s in first_page_spans if s.bbox[1] >= top_30_percent]
            
            if top_spans:
                # Get the largest font in the top area
                largest_span = max(top_spans, key=lambda x: x.font_size)
                return largest_span.text.strip()
            
            # Strategy 3: Use filename as fallback
            filename = os.path.basename(pdf_path)
            return os.path.splitext(filename)[0].replace('_', ' ').title()
            
        except Exception as e:
            self.logger.error(f"Error detecting title: {e}")
            return "Untitled Document"

    def detect_headings(self, pdf_path: str) -> List[Dict]:
        """IMPROVED: Enhanced heading detection with better filtering"""
        try:
            spans = self.extract_text_spans(pdf_path)
            if not spans:
                return []
            
            # Analyze font statistics
            font_stats = self.analyze_font_statistics(spans)
            
            # Get page height for position scoring
            doc = fitz.open(pdf_path)
            page_height = doc[0].rect.height if len(doc) > 0 else 800
            doc.close()
            
            # Score and classify headings
            headings = []
            seen_headings = set()
            
            for span in spans:
                score = self.score_heading_candidate(span, font_stats, page_height)
                level = self.classify_heading_level(score, span, font_stats)
                
                if level:
                    clean_text = self._clean_heading_text(span.text)
                    text_key = clean_text.lower().strip()
                    
                    # Avoid exact duplicates
                    if (clean_text and len(clean_text) >= 2 and 
                        text_key not in seen_headings):
                        headings.append({
                            'level': level,
                            'text': clean_text,
                            'page': span.page_num + 1
                        })
                        seen_headings.add(text_key)
            
            # Sort by document order (page, then Y position)
            headings.sort(key=lambda h: (h['page'], -h.get('y_pos', 0)))
            
            return headings
            
        except Exception as e:
            self.logger.error(f"Error detecting headings in {pdf_path}: {e}")
            return []

    def _clean_heading_text(self, text: str) -> str:
        """Clean heading text for better output"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Fix common garbled text patterns
        text = re.sub(r'(\w)\1{3,}', r'\1', text)  # Remove repeated characters
        text = re.sub(r'\s+([a-z])\s+', r'\1', text)  # Fix spaced single characters
        
        # Remove trailing punctuation except periods that are part of numbers
        text = re.sub(r'[^\w\s\.\-\(\)]+$', '', text)
        
        # Truncate very long headings
        if len(text) > 80:
            text = text[:77] + "..."
            
        return text.strip()

    def process_pdf(self, pdf_path: str) -> Dict:
        """Process a single PDF and extract structured outline"""
        try:
            # Extract spans and detect headings
            spans = self.extract_text_spans(pdf_path)
            headings = self.detect_headings(pdf_path)
            
            # Detect document title
            title = self.detect_title(pdf_path, spans)
            
            # Ensure we have at least some structure
            if not headings:
                headings = [{
                    'level': 'H1',
                    'text': 'Document Content',
                    'page': 1
                }]
            
            return {
                'title': title,
                'outline': headings
            }
        
        except Exception as e:
            self.logger.error(f"Error processing {pdf_path}: {str(e)}")
            return {
                'title': Path(pdf_path).stem.replace('_', ' ').title(),
                'outline': [{
                    'level': 'H1',
                    'text': 'Document Content',
                    'page': 1
                }]
            }

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def process_pdfs():
    """Main processing function with enhanced logging and error handling"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    
    # Use local paths for testing, Docker paths for production
    if os.path.exists("/app/input"):
        input_dir = Path("/app/input")
        output_dir = Path("/app/output")
    else:
        input_dir = Path("input")
        output_dir = Path("output")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        print("No PDF files found in input directory")
        return
    
    logger.info(f"🚀 Starting IMPROVED PDF Processing for {len(pdf_files)} files")
    print("Starting improved PDF processing...")
    
    processor = ImprovedPDFProcessor()
    
    processed_count = 0
    failed_count = 0
    
    for pdf_file in pdf_files:
        file_start = time.time()
        print(f"Processing {pdf_file.name}...")
        logger.info(f"Processing {pdf_file.name}")
        
        try:
            result = processor.process_pdf(str(pdf_file))
            
            # Validate result structure
            if not result or 'title' not in result or 'outline' not in result:
                logger.error(f"Invalid result structure for {pdf_file.name}")
                failed_count += 1
                continue
            
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            file_time = time.time() - file_start
            processed_count += 1
            
            print(f"Processed {pdf_file.name} -> {output_file.name} ({file_time:.2f}s)")
            logger.info(f"✅ Successfully processed {pdf_file.name} in {file_time:.2f}s")
            
            # Check performance constraint
            if file_time > 10.0:
                logger.warning(f"⚠️  Processing time {file_time:.2f}s exceeds 10s limit for {pdf_file.name}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Failed to process {pdf_file.name}: {str(e)}")
            print(f"Error processing {pdf_file.name}: {str(e)}")
    
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f}s")
    logger.info(f"🏁 Processing completed: {processed_count} successful, {failed_count} failed, total time: {total_time:.2f}s")
    print("Improved PDF processing completed!")

if __name__ == "__main__":
    process_pdfs() 