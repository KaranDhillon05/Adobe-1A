# 🚀 Quick Commands Reference - Adobe Hackathon 2025

## ⚡ One-Line Complete Test
```bash
docker build --platform linux/amd64 -t pdf-processor . && docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-processor && python3 validate_improvements.py
```

## 🐳 Docker Commands

### Build Enhanced Container
```bash
docker build --platform linux/amd64 -t pdf-processor .
```

### Run Enhanced Processing
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-processor
```

### Build + Run in One Command
```bash
docker build --platform linux/amd64 -t pdf-processor . && docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-processor
```

## 🖥️ Local Commands

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Enhanced Processor
```bash
python3 process_pdfs_trained.py
```

### Run Validation Script
```bash
python3 validate_improvements.py
```

### Complete Local Test
```bash
pip install -r requirements.txt && python3 process_pdfs_trained.py && python3 validate_improvements.py
```

## 🔍 Verification Commands

### Check Enhanced Output Files
```bash
ls -la output/*_enhanced.json
```

### View Sample Results
```bash
cat output/file01_enhanced.json | head -50
```

### Count Total Headings
```bash
grep -c '"text":' output/*_enhanced.json
```

### Show Improvement Summary
```bash
python3 validate_improvements.py
```

## 📊 Expected Results

- **Enhanced Output Files**: `*_enhanced.json` in output directory
- **Total Headings**: 952+ across all documents
- **Key Detection**: "12. Amount of advance required." in file01.pdf
- **Success Message**: "✅ MAJOR SUCCESS: Enhanced system works while basic system failed completely"

## 🎯 For Judges - Recommended Flow

1. **Quick Test**: Run the one-line complete test
2. **Verify Results**: Check that enhanced JSON files are generated
3. **Review Validation**: Confirm 952+ headings detected vs 0 in basic system
4. **Spot Check**: Look at file01_enhanced.json for numbered sections

---
**🏆 Ready for Victory! Copy and paste any command above to test the enhanced system.**