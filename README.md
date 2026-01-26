# Pickaboo - AI-Powered Gift Recommendation System

An intelligent gift recommendation platform that uses RAG (Retrieval-Augmented Generation) to match recipients with real products from a semantic search database, powered by AI agents.

## 🎁 Features

- **RAG-Based Product Matching**: Semantic search over real e-commerce products using vector embeddings
- **AI-Powered Question Generation**: Intelligent detective agent generates targeted questions to understand recipients
- **Persona Building**: Create detailed recipient profiles with age, gender, relationship, occasion, and budget
- **Smart Recommendations**: Get personalized gift suggestions based on AI analysis of answers and real product catalog
- **Budget-Aware**: Four predefined budget ranges (Under 25€, 25-50€, 50-100€, Over 100€)
- **Vector Search**: Fast semantic product search powered by pgvector
- **Public Access**: No authentication required - start finding gifts immediately

## 🏗️ Architecture

### RAG Pipeline

Pickaboo uses a sophisticated RAG (Retrieval-Augmented Generation) architecture:

```
Scraped Products (JSON)
    ↓
Transform & Aggregate Variants
    ↓
Generate Vector Embeddings (sentence-transformers)
    ↓
Store in PostgreSQL with pgvector
    ↓
Semantic Search (Retrieval)
    ↓
LLM Re-ranking (Augmented Generation)
    ↓
Personalized Product Recommendations
```

### System Architecture

Built with clean architecture principles:

- **Domain Layer**: Core entities (Persona, Question, Answer, Product)
- **Application Layer**: Business logic and AI agent integration
- **Infrastructure Layer**: 
  - FastAPI REST API
  - SQLAlchemy ORM with PostgreSQL + pgvector
  - Pydantic-AI for intelligent agents
  - Sentence Transformers for embeddings
  - Rate limiting
- **Testing**: Comprehensive pytest unit and integration tests

## 🚀 Quick Start

### Prerequisites

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
2. **Configure your `.env` file**:
   - `HF_TOKEN`: Get your HuggingFace API token from [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - `DATABASE_URL`: Database connection string (default works with Docker)
   - `POSTGRES_*`: PostgreSQL credentials (defaults are fine for local development)

### Using Docker (Recommended)

1. Install Docker Desktop
2. Run the application:
```bash
docker compose up --build
```
3. Run the database migration (in another terminal):
```bash
docker compose exec api python scripts/run_migration.py
```
4. (Optional) Import example products:
```bash
curl -X POST "http://localhost:8000/products/import" \
  -F "file=@data/products_example.json"
```
5. API available at `http://localhost:8000`
6. Stop services:
```bash
docker compose down
```

### Local Development (Without Docker)

1. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Configure SQLite (optional for development):
   - In `src/database/core.py`, change `DATABASE_URL` to use SQLite

3. Run the application:
```bash
uvicorn src.main:app --reload
```

## 🧪 Testing

Run all tests:
```bash
pytest
```

Run specific test files:
```bash
pytest tests/test_questions_service.py
pytest tests/test_recommendations.py
```

## 📋 API Endpoints

### Personas
- `POST /personas` - Create a new recipient persona
- `GET /personas/{id}` - Get persona details

### Questions
- `GET /personas/{id}/questions` - Generate AI-powered questions for a persona
- `POST /questions/answers` - Submit bulk answers

### Recommendations
- `GET /personas/{id}/recommendations` - Get personalized gift recommendations (uses RAG if products available)

### Products (New!)
- `POST /products/import` - Import products from JSON file
- `GET /products/search` - Semantic search for products
- `GET /products/{id}` - Get single product by ID
- `GET /products/stats/count` - Get total product count

## 🛍️ Product Management

### Importing Products

Upload your scraped product data (variant-level JSON):

```bash
curl -X POST "http://localhost:8000/products/import" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/products.json"
```

**Expected JSON Format** (variant-level records):
```json
[
  {
    "store_url": "https://www.teddyfresh.com",
    "product_id": 7270065274927,
    "product_title": "Women's Classic Sweatpants",
    "vendor": "Teddy Fresh",
    "product_type": "Fleece Pants",
    "variant_id": 41634206941231,
    "variant_title": "Khaki / M",
    "price_eur": 55.0,
    "sku": "TF23FL86W-KHA-M",
    "available": true,
    "product_url": "https://www.teddyfresh.com/products/..."
  }
]
```

The system will:
1. Group variants by product
2. Extract colors and sizes
3. Aggregate pricing and availability
4. Detect gender target
5. Generate searchable tags
6. Create vector embeddings
7. Store in database with vector index

### Semantic Search

Search products using natural language:

```bash
# Basic search
curl "http://localhost:8000/products/search?query=comfortable%20women%20loungewear&top_k=5"

# With price filter
curl "http://localhost:8000/products/search?query=men%20hoodie&min_price=50&max_price=100"

# With gender filter
curl "http://localhost:8000/products/search?query=cozy%20clothing&gender=women"
```

### How RAG Works

When products are available:

1. **Query Building**: System builds semantic query from recipient profile (age, gender, preferences, occasion)
2. **Vector Retrieval**: Searches product database using cosine similarity on embeddings
3. **Filtering**: Applies budget and gender filters
4. **LLM Re-ranking**: AI agent evaluates candidates and selects best matches with reasoning
5. **Response**: Returns products with match explanations and confidence scores

**Fallback**: If no products in database, falls back to original LLM-only gift suggestions.

## 📊 Vector Database

Pickaboo uses **pgvector** for efficient semantic search:

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Index Type**: IVFFlat with cosine distance
- **Search Speed**: Sub-second queries on thousands of products
- **Filters**: Supports price range, gender, and availability filtering

## 🤖 AI Agents

The system uses two AI agents powered by pydantic-ai:

1. **Gift Detective**: Generates smart questions based on recipient profile (age, gender, occasion, relationship, budget) and **conversation history**
   - **First Round**: Asks 3 broad questions to understand basic preferences
   - **Second Round**: Asks 3 deeper, more specific follow-up questions based on the first answers
   - Remembers all previous questions and answers for each persona
   - Avoids repeating similar questions
   - Builds a complete understanding of the recipient over two rounds

2. **Gift Recommendation Agent**: Analyzes all answers and persona to suggest perfect gifts

### Two-Round Question System

The system uses a strategic two-round approach:

**Round 1 - Broad Discovery (3 questions)**
- Asked immediately after creating a persona
- General questions to understand basic preferences
- Example: "Does she prefer practical or decorative items?"

**Round 2 - Deep Dive (3 questions)**
- Asked after answering the first 3 questions
- Specific follow-ups based on Round 1 answers
- Example: If she likes decorative items → "What's her home decor style?"

**Example Flow:**
```
Create persona → Get 3 initial questions
├─ Q1: "Does she like jewelry?"
├─ Q2: "Is she into tech gadgets?"
└─ Q3: "Does she prefer experiences or physical gifts?"

Answer 3 questions
├─ A1: "Yes, especially necklaces"
├─ A2: "Not really"
└─ A3: "Physical gifts"

Get 3 deeper questions (based on answers)
├─ Q4: "What style of necklaces does she prefer?" (builds on A1)
├─ Q5: "Does she like home decor items?" (follows from A2/A3)
└─ Q6: "What's her favorite metal tone?" (deeper into A1)
```

## 💾 Database Schema

- **Personas**: Recipient profiles with demographics and budget
- **Questions**: AI-generated questions with multiple-choice options (stored as JSONB)
- **Answers**: User responses linked to questions and personas
- **Products**: E-commerce products with vector embeddings, pricing, variants, and metadata
- **Conversation History**: Each persona maintains a complete history of questions and answers for contextual AI interactions

### Products Table Structure

- **Identification**: UUID, store_product_id, store_url
- **Basic Info**: name, vendor, product_type, description
- **Pricing**: price_eur, price_min, price_max
- **Attributes**: colors[], sizes[], gender_target, tags[], available
- **Raw Data**: variants (JSONB for all variant records)
- **Vector Search**: embedding (vector(384)) with IVFFlat index
- **Indexes**: B-tree on price_eur, available, gender_target for fast filtering

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 17 with pgvector extension
- **ORM**: SQLAlchemy
- **AI**: Pydantic-AI with HuggingFace models (DeepSeek-V3.1)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Search**: pgvector with IVFFlat indexing
- **Validation**: Pydantic v2
- **Testing**: Pytest
- **Containerization**: Docker & Docker Compose

## 📦 Project Structure

```
Pickaboo/
├── src/
│   ├── build_persona/        # Persona creation and management
│   ├── questions/            # Question generation and answers
│   ├── questions_agent/      # AI detective agent
│   ├── recommendations/      # Gift recommendation logic with RAG integration
│   ├── products/             # Product management and RAG pipeline (NEW)
│   │   ├── entity.py         # SQLAlchemy Product model
│   │   ├── models.py         # Pydantic models
│   │   ├── transformer.py    # Variant aggregation logic
│   │   ├── embedding_service.py  # Vector embedding generation
│   │   ├── repository.py     # Vector search and data access
│   │   ├── import_service.py # JSON import pipeline
│   │   ├── matching_service.py   # RAG pipeline orchestration
│   │   └── controller.py     # FastAPI product endpoints
│   ├── database/             # Database configuration
│   └── main.py               # FastAPI application
├── tests/                    # Unit and integration tests
├── migrations/               # SQL migration scripts (NEW)
├── scripts/                  # Utility scripts (NEW)
├── data/                     # Product data files (NEW)
├── docker-compose.yml        # Docker services configuration
├── Dockerfile                # Application container
└── requirements.txt          # Python dependencies
```




---

**Happy Gift Hunting! 🎉**