"""
Standalone script to generate 500+ reviews dataset
Run this to create the initial dataset before starting the API
"""
import sys
import logging
from pathlib import Path
from review_generator import ReviewGenerator, ReviewExporter
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

def main():
    """Generate and export reviews"""
    try:
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        logger.info("Data directory ensured")
        
        # Generate reviews
        hotel_id = config.DB_NAME  # Use default hotel ID
        count = 500  # Generate 500 reviews
        
        logger.info(f"Starting review generation: {count} reviews for {hotel_id}")
        
        generator = ReviewGenerator()
        reviews = generator.generate_reviews(count)
        
        if not reviews:
            logger.error("No reviews were generated")
            return 1
        
        # Export
        exporter = ReviewExporter()
        jsonl_path = exporter.export_jsonl(reviews, "data/reviews_raw.jsonl")
        csv_path = exporter.export_csv(reviews, "data/reviews_raw.csv")
        
        logger.info("=" * 60)
        logger.info("✓ Review Generation Completed Successfully!")
        logger.info("=" * 60)
        logger.info(f"Generated: {len(reviews)} reviews")
        logger.info(f"JSONL Export: {jsonl_path}")
        logger.info(f"CSV Export: {csv_path}")
        logger.info("\nNext steps:")
        logger.info("1. Start the API: python -m uvicorn api:app --reload")
        logger.info("2. Open Swagger UI: http://localhost:8000/docs")
        logger.info("3. Test endpoints with the generated data")
        
        return 0
    
    except Exception as e:
        logger.error(f"Failed to generate reviews: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
