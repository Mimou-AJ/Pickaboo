"""Run database migration to add products table."""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the migration SQL script."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cleanfastapi")
    
    print(f"Connecting to database...")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Read migration file
    migration_path = Path(__file__).parent.parent / "migrations" / "001_add_products_table.sql"
    
    if not migration_path.exists():
        print(f"Error: Migration file not found at {migration_path}")
        sys.exit(1)
    
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    print(f"Running migration: {migration_path.name}")
    
    # Execute migration
    try:
        with engine.connect() as conn:
            # Split SQL by semicolons and execute each statement
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            for statement in statements:
                print(f"Executing: {statement[:50]}...")
                conn.execute(text(statement))
                conn.commit()
        
        print("✓ Migration completed successfully!")
        print("Products table created with pgvector support.")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
