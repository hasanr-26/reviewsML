# Hotel Reviews Analysis & Tagging POC

Review analysis system that moderates hotel reviews using LLM + regex detection, assigns sentiment/topic tags, and makes PUBLISH/REJECT decisions based on business rules.

## Prerequisites

- Python 3.8+
- MongoDB (running locally)
- Groq API Key (free: https://console.groq.com/keys)

## Setup

```bash
cd reviews_poc
pip install -r requirements.txt
```

`.env` file:
```
GROQ_API_KEY=your_key_here
DB_HOST=localhost
DB_PORT=27017
DB_NAME=reviews_poc
```

generate the dataset:
```bash
python generate_dataset.py
```

## Running

```bash
python -m uvicorn api:app --reload
```

Open http://localhost:8000/docs for the Swagger UI.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/reviews/analyze-one` | Analyze a single review |
| POST | `/reviews/analyze-bulk` | Analyze reviews from a file (jsonl/csv/json) |
| POST | `/reviews/generate` | Generate synthetic reviews using AI |
| GET | `/reports/summary?hotel_id=HOTEL_001` | Get stats for a hotel |
| GET | `/db/info` | MongoDB status and counts |

## How It Works

Each review goes through:
1. **LLM Analysis** — Groq Mixtral extracts sentiment, signals, and topics
2. **Regex Backup** — patterns catch prices, phone numbers, links, profanity that LLM might miss
3. **Business Rules** — any flagged signal triggers REJECT, otherwise PUBLISH
4. **Tagging** — sentiment tag + topic tags + special tags assigned
5. **Storage** — raw and enriched reviews saved to MongoDB

## Rejection Rules

A review is rejected if it contains:
- Price/tariff mentions (₹, Rs, "per night", etc.)
- Hotel owner or manager names
- Phone numbers or email addresses
- Profanity or abusive language
- Spam links or advertisements
- Hate speech, sexual, or violent content

## Project Structure

```
reviews_poc/
├── api.py                 # FastAPI server (6 endpoints)
├── config.py              # Settings (LLM, DB, tags)
├── database.py            # MongoDB connection and indexes
├── models.py              # Pydantic request/response models
├── prompts.py             # LLM prompts and regex patterns
├── review_analyzer.py     # Analysis pipeline (LLM + regex + rules)
├── review_generator.py    # AI review generation
├── utils.py               # File import/export helpers
├── generate_dataset.py    # Script to generate 500 reviews
└── requirements.txt       # Dependencies
```

## Tags

**Sentiment** (1 per review): `SENTIMENT_POSITIVE`, `SENTIMENT_NEUTRAL`, `SENTIMENT_NEGATIVE`

**Topics**: `CLEANLINESS`, `ROOM_QUALITY`, `BATHROOM`, `FOOD_BREAKFAST`, `RESTAURANT_FOOD`, `SERVICE_STAFF`, `CHECKIN_CHECKOUT`, `LOCATION`, `AMENITIES`, `WIFI`, `NOISE`, `PARKING`, `SAFETY_SECURITY`, `MAINTENANCE`

**Special**: `PRICE_MENTIONED`, `OWNER_MENTIONED`, `CONTACT_INFO_MENTIONED`, `ABUSIVE_CONTENT`, `SPAM_SUSPECT`
