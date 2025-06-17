#!/usr/bin/env python3
"""
Semantic Model Trainer for PDF Heading Detection
Adobe India Hackathon 2025 - Challenge 1A

Enhances semantic similarity model with domain-specific heading patterns
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticModelTrainer:
    """Trains and enhances semantic similarity model for heading detection"""
    
    def __init__(self, base_model: str = "all-MiniLM-L6-v2"):
        self.base_model_name = base_model
        self.model = SentenceTransformer(base_model)
        
        # Predefined heading categories for semantic enhancement
        self.heading_categories = {
            'introductory': [
                'Introduction', 'Overview', 'Background', 'Preface', 'Abstract',
                'Executive Summary', 'Getting Started', 'Prologue'
            ],
            'structural': [
                'Chapter', 'Section', 'Part', 'Unit', 'Module', 'Book',
                'Volume', 'Article', 'Paper', 'Document'
            ],
            'methodological': [
                'Methodology', 'Methods', 'Approach', 'Implementation',
                'Procedure', 'Process', 'Algorithm', 'Framework'
            ],
            'analytical': [
                'Analysis', 'Results', 'Findings', 'Data', 'Statistics',
                'Evaluation', 'Assessment', 'Review', 'Study'
            ],
            'conclusive': [
                'Conclusion', 'Summary', 'Discussion', 'Implications',
                'Recommendations', 'Future Work', 'Limitations', 'Epilogue'
            ],
            'reference': [
                'References', 'Bibliography', 'Citations', 'Sources',
                'Index', 'Glossary', 'Appendix', 'Annexes'
            ],
            'organizational': [
                'Table of Contents', 'Contents', 'Index', 'List of Figures',
                'List of Tables', 'Acknowledgments', 'Dedication'
            ]
        }
        
        logger.info(f"Initialized semantic trainer with base model: {base_model}")

    def load_training_data(self, data_dir: str) -> Dict[str, List[str]]:
        """Load semantic training data"""
        
        data_path = Path(data_dir) / "semantic_training_data.json"
        
        if not data_path.exists():
            logger.warning(f"Semantic training data not found at {data_path}")
            return {}
        
        with open(data_path, 'r') as f:
            training_data = json.load(f)
        
        logger.info("Loaded semantic training data:")
        for category, examples in training_data.items():
            logger.info(f"  {category}: {len(examples)} examples")
        
        return training_data

    def create_positive_pairs(self, training_data: Dict[str, List[str]]) -> List[Tuple[str, str, float]]:
        """Create positive pairs for contrastive learning"""
        
        positive_pairs = []
        
        # Create pairs within the same category (high similarity)
        for category, examples in training_data.items():
            if len(examples) > 1:
                for i in range(len(examples)):
                    for j in range(i + 1, len(examples)):
                        positive_pairs.append((examples[i], examples[j], 0.9))
        
        # Create pairs with predefined categories
        for category, predefined_examples in self.heading_categories.items():
            for predefined in predefined_examples:
                # Match with training examples
                for training_category, training_examples in training_data.items():
                    for training_example in training_examples:
                        if self._are_semantically_similar(predefined, training_example):
                            positive_pairs.append((predefined, training_example, 0.85))
        
        logger.info(f"Created {len(positive_pairs)} positive pairs")
        return positive_pairs

    def create_negative_pairs(self, training_data: Dict[str, List[str]]) -> List[Tuple[str, str, float]]:
        """Create negative pairs for contrastive learning"""
        
        negative_pairs = []
        
        # Non-heading examples (from detailed training data)
        non_heading_examples = [
            "Please click here to continue",
            "Do not check this box",
            "The quick brown fox jumps",
            "This is regular paragraph text",
            "Lorem ipsum dolor sit amet",
            "Copyright 2024 Company Name",
            "Page 1 of 10",
            "www.example.com",
            "user@email.com",
            "Save and Continue",
            "Cancel",
            "Submit Form",
            "Next Page",
            "Previous",
            "Error: File not found",
            "Loading...",
            "Click OK to proceed"
        ]
        
        # Create negative pairs
        all_headings = []
        for examples in training_data.values():
            all_headings.extend(examples)
        
        for predefined in self.heading_categories.values():
            all_headings.extend(predefined)
        
        # Pair headings with non-headings (low similarity)
        for heading in all_headings[:50]:  # Limit to avoid too many pairs
            for non_heading in non_heading_examples:
                negative_pairs.append((heading, non_heading, 0.1))
        
        logger.info(f"Created {len(negative_pairs)} negative pairs")
        return negative_pairs

    def _are_semantically_similar(self, text1: str, text2: str, threshold: float = 0.6) -> bool:
        """Check if two texts are semantically similar"""
        
        # Simple keyword matching for efficiency
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0
        return jaccard_similarity > threshold

    def create_training_examples(self, positive_pairs: List[Tuple[str, str, float]], 
                                negative_pairs: List[Tuple[str, str, float]]) -> List[InputExample]:
        """Create training examples for sentence transformer"""
        
        training_examples = []
        
        # Add positive pairs
        for text1, text2, score in positive_pairs:
            training_examples.append(InputExample(texts=[text1, text2], label=score))
        
        # Add negative pairs
        for text1, text2, score in negative_pairs:
            training_examples.append(InputExample(texts=[text1, text2], label=score))
        
        logger.info(f"Created {len(training_examples)} training examples")
        return training_examples

    def create_evaluation_examples(self, training_data: Dict[str, List[str]]) -> List[InputExample]:
        """Create evaluation examples"""
        
        eval_examples = []
        
        # Test pairs with known similarities
        test_pairs = [
            ("Introduction", "Overview", 0.8),
            ("Chapter 1", "Section 1", 0.7),
            ("Summary", "Conclusion", 0.9),
            ("References", "Bibliography", 0.95),
            ("Introduction", "Please click here", 0.1),
            ("Chapter", "Lorem ipsum", 0.05),
            ("Methodology", "Methods", 0.9),
            ("Analysis", "Results", 0.7),
        ]
        
        for text1, text2, score in test_pairs:
            eval_examples.append(InputExample(texts=[text1, text2], label=score))
        
        return eval_examples

    def fine_tune_model(self, training_examples: List[InputExample], 
                       eval_examples: List[InputExample], 
                       output_dir: str = "models/semantic_heading_model") -> SentenceTransformer:
        """Fine-tune the semantic model"""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create data loader
        train_dataloader = DataLoader(training_examples, shuffle=True, batch_size=16)
        
        # Define loss function
        train_loss = losses.CosineSimilarityLoss(self.model)
        
        # Create evaluator
        evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
            eval_examples, name='heading-eval'
        )
        
        logger.info("Starting semantic model fine-tuning...")
        
        # Fine-tune the model
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=3,
            evaluation_steps=100,
            warmup_steps=100,
            output_path=output_dir,
            save_best_model=True,
            show_progress_bar=True
        )
        
        logger.info(f"Model saved to {output_dir}")
        return self.model

    def evaluate_enhanced_model(self, model_path: str, training_data: Dict[str, List[str]]) -> Dict:
        """Evaluate the enhanced semantic model"""
        
        # Load the fine-tuned model
        enhanced_model = SentenceTransformer(model_path)
        
        # Test examples
        test_examples = [
            "Introduction",
            "Chapter 1: Overview", 
            "1. Background Information",
            "Summary and Conclusions",
            "Section 2.1: Methodology",
            "References",
            "Table of Contents",
            "This is regular text content",
            "Please click here",
            "Error message"
        ]
        
        # Get embeddings
        test_embeddings = enhanced_model.encode(test_examples)
        
        # Create reference heading embeddings
        reference_headings = []
        for category_headings in self.heading_categories.values():
            reference_headings.extend(category_headings[:3])  # Top 3 from each category
        
        reference_embeddings = enhanced_model.encode(reference_headings)
        
        # Calculate similarities
        similarities = cosine_similarity(test_embeddings, reference_embeddings)
        max_similarities = np.max(similarities, axis=1)
        
        # Classify based on similarity threshold
        threshold = 0.6
        predictions = max_similarities > threshold
        
        # Expected ground truth (manual annotation)
        ground_truth = [True, True, True, True, True, True, True, False, False, False]
        
        # Calculate metrics
        accuracy = np.mean(predictions == ground_truth)
        true_positives = np.sum((predictions == True) & (ground_truth == True))
        false_positives = np.sum((predictions == True) & (ground_truth == False))
        false_negatives = np.sum((predictions == False) & (ground_truth == True))
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        results = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'test_results': []
        }
        
        # Add detailed results
        for i, (example, similarity, pred, truth) in enumerate(zip(test_examples, max_similarities, predictions, ground_truth)):
            results['test_results'].append({
                'text': example,
                'max_similarity': float(similarity),
                'predicted_heading': bool(pred),
                'actual_heading': bool(truth),
                'correct': bool(pred == truth)
            })
        
        logger.info("Enhanced model evaluation:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")
        logger.info(f"  F1 Score: {f1:.4f}")
        
        return results

    def analyze_heading_clusters(self, training_data: Dict[str, List[str]], 
                               model_path: str, output_dir: str):
        """Analyze heading clusters using the enhanced model"""
        
        model = SentenceTransformer(model_path)
        
        # Collect all headings
        all_headings = []
        heading_sources = []
        
        for category, examples in training_data.items():
            all_headings.extend(examples)
            heading_sources.extend([category] * len(examples))
        
        if len(all_headings) < 5:
            logger.warning("Not enough headings for cluster analysis")
            return
        
        # Get embeddings
        embeddings = model.encode(all_headings)
        
        # Perform clustering
        n_clusters = min(8, len(all_headings) // 2)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Analyze clusters
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_indices = np.where(cluster_labels == i)[0]
            cluster_headings = [all_headings[idx] for idx in cluster_indices]
            cluster_sources = [heading_sources[idx] for idx in cluster_indices]
            
            cluster_analysis[f'cluster_{i}'] = {
                'headings': cluster_headings,
                'sources': cluster_sources,
                'size': len(cluster_headings)
            }
        
        # Save cluster analysis
        output_path = Path(output_dir) / "cluster_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(cluster_analysis, f, indent=2)
        
        logger.info(f"Cluster analysis saved to {output_path}")
        
        # Create visualization
        try:
            from sklearn.decomposition import PCA
            
            # Reduce dimensions for visualization
            pca = PCA(n_components=2, random_state=42)
            embeddings_2d = pca.fit_transform(embeddings)
            
            # Create plot
            plt.figure(figsize=(12, 8))
            scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], 
                                c=cluster_labels, cmap='tab10', alpha=0.7)
            
            # Add labels for some points
            for i, heading in enumerate(all_headings[:20]):  # Limit labels for clarity
                plt.annotate(heading[:20], (embeddings_2d[i, 0], embeddings_2d[i, 1]), 
                           fontsize=8, alpha=0.8)
            
            plt.title('Heading Clusters - Semantic Model')
            plt.xlabel('PCA Component 1')
            plt.ylabel('PCA Component 2')
            plt.colorbar(scatter)
            plt.tight_layout()
            plt.savefig(Path(output_dir) / "heading_clusters.png", dpi=300, bbox_inches='tight')
            plt.close()
            
        except ImportError:
            logger.warning("Scikit-learn not available for PCA visualization")

def main():
    """Main function to train semantic model"""
    print("🧠 Semantic Model Trainer for PDF Heading Detection")
    print("=" * 54)
    
    # Check if training data exists
    data_dir = "training_data"
    if not Path(data_dir).exists():
        print("❌ Training data not found! Please run training_data_generator.py first.")
        return
    
    # Initialize trainer
    trainer = SemanticModelTrainer()
    
    # Load training data
    training_data = trainer.load_training_data(data_dir)
    
    if not training_data:
        print("❌ No semantic training data available!")
        return
    
    # Create training pairs
    positive_pairs = trainer.create_positive_pairs(training_data)
    negative_pairs = trainer.create_negative_pairs(training_data)
    
    # Create training and evaluation examples
    training_examples = trainer.create_training_examples(positive_pairs, negative_pairs)
    eval_examples = trainer.create_evaluation_examples(training_data)
    
    # Fine-tune model
    output_dir = "models/semantic_heading_model"
    enhanced_model = trainer.fine_tune_model(training_examples, eval_examples, output_dir)
    
    # Evaluate enhanced model
    results = trainer.evaluate_enhanced_model(output_dir, training_data)
    
    # Save evaluation results
    with open(Path(output_dir) / "evaluation_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Analyze heading clusters
    trainer.analyze_heading_clusters(training_data, output_dir, output_dir)
    
    print(f"\n✅ Semantic model training complete!")
    print(f"📊 F1 Score: {results['f1_score']:.4f}")
    print(f"💾 Model saved to: {output_dir}")

if __name__ == "__main__":
    main()