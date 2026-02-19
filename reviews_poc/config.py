
import os
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = "mixtral-8x7b-32768"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 500
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "27017"))
DB_NAME = os.getenv("DB_NAME", "reviews_poc")



SENTIMENT_TAGS = [
    "SENTIMENT_POSITIVE",
    "SENTIMENT_NEUTRAL",
    "SENTIMENT_NEGATIVE"
]

TOPIC_TAGS = [
    "CLEANLINESS",
    "ROOM_QUALITY",
    "BATHROOM",
    "FOOD_BREAKFAST",
    "RESTAURANT_FOOD",
    "SERVICE_STAFF",
    "CHECKIN_CHECKOUT",
    "LOCATION",
    "AMENITIES",
    "WIFI",
    "NOISE",
    "PARKING",
    "SAFETY_SECURITY",
    "MAINTENANCE"
]

SPECIAL_TAGS = [
    "PRICE_MENTIONED",
    "OWNER_MENTIONED",
    "CONTACT_INFO_MENTIONED",
    "ABUSIVE_CONTENT",
    "SPAM_SUSPECT"
]

ALL_TAGS = SENTIMENT_TAGS + TOPIC_TAGS + SPECIAL_TAGS

TOPICS_FOR_GENERATION = [
    "Cleanliness and room condition",
    "Bathroom quality and amenities",
    "Breakfast and restaurant food quality",
    "Staff behavior and customer service",
    "Check-in and check-out experience",
    "Hotel location and nearby attractions",
    "Pool, gym, and other amenities",
    "WiFi quality and connectivity",
    "Noise levels and quiet atmosphere",
    "Parking availability and quality",
    "Safety and security measures",
    "Maintenance and repairs"
]

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
