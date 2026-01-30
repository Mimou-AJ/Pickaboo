-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create products table with vector embeddings
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_product_id VARCHAR(100) NOT NULL,
    store_url VARCHAR(500) NOT NULL,
    product_url VARCHAR(1000),
    name VARCHAR(500) NOT NULL,
    vendor VARCHAR(200),
    product_type VARCHAR(200),
    price_eur FLOAT,
    price_min FLOAT,
    price_max FLOAT,
    available BOOLEAN DEFAULT true,
    colors TEXT[],
    sizes TEXT[],
    gender_target VARCHAR(50),
    tags TEXT[],
    variants JSONB,
    description TEXT,
    image_url VARCHAR(1000),
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_product_id, store_url)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_products_price ON products (price_eur);
CREATE INDEX IF NOT EXISTS idx_products_available ON products (available);
CREATE INDEX IF NOT EXISTS idx_products_gender ON products (gender_target);

-- Create IVFFlat index for vector similarity search
-- Note: This index should be created after data is loaded for better performance
-- For now, we create it with a default list count
CREATE INDEX IF NOT EXISTS products_embedding_idx ON products 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
