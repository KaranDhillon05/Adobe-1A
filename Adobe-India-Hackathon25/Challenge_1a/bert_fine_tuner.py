#!/usr/bin/env python3
"""
BERT Fine-Tuner for PDF Heading Classification
Adobe India Hackathon 2025 - Challenge 1A

Fine-tunes BERT model specifically for PDF heading vs non-heading classification
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification, 
    Trainer, TrainingArguments, EarlyStoppingCallback
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from pathlib import Path
import json
import logging
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HeadingDataset(Dataset):
    """Dataset class for heading classification"""
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        # Tokenize text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class BERTFineTuner:
    """Fine-tunes BERT model for PDF heading classification"""
    
    def __init__(self, model_name: str = "prajjwal1/bert-tiny", max_length: int = 128):
        self.model_name = model_name
        self.max_length = max_length
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        
        logger.info(f"Using device: {self.device}")
        logger.info(f"Model: {model_name}")
        
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=2,  # Binary classification
            problem_type="single_label_classification"
        )
        
        # Add padding token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.model.config.eos_token_id

    def load_training_data(self, data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load training, validation, and test data"""
        
        data_path = Path(data_dir)
        
        train_df = pd.read_csv(data_path / "bert_train.csv")
        val_df = pd.read_csv(data_path / "bert_val.csv")
        test_df = pd.read_csv(data_path / "bert_test.csv")
        
        logger.info(f"Loaded training data:")
        logger.info(f"  Train: {len(train_df)} examples")
        logger.info(f"  Validation: {len(val_df)} examples")
        logger.info(f"  Test: {len(test_df)} examples")
        
        return train_df, val_df, test_df

    def create_datasets(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
        """Create PyTorch datasets"""
        
        train_dataset = HeadingDataset(
            texts=train_df['text'].tolist(),
            labels=train_df['label'].tolist(),
            tokenizer=self.tokenizer,
            max_length=self.max_length
        )
        
        val_dataset = HeadingDataset(
            texts=val_df['text'].tolist(),
            labels=val_df['label'].tolist(),
            tokenizer=self.tokenizer,
            max_length=self.max_length
        )
        
        test_dataset = HeadingDataset(
            texts=test_df['text'].tolist(),
            labels=test_df['label'].tolist(),
            tokenizer=self.tokenizer,
            max_length=self.max_length
        )
        
        return train_dataset, val_dataset, test_dataset

    def compute_metrics(self, eval_pred):
        """Compute metrics for evaluation"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted')
        accuracy = accuracy_score(labels, predictions)
        
        return {
            'accuracy': accuracy,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }

    def fine_tune(self, train_dataset, val_dataset, output_dir: str = "models/bert_heading_classifier"):
        """Fine-tune BERT model"""
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,  # Reduced for faster training
            per_device_train_batch_size=8,  # Reduced for compatibility
            per_device_eval_batch_size=8,
            warmup_steps=50,
            weight_decay=0.01,
            logging_dir=f'{output_dir}/logs',
            logging_steps=10,
            eval_strategy="steps",  # Updated parameter name
            eval_steps=25,
            save_strategy="steps",
            save_steps=25,
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            greater_is_better=True,
            save_total_limit=2,
            dataloader_num_workers=0,  # Avoid multiprocessing issues
            remove_unused_columns=False
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self.compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
        )
        
        logger.info("Starting BERT fine-tuning...")
        
        # Train the model
        trainer.train()
        
        # Save the model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Model saved to {output_dir}")
        
        return trainer

    def evaluate_model(self, trainer, test_dataset, test_df: pd.DataFrame, output_dir: str):
        """Evaluate the fine-tuned model"""
        
        logger.info("Evaluating fine-tuned model...")
        
        # Get predictions
        predictions = trainer.predict(test_dataset)
        y_pred = np.argmax(predictions.predictions, axis=1)
        y_true = test_df['label'].values
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')
        
        # Get per-class metrics
        precision_per_class, recall_per_class, f1_per_class, support = precision_recall_fscore_support(
            y_true, y_pred, average=None
        )
        
        # Create confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        # Compile results
        results = {
            'overall_metrics': {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1)
            },
            'per_class_metrics': {
                'non_heading': {
                    'precision': float(precision_per_class[0]),
                    'recall': float(recall_per_class[0]),
                    'f1_score': float(f1_per_class[0]),
                    'support': int(support[0])
                },
                'heading': {
                    'precision': float(precision_per_class[1]),
                    'recall': float(recall_per_class[1]),
                    'f1_score': float(f1_per_class[1]),
                    'support': int(support[1])
                }
            },
            'confusion_matrix': cm.tolist()
        }
        
        # Save results
        results_path = Path(output_dir) / "evaluation_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Create and save confusion matrix plot
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Non-Heading', 'Heading'], 
                   yticklabels=['Non-Heading', 'Heading'])
        plt.title('Confusion Matrix - BERT Heading Classifier')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(Path(output_dir) / "confusion_matrix.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Log results
        logger.info("Evaluation Results:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")
        logger.info(f"  F1 Score: {f1:.4f}")
        logger.info(f"  Non-Heading F1: {f1_per_class[0]:.4f}")
        logger.info(f"  Heading F1: {f1_per_class[1]:.4f}")
        
        return results

    def test_on_examples(self, model_dir: str, test_examples: List[str]) -> List[Dict]:
        """Test the fine-tuned model on specific examples"""
        
        # Load fine-tuned model
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model.to(self.device)
        model.eval()
        
        results = []
        
        with torch.no_grad():
            for text in test_examples:
                # Tokenize
                inputs = tokenizer(
                    text,
                    truncation=True,
                    padding='max_length',
                    max_length=self.max_length,
                    return_tensors='pt'
                ).to(self.device)
                
                # Get prediction
                outputs = model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
                
                results.append({
                    'text': text,
                    'predicted_class': predicted_class,
                    'is_heading': predicted_class == 1,
                    'confidence': confidence,
                    'heading_probability': probabilities[0][1].item(),
                    'non_heading_probability': probabilities[0][0].item()
                })
        
        return results

def main():
    """Main function to fine-tune BERT model"""
    print("🤖 BERT Fine-Tuner for PDF Heading Classification")
    print("=" * 52)
    
    # Check if training data exists
    data_dir = "training_data"
    if not Path(data_dir).exists():
        print("❌ Training data not found! Please run training_data_generator.py first.")
        return
    
    # Initialize fine-tuner
    fine_tuner = BERTFineTuner()
    
    # Load data
    train_df, val_df, test_df = fine_tuner.load_training_data(data_dir)
    
    # Create datasets
    train_dataset, val_dataset, test_dataset = fine_tuner.create_datasets(train_df, val_df, test_df)
    
    # Fine-tune model
    output_dir = "models/bert_heading_classifier"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    trainer = fine_tuner.fine_tune(train_dataset, val_dataset, output_dir)
    
    # Evaluate model
    results = fine_tuner.evaluate_model(trainer, test_dataset, test_df, output_dir)
    
    # Test on sample examples
    test_examples = [
        "Introduction",
        "Chapter 1: Overview",
        "1. Background Information",
        "This is a regular paragraph with normal text content.",
        "Summary and Conclusions",
        "Please click here to continue",
        "Section 2.1: Methodology",
        "The quick brown fox jumps over the lazy dog.",
        "References",
        "Table of Contents"
    ]
    
    print("\n🧪 Testing on sample examples:")
    example_results = fine_tuner.test_on_examples(output_dir, test_examples)
    
    for result in example_results:
        status = "✅ HEADING" if result['is_heading'] else "❌ NON-HEADING"
        print(f"{status} | {result['confidence']:.3f} | {result['text']}")
    
    print(f"\n✅ Fine-tuning complete! Model saved to: {output_dir}")
    print(f"📊 Final F1 Score: {results['overall_metrics']['f1_score']:.4f}")

if __name__ == "__main__":
    main()