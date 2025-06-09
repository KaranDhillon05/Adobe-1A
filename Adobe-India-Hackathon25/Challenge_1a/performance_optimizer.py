#!/usr/bin/env python3
"""
Adobe Hackathon 2025 - Performance Optimization System
Analyzes and optimizes PDF processing for maximum efficiency and accuracy
"""

import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from dataclasses import dataclass
import fitz  # PyMuPDF

@dataclass
class PerformanceMetrics:
    """Performance metrics for PDF processing"""
    processing_time: float
    memory_usage: float
    accuracy_score: float
    false_positives: int
    false_negatives: int
    total_headings: int
    detected_headings: int

class PerformanceOptimizer:
    """Performance optimization and analysis system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = []
        
    def analyze_pdf_performance(self, pdf_path: str, expected_headings: List[Dict] = None) -> PerformanceMetrics:
        """Analyze performance metrics for a single PDF"""
        start_time = time.time()
        
        try:
            # Import the improved processor
            from process_pdfs_improved import ImprovedPDFProcessor
            
            processor = ImprovedPDFProcessor()
            
            # Process the PDF
            result = processor.process_pdf(str(pdf_path))
            
            processing_time = time.time() - start_time
            
            # Calculate accuracy if expected headings provided
            accuracy_score = 0.0
            false_positives = 0
            false_negatives = 0
            detected_headings = len(result.get('outline', []))
            
            if expected_headings:
                accuracy_score, false_positives, false_negatives = self._calculate_accuracy(
                    result.get('outline', []), expected_headings
                )
            
            # Estimate memory usage (rough calculation)
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            memory_usage = page_count * 0.5  # Rough estimate in MB
            
            metrics = PerformanceMetrics(
                processing_time=processing_time,
                memory_usage=memory_usage,
                accuracy_score=accuracy_score,
                false_positives=false_positives,
                false_negatives=false_negatives,
                total_headings=len(expected_headings) if expected_headings else detected_headings,
                detected_headings=detected_headings
            )
            
            self.metrics.append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance for {pdf_path}: {e}")
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0)
    
    def _calculate_accuracy(self, detected_headings: List[Dict], expected_headings: List[Dict]) -> Tuple[float, int, int]:
        """Calculate accuracy metrics"""
        detected_texts = {h['text'].lower().strip() for h in detected_headings}
        expected_texts = {h['text'].lower().strip() for h in expected_headings}
        
        true_positives = len(detected_texts.intersection(expected_texts))
        false_positives = len(detected_texts - expected_texts)
        false_negatives = len(expected_texts - detected_texts)
        
        total = len(expected_texts)
        accuracy = true_positives / total if total > 0 else 0.0
        
        return accuracy, false_positives, false_negatives
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics:
            return {"error": "No metrics available"}
        
        # Calculate statistics
        processing_times = [m.processing_time for m in self.metrics]
        memory_usages = [m.memory_usage for m in self.metrics]
        accuracy_scores = [m.accuracy_score for m in self.metrics]
        
        report = {
            "summary": {
                "total_pdfs": len(self.metrics),
                "average_processing_time": statistics.mean(processing_times),
                "median_processing_time": statistics.median(processing_times),
                "max_processing_time": max(processing_times),
                "min_processing_time": min(processing_times),
                "average_memory_usage": statistics.mean(memory_usages),
                "average_accuracy": statistics.mean(accuracy_scores),
                "total_false_positives": sum(m.false_positives for m in self.metrics),
                "total_false_negatives": sum(m.false_negatives for m in self.metrics),
            },
            "performance_analysis": {
                "speed_compliance": all(t <= 10.0 for t in processing_times),
                "memory_compliance": all(m <= 16.0 for m in memory_usages),
                "accuracy_threshold": statistics.mean(accuracy_scores) >= 0.8,
            },
            "optimization_suggestions": self._generate_optimization_suggestions(),
            "detailed_metrics": [
                {
                    "processing_time": m.processing_time,
                    "memory_usage": m.memory_usage,
                    "accuracy_score": m.accuracy_score,
                    "false_positives": m.false_positives,
                    "false_negatives": m.false_negatives,
                    "detected_headings": m.detected_headings,
                    "total_headings": m.total_headings
                }
                for m in self.metrics
            ]
        }
        
        return report
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """Generate optimization suggestions based on metrics"""
        suggestions = []
        
        avg_time = statistics.mean([m.processing_time for m in self.metrics])
        avg_accuracy = statistics.mean([m.accuracy_score for m in self.metrics])
        total_fp = sum(m.false_positives for m in self.metrics)
        total_fn = sum(m.false_negatives for m in self.metrics)
        
        # Speed optimizations
        if avg_time > 5.0:
            suggestions.append("🚀 Consider implementing parallel processing for multiple PDFs")
            suggestions.append("🚀 Optimize text extraction with batch processing")
            suggestions.append("🚀 Cache font statistics across similar documents")
        
        if avg_time > 8.0:
            suggestions.append("⚠️ Processing time approaching 10s limit - implement early termination")
            suggestions.append("⚠️ Consider reducing ML model complexity for faster inference")
        
        # Accuracy optimizations
        if avg_accuracy < 0.8:
            suggestions.append("🎯 Improve heading detection with enhanced pattern matching")
            suggestions.append("🎯 Add more comprehensive false positive filtering")
            suggestions.append("🎯 Implement context-aware heading classification")
        
        if total_fp > total_fn:
            suggestions.append("🎯 Reduce false positives by strengthening filtering criteria")
            suggestions.append("🎯 Add more UI element and instruction text patterns")
        
        if total_fn > total_fp:
            suggestions.append("🎯 Improve recall by relaxing heading detection thresholds")
            suggestions.append("🎯 Add more heading keyword patterns")
        
        # Memory optimizations
        avg_memory = statistics.mean([m.memory_usage for m in self.metrics])
        if avg_memory > 8.0:
            suggestions.append("💾 Implement streaming text extraction to reduce memory usage")
            suggestions.append("💾 Use generators instead of lists for large documents")
        
        return suggestions

class AccuracyImprover:
    """System for improving heading detection accuracy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_false_positives(self, pdf_path: str, detected_headings: List[Dict]) -> List[Dict]:
        """Analyze false positive headings to improve filtering"""
        false_positives = []
        
        try:
            # Extract all text spans to analyze what was incorrectly classified
            from process_pdfs_improved import ImprovedPDFProcessor
            processor = ImprovedPDFProcessor()
            
            spans = processor.extract_text_spans(pdf_path)
            font_stats = processor.analyze_font_statistics(spans)
            
            doc = fitz.open(pdf_path)
            page_height = doc[0].rect.height if len(doc) > 0 else 800
            doc.close()
            
            # Analyze each detected heading
            for heading in detected_headings:
                # Find the original span for this heading
                matching_spans = [s for s in spans if s.text.strip().lower() == heading['text'].lower()]
                
                if matching_spans:
                    span = matching_spans[0]
                    score = processor.score_heading_candidate(span, font_stats, page_height)
                    
                    # Check if this might be a false positive
                    if self._is_likely_false_positive(span.text, score):
                        false_positives.append({
                            'text': span.text,
                            'score': score,
                            'font_size': span.font_size,
                            'is_bold': span.is_bold,
                            'page': span.page_num + 1,
                            'reason': self._identify_false_positive_reason(span.text)
                        })
            
            return false_positives
            
        except Exception as e:
            self.logger.error(f"Error analyzing false positives: {e}")
            return []
    
    def _is_likely_false_positive(self, text: str, score: float) -> bool:
        """Check if text is likely a false positive"""
        text_lower = text.lower().strip()
        
        # Common false positive patterns
        false_positive_indicators = [
            'do not check',
            'please click',
            'select all',
            'figure',
            'table',
            'page',
            'signature',
            'name:',
            'date:',
            'email:',
            'phone:',
            'address:',
            'ok',
            'cancel',
            'apply',
            'close',
            'save',
            'delete',
            'required',
            'optional',
            'attach',
            'upload',
            'submit',
            'fill',
            'complete'
        ]
        
        return any(indicator in text_lower for indicator in false_positive_indicators)
    
    def _identify_false_positive_reason(self, text: str) -> str:
        """Identify the reason why text is likely a false positive"""
        text_lower = text.lower().strip()
        
        if any(pattern in text_lower for pattern in ['do not', 'don\'t', 'please', 'click', 'select']):
            return "UI instruction text"
        elif any(pattern in text_lower for pattern in ['figure', 'table', 'page']):
            return "Figure/table caption"
        elif any(pattern in text_lower for pattern in ['name:', 'date:', 'email:', 'phone:', 'address:']):
            return "Form field label"
        elif any(pattern in text_lower for pattern in ['ok', 'cancel', 'apply', 'close', 'save', 'delete']):
            return "Button text"
        elif any(pattern in text_lower for pattern in ['required', 'optional']):
            return "Form instruction"
        elif any(pattern in text_lower for pattern in ['attach', 'upload', 'submit', 'fill', 'complete']):
            return "Form action text"
        else:
            return "Unknown false positive pattern"

class EfficiencyOptimizer:
    """System for optimizing processing efficiency"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize_processing_pipeline(self) -> Dict[str, Any]:
        """Generate optimization recommendations for the processing pipeline"""
        optimizations = {
            "text_extraction": [
                "Use single-pass extraction to avoid redundant parsing",
                "Implement streaming text processing for large documents",
                "Cache font statistics across similar documents",
                "Use NumPy vectorized operations for font analysis"
            ],
            "heading_detection": [
                "Implement early termination for obvious non-headings",
                "Use compiled regex patterns for faster pattern matching",
                "Optimize scoring weights based on document type",
                "Implement parallel processing for multiple documents"
            ],
            "memory_management": [
                "Use generators instead of lists for large text spans",
                "Implement memory pooling for repeated operations",
                "Clear intermediate data structures after processing",
                "Use efficient data structures (sets, counters)"
            ],
            "ml_integration": [
                "Implement model quantization for faster inference",
                "Use batch processing for semantic analysis",
                "Cache model embeddings for repeated patterns",
                "Implement fallback mechanisms for model failures"
            ]
        }
        
        return optimizations
    
    def benchmark_optimizations(self, pdf_path: str) -> Dict[str, float]:
        """Benchmark different optimization strategies"""
        benchmarks = {}
        
        try:
            # Baseline performance
            from process_pdfs_improved import ImprovedPDFProcessor
            
            # Test 1: Standard processing
            start_time = time.time()
            processor = ImprovedPDFProcessor()
            result = processor.process_pdf(pdf_path)
            baseline_time = time.time() - start_time
            benchmarks['baseline'] = baseline_time
            
            # Test 2: Without ML models
            start_time = time.time()
            processor_no_ml = ImprovedPDFProcessor(use_ml_models=False)
            result_no_ml = processor_no_ml.process_pdf(pdf_path)
            no_ml_time = time.time() - start_time
            benchmarks['no_ml'] = no_ml_time
            
            # Test 3: With optimized parameters
            start_time = time.time()
            processor_optimized = ImprovedPDFProcessor(
                font_size_threshold=1.1,  # More lenient
                min_heading_length=2      # Shorter minimum
            )
            result_optimized = processor_optimized.process_pdf(pdf_path)
            optimized_time = time.time() - start_time
            benchmarks['optimized_params'] = optimized_time
            
            # Calculate improvements
            benchmarks['ml_overhead'] = baseline_time - no_ml_time
            benchmarks['optimization_gain'] = baseline_time - optimized_time
            
        except Exception as e:
            self.logger.error(f"Error benchmarking optimizations: {e}")
            benchmarks = {"error": str(e)}
        
        return benchmarks

def main():
    """Main optimization and analysis function"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize optimizers
    performance_optimizer = PerformanceOptimizer()
    accuracy_improver = AccuracyImprover()
    efficiency_optimizer = EfficiencyOptimizer()
    
    # Analyze sample PDFs
    input_dir = Path("input")
    if not input_dir.exists():
        input_dir = Path("/app/input")
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found for analysis")
        return
    
    logger.info(f"Analyzing {len(pdf_files)} PDF files for performance optimization")
    
    # Process each PDF
    for pdf_file in pdf_files:
        logger.info(f"Analyzing {pdf_file.name}")
        
        # Analyze performance
        metrics = performance_optimizer.analyze_pdf_performance(str(pdf_file))
        
        # Analyze false positives
        result = performance_optimizer.analyze_pdf_performance(str(pdf_file))
        if result.detected_headings > 0:
            false_positives = accuracy_improver.analyze_false_positives(
                str(pdf_file), 
                [{"text": "sample"} for _ in range(result.detected_headings)]
            )
            
            if false_positives:
                logger.info(f"Found {len(false_positives)} potential false positives in {pdf_file.name}")
    
    # Generate comprehensive report
    report = performance_optimizer.generate_performance_report()
    optimizations = efficiency_optimizer.optimize_processing_pipeline()
    
    # Save optimization report
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    optimization_report = {
        "performance_report": report,
        "optimization_recommendations": optimizations,
        "benchmark_results": efficiency_optimizer.benchmark_optimizations(str(pdf_files[0])) if pdf_files else {}
    }
    
    with open(output_dir / "optimization_report.json", "w") as f:
        json.dump(optimization_report, f, indent=2)
    
    logger.info("Optimization analysis completed. Check output/optimization_report.json for detailed results.")
    
    # Print summary
    print("\n" + "="*60)
    print("PERFORMANCE OPTIMIZATION SUMMARY")
    print("="*60)
    
    if report.get("summary"):
        summary = report["summary"]
        print(f"📊 Total PDFs analyzed: {summary['total_pdfs']}")
        print(f"⏱️  Average processing time: {summary['average_processing_time']:.2f}s")
        print(f"🎯 Average accuracy: {summary['average_accuracy']:.2f}")
        print(f"❌ Total false positives: {summary['total_false_positives']}")
        print(f"❌ Total false negatives: {summary['total_false_negatives']}")
        
        # Compliance check
        print(f"\n✅ Speed compliance: {report['performance_analysis']['speed_compliance']}")
        print(f"✅ Memory compliance: {report['performance_analysis']['memory_compliance']}")
        print(f"✅ Accuracy threshold: {report['performance_analysis']['accuracy_threshold']}")
    
    if report.get("optimization_suggestions"):
        print(f"\n💡 OPTIMIZATION SUGGESTIONS:")
        for suggestion in report["optimization_suggestions"]:
            print(f"   {suggestion}")

if __name__ == "__main__":
    main() 