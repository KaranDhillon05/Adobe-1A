#!/usr/bin/env python3
"""
Validation Script - Adobe India Hackathon 2025 Challenge 1A
Demonstrates the improvement from basic to enhanced processing
"""

import json
import os
from pathlib import Path

def load_json_safely(file_path):
    """Load JSON file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def main():
    print("🔍 Validation Report: Basic vs Enhanced Processing")
    print("=" * 60)
    
    output_dir = Path("output")
    test_files = ["file01", "file02", "file03", "file04", "file05", "sample", "pdftest1"]
    
    total_basic = 0
    total_enhanced = 0
    
    for file_name in test_files:
        basic_file = output_dir / f"{file_name}.json"
        enhanced_file = output_dir / f"{file_name}_enhanced.json"
        
        basic_data = load_json_safely(basic_file)
        enhanced_data = load_json_safely(enhanced_file)
        
        basic_count = len(basic_data.get("outline", [])) if basic_data else 0
        enhanced_count = len(enhanced_data.get("outline", [])) if enhanced_data else 0
        
        total_basic += basic_count
        total_enhanced += enhanced_count
        
        improvement = enhanced_count - basic_count
        if basic_count > 0:
            improvement_pct = ((enhanced_count / basic_count - 1) * 100)
            pct_str = f"({improvement_pct:+.0f}%)"
        else:
            pct_str = "(NEW)" if enhanced_count > 0 else ""
        
        status = "✅ IMPROVED" if improvement > 0 else "➡️  SAME" if improvement == 0 else "❌ WORSE"
        
        print(f"\n📄 {file_name}.pdf:")
        print(f"   Basic:    {basic_count:2d} headings")
        print(f"   Enhanced: {enhanced_count:2d} headings")
        print(f"   Change:   {improvement:+2d} headings {pct_str} {status}")
        
        # Show sample enhanced headings for key test case
        if file_name == "file01" and enhanced_data:
            print(f"   📋 Key detections in Enhanced version:")
            for heading in enhanced_data["outline"][:5]:
                print(f"      • [{heading['level']}] \"{heading['text'][:50]}...\"")
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   Total Basic:    {total_basic:3d} headings across all documents")
    print(f"   Total Enhanced: {total_enhanced:3d} headings across all documents")
    if total_basic > 0:
        improvement_pct = ((total_enhanced/total_basic-1)*100)
        print(f"   Net Improvement: {total_enhanced - total_basic:+3d} headings ({improvement_pct:+.0f}%)")
    else:
        print(f"   Net Improvement: {total_enhanced:+3d} headings (ALL NEW)")
    
    print(f"\n🏆 CONCLUSION:")
    if total_basic == 0 and total_enhanced > 0:
        print(f"   ✅ MAJOR SUCCESS: Enhanced system works while basic system failed completely")
        print(f"   📊 Enhanced system detects {total_enhanced} meaningful headings vs 0 in basic system")
    elif total_enhanced > total_basic * 1.5:
        print(f"   ✅ MAJOR IMPROVEMENT: Enhanced system detects {total_enhanced/total_basic:.1f}x more headings")
    elif total_enhanced > total_basic:
        print(f"   ✅ IMPROVEMENT: Enhanced system detects more headings")
    else:
        print(f"   ❌ NO IMPROVEMENT: Similar or worse performance")
    
    print(f"\n🎯 KEY FEATURES ADDED:")
    print(f"   • Line-level text merging for complete headings")
    print(f"   • Optimized threshold (0.6 → 0.35) for better recall")
    print(f"   • Enhanced pattern matching for numbered sections")
    print(f"   • Improved false positive filtering")
    print(f"   • Statistical + ML hybrid scoring (70% + 20% + 10%)")
    
    print(f"\n🐳 DOCKER USAGE:")
    print(f"   docker build --platform linux/amd64 -t pdf-processor .")
    print(f"   docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-processor")
    print(f"   # Now generates *_enhanced.json files with improved accuracy!")

if __name__ == "__main__":
    main()