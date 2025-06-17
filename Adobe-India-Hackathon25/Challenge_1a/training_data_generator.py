#!/usr/bin/env python3
"""
Training Data Generator for PDF Heading Detection Models
Adobe India Hackathon 2025 - Challenge 1A

Generates high-quality training data from PDFs for fine-tuning:
1. BERT classification model (heading vs non-heading)
2. Semantic similarity model enhancement
"""

import fitz
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """Single training example for model fine-tuning"""
    text: str
    is_heading: bool
    confidence: float
    features: Dict[str, Any]
    source_pdf: str
    page: int

class TrainingDataGenerator:
    """Generates training data from PDFs using statistical analysis as ground truth"""
    
    def __init__(self):
        self.font_size_threshold = 1.15
        self.heading_patterns = [
            r'^\d+\.\s+[A-Z]',           # "1. Introduction"
            r'^(Chapter|Section)\s+\d+',  # "Chapter 5"
            r'^[A-Z][A-Z\s]{2,20}$',     # "SUMMARY", "TABLE OF CONTENTS"
            r'^\d+\.\d+\s+[A-Z]',        # "1.1 Overview"
            r'^(Introduction|Conclusion|Summary|Abstract|References|Bibliography)$',
            r'^(Overview|Background|Methodology|Results|Discussion|Appendix)$',
            r'^(Objectives|Scope|Implementation|Analysis|Evaluation)$'
        ]
        
        self.false_positive_patterns = [
            r'^(do not|don\'t)\s+check\s+.*',
            r'^(please|click|select)\s+.*',
            r'^https?://',
            r'^www\.',
            r'@\w+\.\w+',
            r'^\d{4}-\d{2}-\d{2}',
            r'^[A-F0-9]{8,}$',
            r'^[^\w\s]+$',
            r'^\d+$',
            r'^(ok|cancel|submit|save|next|previous|back)$',
            r'^(yes|no|true|false)$'
        ]

    def extract_text_spans_with_features(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text spans with comprehensive features for training"""
        spans_data = []
        
        try:
            doc = fitz.open(pdf_path)
            
            # Calculate document-level statistics
            all_font_sizes = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["text"].strip():
                                    all_font_sizes.append(span["size"])
            
            median_font_size = np.median(all_font_sizes) if all_font_sizes else 12.0
            
            # Extract spans with features
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                page_height = page.rect.height
                
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text and len(text) > 1:
                                    
                                    # Calculate comprehensive features
                                    features = self._calculate_features(
                                        span, text, median_font_size, page_height, page_num + 1
                                    )
                                    
                                    spans_data.append({
                                        'text': text,
                                        'page': page_num + 1,
                                        'features': features,
                                        'source_pdf': os.path.basename(pdf_path)
                                    })
            
            doc.close()
            logger.info(f"Extracted {len(spans_data)} spans with features from {pdf_path}")
            return spans_data
            
        except Exception as e:
            logger.error(f"Error extracting from {pdf_path}: {e}")
            return []

    def _calculate_features(self, span: Dict, text: str, median_font_size: float, 
                          page_height: float, page_num: int) -> Dict[str, Any]:
        """Calculate comprehensive features for a text span"""
        
        # Font-based features
        font_size_ratio = span["size"] / median_font_size if median_font_size > 0 else 1.0
        is_bold = "Bold" in span["font"] or "bold" in span["font"].lower()
        is_italic = "Italic" in span["font"] or "italic" in span["font"].lower()
        
        # Text-based features
        word_count = len(text.split())
        char_count = len(text)
        has_numbers = bool(re.search(r'\d', text))
        starts_with_number = bool(re.match(r'^\d', text))
        is_uppercase = text.isupper()
        is_title_case = text.istitle()
        
        # Position-based features
        bbox = span["bbox"]
        x_position = bbox[0]
        y_position = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        y_ratio = y_position / page_height if page_height > 0 else 0.5
        
        # Pattern matching features
        matches_heading_pattern = any(re.match(pattern, text, re.IGNORECASE) 
                                    for pattern in self.heading_patterns)
        matches_false_positive = any(re.match(pattern, text, re.IGNORECASE) 
                                   for pattern in self.false_positive_patterns)
        
        # Content analysis features
        capitalized_words = sum(1 for word in text.split() if word and word[0].isupper())
        capitalization_ratio = capitalized_words / word_count if word_count > 0 else 0
        
        # Structural features
        ends_with_colon = text.endswith(':')
        has_punctuation = bool(re.search(r'[.!?;,]', text))
        is_short = word_count <= 8
        is_very_short = word_count <= 3
        
        return {
            # Font features
            'font_size': span["size"],
            'font_size_ratio': font_size_ratio,
            'is_bold': is_bold,
            'is_italic': is_italic,
            'font_name': span["font"],
            
            # Text features
            'word_count': word_count,
            'char_count': char_count,
            'has_numbers': has_numbers,
            'starts_with_number': starts_with_number,
            'is_uppercase': is_uppercase,
            'is_title_case': is_title_case,
            'capitalization_ratio': capitalization_ratio,
            
            # Position features
            'x_position': x_position,
            'y_position': y_position,
            'y_ratio': y_ratio,
            'width': width,
            'height': height,
            'page_num': page_num,
            
            # Pattern features
            'matches_heading_pattern': matches_heading_pattern,
            'matches_false_positive': matches_false_positive,
            
            # Content features
            'ends_with_colon': ends_with_colon,
            'has_punctuation': has_punctuation,
            'is_short': is_short,
            'is_very_short': is_very_short
        }

    def label_training_data(self, spans_data: List[Dict]) -> List[TrainingExample]:
        """Label spans as headings or non-headings using statistical analysis"""
        training_examples = []
        
        for span_data in spans_data:
            text = span_data['text']
            features = span_data['features']
            
            # Calculate confidence score using our proven statistical method
            confidence = self._calculate_statistical_confidence(features, text)
            
            # Label as heading if confidence is high
            is_heading = confidence > 0.7
            
            # Adjust confidence for edge cases
            if features['matches_false_positive']:
                is_heading = False
                confidence = min(confidence, 0.3)
            
            if features['matches_heading_pattern']:
                is_heading = True
                confidence = max(confidence, 0.8)
            
            training_examples.append(TrainingExample(
                text=text,
                is_heading=is_heading,
                confidence=confidence,
                features=features,
                source_pdf=span_data['source_pdf'],
                page=span_data['page']
            ))
        
        return training_examples

    def _calculate_statistical_confidence(self, features: Dict, text: str) -> float:
        """Calculate confidence using our proven statistical method"""
        
        # Font size component (40% weight)
        font_score = min(features['font_size_ratio'] - 1.0, 1.0) if features['font_size_ratio'] > 1.0 else 0.0
        font_score = max(0.0, font_score)
        
        # Content component (35% weight)
        content_score = 0.0
        if features['matches_heading_pattern']:
            content_score += 0.8
        if features['is_title_case'] or features['is_uppercase']:
            content_score += 0.3
        if features['starts_with_number']:
            content_score += 0.2
        if features['is_short']:
            content_score += 0.1
        content_score = min(content_score, 1.0)
        
        # Formatting component (15% weight)
        format_score = 0.0
        if features['is_bold']:
            format_score += 0.5
        if features['is_italic']:
            format_score += 0.2
        if features['ends_with_colon']:
            format_score += 0.3
        format_score = min(format_score, 1.0)
        
        # Position component (10% weight)
        position_score = 0.0
        if features['y_ratio'] < 0.1:  # Top of page
            position_score += 0.5
        if features['x_position'] < 100:  # Left margin
            position_score += 0.3
        position_score = min(position_score, 1.0)
        
        # Combine scores
        final_score = (
            font_score * 0.4 +
            content_score * 0.35 +
            format_score * 0.15 +
            position_score * 0.10
        )
        
        # Apply penalties
        if features['matches_false_positive']:
            final_score *= 0.1
        if features['word_count'] > 15:
            final_score *= 0.5
        if not features['has_punctuation'] and features['word_count'] > 5:
            final_score *= 0.8
        
        return min(max(final_score, 0.0), 1.0)

    def create_bert_training_data(self, training_examples: List[TrainingExample]) -> pd.DataFrame:
        """Create training data for BERT classification model"""
        
        # Filter high-confidence examples for better training quality
        high_confidence_examples = [
            ex for ex in training_examples 
            if ex.confidence > 0.3  # Lower threshold to get more training data
        ]
        
        data = []
        for example in high_confidence_examples:
            data.append({
                'text': example.text,
                'label': 1 if example.is_heading else 0,
                'confidence': example.confidence,
                'source_pdf': example.source_pdf,
                'page': example.page
            })
        
        df = pd.DataFrame(data)
        
        # Balance the dataset
        positive_samples = df[df['label'] == 1]
        negative_samples = df[df['label'] == 0]
        
        # Ensure balanced dataset
        min_samples = min(len(positive_samples), len(negative_samples))
        if min_samples > 0:
            balanced_positive = positive_samples.sample(n=min_samples, random_state=42)
            balanced_negative = negative_samples.sample(n=min_samples, random_state=42)
            df = pd.concat([balanced_positive, balanced_negative]).reset_index(drop=True)
        
        logger.info(f"Created BERT training data: {len(df)} examples")
        logger.info(f"Positive samples: {len(df[df['label'] == 1])}")
        logger.info(f"Negative samples: {len(df[df['label'] == 0])}")
        
        return df

    def create_semantic_training_data(self, training_examples: List[TrainingExample]) -> Dict[str, List[str]]:
        """Create training data for semantic similarity enhancement"""
        
        # Extract heading examples by category
        heading_categories = {
            'introductions': [],
            'chapters': [],
            'sections': [],
            'summaries': [],
            'technical': [],
            'general': []
        }
        
        for example in training_examples:
            if example.is_heading and example.confidence > 0.8:
                text = example.text.lower()
                
                if any(word in text for word in ['introduction', 'intro', 'overview', 'background']):
                    heading_categories['introductions'].append(example.text)
                elif any(word in text for word in ['chapter', 'part', 'section']):
                    heading_categories['chapters'].append(example.text)
                elif re.match(r'^\d+\.\d*', text):
                    heading_categories['sections'].append(example.text)
                elif any(word in text for word in ['summary', 'conclusion', 'results', 'discussion']):
                    heading_categories['summaries'].append(example.text)
                elif any(word in text for word in ['implementation', 'analysis', 'methodology', 'evaluation']):
                    heading_categories['technical'].append(example.text)
                else:
                    heading_categories['general'].append(example.text)
        
        # Log statistics
        for category, examples in heading_categories.items():
            logger.info(f"Semantic training - {category}: {len(examples)} examples")
        
        return heading_categories

    def generate_training_data_from_pdfs(self, pdf_directory: str, output_directory: str):
        """Generate comprehensive training data from PDF directory"""
        
        pdf_dir = Path(pdf_directory)
        output_dir = Path(output_directory)
        output_dir.mkdir(exist_ok=True)
        
        if not pdf_dir.exists():
            logger.error(f"PDF directory not found: {pdf_directory}")
            return
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            logger.error(f"No PDF files found in {pdf_directory}")
            return
        
        logger.info(f"Processing {len(pdf_files)} PDF files for training data generation")
        
        all_training_examples = []
        
        # Process each PDF
        for pdf_file in pdf_files:
            logger.info(f"Processing {pdf_file.name}...")
            
            # Extract spans with features
            spans_data = self.extract_text_spans_with_features(str(pdf_file))
            
            # Label the data
            training_examples = self.label_training_data(spans_data)
            all_training_examples.extend(training_examples)
        
        logger.info(f"Generated {len(all_training_examples)} training examples total")
        
        # Create BERT training data
        bert_df = self.create_bert_training_data(all_training_examples)
        bert_df.to_csv(output_dir / "bert_training_data.csv", index=False)
        logger.info(f"Saved BERT training data: {len(bert_df)} examples")
        
        # Split into train/validation/test
        if len(bert_df) < 10:
            # For small datasets, use simple split without stratification
            train_df, temp_df = train_test_split(bert_df, test_size=0.3, random_state=42)
            if len(temp_df) >= 2:
                val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)
            else:
                val_df = temp_df
                test_df = temp_df
        else:
            train_df, temp_df = train_test_split(bert_df, test_size=0.3, random_state=42, stratify=bert_df['label'])
            val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42, stratify=temp_df['label'])
        
        train_df.to_csv(output_dir / "bert_train.csv", index=False)
        val_df.to_csv(output_dir / "bert_val.csv", index=False)
        test_df.to_csv(output_dir / "bert_test.csv", index=False)
        
        logger.info(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        # Create semantic training data
        semantic_data = self.create_semantic_training_data(all_training_examples)
        with open(output_dir / "semantic_training_data.json", 'w') as f:
            json.dump(semantic_data, f, indent=2, ensure_ascii=False)
        
        # Save detailed training examples for analysis
        examples_data = []
        for ex in all_training_examples:
            # Convert all values to JSON-serializable types
            features_serializable = {}
            for key, value in ex.features.items():
                if isinstance(value, (bool, int, float, str)):
                    features_serializable[key] = value
                else:
                    features_serializable[key] = str(value)
            
            examples_data.append({
                'text': ex.text,
                'is_heading': bool(ex.is_heading),
                'confidence': float(ex.confidence),
                'source_pdf': ex.source_pdf,
                'page': int(ex.page),
                'features': features_serializable
            })
        
        with open(output_dir / "detailed_training_examples.json", 'w') as f:
            json.dump(examples_data, f, indent=2, ensure_ascii=False)
        
        # Generate statistics
        self._generate_training_statistics(all_training_examples, output_dir)
        
        logger.info(f"Training data generation complete! Files saved to {output_dir}")

    def _generate_training_statistics(self, training_examples: List[TrainingExample], output_dir: Path):
        """Generate comprehensive statistics about the training data"""
        
        stats = {
            'total_examples': len(training_examples),
            'heading_examples': len([ex for ex in training_examples if ex.is_heading]),
            'non_heading_examples': len([ex for ex in training_examples if not ex.is_heading]),
            'high_confidence_examples': len([ex for ex in training_examples if ex.confidence > 0.8]),
            'medium_confidence_examples': len([ex for ex in training_examples if 0.5 < ex.confidence <= 0.8]),
            'low_confidence_examples': len([ex for ex in training_examples if ex.confidence <= 0.5]),
            'source_pdfs': list(set(ex.source_pdf for ex in training_examples)),
            'confidence_distribution': {
                'mean': np.mean([ex.confidence for ex in training_examples]),
                'std': np.std([ex.confidence for ex in training_examples]),
                'min': np.min([ex.confidence for ex in training_examples]),
                'max': np.max([ex.confidence for ex in training_examples])
            }
        }
        
        with open(output_dir / "training_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Training statistics:")
        logger.info(f"  Total examples: {stats['total_examples']}")
        logger.info(f"  Headings: {stats['heading_examples']} ({stats['heading_examples']/stats['total_examples']*100:.1f}%)")
        logger.info(f"  Non-headings: {stats['non_heading_examples']} ({stats['non_heading_examples']/stats['total_examples']*100:.1f}%)")
        logger.info(f"  High confidence: {stats['high_confidence_examples']}")

def main():
    """Main function to generate training data"""
    print("🏋️ Training Data Generator for PDF Heading Detection")
    print("=" * 55)
    
    generator = TrainingDataGenerator()
    
    # Use input directory with PDFs
    pdf_directory = "input"
    output_directory = "training_data"
    
    generator.generate_training_data_from_pdfs(pdf_directory, output_directory)

if __name__ == "__main__":
    main()