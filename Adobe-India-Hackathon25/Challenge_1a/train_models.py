#!/usr/bin/env python3
"""
Complete Model Training Pipeline
Adobe India Hackathon 2025 - Challenge 1A

Runs the complete training pipeline:
1. Generate training data from PDFs
2. Fine-tune BERT model for classification
3. Enhance semantic similarity model
4. Evaluate and validate models
"""

import subprocess
import sys
import time
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status"""
    logger.info(f"Starting: {description}")
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ Completed: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed: {description}")
        logger.error(f"Error: {e.stderr}")
        return False

def check_prerequisites() -> bool:
    """Check if all prerequisites are available"""
    logger.info("Checking prerequisites...")
    
    # Check if input directory exists with PDFs
    input_dir = Path("input")
    if not input_dir.exists():
        logger.error("Input directory 'input' not found!")
        return False
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        logger.error("No PDF files found in input directory!")
        return False
    
    logger.info(f"Found {len(pdf_files)} PDF files for training")
    
    # Check Python packages
    required_packages = [
        'torch', 'transformers', 'sentence-transformers', 
        'sklearn', 'pandas', 'numpy', 'matplotlib', 'seaborn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install with: pip install " + " ".join(missing_packages))
        return False
    
    logger.info("✅ All prerequisites satisfied")
    return True

def install_requirements() -> bool:
    """Install additional requirements for training"""
    logger.info("Installing training requirements...")
    
    training_requirements = [
        "torch>=1.9.0",
        "transformers>=4.20.0", 
        "sentence-transformers>=2.2.0",
        "scikit-learn>=1.0.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0"
    ]
    
    for req in training_requirements:
        command = f"{sys.executable} -m pip install {req}"
        if not run_command(command, f"Installing {req}"):
            return False
    
    return True

def generate_training_data() -> bool:
    """Generate training data from PDFs"""
    return run_command(
        f"{sys.executable} training_data_generator.py",
        "Generating training data from PDFs"
    )

def train_bert_model() -> bool:
    """Fine-tune BERT model"""
    return run_command(
        f"{sys.executable} bert_fine_tuner.py",
        "Fine-tuning BERT model for heading classification"
    )

def train_semantic_model() -> bool:
    """Enhance semantic similarity model"""
    return run_command(
        f"{sys.executable} semantic_model_trainer.py", 
        "Training enhanced semantic similarity model"
    )

def validate_models() -> bool:
    """Validate trained models"""
    logger.info("Validating trained models...")
    
    # Check if models were created
    bert_path = Path("models/bert_heading_classifier")
    semantic_path = Path("models/semantic_heading_model")
    
    if not bert_path.exists():
        logger.error("BERT model not found after training")
        return False
    
    if not semantic_path.exists():
        logger.error("Semantic model not found after training")
        return False
    
    # Check model files
    bert_files = list(bert_path.glob("*"))
    semantic_files = list(semantic_path.glob("*"))
    
    logger.info(f"BERT model files: {len(bert_files)}")
    logger.info(f"Semantic model files: {len(semantic_files)}")
    
    # Load evaluation results
    try:
        with open(bert_path / "evaluation_results.json") as f:
            bert_results = json.load(f)
        
        logger.info("BERT Model Performance:")
        logger.info(f"  Accuracy: {bert_results['overall_metrics']['accuracy']:.4f}")
        logger.info(f"  F1 Score: {bert_results['overall_metrics']['f1_score']:.4f}")
        
    except Exception as e:
        logger.warning(f"Could not load BERT evaluation results: {e}")
    
    try:
        with open(semantic_path / "evaluation_results.json") as f:
            semantic_results = json.load(f)
        
        logger.info("Semantic Model Performance:")
        logger.info(f"  Accuracy: {semantic_results['accuracy']:.4f}")
        logger.info(f"  F1 Score: {semantic_results['f1_score']:.4f}")
        
    except Exception as e:
        logger.warning(f"Could not load semantic evaluation results: {e}")
    
    logger.info("✅ Model validation completed")
    return True

def test_enhanced_system() -> bool:
    """Test the enhanced system with trained models"""
    return run_command(
        f"{sys.executable} process_pdfs_trained.py",
        "Testing enhanced PDF processing with trained models"
    )

def main():
    """Main training pipeline"""
    start_time = time.time()
    
    print("🏋️ Complete Model Training Pipeline")
    print("Adobe India Hackathon 2025 - Challenge 1A")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return False
    
    # Create output directories
    Path("training_data").mkdir(exist_ok=True)
    Path("models").mkdir(exist_ok=True)
    
    # Training pipeline steps
    steps = [
        ("Installing requirements", install_requirements),
        ("Generating training data", generate_training_data),
        ("Fine-tuning BERT model", train_bert_model),
        ("Training semantic model", train_semantic_model),
        ("Validating models", validate_models),
        ("Testing enhanced system", test_enhanced_system)
    ]
    
    successful_steps = 0
    failed_steps = []
    
    for step_name, step_function in steps:
        if step_function():
            successful_steps += 1
            logger.info(f"✅ Step completed: {step_name}")
        else:
            failed_steps.append(step_name)
            logger.error(f"❌ Step failed: {step_name}")
            
            # Ask if user wants to continue
            response = input(f"\n⚠️  Step '{step_name}' failed. Continue with remaining steps? (y/n): ")
            if response.lower() != 'y':
                break
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("🏁 Training Pipeline Complete")
    print(f"{'='*60}")
    print(f"✅ Successful steps: {successful_steps}/{len(steps)}")
    if failed_steps:
        print(f"❌ Failed steps: {failed_steps}")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    
    if successful_steps == len(steps):
        print("\n🎉 All models trained successfully!")
        print("📊 Enhanced PDF processing system is ready!")
        print("\nNext steps:")
        print("1. Run 'python process_pdfs_trained.py' to process PDFs with enhanced models")
        print("2. Compare results with baseline system")
        print("3. Fine-tune hyperparameters if needed")
        
        return True
    else:
        print(f"\n⚠️  Training completed with {len(failed_steps)} failed steps.")
        print("Please check the logs and retry failed steps individually.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)