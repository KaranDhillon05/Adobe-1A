#!/usr/bin/env python3
"""
Enhanced PDF Processor with Fine-Tuned Models
Adobe India Hackathon 2025 - Challenge 1A

Combines statistical analysis with fine-tuned ML models for maximum accuracy
"""

import fitz
import json
import os
import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TextSpan:
    """Represents a text span from PDF"""
    text: str
    page: int
    font_size: float
    font_name: str
    bbox: tuple
    is_bold: bool = False
    is_italic: bool = False

@dataclass
class HeadingCandidate:
    """Represents a heading candidate with all scores"""
    span: TextSpan
    statistical_score: float
    semantic_score: float
    bert_score: float
    combined_score: float
    confidence: float

class TrainedPDFProcessor:
    """PDF processor using fine-tuned models + statistical analysis"""
    
    def __init__(self, 
                 bert_model_path: str = "models/bert_heading_classifier",
                 semantic_model_path: str = "models/semantic_heading_model",
                 use_trained_models: bool = True):
        
        self.use_trained_models = use_trained_models
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        
        # Statistical analysis parameters (proven effective)
        self.font_size_threshold = 1.15
        self.min_heading_length = 2
        self.max_heading_length = 150
        
        # Model weights for combination (prioritize statistical analysis)
        self.weights = {
            'statistical': 0.7,  # Base statistical analysis - most reliable
            'semantic': 0.2,     # Fine-tuned semantic similarity
            'bert': 0.1         # Fine-tuned BERT classification
        }
        
        # Initialize models
        self.bert_model = None
        self.bert_tokenizer = None
        self.semantic_model = None
        self.heading_embeddings = None
        
        if self.use_trained_models:
            self._load_trained_models(bert_model_path, semantic_model_path)
        
        # False positive patterns - targeted approach
        self.false_positive_patterns = [
            r'^https?://',
            r'^www\.',
            r'@\w+\.\w+',
            r'^\d{4}-\d{2}-\d{2}',
            r'^[A-F0-9]{8,}$',
            r'^[^\w\s]+$',
            r'^\d+\s*$',  # Only pure numbers, not "1. Name"
            r'^\.(pdf|tex|doc|docx)$',  # File extensions
            r'^(huge|tiny|small|large|normal)$',  # Size descriptors
            r'^(the|and|for|with|from|into|over|under)$',  # Common prepositions
            r'^\w{1,2}$'  # Very short words (except important ones)
        ]
        
        # Heading patterns - EXPANDED for better detection
        self.heading_patterns = [
            r'^\d+\.\s+[A-Z]',  # "1. Name of Government" - most specific first
            r'^\d+\.\s+',       # "1. Name of Government" - broader match
            r'^\d+\s+[A-Z]',    # "1 Template" - with capital letter
            r'^\d+\s+',         # "1 Template" - broader match
            r'^\d+\.\d+',       # "1.1 How to compile"
            r'^(Chapter|Section)\s+\d+',
            r'^[A-Z][A-Z\s]{2,20}$',  # ALL CAPS
            r'^[A-Z][a-z]+\s+[A-Z]',  # Title Case
            r'^(Introduction|Conclusion|Summary|Abstract|References|Bibliography|Contents|Template|Overview|Background|Methodology|Results|Discussion|Appendix)$',
            r'^(Timeline|Summary|Milestones|Approach)$',
            r'^(Application\s+form|Request\s+for|Business\s+Plan|Revision\s+History|Table\s+of\s+Contents|Name\s+of|Designation|Whether|Amount\s+of)'
        ]

    def _load_trained_models(self, bert_path: str, semantic_path: str):
        """Load fine-tuned models"""
        try:
            # Load fine-tuned BERT model
            if Path(bert_path).exists():
                logger.info(f"Loading fine-tuned BERT model from {bert_path}")
                self.bert_tokenizer = AutoTokenizer.from_pretrained(bert_path)
                self.bert_model = AutoModelForSequenceClassification.from_pretrained(bert_path)
                self.bert_model.to(self.device)
                self.bert_model.eval()
                logger.info("✅ Fine-tuned BERT model loaded")
            else:
                logger.warning(f"BERT model not found at {bert_path}, using base model")
                self.bert_tokenizer = AutoTokenizer.from_pretrained('prajjwal1/bert-tiny')
                self.bert_model = AutoModelForSequenceClassification.from_pretrained('prajjwal1/bert-tiny')
                self.bert_model.to(self.device)
            
            # Load fine-tuned semantic model
            if Path(semantic_path).exists():
                logger.info(f"Loading enhanced semantic model from {semantic_path}")
                self.semantic_model = SentenceTransformer(semantic_path)
                logger.info("✅ Enhanced semantic model loaded")
            else:
                logger.warning(f"Semantic model not found at {semantic_path}, using base model")
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create reference heading embeddings
            reference_headings = [
                "Introduction", "Chapter", "Section", "Summary", "Conclusion",
                "Overview", "Background", "Methodology", "Results", "Discussion",
                "Abstract", "References", "Appendix", "Table of Contents"
            ]
            self.heading_embeddings = self.semantic_model.encode(reference_headings)
            
        except Exception as e:
            logger.error(f"Error loading trained models: {e}")
            logger.warning("Falling back to statistical analysis only")
            self.use_trained_models = False

    def extract_text_spans(self, pdf_path: str) -> List[TextSpan]:
        """Extract text spans from PDF with proper line and span merging"""
        spans = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                for block in blocks["blocks"]:
                    if "lines" in block:
                        # Process each line and merge spans within lines
                        for line in block["lines"]:
                            line_text_parts = []
                            line_spans = []
                            
                            # Collect all spans in this line
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text:  # Include all non-empty text
                                    line_text_parts.append(text)
                                    line_spans.append(span)
                            
                            # Merge spans within the same line
                            if line_text_parts and line_spans:
                                merged_text = " ".join(line_text_parts).strip()
                                if len(merged_text) >= self.min_heading_length:
                                    # Use the first span's properties for the merged text
                                    first_span = line_spans[0]
                                    last_span = line_spans[-1]
                                    
                                    # Create a bbox that encompasses the entire line
                                    merged_bbox = (
                                        first_span["bbox"][0],  # leftmost x
                                        first_span["bbox"][1],  # top y
                                        last_span["bbox"][2],   # rightmost x
                                        last_span["bbox"][3]    # bottom y
                                    )
                                    
                                    spans.append(TextSpan(
                                        text=merged_text,
                                        page=page_num + 1,
                                        font_size=first_span["size"],
                                        font_name=first_span["font"],
                                        bbox=merged_bbox,
                                        is_bold="Bold" in first_span["font"],
                                        is_italic="Italic" in first_span["font"]
                                    ))
                
                # Enhanced table extraction for structured content with better multi-line handling
                try:
                    tables = page.find_tables()
                    for table_idx, table in enumerate(tables):
                        table_bbox = table.bbox
                        table_data = table.extract()
                        
                        for row_idx, row in enumerate(table_data):
                            for col_idx, cell in enumerate(row):
                                if cell and isinstance(cell, str):
                                    # More aggressive multi-line cell text merging
                                    cell_text = cell.strip()
                                    if not cell_text:
                                        continue
                                    
                                    # Handle multi-line content better - normalize all whitespace
                                    # This handles cases where text spans multiple lines in table cells
                                    cell_text = " ".join(cell_text.split())
                                    
                                    # Only skip if actually too short
                                    if len(cell_text) < self.min_heading_length:
                                        continue
                                    
                                    # More conservative duplicate checking - only skip exact matches
                                    is_duplicate = False
                                    for existing_span in spans:
                                        if existing_span.page == page_num + 1:
                                            existing_text = existing_span.text.strip()
                                            # Only skip if we have the exact same text
                                            if existing_text.lower() == cell_text.lower():
                                                is_duplicate = True
                                                break
                                    
                                    if not is_duplicate:
                                        # Better positioning within table
                                        cell_x = table_bbox[0] + (col_idx * (table_bbox[2] - table_bbox[0]) / max(len(row), 1))
                                        cell_y = table_bbox[1] + (row_idx * (table_bbox[3] - table_bbox[1]) / max(len(table_data), 1))
                                        
                                        cell_bbox = (cell_x, cell_y, cell_x + 100, cell_y + 15)
                                        
                                        spans.append(TextSpan(
                                            text=cell_text,
                                            page=page_num + 1,
                                            font_size=11.0,
                                            font_name="table-cell",
                                            bbox=cell_bbox,
                                            is_bold=False,
                                            is_italic=False
                                        ))
                        
                        logger.info(f"Extracted {len([r for r in table_data if any(c for c in r if c)])} table rows from page {page_num + 1}")
                        
                except Exception as e:
                    logger.warning(f"Table extraction failed for page {page_num + 1}: {e}")
            
            # Remove duplicates but keep all reasonable candidates
            spans = self._remove_duplicate_spans(spans)
            
            doc.close()
            logger.info(f"Extracted {len(spans)} text spans from {pdf_path}")
            return spans
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return []
    
    def _extract_table_text(self, page, page_num):
        """Extract text from tables with proper multi-line cell handling"""
        table_spans = []
        try:
            tables = page.find_tables()
            for table in tables:
                table_data = table.extract()
                for row_idx, row in enumerate(table_data):
                    for col_idx, cell in enumerate(row):
                        if cell and isinstance(cell, str):
                            cell_text = cell.strip()
                            # Clean up cell text and handle multi-line content
                            cell_text = " ".join(cell_text.split())  # Normalize whitespace
                            if len(cell_text) >= self.min_heading_length:
                                # Create a bbox estimate for table cells
                                cell_bbox = (col_idx * 100, row_idx * 20, (col_idx + 1) * 100, (row_idx + 1) * 20)
                                table_spans.append(TextSpan(
                                    text=cell_text,
                                    page=page_num,
                                    font_size=12.0,
                                    font_name="table",
                                    bbox=cell_bbox,
                                    is_bold=False,
                                    is_italic=False
                                ))
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        return table_spans
    
    def _merge_close_lines(self, block_lines):
        """Merge lines that are close together (likely multi-line headings)"""
        if len(block_lines) <= 1:
            return block_lines
        
        merged = []
        current_text = block_lines[0][0]
        current_span = block_lines[0][1]
        
        for i in range(1, len(block_lines)):
            line_text, line_span = block_lines[i]
            
            # Check if this line seems to continue the previous one
            if (len(current_text) < 100 and  # Don't merge very long lines
                not current_text.endswith('.') and  # Don't merge after periods
                len(line_text) < 80):  # Don't merge very long continuation
                
                current_text += " " + line_text
            else:
                # Start a new merged line
                merged.append((current_text, current_span))
                current_text = line_text
                current_span = line_span
        
        # Add the last merged line
        merged.append((current_text, current_span))
        return merged
    
    def _remove_duplicate_spans(self, spans):
        """Remove duplicate spans, keeping the longer/more complete ones"""
        if not spans:
            return spans
        
        # Sort by text length (longest first) to prefer complete text
        spans.sort(key=lambda x: len(x.text), reverse=True)
        
        unique_spans = []
        seen_texts = set()
        
        for span in spans:
            text_key = span.text.lower().strip()
            
            # Skip if we've seen this exact text
            if text_key in seen_texts:
                continue
            
            # Check if this is a substring of existing text
            is_substring = False
            for existing_text in seen_texts:
                if text_key in existing_text and len(text_key) < len(existing_text) * 0.7:
                    is_substring = True
                    break
            
            if not is_substring:
                # Remove any existing texts that are substrings of this one
                texts_to_remove = [t for t in seen_texts if t in text_key and len(t) < len(text_key) * 0.7]
                for text in texts_to_remove:
                    seen_texts.remove(text)
                    # Also remove corresponding spans
                    unique_spans = [s for s in unique_spans if s.text.lower().strip() != text]
                
                unique_spans.append(span)
                seen_texts.add(text_key)
        
        return unique_spans
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # Check if one is substring of another
        if text1 in text2 or text2 in text1:
            return 0.8
        
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

    def calculate_statistical_score(self, span: TextSpan, median_font_size: float) -> float:
        """Calculate statistical score using proven method"""
        
        text = span.text.strip()
        
        # Font size component (40% weight) - FIXED to be more lenient
        font_ratio = span.font_size / median_font_size if median_font_size > 0 else 1.0
        # Accept fonts that are 10% larger than median (was 100% larger)
        font_score = min(max((font_ratio - 1.0) * 2.0, 0.0), 1.0) if font_ratio > 1.1 else 0.0
        
        # Content component (35% weight) - balanced approach
        content_score = 0.0
        
        # Strong patterns get high scores
        if any(re.match(pattern, text, re.IGNORECASE) for pattern in self.heading_patterns):
            content_score += 0.8
        
        # Title case or upper case - strong indicators (but not single words)
        if (text.istitle() or text.isupper()) and len(text.split()) > 1:
            content_score += 0.5
        elif text.istitle() or text.isupper():
            content_score += 0.3
            
        # Starts with number - very likely heading (improved pattern)
        if re.match(r'^\d+\.\s+[A-Z]', text):  # "1. Name of Government"
            content_score += 0.9
        elif re.match(r'^\d+[\.\s]', text):
            content_score += 0.7
            
        # Reasonable length for headings
        word_count = len(text.split())
        if 2 <= word_count <= 8:
            content_score += 0.4
        elif word_count == 1 and len(text) > 3:  # Single meaningful words
            content_score += 0.2
        elif word_count > 8:
            content_score -= 0.2  # Penalize very long text
            
        # Common heading words
        if any(word in text.lower() for word in ['chapter', 'section', 'introduction', 'conclusion', 'summary', 'overview', 'background', 'template', 'contents', 'references', 'appendix', 'methodology']):
            content_score += 0.6
            
        # Ends with colon (like "Timeline:")
        if text.endswith(':'):
            content_score += 0.4
            
        content_score = min(content_score, 1.0)
        
        # Formatting component (15% weight)
        format_score = 0.0
        if span.is_bold:
            format_score += 0.5
        if span.is_italic:
            format_score += 0.2
        if text.endswith(':'):
            format_score += 0.3
        format_score = min(format_score, 1.0)
        
        # Position component (10% weight)
        position_score = 0.3  # Default reasonable score
        
        # Combine scores
        final_score = (
            font_score * 0.4 +
            content_score * 0.35 +
            format_score * 0.15 +
            position_score * 0.10
        )
        
        # Apply penalties for false positives
        if any(re.match(pattern, text, re.IGNORECASE) for pattern in self.false_positive_patterns):
            final_score *= 0.05  # Strong penalty for clear false positives
        
        # Additional quality checks
        if len(text.split()) > 12:  # Very long text unlikely to be heading
            final_score *= 0.3
        
        # Penalize very short single-character or two-character words unless they're meaningful
        if len(text) <= 2 and text.lower() not in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'a', 'b', 'c']:
            final_score *= 0.2
            
        # Boost score for numbered sections
        if re.match(r'^\d+\.\s+[A-Z]', text):
            final_score *= 1.3
        
        return min(max(final_score, 0.0), 1.0)

    def calculate_semantic_score(self, text: str) -> float:
        """Calculate semantic similarity score using enhanced model"""
        if not self.semantic_model or self.heading_embeddings is None:
            return 0.0
        
        try:
            # Get text embedding
            text_embedding = self.semantic_model.encode([text])
            
            # Calculate similarities with reference headings
            similarities = cosine_similarity(text_embedding, self.heading_embeddings)[0]
            
            # Return maximum similarity
            return float(np.max(similarities))
            
        except Exception as e:
            logger.warning(f"Error calculating semantic score for '{text}': {e}")
            return 0.0

    def calculate_bert_score(self, text: str) -> float:
        """Calculate BERT classification score using fine-tuned model"""
        if not self.bert_model or not self.bert_tokenizer:
            return 0.0
        
        try:
            # Tokenize text
            inputs = self.bert_tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=128,
                return_tensors='pt'
            ).to(self.device)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)
                heading_probability = probabilities[0][1].item()  # Class 1 = heading
            
            return heading_probability
            
        except Exception as e:
            logger.warning(f"Error calculating BERT score for '{text}': {e}")
            return 0.0

    def score_heading_candidates(self, spans: List[TextSpan]) -> List[HeadingCandidate]:
        """Score all text spans as potential headings"""
        
        # Calculate median font size
        font_sizes = [span.font_size for span in spans]
        median_font_size = np.median(font_sizes) if font_sizes else 12.0
        
        candidates = []
        
        for span in spans:
            # Calculate individual scores
            statistical_score = self.calculate_statistical_score(span, median_font_size)
            
            semantic_score = 0.0
            bert_score = 0.0
            
            if self.use_trained_models:
                semantic_score = self.calculate_semantic_score(span.text)
                bert_score = self.calculate_bert_score(span.text)
            
            # Combine scores using weighted average
            combined_score = (
                statistical_score * self.weights['statistical'] +
                semantic_score * self.weights['semantic'] +
                bert_score * self.weights['bert']
            )
            
            # Calculate confidence based on agreement between methods
            score_variance = np.var([statistical_score, semantic_score, bert_score])
            confidence = 1.0 - min(score_variance, 1.0)  # Higher agreement = higher confidence
            
            candidate = HeadingCandidate(
                span=span,
                statistical_score=statistical_score,
                semantic_score=semantic_score,
                bert_score=bert_score,
                combined_score=combined_score,
                confidence=confidence
            )
            
            candidates.append(candidate)
        
        return candidates

    def filter_and_rank_headings(self, candidates: List[HeadingCandidate], 
                                threshold: float = 0.35) -> List[HeadingCandidate]:
        """Filter and rank heading candidates"""
        
        # Filter by combined score threshold
        filtered_candidates = [c for c in candidates if c.combined_score > threshold]
        
        # Remove duplicates (same text, different pages)
        seen_texts = set()
        unique_candidates = []
        for candidate in filtered_candidates:
            text_key = candidate.span.text.lower().strip()
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_candidates.append(candidate)
        
        # Sort by page number first, then by vertical position (top to bottom)
        unique_candidates.sort(key=lambda x: (x.span.page, x.span.bbox[1]))
        
        logger.info(f"Filtered to {len(unique_candidates)} heading candidates")
        return unique_candidates

    def assign_heading_levels(self, candidates: List[HeadingCandidate]) -> List[Dict[str, Any]]:
        """Assign heading levels based on scores and structure"""
        
        outline = []
        last_level = "H4"
        
        for i, candidate in enumerate(candidates):
            text = candidate.span.text
            score = candidate.combined_score
            
            # Simplified and consistent heading level assignment
            level = "H4"  # Default
            text_clean = text.strip()
            
            # H1: Document titles only (should be unique per document)
            if (candidate.span.page == 1 and 
                (any(word in text_clean.lower() for word in ['application form', 'document', 'report', 'guide', 'manual']) or
                 (len(text_clean.split()) >= 4 and not re.match(r'^\d+\.', text_clean)))):
                level = "H1"
            
            # H2: Main numbered sections (1., 2., 3., etc.) - consistent level for all
            elif re.match(r'^\d{1,2}\.\s+[A-Za-z]', text_clean):  # "1. Name of Government Servant"
                level = "H2"
            
            # H2: Major sections without numbers but important content
            elif (score > 0.6 and 
                  any(word in text_clean.lower() for word in ['overview', 'introduction', 'conclusion', 'summary', 'background', 'amount of advance'])):
                level = "H2"
            
            # H3: Sub-sections, table headers, field labels
            elif (re.match(r'^\d+\.\d+', text_clean) or  # "1.1 Subsection"
                  text_clean.istitle() or
                  text_clean.endswith(':') or
                  (len(text_clean.split()) <= 3 and len(text_clean) > 8) or  # Short descriptive text
                  any(word in text_clean.lower() for word in ['name', 'age', 'designation', 'service', 'date'])):
                level = "H3"
            
            # H4: Everything else that qualifies as a heading
            else:
                level = "H4"
            
            # Simple consistency check: avoid too many H1s
            h1_count = sum(1 for item in outline if item["level"] == "H1")
            if level == "H1" and h1_count >= 1:
                level = "H2"
            
            heading_dict = {
                "level": level,
                "text": text_clean,
                "page": candidate.span.page
            }
            
            outline.append(heading_dict)
            last_level = level
        
        return outline

    def process_pdf_enhanced(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF using enhanced hybrid approach"""
        start_time = time.time()
        
        logger.info(f"Processing {pdf_path} with enhanced trained models...")
        
        # Extract text spans
        spans = self.extract_text_spans(pdf_path)
        if not spans:
            return {"title": "Unknown", "outline": [], "metadata": {"error": "No text extracted"}}
        
        # Score all candidates
        candidates = self.score_heading_candidates(spans)
        
        # Filter and rank
        filtered_candidates = self.filter_and_rank_headings(candidates)
        
        # Assign levels and create outline
        outline = self.assign_heading_levels(filtered_candidates)
        
        # Determine title (highest scoring heading)
        title = outline[0]["text"] if outline else "Enhanced Processing Result"
        
        processing_time = time.time() - start_time
        
        result = {
            "title": title,
            "outline": outline,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "method": "Enhanced Hybrid (Statistical + Fine-tuned ML)",
                "total_spans": len(spans),
                "heading_candidates": len(filtered_candidates),
                "models_used": {
                    "statistical_analysis": True,
                    "fine_tuned_bert": self.use_trained_models and self.bert_model is not None,
                    "enhanced_semantic": self.use_trained_models and self.semantic_model is not None
                },
                "score_weights": self.weights
            }
        }
        
        logger.info(f"Enhanced processing completed in {processing_time:.2f}s")
        logger.info(f"Found {len(outline)} headings")
        
        return result

def main():
    """Main function to run enhanced PDF processing"""
    print("🚀 Enhanced PDF Processor with Fine-Tuned Models")
    print("=" * 52)
    
    # Check if trained models exist
    bert_path = "models/bert_heading_classifier"
    semantic_path = "models/semantic_heading_model"
    
    use_trained = Path(bert_path).exists() or Path(semantic_path).exists()
    
    if not use_trained:
        print("⚠️  Trained models not found. Running training first...")
        print("Please run: python training_data_generator.py")
        print("Then run: python bert_fine_tuner.py")
        print("Then run: python semantic_model_trainer.py")
        return
    
    # Initialize processor
    processor = TrainedPDFProcessor(
        bert_model_path=bert_path,
        semantic_model_path=semantic_path,
        use_trained_models=use_trained
    )
    
    # Input and output directories
    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    if not input_dir.exists():
        print(f"❌ Input directory '{input_dir}' not found!")
        return
    
    # Process all PDFs
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in '{input_dir}'!")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        print(f"\n🔄 Processing: {pdf_file.name}")
        
        # Process with enhanced approach
        result = processor.process_pdf_enhanced(str(pdf_file))
        
        # Save result
        output_file = output_dir / f"{pdf_file.stem}_enhanced.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved enhanced result: {output_file}")
        print(f"   📊 Found {len(result['outline'])} headings")
        print(f"   ⏱️  Processing time: {result['metadata']['processing_time']}s")
        print(f"   🤖 Models used: BERT={result['metadata']['models_used']['fine_tuned_bert']}, Semantic={result['metadata']['models_used']['enhanced_semantic']}")
        
        # Show top 5 headings with scores
        print(f"   🏆 Top detected headings:")
        for i, heading in enumerate(result['outline'][:5], 1):
            scores = heading.get('scores', {})
            print(f"      {i}. [{heading['level']}] {heading['text'][:50]}... (score: {scores.get('combined', 0):.3f})")

if __name__ == "__main__":
    main()