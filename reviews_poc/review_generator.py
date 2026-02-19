"""
Review generation module using Groq API
"""
import json
import logging
from typing import List, Dict
import uuid
from datetime import datetime, timedelta
import random
from groq import Groq
import config
from prompts import REVIEW_GENERATION_PROMPT, PROMPT_VERSION

logger = logging.getLogger(__name__)

# Groq client will be initialized on first use
client = None

def _get_client():
    """Lazy-load Groq client on first use"""
    global client
    if client is None:
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is not set. Please add it to your .env file.")
        client = Groq(api_key=config.GROQ_API_KEY)
    return client

class ReviewGenerator:
    """Generate realistic hotel reviews using Groq"""
    
    def __init__(self):
        self.hotel_id = "HOTEL_001"
        self.rating_weights = {1: 0.1, 2: 0.1, 3: 0.2, 4: 0.3, 5: 0.3}
        self.sources = ["google", "booking", "internal"]
        self.reviewer_names = [
            "Rajesh Kumar", "Priya Singh", "Amit Patel", "Neha Sharma", "Vikram Rao",
            "Kavya Desai", "Arjun Menon", "Sangeeta Gupta", "Rohan Verma", "Isha Kapoor",
            "Deepak Mishra", "Anjali Nair", "Sanjay Reddy", "Pooja Kumari", "Nikhil Joshi",
            "Divya Sinha", "Rahul Chatterjee", "Sneha Dubey", "Varun Singh", "Meera Iyer",
            "John Smith", "Sarah Johnson", "Michael Brown", "Emma Davis", "Robert Wilson",
            "Lisa Anderson", "David Martinez", "Jennifer Taylor", "James Thomas", "Mary White"
        ]
    
    def generate_reviews(self, count: int) -> List[Dict]:
        """Generate reviews using Groq"""
        reviews = []
        logger.info(f"Starting generation of {count} reviews")
        
        for i in range(count):
            try:
                rating = self._weighted_random_rating()
                topic = random.choice(config.TOPICS_FOR_GENERATION)
                reviewer_name = random.choice(self.reviewer_names)
                source = random.choice(self.sources)
                
                # ~20% problematic reviews
                if random.random() < 0.2:
                    review_text = self._generate_problematic_review(rating, topic, reviewer_name)
                else:
                    review_text = self._generate_normal_review(rating, topic, reviewer_name)
                
                if review_text:
                    review_id = f"{self.hotel_id}_{uuid.uuid4().hex[:12]}"
                    created_at = datetime.utcnow() - timedelta(days=random.randint(1, 365))
                    
                    review = {
                        "review_id": review_id,
                        "hotel_id": self.hotel_id,
                        "rating": rating,
                        "review_text": review_text,
                        "reviewer_name": reviewer_name,
                        "source": source,
                        "created_at": created_at.isoformat()
                    }
                    reviews.append(review)
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"Generated {i + 1}/{count} reviews")
            
            except Exception as e:
                logger.error(f"Error generating review {i + 1}: {e}")
                continue
        
        logger.info(f"Successfully generated {len(reviews)} reviews")
        return reviews
    
    def _generate_normal_review(self, rating: int, topic: str, reviewer_name: str) -> str:
        """Generate a normal review without problematic content"""
        try:
            prompt = REVIEW_GENERATION_PROMPT.format(
                topic=topic,
                rating=rating,
                reviewer_name=reviewer_name
            )
            
            response = _get_client().chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                timeout=30
            )
            
            review_text = response.choices[0].message.content.strip()
            return review_text if len(review_text) > 10 else None
        
        except Exception as e:
            logger.error(f"Groq API error in normal review generation: {e}")
            return None
    
    def _generate_problematic_review(self, rating: int, topic: str, reviewer_name: str) -> str:
        """Generate a review with problematic content (price, owner name, etc.)"""
        problematic_templates = [
            # Price mentions
            f"The room was nice but I paid ₹{random.randint(3000, 8000)} per night. {topic} was okay.",
            f"Location is great, Rs. {random.randint(4000, 7000)} seemed expensive though. {topic} was average.",
            f"I paid {random.randint(2000, 6000)} rupees which felt high. {topic} was decent.",
            
            # Owner/manager mentions
            f"The owner Mr. Sharma was helpful but {topic} could be better.",
            f"Manager Priya was nice but the {topic} was disappointing.",
            f"Spoke with owner Rajesh Kumar about {topic} - he promised improvements.",
            
            # Email/phone mentions
            f"For complaints, contact {random.choice(['admin@grandparadise.com', '9876543210', 'info@hotel.in'])}",
            
            # Abusive language
            f"The damn {topic} was horrible! Waste of money!",
            f"Bloody awful {topic}! Worst experience ever!",
            
            # Spam-like
            f"Check out my blog: www.myhotelreviews.com for more reviews about {topic}",
        ]
        
        return random.choice(problematic_templates)
    
    def _weighted_random_rating(self) -> int:
        """Return a weighted random rating"""
        ratings = list(self.rating_weights.keys())
        weights = list(self.rating_weights.values())
        return random.choices(ratings, weights=weights, k=1)[0]

class ReviewExporter:
    """Export reviews to JSONL and CSV formats"""
    
    @staticmethod
    def export_jsonl(reviews: List[Dict], filepath: str) -> str:
        """Export reviews to JSONL format"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for review in reviews:
                    f.write(json.dumps(review, ensure_ascii=False) + '\n')
            logger.info(f"Exported {len(reviews)} reviews to JSONL: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export JSONL: {e}")
            raise
    
    @staticmethod
    def export_csv(reviews: List[Dict], filepath: str) -> str:
        """Export reviews to CSV format"""
        try:
            import pandas as pd
            df = pd.DataFrame(reviews)
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported {len(reviews)} reviews to CSV: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise

def generate_and_export_reviews(hotel_id: str, count: int) -> Dict:
    """Main function to generate and export reviews"""
    generator = ReviewGenerator()
    exporter = ReviewExporter()
    
    # Generate reviews
    reviews = generator.generate_reviews(count)
    
    # Export to JSONL and CSV
    jsonl_path = f"data/reviews_raw.jsonl"
    csv_path = f"data/reviews_raw.csv"
    
    exporter.export_jsonl(reviews, jsonl_path)
    exporter.export_csv(reviews, csv_path)
    
    return {
        "hotel_id": hotel_id,
        "total_generated": len(reviews),
        "jsonl_path": jsonl_path,
        "csv_path": csv_path
    }
