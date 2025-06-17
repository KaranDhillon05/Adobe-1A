#!/usr/bin/env python3
"""
Simple validation utility for Challenge 1a JSON outputs
Ensures outputs match the required schema format
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

def validate_challenge_1a_output(data: Dict[str, Any]) -> bool:
    """Validate Challenge 1a output against required schema"""
    try:
        # Check required top-level fields
        if not isinstance(data, dict):
            print("❌ Output must be a JSON object")
            return False
        
        if "title" not in data:
            print("❌ Missing required field: title")
            return False
        
        if "outline" not in data:
            print("❌ Missing required field: outline")
            return False
        
        # Validate title
        if not isinstance(data["title"], str):
            print("❌ Field 'title' must be a string")
            return False
        
        # Validate outline
        outline = data["outline"]
        if not isinstance(outline, list):
            print("❌ Field 'outline' must be an array")
            return False
        
        # Validate outline items
        for i, item in enumerate(outline):
            if not isinstance(item, dict):
                print(f"❌ Outline item {i} must be an object")
                return False
            
            # Check required fields
            required_fields = ["level", "text", "page"]
            for field in required_fields:
                if field not in item:
                    print(f"❌ Outline item {i} missing required field: {field}")
                    return False
            
            # Validate level
            if item["level"] not in ["H1", "H2", "H3", "H4", "H5", "H6"]:
                print(f"❌ Outline item {i} has invalid level: {item['level']}")
                return False
            
            # Validate text
            if not isinstance(item["text"], str):
                print(f"❌ Outline item {i} field 'text' must be a string")
                return False
            
            # Validate page
            if not isinstance(item["page"], int) or item["page"] < 1:
                print(f"❌ Outline item {i} field 'page' must be a positive integer")
                return False
        
        print("✅ JSON output validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def validate_file(file_path: str) -> bool:
    """Validate a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Validating {file_path}...")
        return validate_challenge_1a_output(data)
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

def main():
    """Main validation function"""
    if len(sys.argv) != 2:
        print("Usage: python validate_output.py <json_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    if validate_file(file_path):
        print("🎉 Validation successful!")
        sys.exit(0)
    else:
        print("💥 Validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()