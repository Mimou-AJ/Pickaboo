# Pickaboo - AI-Powered Gift Recommendation System

An intelligent gift recommendation platform that uses AI agents to understand recipients and suggest personalized gifts based on their preferences, budget, and occasion.

## 🎁 Features

- **RAG-Powered Product Search**: Retrieval-Augmented Generation pipeline with real product matching
- **Semantic Search**: Vector-based product search using sentence transformers (384-dimensional embeddings)
- **AI-Powered Question Generation**: Intelligent detective agent generates targeted questions to understand gift recipients
- **Persona Building**: Create detailed recipient profiles with age, gender, relationship, occasion, and budget
- **Smart Recommendations**: Get personalized gift suggestions from real product catalog with LLM re-ranking
- **Budget-Aware**: Four predefined budget ranges (Under 25€, 25-50€, 50-100€, Over 100€)
- **Product Import**: Upload scraped e-commerce data and automatically process into searchable products
- **Public Access**: No authentication required - start finding gifts immediately

## 🏗️ Architecture

Built with clean architecture principles and RAG (Retrieval-Augmented Generation) pipeline:

### RAG Pipeline Flow
```
Scraped Products (JSON) 
    → Transform & Aggregate Variants
    → Generate Vector Embeddings (sentence-transformers)
    → Store in PostgreSQL with pgvector
    → Semantic Search (Retrieval)
    → LLM Re-ranking (DeepSeek-V3)
    → Personalized Product Recommendations
```

### Architecture Layers
- **Domain Layer**: Core entities (Persona, Question, Answer, Product)
- **Application Layer**: Business logic, AI agents, and RAG pipeline
- **Infrastructure Layer**: 
  - FastAPI REST API
  - SQLAlchemy ORM with PostgreSQL + pgvector
  - Pydantic-AI for intelligent agents (DeepSeek-V3, HuggingFace)
  - Sentence Transformers (all-MiniLM-L6-v2) for embeddings
  - Vector similarity search with IVFFlat indexing
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
3. Run database migration (first time only):
```bash
docker compose exec api python scripts/run_migration.py
```
4. API available at `http://localhost:8000`
5. Stop services:
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
pytest tests/test_products_transformer.py
```

## 📦 Product Management & RAG Pipeline

### Import Products from JSON

Upload scraped product data to build the searchable product catalog:

```bash
# Import products from JSON file
curl -X POST "http://localhost:8000/products/import" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/products_example.json"
```

**JSON Format** (variant-level data):
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

The import pipeline:
1. **Transforms** variant-level data into aggregated products
2. **Extracts** colors, sizes, gender target, and tags
3. **Generates** 384-dimensional embeddings using sentence transformers
4. **Stores** in PostgreSQL with vector similarity indexing
5. **Deduplicates** based on store_product_id + store_url

### Semantic Product Search

Search products using natural language with vector similarity:

```bash
# Basic semantic search
curl "http://localhost:8000/products/search?query=comfortable%20women%20loungewear&top_k=5"

# With price filter
curl "http://localhost:8000/products/search?query=cozy%20clothing&min_price=25&max_price=75"

# With gender filter
curl "http://localhost:8000/products/search?query=casual%20wear&gender=women&top_k=10"
```

**How Vector Search Works:**
- Converts your query into a 384-dimensional embedding
- Uses pgvector's cosine distance (`<=>` operator) for similarity
- Applies IVFFlat indexing for fast approximate nearest neighbor search
- Filters by price range and gender preferences
- Returns products with similarity scores (0.0 - 1.0)

### Get Product Details

```bash
# Get single product by ID
curl "http://localhost:8000/products/{product_id}"

# Get product count
curl "http://localhost:8000/products/stats/count"
```

### RAG-Powered Recommendations

When you request recommendations, the system now uses the full RAG pipeline:

1. **Builds Query** from recipient profile (age, gender, occasion, preferences)
2. **Retrieval**: Semantic search finds 15 candidate products from vector database
3. **Augmentation**: Builds rich prompt with profile + candidate products
4. **Generation**: DeepSeek-V3 LLM re-ranks and selects top 5 with reasoning
5. **Returns**: Real products with match explanations and confidence scores

**Fallback**: If no products exist in the catalog, falls back to LLM-only recommendations.

## 📋 API Endpoints

### Personas
- `POST /personas` - Create a new recipient persona
- `GET /personas/{id}` - Get persona details

### Questions
- `GET /personas/{id}/questions` - Generate AI-powered questions for a persona
- `POST /questions/answers` - Submit bulk answers

### Recommendations
- `GET /personas/{id}/recommendations` - Get personalized gift recommendations (RAG-powered)

### Products
- `POST /products/import` - Import products from JSON file
- `GET /products/search` - Semantic search for products
- `GET /products/{product_id}` - Get single product details
- `GET /products/stats/count` - Get total product count

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
- **Conversation History**: Each persona maintains a complete history of questions and answers for contextual AI interactions

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 17
- **ORM**: SQLAlchemy
- **AI**: Pydantic-AI with HuggingFace models
- **Validation**: Pydantic v2
- **Testing**: Pytest
- **Containerization**: Docker & Docker Compose

## 📦 Project Structure

```
Pickaboo/
├── src/
│   ├── auth/                 # (Removed - no longer needed)
│   ├── build_persona/        # Persona creation and management
│   ├── questions/            # Question generation and answers
│   ├── questions_agent/      # AI detective agent
│   ├── recommendations/      # Gift recommendation logic
│   ├── database/             # Database configuration
│   └── main.py               # FastAPI application
├── tests/                    # Unit and integration tests
├── docker-compose.yml        # Docker services configuration
├── Dockerfile                # Application container
└── requirements.txt          # Python dependencies
```




---

**Happy Gift Hunting! 🎉**