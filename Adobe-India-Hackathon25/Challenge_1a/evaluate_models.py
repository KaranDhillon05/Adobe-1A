#!/usr/bin/env python3
"""
Model Evaluation and Comparison Tool
Adobe India Hackathon 2025 - Challenge 1A

Compares performance between:
1. Statistical analysis only
2. ML-only approach 
3. Enhanced hybrid approach with trained models
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Evaluates and compares different PDF processing approaches"""
    
    def __init__(self):
        self.results = {
            'statistical': {},
            'ml_only': {},
            'enhanced': {}
        }

    def load_results(self, output_dir: str = "output") -> Dict[str, Dict]:
        """Load results from all processing approaches"""
        
        output_path = Path(output_dir)
        
        # Load statistical results (baseline)
        for json_file in output_path.glob("*.json"):
            if not any(suffix in json_file.name for suffix in ['_ml_only', '_enhanced']):
                with open(json_file) as f:
                    data = json.load(f)
                    self.results['statistical'][json_file.stem] = data
        
        # Load ML-only results
        for json_file in output_path.glob("*_ml_only.json"):
            with open(json_file) as f:
                data = json.load(f)
                base_name = json_file.name.replace('_ml_only.json', '')
                self.results['ml_only'][base_name] = data
        
        # Load enhanced results
        for json_file in output_path.glob("*_enhanced.json"):
            with open(json_file) as f:
                data = json.load(f)
                base_name = json_file.name.replace('_enhanced.json', '')
                self.results['enhanced'][base_name] = data
        
        logger.info(f"Loaded results:")
        logger.info(f"  Statistical: {len(self.results['statistical'])} files")
        logger.info(f"  ML-only: {len(self.results['ml_only'])} files") 
        logger.info(f"  Enhanced: {len(self.results['enhanced'])} files")
        
        return self.results

    def calculate_metrics(self) -> Dict[str, Dict]:
        """Calculate performance metrics for each approach"""
        
        metrics = {}
        
        for approach_name, approach_results in self.results.items():
            if not approach_results:
                continue
                
            # Calculate aggregate metrics
            total_headings = sum(len(result['outline']) for result in approach_results.values())
            total_processing_time = sum(
                result.get('metadata', {}).get('processing_time', 0) 
                for result in approach_results.values()
            )
            avg_processing_time = total_processing_time / len(approach_results) if approach_results else 0
            avg_headings_per_doc = total_headings / len(approach_results) if approach_results else 0
            
            # Calculate quality indicators
            quality_scores = []
            for result in approach_results.values():
                outline = result.get('outline', [])
                if outline:
                    # Quality heuristics
                    has_proper_levels = any(h.get('level') in ['H1', 'H2'] for h in outline)
                    reasonable_count = 1 <= len(outline) <= 50
                    proper_text_length = all(
                        2 <= len(h.get('text', '')) <= 100 
                        for h in outline
                    )
                    
                    quality_score = sum([has_proper_levels, reasonable_count, proper_text_length]) / 3
                    quality_scores.append(quality_score)
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            metrics[approach_name] = {
                'total_documents': len(approach_results),
                'total_headings': total_headings,
                'avg_headings_per_doc': round(avg_headings_per_doc, 2),
                'avg_processing_time': round(avg_processing_time, 2),
                'avg_quality_score': round(avg_quality, 3),
                'processing_speed': round(1 / avg_processing_time if avg_processing_time > 0 else 0, 2)
            }
        
        return metrics

    def compare_specific_document(self, doc_name: str) -> Dict[str, Any]:
        """Compare results for a specific document across all approaches"""
        
        comparison = {
            'document': doc_name,
            'approaches': {}
        }
        
        for approach_name, approach_results in self.results.items():
            if doc_name in approach_results:
                result = approach_results[doc_name]
                
                comparison['approaches'][approach_name] = {
                    'title': result.get('title', 'Unknown'),
                    'heading_count': len(result.get('outline', [])),
                    'processing_time': result.get('metadata', {}).get('processing_time', 0),
                    'headings': result.get('outline', [])[:5],  # Top 5 headings
                    'method': result.get('metadata', {}).get('method', 'Unknown')
                }
        
        return comparison

    def analyze_heading_quality(self) -> Dict[str, Any]:
        """Analyze the quality of detected headings"""
        
        quality_analysis = {}
        
        for approach_name, approach_results in self.results.items():
            if not approach_results:
                continue
            
            all_headings = []
            for result in approach_results.values():
                all_headings.extend(result.get('outline', []))
            
            if not all_headings:
                continue
            
            # Analyze heading characteristics
            heading_lengths = [len(h.get('text', '')) for h in all_headings]
            heading_levels = [h.get('level', 'H4') for h in all_headings]
            
            # Count level distribution
            level_counts = {}
            for level in heading_levels:
                level_counts[level] = level_counts.get(level, 0) + 1
            
            # Quality indicators
            reasonable_lengths = sum(1 for length in heading_lengths if 5 <= length <= 80)
            has_structure = len(set(heading_levels)) > 1
            
            quality_analysis[approach_name] = {
                'total_headings': len(all_headings),
                'avg_heading_length': round(sum(heading_lengths) / len(heading_lengths), 1),
                'level_distribution': level_counts,
                'reasonable_length_ratio': round(reasonable_lengths / len(all_headings), 3),
                'has_hierarchical_structure': has_structure
            }
        
        return quality_analysis

    def create_performance_charts(self, metrics: Dict, output_dir: str = "evaluation"):
        """Create performance comparison charts"""
        
        Path(output_dir).mkdir(exist_ok=True)
        
        # Prepare data for plotting
        approaches = list(metrics.keys())
        
        if not approaches:
            logger.warning("No data available for charts")
            return
        
        # 1. Processing Time Comparison
        processing_times = [metrics[app]['avg_processing_time'] for app in approaches]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(approaches, processing_times, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        plt.title('Average Processing Time Comparison')
        plt.ylabel('Time (seconds)')
        plt.xlabel('Approach')
        
        # Add value labels on bars
        for bar, time in zip(bars, processing_times):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{time:.2f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/processing_time_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Headings per Document
        headings_per_doc = [metrics[app]['avg_headings_per_doc'] for app in approaches]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(approaches, headings_per_doc, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        plt.title('Average Headings Detected per Document')
        plt.ylabel('Number of Headings')
        plt.xlabel('Approach')
        
        for bar, count in zip(bars, headings_per_doc):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{count:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/headings_per_doc_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Quality Score Comparison
        quality_scores = [metrics[app]['avg_quality_score'] for app in approaches]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(approaches, quality_scores, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        plt.title('Average Quality Score Comparison')
        plt.ylabel('Quality Score (0-1)')
        plt.xlabel('Approach')
        plt.ylim(0, 1)
        
        for bar, score in zip(bars, quality_scores):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/quality_score_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Performance charts saved to {output_dir}/")

    def generate_evaluation_report(self, output_file: str = "evaluation/evaluation_report.json"):
        """Generate comprehensive evaluation report"""
        
        Path(output_file).parent.mkdir(exist_ok=True)
        
        # Calculate metrics
        metrics = self.calculate_metrics()
        quality_analysis = self.analyze_heading_quality()
        
        # Find common documents for detailed comparison
        common_docs = set()
        if self.results:
            common_docs = set(list(self.results.values())[0].keys())
            for approach_results in self.results.values():
                common_docs &= set(approach_results.keys())
        
        # Compare common documents
        document_comparisons = {}
        for doc in list(common_docs)[:3]:  # Limit to first 3 for brevity
            document_comparisons[doc] = self.compare_specific_document(doc)
        
        # Compile comprehensive report
        report = {
            'evaluation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'approaches_evaluated': list(metrics.keys()),
                'total_documents': len(common_docs),
                'evaluation_criteria': [
                    'Processing speed',
                    'Number of headings detected', 
                    'Quality of detected headings',
                    'Consistency across documents'
                ]
            },
            'performance_metrics': metrics,
            'quality_analysis': quality_analysis,
            'document_comparisons': document_comparisons,
            'recommendations': self._generate_recommendations(metrics, quality_analysis)
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Evaluation report saved to {output_file}")
        return report

    def _generate_recommendations(self, metrics: Dict, quality_analysis: Dict) -> List[str]:
        """Generate recommendations based on evaluation results"""
        
        recommendations = []
        
        if not metrics:
            return ["No data available for recommendations"]
        
        # Speed recommendations
        fastest_approach = min(metrics.keys(), key=lambda x: metrics[x]['avg_processing_time'])
        recommendations.append(f"Fastest processing: {fastest_approach} approach")
        
        # Quality recommendations  
        if quality_analysis:
            best_quality = max(quality_analysis.keys(), 
                              key=lambda x: quality_analysis[x].get('reasonable_length_ratio', 0))
            recommendations.append(f"Best heading quality: {best_quality} approach")
        
        # Balance recommendations
        if 'enhanced' in metrics and 'statistical' in metrics:
            enhanced_time = metrics['enhanced']['avg_processing_time']
            statistical_time = metrics['statistical']['avg_processing_time']
            
            if enhanced_time <= statistical_time * 1.5:  # Less than 50% slower
                recommendations.append("Enhanced approach provides good balance of speed and accuracy")
            else:
                recommendations.append("Statistical approach recommended for high-volume processing")
        
        return recommendations

    def print_summary(self):
        """Print evaluation summary to console"""
        
        metrics = self.calculate_metrics()
        
        print("\n📊 Model Evaluation Summary")
        print("=" * 50)
        
        if not metrics:
            print("❌ No results found to evaluate")
            return
        
        # Create comparison table
        df_data = []
        for approach, data in metrics.items():
            df_data.append({
                'Approach': approach.title(),
                'Avg Time (s)': data['avg_processing_time'],
                'Avg Headings': data['avg_headings_per_doc'],
                'Quality Score': data['avg_quality_score'],
                'Documents': data['total_documents']
            })
        
        df = pd.DataFrame(df_data)
        print(df.to_string(index=False))
        
        # Identify best performers
        if len(df) > 1:
            print(f"\n🏆 Performance Leaders:")
            fastest = df.loc[df['Avg Time (s)'].idxmin(), 'Approach']
            most_headings = df.loc[df['Avg Headings'].idxmax(), 'Approach'] 
            highest_quality = df.loc[df['Quality Score'].idxmax(), 'Approach']
            
            print(f"  ⚡ Fastest: {fastest}")
            print(f"  📄 Most headings: {most_headings}")
            print(f"  ✨ Highest quality: {highest_quality}")

def main():
    """Main evaluation function"""
    print("📈 Model Evaluation and Comparison Tool")
    print("Adobe India Hackathon 2025 - Challenge 1A")
    print("=" * 55)
    
    evaluator = ModelEvaluator()
    
    # Load all results
    results = evaluator.load_results()
    
    if not any(results.values()):
        print("❌ No results found to evaluate!")
        print("Please run the different processing approaches first:")
        print("1. python process_pdfs.py (statistical)")
        print("2. python process_pdfs_ml_only.py (ML-only)")
        print("3. python process_pdfs_trained.py (enhanced)")
        return
    
    # Generate evaluation report
    report = evaluator.generate_evaluation_report()
    
    # Create performance charts
    metrics = evaluator.calculate_metrics()
    evaluator.create_performance_charts(metrics)
    
    # Print summary
    evaluator.print_summary()
    
    print(f"\n✅ Evaluation complete!")
    print(f"📋 Report: evaluation/evaluation_report.json")
    print(f"📊 Charts: evaluation/*.png")

if __name__ == "__main__":
    main()