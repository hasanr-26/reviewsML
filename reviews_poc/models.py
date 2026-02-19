"""
Pydantic models for API and data validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ReviewInput(BaseModel):
    """Input model for single review analysis"""
    hotel_id: str = Field(..., description="Hotel ID")
    review_text: str = Field(..., description="Review text")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    reviewer_name: Optional[str] = None
    source: Optional[str] = "internal"

class ReviewAnalysisOutput(BaseModel):
    """Output model for review analysis"""
    review_id: str
    hotel_id: str
    rating: int
    review_text: str
    summary: str
    sentiment: str
    publish_decision: str
    rejection_reasons: List[str]
    tags: List[str]
    detected_signals: dict
    flags: List[str]

class BulkAnalysisInput(BaseModel):
    """Input model for bulk review analysis"""
    hotel_id: str = Field(..., description="Hotel ID")
    input_format: str = Field(..., description="Format: jsonl, csv, json")
    input_path: str = Field(..., description="Path to input file")

class BulkAnalysisOutput(BaseModel):
    """Output model for bulk analysis"""
    total_reviews: int
    published_count: int
    rejected_count: int
    db_rows_inserted: int
    csv_output_path: str
    processing_time_seconds: float

class ReviewGenerationInput(BaseModel):
    """Input model for review generation"""
    hotel_id: str = Field(..., description="Hotel ID")
    count: int = Field(default=500, ge=1, le=5000, description="Number of reviews")

class ReviewGenerationOutput(BaseModel):
    """Output model for review generation"""
    hotel_id: str
    total_generated: int
    jsonl_path: str
    csv_path: str

class SummaryReportOutput(BaseModel):
    """Output model for summary report"""
    hotel_id: str
    total_reviews: int
    published_count: int
    rejected_count: int
    publish_percentage: float
    rejection_reason_counts: dict
    tag_distribution: dict
    sentiment_distribution: dict

class ReviewRawDB(BaseModel):
    review_id: str
    hotel_id: str
    rating: int
    review_text: str
    reviewer_name: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewEnrichedDB(BaseModel):
    review_id: str
    hotel_id: str
    rating: int
    review_text: str
    publish_decision: str
    rejection_reasons: List[str]
    flags: List[str]
    summary: str
    tags: List[str]
    sentiment: str
    detected_signals: dict
    analyzed_at: datetime
    model_name: str
    prompt_version: str

    class Config:
        from_attributes = True
