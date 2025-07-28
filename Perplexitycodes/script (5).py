# Create the main entry point and Docker configuration

main_entry_point = '''#!/usr/bin/env python3
"""
Adobe Hackathon 2025 - Main Entry Point
Intelligent PDF processing system for both Challenge 1a and Challenge 1b
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add modules to path
sys.path.append(os.path.dirname(__file__))

from challenge1a.processor import Challenge1AProcessor
from challenge1b.processor import Challenge1BProcessor

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/adobe_processor.log')
        ]
    )

def detect_challenge_mode() -> str:
    """Auto-detect which challenge to run based on environment"""
    
    # Check for Challenge 1a structure (standard Docker mount points)
    if Path("/app/input").exists() and Path("/app/output").exists():
        return "1a"
    
    # Check for Challenge 1b structure
    if any(Path(f"/app/challenge1b/Collection {i}").exists() for i in range(1, 4)):
        return "1b"
    
    # Check current directory for challenge files
    if Path("challenge1b_input.json").exists():
        return "1b"
    
    # Default to Challenge 1a if input directory exists
    if Path("./input").exists():
        return "1a"
    
    # Default fallback
    return "1a"

def main():
    """Main entry point with automatic challenge detection"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='Adobe Hackathon PDF Processor')
    parser.add_argument('--challenge', choices=['1a', '1b'], 
                       help='Specify challenge mode (auto-detected if not provided)')
    parser.add_argument('--input-dir', default='/app/input',
                       help='Input directory for Challenge 1a')
    parser.add_argument('--output-dir', default='/app/output',
                       help='Output directory for Challenge 1a')
    parser.add_argument('--collection-dir', default='/app/challenge1b',
                       help='Base directory for Challenge 1b collections')
    
    args = parser.parse_args()
    
    # Detect challenge mode if not specified
    challenge_mode = args.challenge or detect_challenge_mode()
    
    logger.info(f"🚀 Starting Adobe Hackathon PDF Processor")
    logger.info(f"Challenge Mode: {challenge_mode}")
    
    try:
        if challenge_mode == "1a":
            logger.info("🔍 Running Challenge 1a: PDF Outline Extraction")
            processor = Challenge1AProcessor()
            
            success = processor.process_all_pdfs(args.input_dir, args.output_dir)
            
            if success:
                logger.info("✅ Challenge 1a completed successfully")
                return 0
            else:
                logger.error("❌ Challenge 1a failed")
                return 1
                
        elif challenge_mode == "1b":
            logger.info("🧠 Running Challenge 1b: Persona-Driven Content Analysis")
            processor = Challenge1BProcessor()
            
            success = processor.process_all_collections(args.collection_dir)
            
            if success:
                logger.info("✅ Challenge 1b completed successfully")
                return 0
            else:
                logger.error("❌ Challenge 1b failed")
                return 1
        
        else:
            logger.error(f"Invalid challenge mode: {challenge_mode}")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
'''

# Write main entry point
with open("adobe_pdf_processor/main.py", "w") as f:
    f.write(main_entry_point)

# Create requirements file
requirements = '''# Adobe Hackathon 2025 - PDF Processing System Requirements

# Core PDF processing (fastest available)
PyMuPDF>=1.23.0

# Numerical computing and machine learning
numpy>=1.21.0
scikit-learn>=1.0.0

# Natural language processing
nltk>=3.8
sentence-transformers>=2.2.0

# For Challenge 1b semantic analysis (lightweight model)
# Ensures model size stays under 1GB constraint

# Standard library dependencies (should be included in base image)
pathlib2>=2.3.0
typing-extensions>=4.0.0

# Optional: for improved performance
# numba>=0.56.0  # Uncomment if JIT compilation is needed
'''

with open("adobe_pdf_processor/requirements.txt", "w") as f:
    f.write(requirements)

print("✅ Created main entry point and requirements file")