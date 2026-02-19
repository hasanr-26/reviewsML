"""
MongoDB database connection and utilities
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
import logging
import config

logger = logging.getLogger(__name__)

client = None
db = None

def init_db():
    """Initialize MongoDB connection and create indexes"""
    global client, db
    try:
        client = MongoClient(config.MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[config.DB_NAME]
        logger.info(f"Connected to MongoDB: {config.DB_NAME}")
        
        _create_collections()
        _create_indexes()
        
        logger.info("Database initialization completed")
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def _create_collections():
    """Create collections if they don't exist"""
    if "reviews_raw" not in db.list_collection_names():
        db.create_collection("reviews_raw")
        logger.info("Created collection: reviews_raw")
    
    if "reviews_enriched" not in db.list_collection_names():
        db.create_collection("reviews_enriched")
        logger.info("Created collection: reviews_enriched")

def _create_indexes():
    """Create indexes for optimal query performance"""
    try:
        db.reviews_raw.create_index([("review_id", ASCENDING)], unique=True)
        db.reviews_raw.create_index([("hotel_id", ASCENDING)])
        db.reviews_raw.create_index([("created_at", DESCENDING)])
        logger.info("Created indexes for reviews_raw")
        
        db.reviews_enriched.create_index([("review_id", ASCENDING)], unique=True)
        db.reviews_enriched.create_index([("hotel_id", ASCENDING)])
        db.reviews_enriched.create_index([("publish_decision", ASCENDING)])
        db.reviews_enriched.create_index([("sentiment", ASCENDING)])
        db.reviews_enriched.create_index([("analyzed_at", DESCENDING)])
        logger.info("Created indexes for reviews_enriched")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def get_db():
    """Get MongoDB database instance"""
    global db
    if db is None:
        init_db()
    return db

def close_db():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

def get_reviews_raw_collection():
    """Get reviews_raw collection"""
    return get_db().reviews_raw

def get_reviews_enriched_collection():
    """Get reviews_enriched collection"""
    return get_db().reviews_enriched
