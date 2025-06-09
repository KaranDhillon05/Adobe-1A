#!/usr/bin/env python3
"""
Adobe Hackathon 2025 - MULTILINGUAL PDF Processing System
Advanced heading detection with comprehensive language support
"""

import os
import json
import re
import time
import statistics
from pathlib import Path
from collections import Counter, defaultdict
import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional, Set
import sys
import logging
from dataclasses import dataclass
import numpy as np

# Language detection libraries
try:
    import fasttext
    import fasttext.util
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False

try:
    from langdetect import detect, detect_langs, DetectorFactory
    DetectorFactory.seed = 0  # For consistent results
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# ML Model imports
try:
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@dataclass
class TextSpan:
    """Represents a text span with formatting, position, and language information"""
    text: str
    font_name: str
    font_size: float
    font_flags: int
    bbox: Tuple[float, float, float, float]
    page_num: int
    language: Optional[str] = None
    script: Optional[str] = None
    confidence: float = 0.0

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

class LanguageDetector:
    """Advanced language detection with multiple fallback methods"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fasttext_model = None
        self.supported_methods = []
        
        # Initialize available language detection methods
        self._initialize_detectors()
    
    def _initialize_detectors(self):
        """Initialize available language detection libraries"""
        # Try to load FastText model
        if FASTTEXT_AVAILABLE:
            try:
                # Download and load the language identification model
                fasttext.util.download_model('en', if_exists='ignore')
                model_path = 'lid.176.bin'
                
                # Try to load existing model or download
                try:
                    self.fasttext_model = fasttext.load_model(model_path)
                    self.supported_methods.append('fasttext')
                    self.logger.info("✅ FastText language detection loaded")
                except:
                    # Fallback to smaller model
                    try:
                        self.fasttext_model = fasttext.load_model('lid.176.ftz')
                        self.supported_methods.append('fasttext')
                        self.logger.info("✅ FastText compressed model loaded")
                    except Exception as e:
                        self.logger.warning(f"FastText model loading failed: {e}")
            except Exception as e:
                self.logger.warning(f"FastText initialization failed: {e}")
        
        if LANGDETECT_AVAILABLE:
            self.supported_methods.append('langdetect')
            self.logger.info("✅ LangDetect available")
        
        # Fallback to heuristic detection
        self.supported_methods.append('heuristic')
        self.logger.info(f"Language detection methods available: {self.supported_methods}")
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect language with confidence score"""
        if not text or len(text.strip()) < 3:
            return 'unknown', 0.0
        
        # Clean text for detection
        clean_text = self._clean_text_for_detection(text)
        
        # Try FastText first (most accurate and fast)
        if 'fasttext' in self.supported_methods and self.fasttext_model:
            try:
                predictions = self.fasttext_model.predict(clean_text, k=1)
                if predictions and len(predictions[0]) > 0:
                    lang_code = predictions[0][0].replace('__label__', '')
                    confidence = float(predictions[1][0])
                    return self._normalize_language_code(lang_code), confidence
            except Exception as e:
                self.logger.debug(f"FastText detection failed: {e}")
        
        # Try LangDetect as fallback
        if 'langdetect' in self.supported_methods:
            try:
                lang_probs = detect_langs(clean_text)
                if lang_probs:
                    best_lang = lang_probs[0]
                    return self._normalize_language_code(best_lang.lang), best_lang.prob
            except Exception as e:
                self.logger.debug(f"LangDetect failed: {e}")
        
        # Heuristic detection as last resort
        return self._heuristic_language_detection(clean_text)
    
    def _clean_text_for_detection(self, text: str) -> str:
        """Clean text for better language detection"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\.,!?;:\-\(\)\[\]{}\'\"]+', ' ', text)
        
        # Remove numbers and short words for better detection
        words = text.split()
        filtered_words = [w for w in words if len(w) > 2 and not w.isdigit()]
        
        return ' '.join(filtered_words) if filtered_words else text
    
    def _normalize_language_code(self, lang_code: str) -> str:
        """Normalize language codes to ISO 639-1 format"""
        # Common language code mappings
        lang_mapping = {
            'zh': 'zh-cn',  # Chinese
            'zh-cn': 'zh-cn',
            'zh-tw': 'zh-tw',
            'ar': 'ar',     # Arabic
            'hi': 'hi',     # Hindi
            'ja': 'ja',     # Japanese
            'ko': 'ko',     # Korean
            'th': 'th',     # Thai
            'vi': 'vi',     # Vietnamese
            'es': 'es',     # Spanish
            'fr': 'fr',     # French
            'de': 'de',     # German
            'it': 'it',     # Italian
            'pt': 'pt',     # Portuguese
            'ru': 'ru',     # Russian
            'nl': 'nl',     # Dutch
            'pl': 'pl',     # Polish
            'tr': 'tr',     # Turkish
            'sv': 'sv',     # Swedish
            'da': 'da',     # Danish
            'no': 'no',     # Norwegian
            'fi': 'fi',     # Finnish
            'he': 'he',     # Hebrew
            'fa': 'fa',     # Persian
            'ur': 'ur',     # Urdu
            'bn': 'bn',     # Bengali
            'ta': 'ta',     # Tamil
            'te': 'te',     # Telugu
            'ml': 'ml',     # Malayalam
            'kn': 'kn',     # Kannada
            'gu': 'gu',     # Gujarati
            'pa': 'pa',     # Punjabi
            'or': 'or',     # Odia
            'as': 'as',     # Assamese
            'mr': 'mr',     # Marathi
        }
        
        return lang_mapping.get(lang_code.lower(), lang_code.lower())
    
    def _heuristic_language_detection(self, text: str) -> Tuple[str, float]:
        """Heuristic language detection based on script and patterns"""
        if not text:
            return 'unknown', 0.0
        
        # Script-based detection
        scripts = self._detect_script(text)
        
        # Chinese characters
        if 'han' in scripts:
            if any(char in text for char in '的是在了不和有大这主中人上为們到說他一以'):
                return 'zh-cn', 0.7  # Simplified Chinese
            elif any(char in text for char in '的是在了不和有大這主中人上為們到說他一以'):
                return 'zh-tw', 0.7  # Traditional Chinese
            else:
                return 'zh-cn', 0.6  # Default to Simplified
        
        # Arabic script
        if 'arabic' in scripts:
            return 'ar', 0.8
        
        # Devanagari script (Hindi and related languages)
        if 'devanagari' in scripts:
            if any(word in text for word in ['है', 'के', 'में', 'को', 'का', 'से', 'पर', 'यह', 'वह']):
                return 'hi', 0.8
            return 'hi', 0.6
        
        # Japanese
        if 'hiragana' in scripts or 'katakana' in scripts:
            return 'ja', 0.8
        
        # Korean
        if 'hangul' in scripts:
            return 'ko', 0.8
        
        # Thai
        if 'thai' in scripts:
            return 'th', 0.8
        
        # Latin script - use pattern matching
        if 'latin' in scripts:
            return self._detect_latin_language(text)
        
        return 'en', 0.3  # Default fallback
    
    def _detect_script(self, text: str) -> Set[str]:
        """Detect writing scripts in text"""
        scripts = set()
        
        for char in text:
            code_point = ord(char)
            
            # Latin script
            if (0x0041 <= code_point <= 0x005A) or (0x0061 <= code_point <= 0x007A):
                scripts.add('latin')
            
            # Chinese (CJK Unified Ideographs)
            elif 0x4E00 <= code_point <= 0x9FFF:
                scripts.add('han')
            
            # Arabic
            elif 0x0600 <= code_point <= 0x06FF:
                scripts.add('arabic')
            
            # Devanagari
            elif 0x0900 <= code_point <= 0x097F:
                scripts.add('devanagari')
            
            # Hiragana
            elif 0x3040 <= code_point <= 0x309F:
                scripts.add('hiragana')
            
            # Katakana
            elif 0x30A0 <= code_point <= 0x30FF:
                scripts.add('katakana')
            
            # Hangul
            elif 0xAC00 <= code_point <= 0xD7AF:
                scripts.add('hangul')
            
            # Thai
            elif 0x0E00 <= code_point <= 0x0E7F:
                scripts.add('thai')
        
        return scripts
    
    def _detect_latin_language(self, text: str) -> Tuple[str, float]:
        """Detect language for Latin script text"""
        text_lower = text.lower()
        
        # Language-specific patterns
        patterns = {
            'es': ['el', 'la', 'de', 'en', 'y', 'que', 'es', 'se', 'un', 'por', 'con', 'no', 'una', 'su', 'para'],
            'fr': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im'],
            'it': ['il', 'di', 'che', 'e', 'la', 'in', 'un', 'è', 'per', 'una', 'sono', 'con', 'non', 'le', 'si'],
            'pt': ['de', 'e', 'o', 'a', 'que', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os'],
            'nl': ['de', 'het', 'een', 'van', 'en', 'in', 'te', 'dat', 'op', 'voor', 'met', 'als', 'zijn', 'er', 'maar'],
        }
        
        scores = {}
        for lang, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[lang] = score / len(keywords)
        
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            if best_lang[1] > 0.1:  # Minimum threshold
                return best_lang[0], min(0.9, best_lang[1] + 0.3)
        
        return 'en', 0.5  # Default to English

class MultilingualPDFProcessor:
    """Advanced multilingual PDF processor with language-aware heading detection"""
    
    def __init__(self, font_size_threshold: float = 1.15, min_heading_length: int = 2, use_ml_models: bool = False):
        self.font_size_threshold = font_size_threshold
        self.min_heading_length = min_heading_length
        self.use_ml_models = use_ml_models and ML_AVAILABLE
        self.logger = logging.getLogger(__name__)
        
        # Initialize language detector
        self.language_detector = LanguageDetector()
        
        # Language-specific configurations
        self.language_configs = self._initialize_language_configs()
        
        # Universal scoring weights (language-agnostic)
        self.scoring_weights = {
            'font_size': 0.45,
            'content': 0.30,
            'formatting': 0.15,
            'position': 0.10
        }
        
        # Initialize ML models if available
        self.semantic_model = None
        self.classification_model = None
        self.classification_tokenizer = None
        
        if self.use_ml_models:
            try:
                self._initialize_ml_models()
                self.logger.info("✅ Multilingual ML models loaded successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load ML models: {e}. Using algorithmic-only mode.")
                self.use_ml_models = False
    
    def _initialize_language_configs(self) -> Dict[str, Dict]:
        """Initialize language-specific configurations"""
        return {
            # English
            'en': {
                'heading_patterns': [
                    r'^\d+\.\s+[A-Z]',  # "1. Introduction"
                    r'^[A-Z][a-zA-Z\s\-:]+$',  # Title case
                    r'^\d+\.\d+\.?\s+',  # "1.1. Subsection"
                    r'^(Chapter|Section|Appendix)\s+\d+',
                    r'^(Introduction|Conclusion|Summary|Abstract|Overview|Background)',
                ],
                'false_positive_patterns': [
                    r'^(do not|don\'t)\s+check\s+.*',
                    r'^(please|click|select|press|enter|type)\s+.*',
                    r'^(ok|cancel|apply|close|save|delete)\s*$',
                ],
                'title_words': ['guide', 'manual', 'report', 'document', 'handbook', 'tutorial'],
                'min_words': 2,
                'max_words': 15,
            },
            
            # Spanish
            'es': {
                'heading_patterns': [
                    r'^\d+\.\s+[A-ZÁÉÍÓÚÑ]',
                    r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s\-:]+$',
                    r'^(Capítulo|Sección|Apéndice)\s+\d+',
                    r'^(Introducción|Conclusión|Resumen|Antecedentes)',
                ],
                'false_positive_patterns': [
                    r'^(no\s+marcar|no\s+seleccionar)\s+.*',
                    r'^(por\s+favor|haga\s+clic|seleccione)\s+.*',
                ],
                'title_words': ['guía', 'manual', 'informe', 'documento', 'tutorial'],
                'min_words': 2,
                'max_words': 15,
            },
            
            # French
            'fr': {
                'heading_patterns': [
                    r'^\d+\.\s+[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ]',
                    r'^[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ][a-zàâäéèêëïîôöùûüÿçA-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ\s\-:]+$',
                    r'^(Chapitre|Section|Annexe)\s+\d+',
                    r'^(Introduction|Conclusion|Résumé|Contexte)',
                ],
                'false_positive_patterns': [
                    r'^(ne\s+pas\s+cocher|ne\s+pas\s+sélectionner)\s+.*',
                    r'^(veuillez|cliquez|sélectionnez)\s+.*',
                ],
                'title_words': ['guide', 'manuel', 'rapport', 'document', 'tutoriel'],
                'min_words': 2,
                'max_words': 15,
            },
            
            # German
            'de': {
                'heading_patterns': [
                    r'^\d+\.\s+[A-ZÄÖÜ]',
                    r'^[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ\s\-:]+$',
                    r'^(Kapitel|Abschnitt|Anhang)\s+\d+',
                    r'^(Einleitung|Schlussfolgerung|Zusammenfassung|Hintergrund)',
                ],
                'false_positive_patterns': [
                    r'^(nicht\s+auswählen|nicht\s+markieren)\s+.*',
                    r'^(bitte|klicken|auswählen)\s+.*',
                ],
                'title_words': ['anleitung', 'handbuch', 'bericht', 'dokument', 'tutorial'],
                'min_words': 2,
                'max_words': 15,
            },
            
            # Chinese (Simplified)
            'zh-cn': {
                'heading_patterns': [
                    r'^\d+\.\s*[\u4e00-\u9fff]',  # "1. 介绍"
                    r'^第\d+章',  # "第1章"
                    r'^第\d+节',  # "第1节"
                    r'^[\u4e00-\u9fff]{2,10}$',  # Chinese characters only
                ],
                'false_positive_patterns': [
                    r'^请\s*不要\s*选择.*',
                    r'^请\s*点击.*',
                ],
                'title_words': ['指南', '手册', '报告', '文档', '教程'],
                'min_words': 1,  # Chinese words can be shorter
                'max_words': 10,
            },
            
            # Japanese
            'ja': {
                'heading_patterns': [
                    r'^\d+\.\s*[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]',
                    r'^第\d+章',
                    r'^第\d+節',
                    r'^[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]{2,15}$',
                ],
                'false_positive_patterns': [
                    r'^選択しないでください.*',
                    r'^クリックしてください.*',
                ],
                'title_words': ['ガイド', 'マニュアル', 'レポート', 'ドキュメント', 'チュートリアル'],
                'min_words': 1,
                'max_words': 10,
            },
            
            # Arabic
            'ar': {
                'heading_patterns': [
                    r'^\d+\.\s*[\u0600-\u06ff]',
                    r'^الفصل\s+\d+',
                    r'^القسم\s+\d+',
                    r'^[\u0600-\u06ff\s]{3,20}$',
                ],
                'false_positive_patterns': [
                    r'^لا\s+تختر.*',
                    r'^يرجى\s+النقر.*',
                ],
                'title_words': ['دليل', 'كتيب', 'تقرير', 'وثيقة', 'برنامج تعليمي'],
                'min_words': 1,
                'max_words': 10,
            },
            
            # Hindi
            'hi': {
                'heading_patterns': [
                    r'^\d+\.\s*[\u0900-\u097f]',
                    r'^अध्याय\s+\d+',
                    r'^खंड\s+\d+',
                    r'^[\u0900-\u097f\s]{3,20}$',
                ],
                'false_positive_patterns': [
                    r'^कृपया\s+चुनें\s+नहीं.*',
                    r'^कृपया\s+क्लिक.*',
                ],
                'title_words': ['गाइड', 'मैनुअल', 'रिपोर्ट', 'दस्तावेज़', 'ट्यूटोरियल'],
                'min_words': 1,
                'max_words': 10,
            },
        }
    
    def _initialize_ml_models(self):
        """Initialize multilingual ML models"""
        self.logger.info("🤖 Loading multilingual ML models...")
        
        try:
            # Use multilingual sentence transformer
            self.semantic_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            
            # For classification, use a multilingual model
            model_name = 'microsoft/mdeberta-v3-base'
            self.classification_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.classification_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            self.logger.info("🎆 Multilingual ML models ready")
        except Exception as e:
            self.logger.error(f"Failed to initialize multilingual ML models: {e}")
            raise
    
    def extract_text_spans_with_language(self, pdf_path: str) -> List[TextSpan]:
        """Extract text spans with language detection"""
        spans = []
        
        try:
            doc = fitz.open(pdf_path)
            
            # First pass: extract all spans
            all_text_blocks = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_spans = self._extract_clean_text_spans(page, page_num)
                spans.extend(page_spans)
                
                # Collect text for language detection
                page_text = ' '.join([span.text for span in page_spans if len(span.text) > 3])
                if page_text:
                    all_text_blocks.append(page_text)
            
            doc.close()
            
            # Detect document language(s)
            document_languages = self._detect_document_languages(all_text_blocks)
            self.logger.info(f"Detected document languages: {document_languages}")
            
            # Second pass: assign languages to spans
            for span in spans:
                if len(span.text) >= 10:  # Long enough for reliable detection
                    lang, conf = self.language_detector.detect_language(span.text)
                    span.language = lang
                    span.confidence = conf
                else:
                    # Use most common document language for short spans
                    span.language = document_languages[0][0] if document_languages else 'en'
                    span.confidence = 0.5
            
            return self._robust_deduplicate_spans(spans)
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            return []
    
    def _extract_clean_text_spans(self, page, page_num: int) -> List[TextSpan]:
        """Extract text spans cleanly without overlaps or duplicates"""
        spans = []
        
        try:
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if len(text) >= 2:
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
    
    def _detect_document_languages(self, text_blocks: List[str]) -> List[Tuple[str, float]]:
        """Detect primary languages in the document"""
        if not text_blocks:
            return [('en', 0.5)]
        
        language_scores = defaultdict(list)
        
        for block in text_blocks:
            if len(block) > 50:  # Only use substantial text blocks
                lang, conf = self.language_detector.detect_language(block)
                language_scores[lang].append(conf)
        
        # Calculate average confidence for each language
        lang_averages = []
        for lang, scores in language_scores.items():
            avg_score = sum(scores) / len(scores)
            lang_averages.append((lang, avg_score))
        
        # Sort by confidence and return top languages
        lang_averages.sort(key=lambda x: x[1], reverse=True)
        return lang_averages[:3]  # Top 3 languages
    
    def _robust_deduplicate_spans(self, spans: List[TextSpan]) -> List[TextSpan]:
        """Remove duplicate and overlapping text spans"""
        if not spans:
            return []
        
        sorted_spans = sorted(spans, key=lambda s: (s.page_num, s.bbox[1], s.bbox[0]))
        
        unique_spans = []
        seen_texts = set()
        
        for span in sorted_spans:
            text_key = span.text.lower().strip()
            
            if text_key in seen_texts:
                continue
            
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
        
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        return x_overlap > tolerance and y_overlap > tolerance
    
    def is_heading_candidate_multilingual(self, span: TextSpan, font_stats: Dict, page_height: float) -> bool:
        """Language-aware heading candidate detection"""
        text = span.text.strip()
        language = span.language or 'en'
        
        # Basic length check
        if len(text) < self.min_heading_length:
            return False
        
        # Get language-specific configuration
        lang_config = self.language_configs.get(language, self.language_configs['en'])
        
        # Check against language-specific false positive patterns
        for pattern in lang_config['false_positive_patterns']:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        
        # Universal false positive checks
        if self._is_universal_false_positive(text):
            return False
        
        # Font size check
        size_ratio = span.font_size / font_stats["body_font_size"]
        if size_ratio < self.font_size_threshold and not span.is_bold:
            return False
        
        # Language-specific content patterns
        if self._matches_heading_patterns(text, language):
            return True
        
        # Universal heading indicators
        if self._has_universal_heading_indicators(text, span):
            return True
        
        return False
    
    def _is_universal_false_positive(self, text: str) -> bool:
        """Universal false positive patterns that work across languages"""
        # Very long text (likely paragraphs)
        if len(text) > 200:
            return True
        
        # Only numbers and punctuation
        if re.match(r'^[\d\s\.\-\(\)\[\]{}]+$', text):
            return True
        
        # Only punctuation
        if re.match(r'^[^\w\s]+$', text):
            return True
        
        # Common UI elements (language-agnostic)
        if re.match(r'^(OK|Cancel|Yes|No|Submit|Save|Delete|Close|Apply)$', text, re.IGNORECASE):
            return True
        
        # URLs and emails
        if re.match(r'^(https?://|www\.|[\w\.-]+@[\w\.-]+).*', text, re.IGNORECASE):
            return True
        
        return False
    
    def _matches_heading_patterns(self, text: str, language: str) -> bool:
        """Check if text matches language-specific heading patterns"""
        lang_config = self.language_configs.get(language, self.language_configs['en'])
        
        for pattern in lang_config['heading_patterns']:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _has_universal_heading_indicators(self, text: str, span: TextSpan) -> bool:
        """Universal heading indicators that work across languages"""
        # Bold and reasonably sized
        if span.is_bold and span.font_size > 10:
            word_count = len(text.split())
            if 1 <= word_count <= 12:  # Reasonable heading length
                return True
        
        # All caps and short
        if text.isupper() and 2 <= len(text.split()) <= 8:
            return True
        
        # Starts with number (universal pattern)
        if re.match(r'^\d+[\.\)\s]', text):
            return True
        
        return False
    
    def analyze_font_statistics(self, spans: List[TextSpan]) -> Dict[str, any]:
        """Analyze font patterns to identify body text and potential headings"""
        if not spans:
            return {"body_font_size": 12, "font_size_histogram": {}, "unique_sizes": []}
        
        font_sizes = [span.font_size for span in spans if span.font_size > 0]
        size_counter = Counter(font_sizes)
        
        # Body text is the most common font size
        body_font_size = size_counter.most_common(1)[0][0] if size_counter else 12
        
        # Heading threshold
        heading_threshold = body_font_size * self.font_size_threshold
        
        # Statistical analysis for heading sizes (from competitor's approach)
        significant_sizes = []
        median_size = statistics.median(font_sizes) if font_sizes else 12
        
        for size, count in size_counter.items():
            if (size > median_size + 2 and 
                1 < count < len(spans) * 0.1):  # Not too common (body text) or too rare (noise)
                significant_sizes.append(size)
        
        significant_sizes = sorted(significant_sizes, reverse=True)[:3]  # Top 3 for H1, H2, H3
        
        return {
            "body_font_size": body_font_size,
            "heading_threshold": heading_threshold,
            "font_size_histogram": dict(size_counter),
            "unique_sizes": sorted(set(font_sizes), reverse=True),
            "significant_sizes": significant_sizes
        }
    
    def score_heading_candidate_multilingual(self, span: TextSpan, font_stats: Dict, page_height: float) -> float:
        """Multilingual heading candidate scoring"""
        text = span.text.strip()
        language = span.language or 'en'
        
        if not self.is_heading_candidate_multilingual(span, font_stats, page_height):
            return 0.0
        
        score = 0.0
        
        # 1. Font Size Score (45%)
        size_ratio = span.font_size / font_stats["body_font_size"]
        if size_ratio >= self.font_size_threshold:
            if size_ratio >= 2.0:
                font_score = 1.0
            elif size_ratio >= 1.5:
                font_score = 0.9
            elif size_ratio >= 1.2:
                font_score = 0.7
            else:
                font_score = 0.5
            score += font_score * self.scoring_weights['font_size']
        
        # 2. Content Pattern Score (30%)
        content_score = 0.0
        
        # Language-specific patterns
        if self._matches_heading_patterns(text, language):
            content_score = 1.0
        elif self._has_universal_heading_indicators(text, span):
            content_score = 0.8
        else:
            # Length-based scoring with language consideration
            lang_config = self.language_configs.get(language, self.language_configs['en'])
            word_count = len(text.split())
            
            if lang_config['min_words'] <= word_count <= lang_config['max_words']:
                content_score = 0.6
        
        score += content_score * self.scoring_weights['content']
        
        # 3. Formatting Score (15%)
        format_score = 0.0
        if span.is_bold:
            format_score += 0.6
        if span.is_italic:
            format_score += 0.4
        score += format_score * self.scoring_weights['formatting']
        
        # 4. Position Score (10%)
        if page_height > 0:
            relative_y = 1.0 - (span.bbox[1] / page_height)
            if relative_y > 0.8:
                position_score = 1.0
            elif relative_y > 0.6:
                position_score = 0.6
            elif relative_y > 0.4:
                position_score = 0.3
            else:
                position_score = 0.1
            score += position_score * self.scoring_weights['position']
        
        # Language confidence bonus
        if span.confidence and span.confidence > 0.8:
            score *= 1.1  # 10% bonus for high language confidence
        
        return min(score, 1.0)
    
    def classify_heading_level_multilingual(self, score: float, span: TextSpan, font_stats: Dict) -> Optional[str]:
        """Multilingual heading level classification using statistical approach"""
        if score < 0.25:
            return None
        
        # Use statistical font size analysis (from competitor's approach)
        significant_sizes = font_stats.get("significant_sizes", [])
        
        if significant_sizes:
            # Map top 3 font sizes to heading levels
            if span.font_size >= significant_sizes[0]:
                return "H1"
            elif len(significant_sizes) > 1 and span.font_size >= significant_sizes[1]:
                return "H2"
            elif len(significant_sizes) > 2 and span.font_size >= significant_sizes[2]:
                return "H3"
        
        # Fallback to score-based classification
        size_ratio = span.font_size / font_stats["body_font_size"]
        
        if score >= 0.7 or size_ratio >= 1.8:
            return "H1"
        elif score >= 0.5 or size_ratio >= 1.4:
            return "H2"
        elif score >= 0.3 or size_ratio >= 1.15:
            return "H3"
        
        return None
    
    def detect_title_multilingual(self, pdf_path: str, spans: List[TextSpan]) -> str:
        """Multilingual title detection"""
        try:
            # Strategy 1: Check PDF metadata
            doc = fitz.open(pdf_path)
            metadata_title = doc.metadata.get("title", "").strip()
            doc.close()
            
            if metadata_title and len(metadata_title) > 3:
                return metadata_title
            
            # Strategy 2: Find largest text in top area of first page
            first_page_spans = [s for s in spans if s.page_num == 0]
            if not first_page_spans:
                return "Untitled Document"
            
            # Get page dimensions
            doc = fitz.open(pdf_path)
            page = doc[0]
            page_height = page.rect.height
            doc.close()
            
            # Title candidates from top 30% of first page
            top_30_percent = page_height * 0.7
            title_candidates = []
            
            for span in first_page_spans:
                if span.bbox[1] >= top_30_percent:
                    text = span.text.strip()
                    if 5 <= len(text) <= 150:  # Reasonable title length
                        # Score based on font size and position
                        score = span.font_size + (1 - span.bbox[1] / page_height) * 10
                        if span.is_bold:
                            score += 5
                        title_candidates.append((score, text))
            
            if title_candidates:
                title_candidates.sort(reverse=True)
                return title_candidates[0][1]
            
            # Strategy 3: Use filename as fallback
            filename = os.path.basename(pdf_path)
            return os.path.splitext(filename)[0].replace('_', ' ').title()
            
        except Exception as e:
            self.logger.error(f"Error detecting title: {e}")
            return "Untitled Document"
    
    def detect_headings_multilingual(self, pdf_path: str) -> List[Dict]:
        """Multilingual heading detection"""
        try:
            spans = self.extract_text_spans_with_language(pdf_path)
            if not spans:
                return []
            
            font_stats = self.analyze_font_statistics(spans)
            
            # Get page height for position scoring
            doc = fitz.open(pdf_path)
            page_height = doc[0].rect.height if len(doc) > 0 else 800
            doc.close()
            
            headings = []
            seen_headings = set()
            
            for span in spans:
                score = self.score_heading_candidate_multilingual(span, font_stats, page_height)
                level = self.classify_heading_level_multilingual(score, span, font_stats)
                
                if level:
                    clean_text = self._clean_heading_text_multilingual(span.text, span.language)
                    text_key = clean_text.lower().strip()
                    
                    # Avoid duplicates
                    if (clean_text and len(clean_text) >= 2 and text_key not in seen_headings):
                        headings.append({
                            'level': level,
                            'text': clean_text,
                            'page': span.page_num + 1,
                            'language': span.language,
                            'confidence': span.confidence
                        })
                        seen_headings.add(text_key)
            
            # Sort by document order
            headings.sort(key=lambda h: (h['page'], -h.get('score', 0)))
            
            return headings
            
        except Exception as e:
            self.logger.error(f"Error detecting headings in {pdf_path}: {e}")
            return []
    
    def _clean_heading_text_multilingual(self, text: str, language: str = None) -> str:
        """Clean heading text with language awareness"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Language-specific cleaning
        if language in ['zh-cn', 'zh-tw', 'ja']:
            # For CJK languages, be more conservative with punctuation removal
            text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\.\-\(\)]+$', '', text)
        elif language == 'ar':
            # For Arabic, preserve Arabic punctuation
            text = re.sub(r'[^\w\s\u0600-\u06ff\.\-\(\)]+$', '', text)
        else:
            # For Latin-based languages
            text = re.sub(r'[^\w\s\.\-\(\)]+$', '', text)
        
        # Remove repeated characters (common in garbled text)
        text = re.sub(r'(\w)\1{3,}', r'\1', text)
        
        # Truncate very long headings
        max_length = 100 if language in ['zh-cn', 'zh-tw', 'ja'] else 80
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text.strip()
    
    def process_pdf_multilingual(self, pdf_path: str) -> Dict:
        """Process a single PDF with multilingual support"""
        try:
            start_time = time.time()
            
            # Extract spans with language detection
            spans = self.extract_text_spans_with_language(pdf_path)
            
            # Detect headings
            headings = self.detect_headings_multilingual(pdf_path)
            
            # Detect title
            title = self.detect_title_multilingual(pdf_path, spans)
            
            # Detect document languages
            document_languages = []
            if spans:
                text_blocks = [' '.join([s.text for s in spans[i:i+10]]) for i in range(0, len(spans), 10)]
                document_languages = self._detect_document_languages(text_blocks)
            
            processing_time = time.time() - start_time
            
            # Ensure we have some structure
            if not headings:
                headings = [{
                    'level': 'H1',
                    'text': 'Document Content',
                    'page': 1,
                    'language': document_languages[0][0] if document_languages else 'en',
                    'confidence': 0.5
                }]
            
            result = {
                'title': title,
                'outline': headings,
                'metadata': {
                    'processing_time': processing_time,
                    'detected_languages': document_languages,
                    'total_spans': len(spans),
                    'total_headings': len(headings)
                }
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing {pdf_path}: {str(e)}")
            return {
                'title': Path(pdf_path).stem.replace('_', ' ').title(),
                'outline': [{
                    'level': 'H1',
                    'text': 'Document Content',
                    'page': 1,
                    'language': 'en',
                    'confidence': 0.5
                }],
                'metadata': {
                    'error': str(e),
                    'processing_time': 0,
                    'detected_languages': [('en', 0.5)],
                    'total_spans': 0,
                    'total_headings': 1
                }
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

def process_pdfs_multilingual():
    """Main processing function with multilingual support"""
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
    
    logger.info(f"🌍 Starting MULTILINGUAL PDF Processing for {len(pdf_files)} files")
    print("Starting multilingual PDF processing...")
    
    processor = MultilingualPDFProcessor()
    
    processed_count = 0
    failed_count = 0
    
    for pdf_file in pdf_files:
        file_start = time.time()
        print(f"Processing {pdf_file.name}...")
        logger.info(f"Processing {pdf_file.name}")
        
        try:
            result = processor.process_pdf_multilingual(str(pdf_file))
            
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
            
            # Log detected languages
            languages = result.get('metadata', {}).get('detected_languages', [])
            lang_info = ', '.join([f"{lang}({conf:.2f})" for lang, conf in languages[:3]])
            
            print(f"Processed {pdf_file.name} -> {output_file.name} ({file_time:.2f}s) [Languages: {lang_info}]")
            logger.info(f"✅ Successfully processed {pdf_file.name} in {file_time:.2f}s - Languages: {lang_info}")
            
            # Check performance constraint
            if file_time > 10.0:
                logger.warning(f"⚠️  Processing time {file_time:.2f}s exceeds 10s limit for {pdf_file.name}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Failed to process {pdf_file.name}: {str(e)}")
            print(f"Error processing {pdf_file.name}: {str(e)}")
    
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f}s")
    logger.info(f"🏁 Multilingual processing completed: {processed_count} successful, {failed_count} failed, total time: {total_time:.2f}s")
    print("Multilingual PDF processing completed!")

if __name__ == "__main__":
    process_pdfs_multilingual()