# Adobe India Hackathon 2025 - Problem Statement Summary

## Challenge Overview: "Connecting the Dots"

### Theme
**Rethink Reading. Rediscover Knowledge**
Transform PDFs from static documents into intelligent, interactive experiences that understand structure, surface insights, and respond like a trusted research companion.

## Competition Structure

### Round 1A: Document Outline Extraction
**Goal**: Extract structured outlines from raw PDFs with blazing speed and accuracy

**Requirements**:
- Accept PDF files (up to 50 pages)
- Extract document title and hierarchical headings (H1, H2, H3) with page numbers
- Output valid JSON in specified format
- Process within ≤10 seconds for 50-page PDF

**JSON Output Format**:
```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```

### Round 1B: Persona-Driven Document Intelligence
**Goal**: Extract and prioritize relevant content from document collections based on specific persona and tasks

**Input**:
- Document Collection: 3-10 related PDFs
- Persona Definition: Role description with expertise areas
- Job-to-be-Done: Concrete task the persona needs to accomplish

**Sample Test Cases**:
1. **Academic Research**: PhD researcher analyzing Graph Neural Networks papers
2. **Business Analysis**: Investment analyst examining tech company annual reports
3. **Educational Content**: Chemistry student preparing for reaction kinetics exam

**Processing Requirements**:
- ≤60 seconds for document collections
- Model size ≤1GB
- CPU-only processing
- No internet access

### Round 2: Interactive Reading Webapp
Build beautiful, intuitive reading webapp using Adobe's PDF Embed API and Round 1 results.

## Technical Constraints

### System Requirements
- **Architecture**: AMD64 (x86_64) compatible
- **CPU**: 8 cores, 16GB RAM maximum
- **Model Size**: ≤200MB (Challenge 1a), ≤1GB (Challenge 1b)
- **Network**: Offline operation required
- **Platform**: Docker containerization mandatory

### Docker Execution Format
```bash
# Build
docker build --platform linux/amd64 -t mysolutionname:identifier .

# Run
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  mysolutionname:identifier
```

## Scoring Criteria

### Challenge 1A (45 points total)
- **Heading Detection Accuracy**: 25 points (Precision + Recall)
- **Performance**: 10 points (Time & Size Compliance)
- **Bonus - Multilingual Handling**: 10 points (e.g., Japanese)

### Challenge 1B (100 points total)
- **Section Relevance**: 60 points (Match persona + job requirements with proper ranking)
- **Sub-Section Relevance**: 40 points (Quality of granular subsection extraction)

## Key Success Factors

### Pro Tips
- Don't rely solely on font sizes for heading detection
- Test across both simple and complex PDF layouts
- Build modular code for reuse between challenges
- Keep Git repository private until deadline

### Common Pitfalls to Avoid
- No hardcoded headings or file-specific logic
- No API calls or web requests
- Don't exceed runtime/model size constraints
- Avoid over-engineering solutions

## Deliverables

### Required Submissions
1. Git project with working Dockerfile in root directory
2. All dependencies containerized
3. README.md explaining approach, models/libraries used, build/run instructions
4. approach_explanation.md (300-500 words for Challenge 1b)

### Sample Data Location
GitHub repository: https://github.com/jhaaj08/Adobe-India-Hackathon25.git

## Strategic Insights

### Why This Matters
In a document-flooded world, context beats content. This challenge builds the future of intelligent reading, learning, and knowledge connection across diverse domains and user needs.

### Target Audience
- ML hackers focused on algorithmic solutions
- UI builders creating intuitive experiences  
- Insight specialists extracting meaningful patterns
- Full-stack developers building complete systems

The hackathon represents a significant opportunity to shape next-generation document intelligence systems that transform static PDFs into interactive, context-aware knowledge tools.