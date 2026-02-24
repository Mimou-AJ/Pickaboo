-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create products table
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

-- Create indexes
CREATE INDEX IF NOT EXISTS products_embedding_idx ON products 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS products_price_idx ON products(price_eur);
CREATE INDEX IF NOT EXISTS products_available_idx ON products(available);
CREATE INDEX IF NOT EXISTS products_gender_idx ON products(gender_target);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
