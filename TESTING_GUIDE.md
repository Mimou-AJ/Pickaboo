# RAG Pipeline Implementation - Testing Guide

## Overview
This document provides instructions for testing the complete RAG (Retrieval-Augmented Generation) pipeline implementation for Pickaboo.

## Prerequisites
- Docker Desktop installed
- `.env` file configured with `HF_TOKEN`
- Port 8000 and 5432 available

## Step-by-Step Testing

### 1. Start the Application

```bash
# Build and start services
docker compose up --build

# Wait for services to be ready (should see "Application startup complete")
```

### 2. Run Database Migration

In a new terminal:

```bash
# Execute migration to create products table with pgvector
docker compose exec api python scripts/run_migration.py
```

Expected output:
```
Connecting to database: postgresql://...
Executing migration...
Migration completed successfully!
```

### 3. Import Example Products

```bash
# Import the example product data
curl -X POST "http://localhost:8000/products/import" \
  -F "file=@data/products_small.json"
```

Expected response:
```json
{
  "total_variants": 10,
  "unique_products": 6,
  "newly_saved": 6,
  "updated": 0
}
```

### 4. Verify Product Count

```bash
curl "http://localhost:8000/products/stats/count"
```

Expected response:
```json
{
  "total_products": 6
}
```

### 5. Test Semantic Search

```bash
# Search for women's clothing
curl "http://localhost:8000/products/search?query=comfortable+women+clothing&top_k=3"

# Search with price filter
curl "http://localhost:8000/products/search?query=men+clothing&min_price=30&max_price=80&top_k=3"

# Search with gender filter
curl "http://localhost:8000/products/search?query=cozy+items&gender=women"
```

Expected: JSON array of products with names, prices, and metadata matching the query.

### 6. Test RAG Pipeline with Recommendations

```bash
# Step 1: Create a persona
curl -X POST "http://localhost:8000/personas" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "gender": "female",
    "occasion": "birthday",
    "relationship": "friend",
    "budget": "25-50"
  }'
```

Save the `persona_id` from the response.

```bash
# Step 2: Get questions for the persona
curl "http://localhost:8000/personas/{persona_id}/questions"
```

```bash
# Step 3: Submit answers (use question IDs from step 2)
curl -X POST "http://localhost:8000/questions/answers" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {
        "question_id": "question-id-1",
        "answer_text": "Comfortable and casual"
      },
      {
        "question_id": "question-id-2",
        "answer_text": "Indoor activities"
      }
    ]
  }'
```

```bash
# Step 4: Get recommendations (should use RAG with real products!)
curl "http://localhost:8000/personas/{persona_id}/recommendations"
```

Expected: Recommendations should include:
- Real product names from the imported data
- Specific price information (e.g., "€55.00")
- Detailed `reasoning` explaining why each product matches the recipient
- `confidence_score` from the LLM re-ranking

### 7. Check Logs

Monitor the application logs to see the RAG pipeline in action:

```bash
docker compose logs -f api
```

Look for log entries like:
- "Loading embedding model..."
- "Generating embeddings for X products"
- "Found X candidate products for query"
- "Executing semantic search..."

## Validation Checklist

- [ ] Migration script runs successfully
- [ ] Products import without errors
- [ ] Product count matches imported data
- [ ] Semantic search returns relevant results
- [ ] Price filters work correctly
- [ ] Gender filters work correctly
- [ ] RAG pipeline returns real products in recommendations
- [ ] Match reasoning is specific and personalized
- [ ] Confidence scores are included
- [ ] Fallback to LLM-only works when no products match

## Troubleshooting

### Migration Fails
- Check that pgvector image is being used: `docker compose config | grep image`
- Verify DATABASE_URL in .env

### Products Not Found in Search
- Check embeddings were generated: Look for "Generating embeddings" in logs
- Verify products table has data: `docker compose exec db psql -U postgres -d cleanfastapi -c "SELECT COUNT(*) FROM products;"`

### LLM Errors
- Verify HF_TOKEN is set in .env
- Check internet connectivity from container

### Import Takes Long Time
- First run downloads sentence-transformers model (~90MB)
- Subsequent runs should be faster

## Expected Behavior

### With Products in Database:
- Recommendations endpoint returns real products with specific details
- Match reasoning references actual product attributes
- Product URLs point to real stores

### Without Products (Fallback):
- Recommendations endpoint returns generic gift suggestions
- No specific product links
- More general reasoning

## Performance Notes

- Initial model download: ~2-3 minutes
- Product import (10 products): ~30 seconds
- Semantic search: <100ms per query
- Full RAG pipeline: ~5-10 seconds (includes LLM call)

## Testing Complete!

If all steps above complete successfully, the RAG pipeline implementation is working correctly!
