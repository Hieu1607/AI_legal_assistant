# AI Legal Assistant

A comprehensive AI-powered legal document processing and retrieval system that leverages natural language processing and vector search capabilities to assist with legal document analysis and information retrieval.

## 🏗️ Project Structure

```
AI_legal_assistant/
├── configs/           # Configuration files and logging setup
├── data/             # Data storage and processing
│   ├── processed/    # Processed data including chunks and embeddings
│   │   ├── chunks/   # Text chunks from legal documents
│   │   ├── rules/    # Categorized legal rules
│   │   └── vector_store/  # Vector index storage
│   └── raw/          # Raw scraped data
├── demo/             # Demonstration scripts and notebooks
├── docs/             # Documentation files
├── scripts/          # Data processing and utility scripts
├── src/              # Main source code
│   ├── embedding/    # Text embedding modules
│   ├── extract_data/ # Data extraction utilities
│   ├── preprocess/   # Text preprocessing and chunking
│   ├── retrieval/    # Web scraping and data fetching
│   └── store_vector/ # Vector storage and search
└── tests/            # Unit tests
```

## 🔧 Features

### Data Processing Pipeline
- **Web Scraping**: Automated scraping of legal documents from Vietnamese legal websites
- **Text Extraction**: Clean text extraction from HTML documents
- **Chunking**: Intelligent document segmentation for optimal processing
- **Validation**: Data quality assurance and validation

### Embedding & Vector Search
- **Multiple Embedding Options**: Support for both API-based (Google Gemini) and local models
- **Vector Storage**: ChromaDB integration for efficient similarity search
- **Incremental Indexing**: Support for adding new documents without rebuilding entire index
- **Search & Reranking**: Advanced search capabilities with result reranking

### Legal Document Categories
The system processes various types of Vietnamese legal documents organized by topics (`chu_de_1` through `chu_de_15` and beyond).

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Required dependencies (see `pyproject.toml`)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI_legal_assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy and configure your API keys
cp .env.example .env
```

### Configuration
Configure your embedding preferences and API keys in the environment file. The system supports:
- Google Gemini API for embeddings
- Local sentence-transformers models
- ChromaDB for vector storage

## 📊 Usage

### Data Processing
1. **Scrape legal documents**:
```bash
python scripts/scrape_links_from_url.py
python scripts/scrape_HTML_from_url.py
```

2. **Process and chunk documents**:
```bash
python scripts/process_HTML_to_text.py
python scripts/make_chunks.py
```

3. **Build embeddings**:
```bash
python src/embedding/build_embeddings_with_API.py
# or
python src/embedding/build_embeddings_with_local_model.py
```

4. **Initialize and populate vector store**:
```bash
python src/store_vector/init_index.py
python src/store_vector/index_embeddings.py
```

### Search and Retrieval
```bash
python src/store_vector/search_embeddings.py
```

### Demo
Explore the system capabilities using the provided demo:
```bash
python demo/demo_search_embeddings.py
```

Or use the Jupyter notebook:
```bash
jupyter notebook demo/demo_embedding_choices.ipynb
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Available tests:
- `test_chunker.py`: Text chunking functionality
- `test_cleaner.py`: Text cleaning utilities

## 📝 Documentation

- `docs/crawling_guide.md`: Web scraping guidelines
- `docs/schema.md`: Data schema documentation

## 🔄 Development Workflow

### Adding New Documents
1. Add new documents to the raw data directory
2. Process documents through the chunking pipeline
3. Generate embeddings for new chunks
4. Update the vector index incrementally

### Code Quality
The project uses:
- **Black** for code formatting
- **isort** for import sorting
- **Pylint** for code analysis

## 🏷️ Current Development

This project is actively developed with focus on:
- Week 4: Embedding & Vector Indexing Integration
- Performance optimization for large-scale legal document processing
- Enhanced search accuracy and relevance

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]