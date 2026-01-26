# RAG Pipeline Testing Guide

This document describes how to test the complete RAG pipeline after deployment.

## Prerequisites

1. Docker and Docker Compose installed
2. HuggingFace token set in `.env` file
3. All services running: `docker compose up --build`

## Step-by-Step Testing

### 1. Run Database Migration

First time setup - creates the products table with pgvector support:

```bash
docker compose exec api python scripts/run_migration.py
```

Expected output:
```
Connecting to database...
Running migration: 001_add_products_table.sql
Executing: CREATE EXTENSION IF NOT EXISTS vector...
✓ Migration completed successfully!
Products table created with pgvector support.
```

### 2. Import Example Products

Import the sample product data:

```bash
curl -X POST "http://localhost:8000/products/import" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/products_example.json"
```

Expected response:
```json
{
  "total_variants": 15,
  "unique_products": 7,
  "newly_saved": 7,
  "updated": 0,
  "message": "Successfully imported 7 new products and updated 0 existing products"
}
```

### 3. Verify Product Count

Check that products were imported:

```bash
curl "http://localhost:8000/products/stats/count"
```

Expected response:
```json
{
  "total_products": 7
}
```

### 4. Test Semantic Search

Test vector similarity search:

```bash
# Search for women's clothing
curl "http://localhost:8000/products/search?query=comfortable+women+clothing&top_k=3"

# Search with price filter
curl "http://localhost:8000/products/search?query=cozy+wear&min_price=30&max_price=60&top_k=5"

# Search with gender filter
curl "http://localhost:8000/products/search?query=casual+clothing&gender=women"
```

Expected: JSON array of matching products with similarity scores.

### 5. Test Full RAG Pipeline

Create a persona and get RAG-powered recommendations:

```bash
# 1. Create a persona
PERSONA_RESPONSE=$(curl -X POST "http://localhost:8000/personas" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "gender": "female",
    "occasion": "birthday",
    "relationship": "friend",
    "budget": "25-50"
  }')

PERSONA_ID=$(echo $PERSONA_RESPONSE | jq -r '.id')

# 2. Get questions
curl "http://localhost:8000/personas/$PERSONA_ID/questions"

# 3. Submit answers (adjust question IDs based on response)
curl -X POST "http://localhost:8000/questions/answers" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": "...", "selected_choice": "Comfortable and cozy"},
      {"question_id": "...", "selected_choice": "Indoor relaxation"}
    ]
  }'

# 4. Get RAG-powered recommendations
curl "http://localhost:8000/personas/$PERSONA_ID/recommendations?max_recommendations=5"
```

Expected: Recommendations should include:
- Real products from the database
- `match_reasoning` explaining why each product fits
- `confidence` scores
- Product details (name, price, vendor, colors, sizes)

### 6. Verify RAG vs LLM-Only Fallback

The system should:
- **With products in DB**: Return real products with reasoning
- **With empty DB**: Fall back to LLM-only generic recommendations

To test fallback, you can temporarily clear products and verify it still works.

## Unit Tests

Run the test suite:

```bash
# All tests
docker compose exec api pytest

# Specific test files
docker compose exec api pytest tests/test_products_transformer.py -v
docker compose exec api pytest tests/test_products_embedding.py -v
docker compose exec api pytest tests/test_products_repository.py -v
```

Note: Some tests require PostgreSQL with pgvector and are skipped in SQLite environments.

## Troubleshooting

### Migration fails
- Check that Docker is using `pgvector/pgvector:pg17` image
- Verify DATABASE_URL is correct
- Check container logs: `docker compose logs db`

### Import fails
- Verify JSON file format matches expected schema
- Check file encoding (should be UTF-8)
- Look for errors in API logs: `docker compose logs api`

### Search returns no results
- Verify products were imported: check `/products/stats/count`
- Check that embeddings were generated (non-null embedding column)
- Test with different query terms

### RAG pipeline falls back to LLM-only
- This is expected behavior when no products match the criteria
- Check product count and query filters
- Verify budget range includes product prices

## Performance Notes

### First Request Slowness
The first request after startup will be slower (~10-30 seconds) because:
1. Sentence transformer model downloads (358 MB)
2. Model initialization
3. First embedding generation

Subsequent requests will be fast (~100ms for search, ~2-5s for LLM re-ranking).

### Model Cache
The sentence transformer model is cached at:
- Container: `/root/.cache/torch/sentence_transformers/`
- This directory persists between container restarts

### Vector Search Performance
- IVFFlat index provides fast approximate nearest neighbor search
- For 1000+ products, index scan is efficient
- For < 100 products, sequential scan may be used automatically

## Success Criteria

✅ Migration completes without errors
✅ Products import successfully with embeddings
✅ Semantic search returns relevant products
✅ RAG pipeline returns real products with reasoning
✅ Fallback works when no products exist
✅ Unit tests pass
✅ Performance is acceptable (<5s for recommendations)
