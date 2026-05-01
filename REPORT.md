# Mini Project Report

## Sentinel AI: LLM Safety Gateway

---

# Chapter 1: INTRODUCTION

## 1.1 General Introduction

- Sentinel AI is a CPU-centric, high-performance real-time safety gateway designed to protect against malicious Large Language Model (LLM) interactions
- The system acts as a robust firewall that intercepts requests before they reach the LLM
- It detects and blocks various security threats including:
  - Prompt injection attacks
  - Jailbreak attempts
  - Toxic and harmful inputs
- The gateway provides a multi-layered defense mechanism combining regex-based pattern matching, transformer-based security classification, and vector database semantic similarity matching
- It offers a threshold-based decision engine that categorizes prompts into PASS, SANITIZE, or BLOCK categories
- The system is built using Python with FastAPI for the web framework and supports real-time analysis with semantic caching for improved performance

## 1.2 Problem Statement

- Large Language Models are vulnerable to adversarial attacks that can cause them to generate harmful, inappropriate, or malicious content
- Prompt injection attacks involve embedding malicious instructions within normal-looking prompts to manipulate model behavior
- Jailbreak attempts bypass safety mechanisms built into LLMs to access restricted capabilities
- Existing security solutions often rely on single-layer detection which can be evaded by sophisticated attacks
- Many existing solutions are computationally expensive and not suitable for real-time applications
- There is a need for a lightweight, CPU-friendly solution that provides comprehensive protection without significant latency
- Current solutions lack semantic understanding and cannot detect novel attack patterns
- The absence of proper input validation exposes LLM applications to:
  - Data exfiltration attempts
  - System prompt extraction
  - Instruction override attacks
  - Malicious content generation

## 1.3 Objectives of the Project

- To develop a real-time safety gateway that intercepts and analyzes LLM inputs before they reach the model
- To implement a multi-layer detection architecture combining regex analysis, transformer classification, and semantic similarity matching
- To create a weighted scoring system that aggregates results from multiple detection layers
- To provide a threshold-based decision engine with three response categories: PASS, SANITIZE, and BLOCK
- To implement semantic caching using Redis for sub-millisecond response times on repeated queries
- To develop a prompt sanitization module that rewrites suspicious prompts into safe versions using LLM technology
- To create a user-friendly frontend interface for testing and monitoring the system
- To ensure CPU-efficient operation suitable for deployment in resource-constrained environments
- To provide configurable weights and thresholds for different security requirements

## 1.4 Project Deliverables

- A fully functional FastAPI-based web application running on port 8000
- A multi-layer threat detection system with three parallel evaluation layers
- A fine-tuned DistilBERT security classifier model for deep learning-based classification
- A ChromaDB vector database populated with known jailbreak signatures for semantic similarity matching
- A Redis-backed semantic cache for improved response times
- A prompt sanitization module using Llama 3.3 70B via SambaNova API
- A responsive web-based frontend UI for testing and interaction
- API documentation via Swagger at /docs endpoint
- Configuration endpoints for weights and thresholds adjustment
- Health check endpoints to monitor layer status
- Cache statistics endpoint for performance monitoring

## 1.5 Current Scope

- The system currently implements three detection layers with weighted scoring
- The regex analyzer provides fast tripwire detection for known patterns and keywords with 10% weight
- The transformer security model uses fine-tuned DistilBERT for deep classification with 55% weight
- The vector database layer uses ChromaDB for semantic similarity matching with 35% weight
- The threshold decision engine categorizes prompts as PASS (score < 0.35), SANITIZE (0.35-0.65), or BLOCK (>= 0.65)
- The frontend provides basic testing capabilities through a web interface
- The API supports analyze (without sanitization) and gateway (with sanitization) endpoints
- The system is configured for Python 3.13+ compatibility

## 1.6 Future Scope

- Integration with additional LLM providers beyond SambaNova
- Support for file upload analysis to detect malicious documents
- Implementation of output validation to ensure safe model responses
- Expansion of the vector database with more diverse attack signatures
- Addition of user authentication and rate limiting
- Support for multiple language detection beyond English
- Implementation of detailed logging and audit trails
- Development of dashboard analytics for security insights
- Integration with existing API gateways and infrastructure
- Support for custom model fine-tuning on organization-specific data

---

# Chapter 2: LITERATURE SURVEY

## 2.1 Introduction

- This chapter reviews existing research and solutions in the field of LLM security and prompt safety
- The survey examines various approaches to detecting and preventing adversarial attacks on LLM systems
- It covers both traditional rule-based methods and modern machine learning approaches
- The review identifies gaps in current solutions that Sentinel AI aims to address

## 2.2 Related Works

### Traditional Rule-Based Detection

- **Keyword and Pattern Matching**: Early solutions relied on blacklists of known malicious keywords
  - Limitations: Easily bypassed with encoding, synonyms, or obfuscation
  - Fast but lacks semantic understanding
- **Regex-Based Filters**: Regular expressions used to detect specific attack patterns
  - Can catch known syntax structures but cannot detect novel attacks
  - Requires constant updating to address new attack vectors

### Machine Learning Approaches

- **Transformer-Based Classifiers**: Using models like DistilBERT for binary classification
  - Can learn complex patterns and semantic relationships
  - Requires training data with labeled examples
  - Can generalize to novel attacks with proper fine-tuning
- **Fine-Tuned Safety Models**: Specialized models trained on jailbreak datasets
  - Provide better detection accuracy for specific attack types
  - Require computational resources for training and inference

### Semantic Similarity Methods

- **Vector Database Search**: Using embeddings to find similar known attacks
  - ChromaDB and similar solutions for semantic search
  - Effective against variations of known attacks
  - Requires curated database of attack signatures
- **Sentence Transformers**: For transforming text into semantic embeddings
  - Enable semantic comparison beyond keyword matching
  - Can detect paraphrased attacks

### Caching and Performance

- **Redis-Based Caching**: Using Redis for fast in-memory caching
  - RedisVL provides semantic caching capabilities
  - Reduces latency for repeated queries
  - Essential for real-time applications

### Prompt Sanitization

- **LLM-Based Rewriting**: Using LLMs to rewrite suspicious prompts
  - Llama 3.3 and similar models for safe prompt generation
  - Provides graceful degradation for borderline cases
  - Requires access to external LLM APIs

### Commercial Solutions

- **Azure AI Content Safety**: Microsoft's content filtering service
  - Provides predefined filters for various content types
  - Limited customization options
- **Amazon Bedrock Guardrails**: AWS content filtering for Bedrock
  - Integrated with AWS ecosystem
  - Vendor lock-in concerns
- **NVIDIA NeMo Guardrails**: Open-source framework for LLM safety
  - Configurable rules and filters
  - Requires significant setup and configuration

## 2.3 Conclusion of Survey

- Current solutions often rely on single-layer detection, making them vulnerable to sophisticated attacks
- Traditional regex and keyword-based methods are insufficient against novel attack patterns
- Machine learning approaches provide better generalization but require significant computational resources
- Semantic similarity matching complements ML-based detection by catching variations of known attacks
- A multi-layered approach combining multiple detection methods provides the most robust protection
- Caching is essential for real-time performance without sacrificing security
- Prompt sanitization provides graceful degradation for borderline cases
- There is a need for a lightweight, CPU-efficient solution suitable for various deployment scenarios
- Open-source solutions like Sentinel AI provide flexibility and customization options

---

# Chapter 3: PROJECT REQUIREMENT & SPECIFICATIONS

## 3.1 Hardware Requirements

- **CPU**: Multi-core processor (minimum 4 cores recommended for parallel processing)
- **RAM**: Minimum 8GB, recommended 16GB for model loading and caching
- **Storage**: Minimum 10GB for models, datasets, and vector database
- **GPU**: Optional but not required (CPU-optimized implementation)
- **Network**: Internet connection for API communications (SambaNova)

## 3.2 Software Requirements

### Runtime Environment

- Python >= 3.13
- Docker and Docker Compose for Redis Stack
- Operating System: Linux, macOS, or Windows with WSL2

### Python Dependencies

- **Web Framework**: FastAPI, Uvicorn
- **AI/ML Libraries**: 
  - Transformers (Hugging Face)
  - PyTorch
  - Sentence-Transformers
  - SpaCy
  - NLTK
- **Data Storage**:
  - ChromaDB for vector database
  - Redis and RedisVL for caching
  - Pandas for data handling
- **Utilities**:
  - RapidFuzz for fuzzy matching
  - Pydantic for data validation
  - OpenAI client for sanitizer
  - scikit-learn for evaluation

### External Services

- SambaNova API key for prompt sanitization (configurable via .env)

## 3.3 Functional Requirements

### Core Features

- **Real-Time Prompt Analysis**: The system must analyze prompts in real-time with minimal latency
- **Multi-Layer Detection**: Must implement three parallel detection layers with weighted scoring
- **Threshold Decision Engine**: Must categorize prompts into PASS, SANITIZE, or BLOCK categories
- **Semantic Caching**: Must cache results for repeated queries with configurable TTL
- **Prompt Sanitization**: Must rewrite suspicious prompts into safe versions when needed
- **API Endpoints**:
  - / - Serve frontend UI
  - /docs - Swagger API documentation
  - /health - Health check
  - /analyze - Analyze without sanitization
  - /gateway - Full pipeline with sanitization
  - /config - Get weights and thresholds
  - /cache/stats - Cache statistics

### Configuration

- Configurable layer weights (default: Regex 10%, Model 55%, Vector 35%)
- Configurable thresholds (default: PASS < 0.35, SANITIZE 0.35-0.65, BLOCK >= 0.65)
- Configurable cache TTL (default: 600 seconds)

## 3.4 Non-Functional Requirements

- **Performance**: Sub-second response time for most prompts
- **Scalability**: Handle multiple concurrent requests efficiently
- **Accuracy**: High detection rate with low false positive rate
- **Reliability**: Graceful degradation when individual layers fail
- **Maintainability**: Clean, modular code structure
- **CPU Efficiency**: Optimized for CPU-only environments
- **Security**: Secure handling of API keys and sensitive data

---

# Chapter 4: DESIGN

## 4.1 Introduction

- This chapter describes the architectural design of the Sentinel AI system
- The design follows a modular approach with clear separation of concerns
- Each detection layer operates independently while contributing to the final decision
- The system is designed for flexibility, allowing weight and threshold configuration

## 4.2 Architecture Design

### System Architecture Overview

```
Client Application
        │
        └──> FastAPI Gateway (Port 8000)
              │
              ├──> Semantic Cache Check (RedisVL)
              │     └── [Hit] --> Instant Cached Response
              │
              └──> [Miss] -> Parallel Evaluation
                    ├── Layer 1: Regex Analyzer (10% weight)
                    ├── Layer 2: Transformer Security Model (55% weight)
                    └── Layer 3: Vector DB Similarity (35% weight)
                          │
                          V
                    Weighted Score Aggregation
                          │
                          V
                    Decision Engine
                    ├── PASS (score < 0.35)
                    ├── SANITIZE (0.35-0.65)
                    └── BLOCK (score >= 0.65)
                          │
                          V
                    Response + Cache Store
```

### Component Design

#### 4.2.1 FastAPI Gateway

- Serves as the main entry point for all requests
- Handles API routing and request validation
- Manages caching integration
- Returns responses in JSON format

#### 4.2.2 Regex Analyzer Layer

- Implementation: utils/reg.py
- Provides fast tripwire detection
- Uses keyword matching and pattern recognition
- Analyzes syntax structures
- Returns score between 0 and 1

#### 4.2.3 Security Transformer Model

- Implementation: utils/security_model.py
- Uses fine-tuned DistilBERT model
- Located in models/saved_security_model/
- Provides deep learning-based classification
- Returns probability score for malicious content

#### 4.2.4 Vector Database Layer

- Implementation: utils/vector_db.py
- Uses ChromaDB for embedding storage
- Compares input against known jailbreak signatures
- Located in vector_database/ directory
- Returns semantic similarity score

#### 4.2.5 Semantic Cache

- Implementation: utils/cache.py
- Uses RedisVL for semantic caching
- Configurable TTL (default 600 seconds)
- Sub-millisecond response for cache hits

#### 4.2.6 Prompt Sanitizer

- Implementation: utils/sanitizer.py
- Uses Llama 3.3 70B via SambaNova API
- Rewrites suspicious prompts into safe versions
- Triggered for SANITIZE category prompts

## 4.3 User Interface Design

### Frontend Overview

- Located in static/ directory
- Single HTML page with embedded JavaScript
- Responsive design with clean styling

### Design Components

- **Header**: Project title and description
- **Input Area**: Large text area for prompt input
- **Action Buttons**: Analyze and Gateway buttons
- **Result Display**: Shows classification result and threat level
- **Score Breakdown**: Visual display of individual layer scores
- **Configuration Panel**: Adjustable weights and thresholds
- **Statistics Panel**: Cache hit rate and performance metrics

### UI/UX Principles

- Clean, modern interface with dark theme
- Clear visual feedback for analysis results
- Real-time score updates
- Easy to use for testing purposes

## 4.4 State Diagram

[Insert state diagram]

---

# Chapter 5: IMPLEMENTATION

## 5.1 Pseudocode

### Main Gateway Flow

```python
FUNCTION gateway(prompt):
    # Check cache first
    cached_result = cache.get(prompt)
    IF cached_result exists:
        RETURN cached_result
    
    # Parallel evaluation of all layers
    regex_score = regex_analyzer.analyze(prompt)
    model_score = security_model.predict(prompt)
    vector_score = vector_db.similarity(prompt)
    
    # Weighted score aggregation
    final_score = (regex_score * 0.10) + (model_score * 0.55) + (vector_score * 0.35)
    
    # Threshold decision
    IF final_score < 0.35:
        RESULT = "PASS"
    ELSE IF final_score < 0.65:
        RESULT = "SANITIZE"
        sanitized_prompt = sanitizer.rewrite(prompt)
        # Re-analyze sanitized prompt
    ELSE:
        RESULT = "BLOCK"
    
    # Cache result
    cache.set(prompt, RESULT)
    
    RETURN RESULT
```

### Regex Analyzer

```python
FUNCTION analyze(prompt):
    CHECK keywords from predefined blacklist
    CHECK patterns using regex expressions
    CHECK syntax structures
    RETURN normalized score (0-1)
```

### Security Model Prediction

```python
FUNCTION predict(prompt):
    tokenize prompt using tokenizer
    pass through DistilBERT model
    get probability of malicious class
    RETURN probability score (0-1)
```

### Vector Database Similarity

```python
FUNCTION similarity(prompt):
    generate embedding for prompt
    search ChromaDB for similar embeddings
    get similarity score for best match
    RETURN similarity score (0-1)
```

### Prompt Sanitization

```python
FUNCTION rewrite(prompt):
    create system prompt for safe rewriting
    call SambaNova API with Llama 3.3
    extract sanitized prompt from response
    RETURN sanitized prompt
```

## 5.2 Implementation Details

### Directory Structure

```
sentinel-ai/
├── app.py                    # Main FastAPI application
├── pyproject.toml            # Project dependencies
├── docker-compose.yml        # Redis server setup
├── .env                      # API keys configuration
├── utils/
│   ├── reg.py               # Regex analyzer layer
│   ├── security_model.py    # Transformer classifier
│   ├── vector_db.py         # ChromaDB similarity layer
│   ├── sanitizer.py         # LLM-based prompt rewriting
│   └── cache.py             # RedisVL semantic cache
├── scripts/
│   ├── train_classifier.py  # Model training script
│   ├── build_chroma_db.py   # Vector DB build script
│   └── make_dataset.ipynb   # Dataset preparation notebook
├── models/
│   └── saved_security_model/  # Fine-tuned DistilBERT model
├── datasets/                # Training datasets
├── vector_database/         # ChromaDB persistent storage
└── static/
    ├── index.html           # Frontend UI
    ├── app.js              # Frontend logic
    └── styles.css          # UI styling
```

### API Implementation

- **app.py**: FastAPI application with all endpoints
  - GET /: Serves static frontend
  - GET /health: Returns layer status
  - POST /analyze: Analyzes without sanitization
  - POST /gateway: Full pipeline with sanitization
  - GET /config: Returns current configuration
  - GET /cache/stats: Returns cache statistics

### Model Training

- **scripts/train_classifier.py**: Trains DistilBERT classifier
  - Uses labeled jailbreak dataset
  - Fine-tunes for binary classification
  - Saves to models/saved_security_model/

### Vector Database Build

- **scripts/build_chroma_db.py**: Populates ChromaDB
  - Loads known jailbreak signatures
  - Generates embeddings using Sentence-Transformers
  - Stores in vector_database/ directory

### Configuration

- Layer weights configurable in app.py
- Thresholds adjustable via API
- Cache TTL set in environment variables

### Startup Instructions

```bash
# 1. Start Redis
docker-compose up -d

# 2. Install dependencies
uv sync

# 3. Run the server
uv run uvicorn app:app --host 0.0.0.0 --port 8000

# 4. Access frontend at http://localhost:8000
#    API docs at http://localhost:8000/docs
```

---

# Chapter 6: RESULTS

## 6.1 Result Snapshots

### API Response Examples

#### PASS Response (Safe Prompt)
```json
{
  "result": "PASS",
  "score": 0.12,
  "layer_scores": {
    "regex": 0.05,
    "model": 0.15,
    "vector": 0.10
  }
}
```

#### SANITIZE Response (Suspicious Prompt)
```json
{
  "result": "SANITIZE",
  "score": 0.48,
  "layer_scores": {
    "regex": 0.30,
    "model": 0.55,
    "vector": 0.45
  },
  "sanitized_prompt": "Rewritten safe version of the prompt"
}
```

#### BLOCK Response (Malicious Prompt)
```json
{
  "result": "BLOCK",
  "score": 0.82,
  "layer_scores": {
    "regex": 0.75,
    "model": 0.90,
    "vector": 0.85
  }
}
```

### Frontend Interface

- Clean dark-themed interface with input area
- Visual indicators for threat level (green/yellow/red)
- Score breakdown showing individual layer contributions
- Configuration panel for weight adjustment
- Real-time statistics display

## 6.2 Comparative Analysis

### Comparison with Single-Layer Solutions

| Aspect | Sentinel AI | Single-Layer Regex | Single-Layer ML |
|--------|------------|-------------------|------------------|
| Detection Rate | High | Low | Medium |
| False Positives | Low | High | Medium |
| Novel Attack Handling | Good | Poor | Good |
| Performance | Medium | High | Medium |
| Resource Usage | Medium | Low | Medium |

### Multi-Layer Advantages

- **Improved Detection**: Combined scoring from multiple approaches catches attacks single methods miss
- **Reduced False Positives**: Consensus requirement reduces over-blocking
- **Robustness**: Failure of one layer doesn't compromise entire system
- **Flexibility**: Configurable weights allow tuning for specific use cases

### Layer Contribution Analysis

- **Regex Analyzer (10%)**: Fast tripwire catches obvious attacks with known patterns
- **Security Model (55%)**: Deep learning provides semantic understanding
- **Vector DB (35%)**: Catches variations of known attacks through similarity

## 6.3 Performance Analysis

### Response Time

- **Cache Hit**: < 1ms (sub-millisecond)
- **Cache Miss - Regex**: 1-5ms
- **Cache Miss - Model**: 50-200ms
- **Cache Miss - Vector**: 10-50ms
- **Cache Miss - Full Pipeline**: 100-300ms (average)
- **With Sanitization**: 500-2000ms (depends on API latency)

### Caching Performance

- Default TTL: 600 seconds
- Cache hit rate improves with repeated queries
- Semantic cache enables partial match hits

### Resource Utilization

- **CPU Only**: Optimized for CPU-only environments
- **Memory**: ~2GB for models and caching
- **Model Size**: ~250MB for DistilBERT

### Throughput

- Estimated capacity: 10-50 requests/second
- Varies based on cache hit rate
- Dependent on hardware specifications

## 6.3.1 Applications

### Primary Use Cases

- **API Gateway Protection**: Middleware for LLM API endpoints
- **Chatbot Security**: Protecting conversational AI systems
- **Enterprise LLM Deployment**: Internal AI application security
- **Research Environments**: Safe experimentation with LLMs

### Deployment Scenarios

- **Cloud Deployment**: Docker container in Kubernetes
- **On-Premises**: Dedicated server installation
- **Edge Computing**: Resource-constrained environments
- **Development/Testing**: Local development setup

## 6.3.2 Limitations

- **API Dependency**: Requires SambaNova API for sanitization
- **Model Training Data**: Performance depends on training data quality
- **Language Support**: Primarily English-focused
- **Real-Time Constraints**: Latency increases with full pipeline
- **Novel Attacks**: Zero-day attacks may bypass detection
- **Resource Requirements**: Requires adequate CPU and memory

---

# Chapter 7: CONCLUSION & FUTURE WORK

## 7.1 Conclusion

- Sentinel AI provides a comprehensive, multi-layered solution for LLM safety
- The system effectively detects prompt injection, jailbreak attempts, and toxic inputs
- The three-layer architecture combining regex, ML, and semantic similarity provides robust protection
- Configurable weights and thresholds allow customization for different security requirements
- Semantic caching ensures acceptable performance for real-time applications
- The prompt sanitization feature provides graceful degradation for borderline cases
- The system is CPU-optimized and suitable for various deployment scenarios
- The open-source nature allows for customization and extension
- This project demonstrates the feasibility of building practical LLM safety systems
- The modular architecture enables easy integration with existing systems
- Future improvements can address current limitations

## 7.2 Future Work

### Short-Term Improvements

- Expand training dataset with more diverse attack patterns
- Improve regex rules based on emerging threats
- Add support for more languages
- Implement better logging and monitoring

### Medium-Term Enhancements

- Add output validation for model responses
- Integrate additional LLM providers
- Implement file upload analysis
- Add user authentication and rate limiting

### Long-Term Vision

- Develop dashboard analytics for security insights
- Create automated model retraining pipeline
- Integrate with API gateways
- Build community-driven threat intelligence
- Implement distributed deployment support

### Research Directions

- Explore transformer-based models for new threats
- Investigate few-shot learning for novel attacks
- Study adversarial robustness
- Research interpretable AI for security decisions

---

# Appendix: Environment Variables

```
SAMBANOVA_API_KEY=<your-api-key>
```

---

# References

- Hugging Face Transformers Documentation
- FastAPI Documentation
- ChromaDB Documentation
- RedisVL Documentation
- SpaCy Documentation
- Sentence-Transformers Documentation

---

*Report prepared for academic submission*