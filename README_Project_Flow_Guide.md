# Complete Project Flow Guide: Adobe Hackathon PDF Processing System

## System Overview

A sophisticated PDF processing system for Adobe India Hackathon 2025 "Connecting the Dots" challenge, featuring two integrated components:
- **Challenge 1a**: PDF outline extraction with blazing speed
- **Challenge 1b**: Persona-driven content analysis with AI-powered relevance matching

## End-to-End System Architecture

### Data Flow Pipeline
```
PDFs → Docker Container → Core Processing → Challenge Routing → JSON Output
```

The system operates as an assembly line with distinct processing stages:

### Stage 1: Input Processing
- **Function**: Receives PDF files from `/app/input` directory
- **Requirements**: Offline operation, readable files only
- **Constraints**: CPU-only, 8 cores, 16GB RAM available

### Stage 2: Core PDF Processing
- **PyMuPDF Library**: Extracts raw text, font metadata, positioning data
- **Text Analysis**: Identifies font sizes, styles (bold/italic), spatial relationships
- **Performance**: Single-pass processing for maximum efficiency
- **Output**: Structured data objects with text spans

### Stage 3: Challenge Routing

#### Challenge 1a: Document Outline Extraction
- **Goal**: Create intelligent table of contents
- **Process**: Multi-factor font analysis to identify H1/H2/H3 headings
- **Output**: JSON with document title and hierarchical outline
- **Time Constraint**: ≤10 seconds for 50-page PDF

#### Challenge 1b: Persona-Driven Analysis
- **Goal**: Extract content relevant to specific user persona and tasks
- **Process**: AI-powered semantic matching between content and user needs
- **Output**: Ranked and filtered content with importance scores
- **Time Constraint**: ≤60 seconds for document collections

### Stage 4: Output Generation
- **JSON Schema Validation**: Ensures strict format compliance
- **File Writing**: Saves results to `/app/output` directory
- **Quality Control**: Validates data integrity and completeness

## Technical Architecture (4-Layer Design)

### Layer 1: Infrastructure
- **Docker Container**: AMD64 architecture, CPU-only processing
- **File System**: Read-only input, write-only output directories
- **Resource Management**: Strict memory and time limits
- **Network Isolation**: Complete offline operation

### Layer 2: Core Libraries
- **PyMuPDF**: Fastest PDF processing library (15x faster than alternatives)
- **NumPy**: Mathematical operations and data arrays
- **Sentence Transformers**: AI model for text semantic understanding
- **JSON Validator**: Output format compliance verification

### Layer 3: Application Modules
- **PDF Text Extractor**: Preserves formatting information during text extraction
- **Font Analysis Engine**: Identifies font sizes, styles, and patterns
- **Heading Detection**: Multi-factor scoring for heading identification
- **Semantic Matching**: AI-powered content relevance scoring

### Layer 4: Processing Pipelines
- **Pipeline 1a**: Optimized for speed and outline extraction
- **Pipeline 1b**: Optimized for content understanding and filtering

## Challenge 1a: Advanced Heading Detection Algorithm

### Multi-Factor Scoring System
Each text element receives a composite score based on four weighted factors:

**Formula**: `Total Score = (Size × 0.4) + (Format × 0.3) + (Position × 0.2) + (Content × 0.1)`

### Scoring Components:

1. **Font Size Score (40% weight)**:
   - Analyze font size histogram to find body text baseline
   - Set heading threshold: 1.2× larger than most common font size
   - Larger text receives exponentially higher scores

2. **Format Score (30% weight)**:
   - Bold text: +2.0 bonus points
   - Italic text: +1.5 bonus points
   - Combined bold+italic: +3.0 bonus points

3. **Position Score (20% weight)**:
   - Text in top 20% of page: +1.5 bonus
   - Left-aligned text: +1.0 bonus
   - Center-aligned text: +0.5 bonus

4. **Content Score (10% weight)**:
   - ALL CAPS text: +1.0 bonus
   - Numbered sections (1., 1.1, etc.): +1.5 bonus
   - Heading keywords ("Chapter", "Section"): +1.0 bonus

### Classification Thresholds:
- **H1 Headlines**: Score > 0.8 (most prominent text)
- **H2 Subheadings**: Score 0.6-0.8 (medium-large prominence)
- **H3 Sub-subheadings**: Score 0.4-0.6 (smaller but notable)

### Title Detection Strategy:
1. Check PDF metadata for embedded title
2. Find largest text in top 20% of first page
3. Use filename as fallback if no clear title found

## Challenge 1b: Persona-Driven Analysis Workflow

### Input Format:
```json
{
  "documents": [{"filename": "doc1.pdf", "title": "Document Title"}],
  "persona": {"role": "Travel Planner"},
  "job_to_be_done": {"task": "Plan a 4-day trip for 10 college friends"}
}
```

### Processing Steps:
1. **Text Chunking**: Break documents into logical sections and paragraphs
2. **Semantic Analysis**: Use AI to understand meaning of each content chunk
3. **Relevance Scoring**: Match content to persona needs using vector similarity
4. **Content Ranking**: Order sections by importance to specific task
5. **Extraction**: Pull most relevant paragraphs and details with context

### Output Format:
```json
{
  "extracted_sections": [{
    "document": "travel_guide.pdf",
    "section_title": "Budget Planning for Groups",
    "importance_rank": 1,
    "page_number": 15
  }]
}
```

## Team Work Division Strategy (3-Person Team)

### Person 1: System Architect & Infrastructure Expert
**Responsibilities**: Docker, I/O, system integration

- **Day 1**: Docker setup, input/output handling, PyMuPDF integration
- **Day 2**: Fast text extraction pipeline, memory optimization
- **Day 3**: JSON output pipeline, schema validation, error handling
- **Day 4**: Integration testing, performance optimization, documentation

### Person 2: Heading Detection & Algorithm Specialist  
**Responsibilities**: Core Challenge 1a algorithm development

- **Day 1**: Sample PDF analysis, multi-factor scoring architecture design
- **Day 2**: Font histogram analysis, scoring system implementation
- **Day 3**: Spatial clustering, hierarchical classification logic
- **Day 4**: Algorithm testing, accuracy optimization, edge case handling

### Person 3: AI/Semantic Analysis & Challenge 1b Expert
**Responsibilities**: Persona-driven content analysis system

- **Day 1**: Semantic matching architecture, offline AI model requirements
- **Day 2**: Sentence Transformers integration, text chunking pipeline
- **Day 3**: Vector similarity matching, content ranking algorithms
- **Day 4**: Multi-document processing, performance optimization

## Performance Requirements & Constraints

### Timing Constraints:
- **Challenge 1a**: Maximum 10 seconds for 50-page PDF
- **Challenge 1b**: Maximum 60 seconds for document collections

### Resource Limits:
- **Model Size**: ≤200MB (Challenge 1a), ≤1GB (Challenge 1b)
- **CPU Only**: No GPU acceleration available
- **Memory**: 16GB RAM maximum
- **Architecture**: AMD64/x86_64 only

### Docker Deployment Example:
```dockerfile
FROM --platform=linux/amd64 python:3.12-slim
RUN pip install --no-cache-dir pymupdf numpy sentence-transformers
COPY src/ /app
WORKDIR /app
ENTRYPOINT ["python", "main.py"]
```

## Success Metrics

### Accuracy Targets:
- High precision/recall on heading detection across diverse PDF layouts
- Robust performance on simple and complex document structures
- Effective semantic matching between persona needs and content relevance

### Performance Goals:
- Meet strict timing requirements consistently
- Efficient memory usage under resource constraints
- Perfect JSON schema compliance for judge evaluation

### Scalability Features:
- Process multiple documents efficiently in parallel
- Handle various PDF formats and layouts gracefully
- Maintain consistent performance across document collections

This comprehensive system transforms static PDF documents into intelligent, structured data suitable for advanced document understanding applications, providing the foundation for next-generation reading experiences.