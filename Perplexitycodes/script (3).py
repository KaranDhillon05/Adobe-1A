# Fix the regex issue and create Challenge 1a processor

challenge_1a_processor = '''"""
Challenge 1a: PDF Outline Extraction
High-performance outline extraction meeting all hackathon constraints
"""

import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any
import sys

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.pdf_processor import PDFProcessor

class Challenge1AProcessor:
    """Optimized processor for Challenge 1a outline extraction"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.processing_times = []
        
    def validate_output_schema(self, output: Dict[str, Any]) -> bool:
        """Validate output against required schema"""
        try:
            # Check required fields
            if "title" not in output or "outline" not in output:
                return False
                
            if not isinstance(output["title"], str):
                return False
                
            if not isinstance(output["outline"], list):
                return False
            
            # Validate each outline item
            for item in output["outline"]:
                if not isinstance(item, dict):
                    return False
                    
                required_fields = ["level", "text", "page"]
                if not all(field in item for field in required_fields):
                    return False
                    
                if not isinstance(item["level"], str):
                    return False
                    
                if not isinstance(item["text"], str):
                    return False
                    
                if not isinstance(item["page"], int):
                    return False
                    
                # Validate level values
                if item["level"] not in ["H1", "H2", "H3", "H4", "H5", "H6"]:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Schema validation error: {e}")
            return False
    
    def process_single_pdf(self, input_path: str) -> Dict[str, Any]:
        """Process single PDF and return structured outline"""
        start_time = time.time()
        
        try:
            # Extract outline using core processor
            result = self.pdf_processor.extract_outline(input_path)
            
            # Validate output
            if not self.validate_output_schema(result):
                self.logger.warning(f"Output schema validation failed for {input_path}")
                result = {"title": "Schema Validation Error", "outline": []}
            
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            self.logger.info(f"Processed {input_path} in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {input_path}: {e}")
            return {"title": "Processing Error", "outline": []}
    
    def process_all_pdfs(self, input_dir: str, output_dir: str) -> bool:
        """Process all PDFs in input directory"""
        try:
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            
            # Create output directory if it doesn't exist
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Find all PDF files
            pdf_files = list(input_path.glob("*.pdf"))
            
            if not pdf_files:
                self.logger.warning(f"No PDF files found in {input_dir}")
                return True
            
            self.logger.info(f"Processing {len(pdf_files)} PDF files")
            
            # Process each PDF
            for pdf_file in pdf_files:
                # Extract outline
                outline_data = self.process_single_pdf(str(pdf_file))
                
                # Save JSON output
                output_file = output_path / f"{pdf_file.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(outline_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Saved outline: {output_file}")
            
            # Performance summary
            if self.processing_times:
                avg_time = sum(self.processing_times) / len(self.processing_times)
                max_time = max(self.processing_times)
                self.logger.info(f"Average processing time: {avg_time:.2f}s")
                self.logger.info(f"Maximum processing time: {max_time:.2f}s")
                
                # Check if we're meeting performance requirements
                if max_time > 10.0:
                    self.logger.warning("⚠️  Maximum processing time exceeds 10s limit!")
                else:
                    self.logger.info("✅ All PDFs processed within 10s limit")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            return False

def main():
    """Main entry point for Challenge 1a"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Default paths as specified in hackathon requirements
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    processor = Challenge1AProcessor()
    
    success = processor.process_all_pdfs(input_dir, output_dir)
    
    if success:
        print("✅ Challenge 1a processing completed successfully")
        return 0
    else:
        print("❌ Challenge 1a processing failed")
        return 1

if __name__ == "__main__":
    exit(main())
'''

# Write Challenge 1a processor
with open("adobe_pdf_processor/challenge1a/processor.py", "w") as f:
    f.write(challenge_1a_processor)

print("✅ Created Challenge 1a processor")