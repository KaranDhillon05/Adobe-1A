#!/usr/bin/env python3
"""
ML-Only PDF Processing Experiment
Adobe India Hackathon 2025 - Challenge 1A

This script processes PDFs using ONLY machine learning models,
without any statistical font analysis or pattern matching.
"""

import fitz
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
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

class MLOnlyPDFProcessor:
    """PDF processor using ONLY machine learning models"""
    
    def __init__(self):
        """Initialize ML models"""
        self.semantic_model = None
        self.classifier_model = None
        self.tokenizer = None
        self.heading_embeddings = None
        
        # Load models
        self._load_models()
        
        # Predefined heading examples for semantic comparison
        self.heading_examples = [
            "Introduction", "Chapter", "Section", "Summary", "Conclusion",
            "Overview", "Background", "Methodology", "Results", "Discussion",
            "Abstract", "Preface", "Appendix", "Bibliography", "References",
            "Table of Contents", "Executive Summary", "Objectives", "Scope",
            "Implementation", "Analysis", "Evaluation", "Recommendations"
        ]
        
        # Generate embeddings for heading examples
        if self.semantic_model:
            self.heading_embeddings = self.semantic_model.encode(self.heading_examples)
            logger.info(f"Generated embeddings for {len(self.heading_examples)} heading examples")

    def _load_models(self):
        """Load ML models"""
        try:
            # Load semantic similarity model
            logger.info("Loading semantic similarity model...")
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✓ Semantic model loaded")
            
            # Load classification model
            logger.info("Loading classification model...")
            self.tokenizer = AutoTokenizer.from_pretrained('prajjwal1/bert-tiny')
            self.classifier_model = AutoModelForSequenceClassification.from_pretrained('prajjwal1/bert-tiny')
            logger.info("✓ Classification model loaded")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            logger.warning("Continuing without ML models...")

    def extract_text_spans(self, pdf_path: str) -> List[TextSpan]:
        """Extract text spans from PDF"""
        spans = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text and len(text) > 1:
                                    spans.append(TextSpan(
                                        text=text,
                                        page=page_num + 1,
                                        font_size=span["size"],
                                        font_name=span["font"],
                                        bbox=span["bbox"],
                                        is_bold="Bold" in span["font"],
                                        is_italic="Italic" in span["font"]
                                    ))
            
            doc.close()
            logger.info(f"Extracted {len(spans)} text spans from {pdf_path}")
            return spans
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return []

    def calculate_semantic_similarity(self, text: str) -> float:
        """Calculate semantic similarity to known headings"""
        if not self.semantic_model or self.heading_embeddings is None:
            return 0.0
        
        try:
            # Generate embedding for the text
            text_embedding = self.semantic_model.encode([text])
            
            # Calculate cosine similarity with heading examples
            similarities = cosine_similarity(text_embedding, self.heading_embeddings)[0]
            
            # Return maximum similarity score
            max_similarity = float(np.max(similarities))
            return max_similarity
            
        except Exception as e:
            logger.warning(f"Error calculating semantic similarity for '{text}': {e}")
            return 0.0

    def classify_with_bert(self, text: str) -> float:
        """Classify text as heading using BERT"""
        if not self.classifier_model or not self.tokenizer:
            return 0.0
        
        try:
            # Tokenize text
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.classifier_model(**inputs)
                
            # Apply softmax to get probabilities
            probabilities = torch.softmax(outputs.logits, dim=-1)
            
            # Assume class 1 is "heading" (this is a simplification)
            # In reality, we'd need a properly trained model
            heading_probability = float(probabilities[0][1])
            
            return heading_probability
            
        except Exception as e:
            logger.warning(f"Error classifying with BERT for '{text}': {e}")
            return 0.0

    def ml_score_text(self, span: TextSpan) -> float:
        """Score text using ONLY ML models"""
        text = span.text.strip()
        
        if len(text) < 2:
            return 0.0
        
        # Calculate semantic similarity score (0-1)
        semantic_score = self.calculate_semantic_similarity(text)
        
        # Calculate BERT classification score (0-1)
        bert_score = self.classify_with_bert(text)
        
        # Combine scores (equal weight for experiment)
        combined_score = (semantic_score + bert_score) / 2.0
        
        logger.debug(f"ML scoring '{text[:50]}...': semantic={semantic_score:.3f}, bert={bert_score:.3f}, combined={combined_score:.3f}")
        
        return combined_score

    def process_pdf_ml_only(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF using ONLY ML models"""
        start_time = time.time()
        
        logger.info(f"Processing {pdf_path} with ML-only approach...")
        
        # Extract text spans
        spans = self.extract_text_spans(pdf_path)
        if not spans:
            return {"title": "Unknown", "outline": [], "metadata": {"error": "No text extracted"}}
        
        # Score all spans using ML
        scored_spans = []
        for span in spans:
            ml_score = self.ml_score_text(span)
            if ml_score > 0.1:  # Very low threshold for ML experiment
                scored_spans.append((span, ml_score))
        
        # Sort by ML score (descending)
        scored_spans.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"ML models scored {len(scored_spans)} potential headings")
        
        # Filter and structure results
        outline = []
        title = "ML-Only Processing Result"
        
        # Take top scoring spans as headings
        for span, score in scored_spans[:20]:  # Limit to top 20 for experiment
            # Determine heading level based on ML score
            if score > 0.7:
                level = "H1"
            elif score > 0.5:
                level = "H2"
            elif score > 0.3:
                level = "H3"
            else:
                level = "H4"
            
            outline.append({
                "level": level,
                "text": span.text,
                "page": span.page,
                "ml_score": round(score, 3),
                "semantic_sim": round(self.calculate_semantic_similarity(span.text), 3),
                "bert_score": round(self.classify_with_bert(span.text), 3)
            })
        
        # Use highest scoring span as title if available
        if scored_spans:
            title = scored_spans[0][0].text
        
        processing_time = time.time() - start_time
        
        result = {
            "title": title,
            "outline": outline,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "method": "ML-Only (Semantic + BERT)",
                "total_spans": len(spans),
                "ml_candidates": len(scored_spans),
                "semantic_model": "all-MiniLM-L6-v2",
                "classification_model": "bert-tiny"
            }
        }
        
        logger.info(f"ML-only processing completed in {processing_time:.2f}s")
        return result

def main():
    """Main function to run ML-only experiment"""
    print("🧠 ML-Only PDF Processing Experiment")
    print("=" * 50)
    
    # Initialize processor
    processor = MLOnlyPDFProcessor()
    
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
    
    print(f"📄 Found {len(pdf_files)} PDF files to process with ML-only approach")
    
    for pdf_file in pdf_files:
        print(f"\n🔄 Processing: {pdf_file.name}")
        
        # Process with ML-only approach
        result = processor.process_pdf_ml_only(str(pdf_file))
        
        # Save result
        output_file = output_dir / f"{pdf_file.stem}_ml_only.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved ML-only result: {output_file}")
        print(f"   📊 Found {len(result['outline'])} headings")
        print(f"   ⏱️  Processing time: {result['metadata']['processing_time']}s")
        
        # Show top 5 headings with scores
        print(f"   🏆 Top ML-detected headings:")
        for i, heading in enumerate(result['outline'][:5], 1):
            print(f"      {i}. [{heading['level']}] {heading['text'][:60]}... (score: {heading['ml_score']})")

if __name__ == "__main__":
    main()