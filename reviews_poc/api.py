"""
FastAPI application for Reviews Analysis POC (MongoDB Version)
"""
import logging
import time
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime

import config
from models import ReviewInput, ReviewAnalysisOutput, BulkAnalysisInput, BulkAnalysisOutput
from models import ReviewGenerationInput, ReviewGenerationOutput, SummaryReportOutput
from database import init_db, get_reviews_raw_collection, get_reviews_enriched_collection, close_db
from review_generator import ReviewGenerator, ReviewExporter, generate_and_export_reviews
from review_analyzer import ReviewAnalyzer
from utils import DataImporter, DataExporter, FileManager, validate_review_input

logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hotel Reviews Analysis POC",
    description="Proof of Concept for review analysis, moderation, and tagging",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Initialize database on application startup"""
    try:
        init_db()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown"""
    close_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/reviews/analyze-one", response_model=ReviewAnalysisOutput)
async def analyze_single_review(review: ReviewInput):
    """
    Analyze a single review submitted via Swagger
    
    This endpoint:
    - Takes a hotel review as input
    - Analyzes it using LLM
    - Applies business rules
    - Returns analysis results
    """
    try:
        review_id = f"{review.hotel_id}_{uuid.uuid4().hex[:12]}"
        
        analyzer = ReviewAnalyzer()
        analysis = analyzer.analyze_review(
            review_id=review_id,
            hotel_id=review.hotel_id,
            rating=review.rating,
            review_text=review.review_text
        )
        
        enriched_collection = get_reviews_enriched_collection()
        enriched_record = {
            "review_id": analysis['review_id'],
            "hotel_id": analysis['hotel_id'],
            "rating": analysis['rating'],
            "review_text": analysis['review_text'],
            "publish_decision": analysis['publish_decision'],
            "rejection_reasons": analysis['rejection_reasons'],
            "flags": analysis['flags'],
            "summary": analysis['summary'],
            "tags": analysis['tags'],
            "sentiment": analysis['sentiment'],
            "detected_signals": analysis['detected_signals'],
            "model_name": analysis['model_name'],
            "prompt_version": analysis['prompt_version'],
            "analyzed_at": datetime.utcnow()
        }
        enriched_collection.insert_one(enriched_record)
        
        logger.info(f"Analyzed review {review_id}: {analysis['publish_decision']}")
        
        return ReviewAnalysisOutput(
            review_id=analysis['review_id'],
            hotel_id=analysis['hotel_id'],
            rating=analysis['rating'],
            review_text=analysis['review_text'],
            summary=analysis['summary'],
            sentiment=analysis['sentiment'],
            publish_decision=analysis['publish_decision'],
            rejection_reasons=analysis['rejection_reasons'],
            tags=analysis['tags'],
            detected_signals=analysis['detected_signals'],
            flags=analysis['flags']
        )
    
    except Exception as e:
        logger.error(f"Error in analyze_single_review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reviews/analyze-bulk", response_model=BulkAnalysisOutput)
async def analyze_bulk_reviews(request: BulkAnalysisInput):
    """
    Analyze multiple reviews from a file
    
    Supports: JSON, CSV, JSONL formats
    Returns: Database and CSV export results
    """
    try:
        start_time = time.time()
        FileManager.ensure_data_dir()
        
        importer = DataImporter()
        reviews_to_analyze = []
        
        logger.info(f"Importing {request.input_format} file: {request.input_path}")
        for review in importer.import_file(request.input_path, request.input_format):
            if validate_review_input(review):
                reviews_to_analyze.append(review)
        
        if not reviews_to_analyze:
            raise ValueError("No valid reviews found in input file")
        
        logger.info(f"Found {len(reviews_to_analyze)} valid reviews to analyze")
        
        raw_collection = get_reviews_raw_collection()
        enriched_collection = get_reviews_enriched_collection()
        
        for review in reviews_to_analyze:
            try:
                raw_record = {
                    "review_id": review.get('review_id', ''),
                    "hotel_id": request.hotel_id,
                    "rating": int(review.get('rating', 3)),
                    "review_text": str(review.get('review_text', '')),
                    "reviewer_name": review.get('reviewer_name', 'Anonymous'),
                    "source": review.get('source', 'internal'),
                    "created_at": datetime.utcnow()
                }
                raw_collection.update_one(
                    {"review_id": raw_record["review_id"]},
                    {"$set": raw_record},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"Failed to store raw review: {e}")
        
        logger.info(f"Stored {len(reviews_to_analyze)} raw reviews in MongoDB")
        
        analyzer = ReviewAnalyzer()
        analyzed_reviews = []
        published_count = 0
        rejected_count = 0
        
        for idx, review in enumerate(reviews_to_analyze, 1):
            try:
                review_id = review.get('review_id', f"{request.hotel_id}_{uuid.uuid4().hex[:8]}")
                rating = int(review.get('rating', 3))
                review_text = str(review.get('review_text', ''))
                
                analysis = analyzer.analyze_review(
                    review_id=review_id,
                    hotel_id=request.hotel_id,
                    rating=rating,
                    review_text=review_text
                )
                
                enriched_record = {
                    "review_id": analysis['review_id'],
                    "hotel_id": analysis['hotel_id'],
                    "rating": analysis['rating'],
                    "review_text": analysis['review_text'],
                    "publish_decision": analysis['publish_decision'],
                    "rejection_reasons": analysis['rejection_reasons'],
                    "flags": analysis['flags'],
                    "summary": analysis['summary'],
                    "tags": analysis['tags'],
                    "sentiment": analysis['sentiment'],
                    "detected_signals": analysis['detected_signals'],
                    "model_name": analysis['model_name'],
                    "prompt_version": analysis['prompt_version'],
                    "analyzed_at": datetime.utcnow()
                }
                enriched_collection.insert_one(enriched_record)
                
                analyzed_reviews.append(analysis)
                if analysis['publish_decision'] == 'PUBLISH':
                    published_count += 1
                else:
                    rejected_count += 1
                
                if idx % 10 == 0:
                    logger.info(f"Processed {idx}/{len(reviews_to_analyze)} reviews")
            
            except Exception as e:
                logger.error(f"Error analyzing review {idx}: {e}")
                continue
        
        csv_path = FileManager.get_export_path("reviews_enriched.csv")
        exporter = DataExporter()
        exporter.export_enriched_csv(analyzed_reviews, csv_path)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Bulk analysis completed: {len(analyzed_reviews)} reviews in {processing_time:.2f}s")
        
        return BulkAnalysisOutput(
            total_reviews=len(analyzed_reviews),
            published_count=published_count,
            rejected_count=rejected_count,
            db_rows_inserted=len(analyzed_reviews),
            csv_output_path=csv_path,
            processing_time_seconds=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error in analyze_bulk_reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reviews/generate", response_model=ReviewGenerationOutput)
async def generate_reviews(request: ReviewGenerationInput):
    """
    Generate realistic hotel reviews using AI
    
    Creates sample reviews with both good and problematic cases
    Exports to both JSONL and CSV formats
    """
    try:
        FileManager.ensure_data_dir()
        logger.info(f"Generating {request.count} reviews for {request.hotel_id}")
        
        result = generate_and_export_reviews(request.hotel_id, request.count)
        
        logger.info(f"Review generation completed: {result['total_generated']} reviews")
        return ReviewGenerationOutput(**result)
    
    except Exception as e:
        logger.error(f"Error in generate_reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/summary", response_model=SummaryReportOutput)
async def get_summary_report(hotel_id: str):
    """
    Get summary statistics for a hotel's reviews
    
    Returns:
    - Total reviews and publish/reject counts
    - Rejection reason distribution
    - Tag distribution
    - Sentiment distribution
    """
    try:
        enriched_collection = get_reviews_enriched_collection()
        
        total_reviews = enriched_collection.count_documents({"hotel_id": hotel_id})
        published_count = enriched_collection.count_documents({
            "hotel_id": hotel_id,
            "publish_decision": "PUBLISH"
        })
        rejected_count = total_reviews - published_count
        
        publish_percentage = (published_count / total_reviews * 100) if total_reviews > 0 else 0
        
        rejection_reason_counts = {}
        rejected_reviews = enriched_collection.find({
            "hotel_id": hotel_id,
            "publish_decision": "REJECT"
        })
        
        for review in rejected_reviews:
            if review.get("rejection_reasons"):
                for reason in review["rejection_reasons"]:
                    rejection_reason_counts[reason] = rejection_reason_counts.get(reason, 0) + 1
        
        sentiment_distribution = {}
        pipeline = [
            {"$match": {"hotel_id": hotel_id}},
            {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
        ]
        sentiment_results = enriched_collection.aggregate(pipeline)
        for doc in sentiment_results:
            sentiment_distribution[doc["_id"]] = doc["count"]
        
        tag_distribution = {}
        all_reviews = enriched_collection.find({"hotel_id": hotel_id})
        for review in all_reviews:
            if review.get("tags"):
                for tag in review["tags"]:
                    tag_distribution[tag] = tag_distribution.get(tag, 0) + 1
        
        return SummaryReportOutput(
            hotel_id=hotel_id,
            total_reviews=total_reviews,
            published_count=published_count,
            rejected_count=rejected_count,
            publish_percentage=round(publish_percentage, 2),
            rejection_reason_counts=rejection_reason_counts,
            tag_distribution=tag_distribution,
            sentiment_distribution=sentiment_distribution
        )
    
    except Exception as e:
        logger.error(f"Error in get_summary_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/info")
async def get_db_info():
    """Get MongoDB statistics"""
    try:
        raw_collection = get_reviews_raw_collection()
        enriched_collection = get_reviews_enriched_collection()
        
        raw_count = raw_collection.count_documents({})
        enriched_count = enriched_collection.count_documents({})
        
        return {
            "reviews_raw_count": raw_count,
            "reviews_enriched_count": enriched_count,
            "database": config.DB_NAME,
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "type": "MongoDB"
        }
    except Exception as e:
        logger.error(f"Error in get_db_info: {e}")
        return {
            "error": str(e),
            "message": "Failed to connect to MongoDB"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
