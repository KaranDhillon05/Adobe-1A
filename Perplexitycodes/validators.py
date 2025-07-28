"""
Schema validation utilities for Adobe Hackathon PDF Processor
Ensures output compliance with hackathon requirements
"""

import json
import jsonschema
from typing import Dict, Any, List
import logging

class SchemaValidator:
    """Validates JSON outputs against required schemas"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Challenge 1a schema
        self.challenge_1a_schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "outline": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "level": {"type": "string", "enum": ["H1", "H2", "H3", "H4", "H5", "H6"]},
                            "text": {"type": "string"},
                            "page": {"type": "integer", "minimum": 1}
                        },
                        "required": ["level", "text", "page"]
                    }
                }
            },
            "required": ["title", "outline"]
        }

        # Challenge 1b schema
        self.challenge_1b_schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "input_documents": {"type": "array", "items": {"type": "string"}},
                        "persona": {"type": "string"},
                        "job_to_be_done": {"type": "string"},
                        "processing_timestamp": {"type": "string"}
                    },
                    "required": ["input_documents", "persona", "job_to_be_done"]
                },
                "extracted_sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "document": {"type": "string"},
                            "section_title": {"type": "string"},
                            "importance_rank": {"type": "integer", "minimum": 1},
                            "page_number": {"type": "integer", "minimum": 1}
                        },
                        "required": ["document", "section_title", "importance_rank", "page_number"]
                    }
                },
                "subsection_analysis": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "document": {"type": "string"},
                            "refined_text": {"type": "string"},
                            "page_number": {"type": "integer", "minimum": 1}
                        },
                        "required": ["document", "refined_text", "page_number"]
                    }
                }
            },
            "required": ["metadata", "extracted_sections", "subsection_analysis"]
        }

    def validate_challenge_1a(self, data: Dict[str, Any]) -> bool:
        """Validate Challenge 1a output"""
        try:
            jsonschema.validate(instance=data, schema=self.challenge_1a_schema)
            self.logger.info("✅ Challenge 1a schema validation passed")
            return True
        except jsonschema.ValidationError as e:
            self.logger.error(f"❌ Challenge 1a schema validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Challenge 1a validation error: {e}")
            return False

    def validate_challenge_1b(self, data: Dict[str, Any]) -> bool:
        """Validate Challenge 1b output"""
        try:
            jsonschema.validate(instance=data, schema=self.challenge_1b_schema)
            self.logger.info("✅ Challenge 1b schema validation passed")
            return True
        except jsonschema.ValidationError as e:
            self.logger.error(f"❌ Challenge 1b schema validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Challenge 1b validation error: {e}")
            return False

    def validate_file(self, file_path: str, challenge: str) -> bool:
        """Validate JSON file against appropriate schema"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if challenge == "1a":
                return self.validate_challenge_1a(data)
            elif challenge == "1b":
                return self.validate_challenge_1b(data)
            else:
                self.logger.error(f"Unknown challenge: {challenge}")
                return False

        except Exception as e:
            self.logger.error(f"Error validating file {file_path}: {e}")
            return False
