# Hotel Reviews Analysis & Tagging POC

A comprehensive Proof of Concept system for analyzing hotel reviews, determining publication eligibility, and automatically tagging them using AI and business rules.

## 🎯 Features

- **AI-Powered Review Generation**: Generate 500+ realistic hotel reviews with problematic cases
- **Smart Analysis**: LLM analysis combined with regex-based backup detection
- **Automated Tagging**: Multi-label tagging with sentiment + topic tags
- **Moderation**: Intelligent decision engine for review publication eligibility
- **Multiple Input Formats**: Support for JSON, CSV, and JSONL
- **Full API**: FastAPI with Swagger UI for easy testing
- **Database Storage**: MongoDB integration for persistence and reporting
- **Export Capabilities**: CSV export of analyzed reviews

## 🏗️ Architecture

```
FastAPI Application
├── Review Generation (AI-powered)
├── Review Analysis (LLM + Business Rules)
├── Database Layer (MongoDB)
└── API Endpoints (Swagger)
```

## 📋 Prerequisites

- Python 3.8+
- MongoDB Server (running locally or remote)
- Groq API Key (free from https://console.groq.com/keys)
- Other dependencies (see requirements.txt)

## 🚀 Installation & Setup

### Step 1: Clone/Setup Project

```bash
cd reviews_poc
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
GROQ_API_KEY=your_groq_api_key_here
DB_HOST=localhost
DB_PORT=27017
DB_NAME=reviews_poc
```

### Step 4: Setup MongoDB

**Install MongoDB** from: https://www.mongodb.com/try/download/community

**Start MongoDB Server**:
```bash
# Windows: In PowerShell
mongod

# Mac:
brew services start mongodb-community

# Linux:
sudo systemctl start mongod
```

**Verify MongoDB is running**:
```bash
mongosh
# Or for older MongoDB:
mongo
```

The application will automatically:
- Connect to MongoDB
- Create the database (`reviews_poc`)
- Create collections (`reviews_raw`, `reviews_enriched`)
- Create necessary indexes

### Step 5: Generate Initial Dataset (500 Reviews)

```bash
python generate_dataset.py
```

This will:
- Generate 500 realistic hotel reviews
- Export to `data/reviews_raw.jsonl`
- Export to `data/reviews_raw.csv`

⚠️ **This requires a valid Groq API key in your `.env` file. Get it free from https://console.groq.com/keys**

## 🎮 Running the Application

### Start the FastAPI Server

```bash
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup completed
```

### Access Swagger UI

Open your browser and go to: **http://localhost:8000/docs**

You should see the interactive Swagger UI with all endpoints.

## 📡 API Endpoints

### 1️⃣ Analyze Single Review

**Endpoint**: `POST /reviews/analyze-one`

**Description**: Analyze a single review (perfect for testing in Swagger)

**Request Body**:
```json
{
  "hotel_id": "HOTEL_001",
  "review_text": "Rooms were clean but I paid 6500 per night",
  "rating": 3,
  "reviewer_name": "John Doe",
  "source": "google"
}
```

**Response**:
```json
{
  "review_id": "HOTEL_001_a1b2c3d4e5f6",
  "hotel_id": "HOTEL_001",
  "rating": 3,
  "summary": "Good rooms but expensive",
  "sentiment": "SENTIMENT_NEUTRAL",
  "publish_decision": "REJECT",
  "rejection_reasons": [
    "Price, tariff, or monetary amount mentioned"
  ],
  "tags": [
    "SENTIMENT_NEUTRAL",
    "ROOM_QUALITY",
    "PRICE_MENTIONED"
  ],
  "detected_signals": {
    "price_mentioned": true,
    "owner_name_mentioned": false,
    "phone_email_present": false,
    "abusive_language": false,
    "spam_or_links": false,
    "hate_sexual_violent": false,
    "too_short": false
  },
  "flags": []
}
```

**Testing in Swagger**:
1. Go to **http://localhost:8000/docs**
2. Find "POST /reviews/analyze-one" section
3. Click "Try it out"
4. Paste the JSON request
5. Click "Execute"

### 2️⃣ Analyze Bulk Reviews from File

**Endpoint**: `POST /reviews/analyze-bulk`

**Description**: Analyze multiple reviews from a file and save to database & CSV

**Request Body**:
```json
{
  "hotel_id": "HOTEL_001",
  "input_format": "jsonl",
  "input_path": "data/reviews_raw.jsonl"
}
```

**Supported Formats**: `jsonl`, `csv`, `json`

**Response**:
```json
{
  "total_reviews": 500,
  "published_count": 425,
  "rejected_count": 75,
  "mysql_rows_inserted": 500,
  "csv_output_path": "exports/reviews_enriched.csv",
  "processing_time_seconds": 245.3
}
```

### 3️⃣ Generate Reviews

**Endpoint**: `POST /reviews/generate`

**Description**: Generate synthetic reviews using AI

**Request Body**:
```json
{
  "hotel_id": "HOTEL_001",
  "count": 500
}
```

**Response**:
```json
{
  "hotel_id": "HOTEL_001",
  "total_generated": 500,
  "jsonl_path": "data/reviews_raw.jsonl",
  "csv_path": "data/reviews_raw.csv"
}
```

### 4️⃣ Get Summary Report

**Endpoint**: `GET /reports/summary?hotel_id=HOTEL_001`

**Description**: Get analytics and statistics for a hotel

**Response**:
```json
{
  "hotel_id": "HOTEL_001",
  "total_reviews": 500,
  "published_count": 425,
  "rejected_count": 75,
  "publish_percentage": 85.0,
  "rejection_reason_counts": {
    "Price, tariff, or monetary amount mentioned": 35,
    "Phone number or email address present": 20,
    "Contains profanity or abusive language": 15,
    "Contains spam, advertisements, or links": 5
  },
  "tag_distribution": {
    "SENTIMENT_POSITIVE": 280,
    "SENTIMENT_NEUTRAL": 150,
    "SENTIMENT_NEGATIVE": 70,
    "CLEANLINESS": 120,
    "ROOM_QUALITY": 95,
    "SERVICE_STAFF": 110,
    "PRICE_MENTIONED": 35
  },
  "sentiment_distribution": {
    "SENTIMENT_POSITIVE": 280,
    "SENTIMENT_NEUTRAL": 150,
    "SENTIMENT_NEGATIVE": 70
  }
}
```

### 5️⃣ Health Check

**Endpoint**: `GET /health`

**Response**: Status and timestamp

### 6️⃣ Database Info

**Endpoint**: `GET /db/info`

**Response**: Database statistics

## 📊 Available Tags

### Sentiment Tags (exactly 1)
- `SENTIMENT_POSITIVE`
- `SENTIMENT_NEUTRAL`
- `SENTIMENT_NEGATIVE`

### Topic Tags (zero or more)
- `CLEANLINESS`
- `ROOM_QUALITY`
- `BATHROOM`
- `FOOD_BREAKFAST`
- `RESTAURANT_FOOD`
- `SERVICE_STAFF`
- `CHECKIN_CHECKOUT`
- `LOCATION`
- `AMENITIES`
- `WIFI`
- `NOISE`
- `PARKING`
- `SAFETY_SECURITY`
- `MAINTENANCE`

### Special Tags (when applicable)
- `PRICE_MENTIONED`
- `OWNER_MENTIONED`
- `CONTACT_INFO_MENTIONED`
- `ABUSIVE_CONTENT`
- `SPAM_SUSPECT`

## 🚫 Hard Reject Rules

A review is **REJECTED** if ANY of these conditions are true:
1. ✗ Price/tariff mentioned (₹, Rs, INR, "per night", etc.)
2. ✗ Hotel owner/manager name mentioned
3. ✗ Phone number or email present
4. ✗ Abusive/profane language
5. ✗ Spam, advertisements, or links
6. ✗ Hate speech, sexual, or violent content

## 📁 Project Structure

```
reviews_poc/
├── api.py                    # FastAPI application
├── config.py                 # Configuration & settings
├── database.py              # MongoDB connection & setup
├── models.py                # Pydantic models
├── prompts.py               # LLM prompts (versioned)
├── review_analyzer.py       # Analysis engine
├── review_generator.py      # Review generation
├── utils.py                 # Utility functions
├── generate_dataset.py      # Dataset generation script
├── database_schema.sql      # MySQL schema
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file

data/
├── reviews_raw.jsonl        # Generated reviews (JSONL)
└── reviews_raw.csv          # Generated reviews (CSV)

exports/
└── reviews_enriched.csv     # Analysis results
```

## 🧪 Testing Workflow

### Quick Test (Single Review in Swagger)

1. Start API: `python -m uvicorn api:app --reload`
2. Open Swagger: http://localhost:8000/docs
3. Test POST /reviews/analyze-one with sample review
4. Check response for publish_decision, tags, sentiment

### Full Workflow Test

1. Generate dataset:
   ```bash
   python generate_dataset.py
   ```

2. Start API:
   ```bash
   python -m uvicorn api:app --reload
   ```

3. Analyze all reviews:
   ```bash
   # Use Swagger to POST /reviews/analyze-bulk
   # Input: data/reviews_raw.jsonl
   ```

4. Check results:
   ```bash
   # GET /reports/summary?hotel_id=HOTEL_001
   # View exports/reviews_enriched.csv
   ```

## 🤖 Model Details

**Recommended Model**: Groq Mixtral-8x7b (free model)

- **Cost**: ~$0.002 per 1K tokens (very affordable)
- **Speed**: Fast (1-2 sec per review)
- **Quality**: Excellent for this task
- **Reliability**: Production-ready

**Why not other models?**
- GPT-4: 10x more expensive, overkill for this task
- Llama 2 (local): Requires more setup, needs GPU
- Claude 3: Similar quality, slightly higher cost

## 🛠️ Troubleshooting

### Error: "Could not connect to MySQL"
- Check if MySQL is running
- Verify connection credentials in `.env`
- Test: `mysql -u root -p -h localhost`

### Error: "Invalid API Key"
- Check your OpenAI API key in `.env`
- Ensure key starts with `sk-`
- Test with OpenAI Python client: `from openai import OpenAI; client = OpenAI()`

### Error: "JSONDecodeError" in review analysis
- This is handled gracefully with fallback defaults
- Check logs for which review failed
- LLM fallback with regex rules is still applied

### Slow performance
- First run will be slower (downloading Model)
- Subsequent runs cached
- Batch processing typically: 500 reviews in 3-5 minutes

### CSV not generated
- Check `exports/` directory exists
- Verify write permissions
- Check logs for detailed error

## 📈 Performance Expectations

- **Single review analysis**: 1-2 seconds
- **500 reviews batch**: 5-15 minutes (depends on Groq rate limits)
- **Database queries**: < 100ms
- **CSV export**: < 5 seconds

## 📝 Logging

Logs are printed to console with timestamp:
```
2024-01-15 10:30:45,123 - review_generator - INFO - Generating 500 reviews
2024-01-15 10:35:12,456 - api - INFO - Bulk analysis completed: 500 reviews in 245.3s
```

## 🔐 Security Considerations

For production deployment:
1. Use environment variables for all secrets
2. Add authentication to API endpoints
3. Use HTTPS for all communications
4. Implement rate limiting
5. Add audit logging
6. Sanitize all inputs
7. Use database credentials with minimal permissions

## 📚 API Documentation

Full interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎓 Understanding the Analysis Flow

```
Input Review
    ↓
[LLM Analysis] → Extract signals, sentiment, topics
    ↓ (fallback)
[Regex Checks] → Detect price, emails, profanity, links
    ↓
[Business Rules] → Apply hard reject rules
    ↓
[Decision] → PUBLISH or REJECT
    ↓
[Tagging] → Multi-label tags
    ↓
[Database] → Store results
    ↓
Output (JSON + Database Record)
```

## 📞 Support

For issues or questions:
1. Check the Logs
2. Review the README's Troubleshooting section
3. Check API response for detailed error messages
4. Verify configuration in `.env`

## 📄 License

This is a Proof of Concept for hotel review analysis.

---

**Happy Reviewing! 🚀**

For the complete workflow:
1. `pip install -r requirements.txt`
2. Setup `.env` with your credentials
3. `mysql -u root -p < database_schema.sql`
4. `python generate_dataset.py`
5. `python -m uvicorn api:app --reload`
6. Open http://localhost:8000/docs
7. Start testing! 🎉
