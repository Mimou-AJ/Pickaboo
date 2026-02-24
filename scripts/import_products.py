import sys
import os
import logging
from sqlalchemy import text

# Add the project root to the python path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.core import SessionLocal, engine, Base
from src.products.import_service import ProductImportService
from src.products.entity import Product  # Ensure models are registered

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_import(file_path: str):
    logger.info(f"Connecting to database...")
    
    # Ensure tables exist (especially pgvector)
    # This is a safe check even if they already exist
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        logger.info(f"Starting import for: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        service = ProductImportService(db)
        # Import full file (set limit to 50GB to cover the 6GB file) - Process in larger batches for speed
        max_bytes = 50 * 1024 * 1024 * 1024
        # Increased batch_size from default 1000 to 5000 for faster processing
        stats = service.import_from_json(file_path, batch_size=5000, max_bytes=max_bytes)
        
        print("\n=== IMPORT COMPLETE ===")
        print(f"Total variants processed: {stats.get('total_variants', 0)}")
        print(f"Unique products: {stats.get('unique_products', 0)}")
        print(f"Newly saved: {stats.get('newly_saved', 0)}")
        print(f"Errors encountered: {stats.get('errors', 0)}")
        
    except Exception as e:
        logger.error(f"Import process failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        # Default path inside Docker container
        target_file = "/app/data/products_example.json"
    
    run_import(target_file)
