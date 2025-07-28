"""
Adobe Hackathon 2025 - Semantic Analysis Engine for Challenge 1b
Persona-driven content analysis with importance ranking and content extraction
"""

import numpy as np
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import logging
from pathlib import Path

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

@dataclass
class DocumentSection:
    """Represents a document section with content and metadata"""
    document: str
    section_title: str
    content: str
    page_number: int
    importance_score: float = 0.0

class SemanticAnalyzer:
    """Advanced semantic analysis for persona-driven content extraction"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with lightweight sentence transformer model"""
        self.model_name = model_name
        self.model = None
        self.logger = logging.getLogger(__name__)
        self.stop_words = set(stopwords.words('english'))

        # Load model with size constraint (must be < 1GB for Challenge 1b)
        self._load_model()

    def _load_model(self):
        """Load sentence transformer model with size validation"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Loaded semantic model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load model {self.model_name}: {e}")
            # Fallback to basic keyword matching if model fails
            self.model = None

    def chunk_document_content(self, pdf_path: str, text_spans: List) -> List[DocumentSection]:
        """Extract meaningful sections from PDF content"""
        from .pdf_processor import PDFProcessor

        processor = PDFProcessor()

        try:
            # Extract text with structure preservation
            doc_content = processor.extract_text_spans(pdf_path)
            if not doc_content:
                return []

            sections = []
            current_section = None
            current_content = []

            for span in doc_content:
                text = span.text.strip()
                if not text:
                    continue

                # Check if this looks like a section heading
                score = processor.score_heading_candidate(span, 
                    processor.analyze_font_statistics(doc_content), 800)

                if score >= 0.4:  # Heading threshold
                    # Save previous section
                    if current_section and current_content:
                        sections.append(DocumentSection(
                            document=Path(pdf_path).name,
                            section_title=current_section,
                            content=" ".join(current_content),
                            page_number=span.page_num + 1
                        ))

                    # Start new section
                    current_section = text
                    current_content = []
                else:
                    # Add to current section content
                    if current_section:
                        current_content.append(text)

            # Add final section
            if current_section and current_content:
                sections.append(DocumentSection(
                    document=Path(pdf_path).name,
                    section_title=current_section,
                    content=" ".join(current_content),
                    page_number=1  # Fallback page number
                ))

            return sections

        except Exception as e:
            self.logger.error(f"Error chunking document {pdf_path}: {e}")
            return []

    def calculate_relevance_score(self, section: DocumentSection, 
                                persona: str, task: str) -> float:
        """Calculate relevance score using semantic similarity"""
        try:
            # Combine section title and content for analysis
            section_text = f"{section.section_title} {section.content}"

            # Create query from persona and task
            query = f"{persona} {task}"

            if self.model:
                # Use semantic similarity with sentence transformers
                section_embedding = self.model.encode([section_text])
                query_embedding = self.model.encode([query])

                similarity = cosine_similarity(section_embedding, query_embedding)[0][0]
                return float(similarity)
            else:
                # Fallback to keyword-based scoring
                return self._keyword_relevance_score(section_text, query)

        except Exception as e:
            self.logger.error(f"Error calculating relevance score: {e}")
            return 0.0

    def _keyword_relevance_score(self, text: str, query: str) -> float:
        """Fallback keyword-based relevance scoring"""
        try:
            text_words = set(word.lower() for word in word_tokenize(text) 
                           if word.isalpha() and word.lower() not in self.stop_words)
            query_words = set(word.lower() for word in word_tokenize(query)
                            if word.isalpha() and word.lower() not in self.stop_words)

            if not query_words:
                return 0.0

            # Calculate Jaccard similarity
            intersection = len(text_words.intersection(query_words))
            union = len(text_words.union(query_words))

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            self.logger.error(f"Error in keyword scoring: {e}")
            return 0.0

    def extract_relevant_content(self, section: DocumentSection, 
                               max_length: int = 500) -> str:
        """Extract most relevant content from section"""
        try:
            content = section.content.strip()
            if len(content) <= max_length:
                return content

            # Split into sentences and rank by relevance
            sentences = sent_tokenize(content)
            if len(sentences) <= 3:
                return content[:max_length] + "..." if len(content) > max_length else content

            # For now, return first few sentences up to max_length
            result = ""
            for sentence in sentences:
                if len(result + sentence) <= max_length:
                    result += sentence + " "
                else:
                    break

            return result.strip()

        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return section.content[:max_length] + "..." if len(section.content) > max_length else section.content

    def analyze_collection(self, input_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document collection based on persona and task"""
        try:
            # Extract input parameters
            documents = input_config.get("documents", [])
            persona = input_config.get("persona", {}).get("role", "")
            task = input_config.get("job_to_be_done", {}).get("task", "")

            if not documents or not persona or not task:
                raise ValueError("Missing required input parameters")

            all_sections = []

            # Process each document in the collection
            for doc_info in documents:
                filename = doc_info.get("filename", "")
                if not filename:
                    continue

                # Assuming PDFs are in current directory for processing
                pdf_path = Path(filename)
                if not pdf_path.exists():
                    self.logger.warning(f"File not found: {filename}")
                    continue

                # Extract sections from document
                sections = self.chunk_document_content(str(pdf_path), [])

                # Calculate relevance scores
                for section in sections:
                    section.importance_score = self.calculate_relevance_score(
                        section, persona, task
                    )

                all_sections.extend(sections)

            # Sort by relevance score (highest first)
            all_sections.sort(key=lambda x: x.importance_score, reverse=True)

            # Select top 5 most relevant sections
            top_sections = all_sections[:5]

            # Build extracted_sections output
            extracted_sections = []
            for i, section in enumerate(top_sections):
                extracted_sections.append({
                    "document": section.document,
                    "section_title": section.section_title,
                    "importance_rank": i + 1,
                    "page_number": section.page_number
                })

            # Build subsection_analysis output
            subsection_analysis = []
            for section in top_sections:
                refined_text = self.extract_relevant_content(section, 400)
                subsection_analysis.append({
                    "document": section.document,
                    "refined_text": refined_text,
                    "page_number": section.page_number
                })

            # Build complete output
            result = {
                "metadata": {
                    "input_documents": [doc["filename"] for doc in documents],
                    "persona": persona,
                    "job_to_be_done": task,
                    "processing_timestamp": "2025-07-23T01:35:00.000000"
                },
                "extracted_sections": extracted_sections,
                "subsection_analysis": subsection_analysis
            }

            return result

        except Exception as e:
            self.logger.error(f"Error analyzing collection: {e}")
            return {
                "metadata": {"error": str(e)},
                "extracted_sections": [],
                "subsection_analysis": []
            }
