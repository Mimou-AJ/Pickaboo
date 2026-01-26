"""Script to run database migrations."""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Execute SQL migration script."""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cleanfastapi")
    
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    # Read migration file
    migration_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "001_add_products_table.sql")
    
    with open(migration_path, 'r') as f:
        sql_script = f.read()
    
    # Execute migration
    print("Executing migration...")
    with engine.connect() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for statement in statements:
            try:
                conn.execute(text(statement))
                conn.commit()
            except Exception as e:
                print(f"Error executing statement: {e}")
                print(f"Statement: {statement[:100]}...")
                raise
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
