"""
Challenge 1b: Persona-Driven Content Analysis
Multi-collection document processing with semantic analysis
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
from core.semantic_analyzer import SemanticAnalyzer
from core.pdf_processor import PDFProcessor

class Challenge1BProcessor:
    """Advanced processor for Challenge 1b persona-driven analysis"""

    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        self.pdf_processor = PDFProcessor()
        self.logger = logging.getLogger(__name__)

    def validate_input_schema(self, input_data: Dict[str, Any]) -> bool:
        """Validate input JSON schema"""
        try:
            # Check required top-level fields
            required_fields = ["challenge_info", "documents", "persona", "job_to_be_done"]
            if not all(field in input_data for field in required_fields):
                return False

            # Validate documents array
            documents = input_data["documents"]
            if not isinstance(documents, list) or len(documents) == 0:
                return False

            for doc in documents:
                if not isinstance(doc, dict):
                    return False
                if "filename" not in doc or "title" not in doc:
                    return False

            # Validate persona
            persona = input_data["persona"]
            if not isinstance(persona, dict) or "role" not in persona:
                return False

            # Validate job_to_be_done
            job = input_data["job_to_be_done"]
            if not isinstance(job, dict) or "task" not in job:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False

    def validate_output_schema(self, output: Dict[str, Any]) -> bool:
        """Validate output against required schema"""
        try:
            # Check required fields
            required_fields = ["metadata", "extracted_sections", "subsection_analysis"]
            if not all(field in output for field in required_fields):
                return False

            # Validate metadata
            metadata = output["metadata"]
            if not isinstance(metadata, dict):
                return False

            required_meta_fields = ["input_documents", "persona", "job_to_be_done"]
            if not all(field in metadata for field in required_meta_fields):
                return False

            # Validate extracted_sections
            sections = output["extracted_sections"]
            if not isinstance(sections, list):
                return False

            for section in sections:
                if not isinstance(section, dict):
                    return False
                required_section_fields = ["document", "section_title", "importance_rank", "page_number"]
                if not all(field in section for field in required_section_fields):
                    return False

            # Validate subsection_analysis
            analysis = output["subsection_analysis"]
            if not isinstance(analysis, list):
                return False

            for item in analysis:
                if not isinstance(item, dict):
                    return False
                required_analysis_fields = ["document", "refined_text", "page_number"]
                if not all(field in item for field in required_analysis_fields):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Output validation error: {e}")
            return False

    def process_collection(self, input_file: str, output_file: str) -> bool:
        """Process a document collection based on input configuration"""
        start_time = time.time()

        try:
            # Load input configuration
            with open(input_file, 'r', encoding='utf-8') as f:
                input_config = json.load(f)

            # Validate input schema
            if not self.validate_input_schema(input_config):
                self.logger.error(f"Invalid input schema in {input_file}")
                return False

            self.logger.info(f"Processing collection: {input_config['challenge_info']['challenge_id']}")
            self.logger.info(f"Persona: {input_config['persona']['role']}")
            self.logger.info(f"Task: {input_config['job_to_be_done']['task']}")

            # Perform semantic analysis
            result = self.semantic_analyzer.analyze_collection(input_config)

            # Validate output schema
            if not self.validate_output_schema(result):
                self.logger.error(f"Invalid output schema for {input_file}")
                return False

            # Save results
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            processing_time = time.time() - start_time
            self.logger.info(f"Processed collection in {processing_time:.2f}s")

            # Check performance constraint (≤60s for collections)
            if processing_time > 60.0:
                self.logger.warning("⚠️  Processing time exceeds 60s limit!")
            else:
                self.logger.info("✅ Collection processed within 60s limit")

            return True

        except Exception as e:
            self.logger.error(f"Error processing collection {input_file}: {e}")
            return False

    def process_all_collections(self, base_dir: str) -> bool:
        """Process all collections in the base directory"""
        try:
            base_path = Path(base_dir)

            # Find all collection directories
            collections = []
            for item in base_path.iterdir():
                if item.is_dir() and item.name.startswith("Collection"):
                    input_file = item / "challenge1b_input.json"
                    if input_file.exists():
                        collections.append({
                            "dir": item,
                            "input": input_file,
                            "output": item / "challenge1b_output.json"
                        })

            if not collections:
                self.logger.warning(f"No collections found in {base_dir}")
                return True

            self.logger.info(f"Found {len(collections)} collections to process")

            success_count = 0
            for collection in collections:
                self.logger.info(f"Processing collection: {collection['dir'].name}")

                if self.process_collection(str(collection["input"]), str(collection["output"])):
                    success_count += 1
                    self.logger.info(f"✅ {collection['dir'].name} completed successfully")
                else:
                    self.logger.error(f"❌ {collection['dir'].name} failed")

            self.logger.info(f"Completed {success_count}/{len(collections)} collections")

            return success_count == len(collections)

        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            return False

def main():
    """Main entry point for Challenge 1b"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')

    # Default base directory for collections
    base_dir = "/app/challenge1b"

    # Alternative: process from current directory if available
    if not Path(base_dir).exists():
        base_dir = "."

    processor = Challenge1BProcessor()

    success = processor.process_all_collections(base_dir)

    if success:
        print("✅ Challenge 1b processing completed successfully")
        return 0
    else:
        print("❌ Challenge 1b processing failed")
        return 1

if __name__ == "__main__":
    exit(main())
