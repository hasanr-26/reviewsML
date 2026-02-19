# Hotel Reviews ML - Complete Code Explanation

## Table of Contents

1. [Overall System Architecture](#1-overall-system-architecture)
2. [How All Files Work Together](#2-how-all-files-work-together)
3. [File-by-File Explanation](#3-file-by-file-explanation)
   - [config.py](#31-configpy---configuration-center)
   - [prompts.py](#32-promptspy---ai-brain-instructions)
   - [models.py](#33-modelspy---data-shape-definitions)
   - [database.py](#34-databasepy---mongodb-connection)
   - [review_generator.py](#35-review_generatorpy---ai-review-creator)
   - [review_analyzer.py](#36-review_analyzerpy---the-core-analysis-engine)
   - [utils.py](#37-utilspy---helper-tools)
   - [api.py](#38-apipy---the-main-api-server)
   - [generate_dataset.py](#39-generate_datasetpy---standalone-data-creator)
   - [create_sample_dataset.py](#310-create_sample_datasetpy---offline-data-creator)
4. [Complete Data Flow](#4-complete-data-flow)
5. [Business Rules Explained](#5-business-rules-explained)

---

## 1. Overall System Architecture

```
                    USER (Browser / Swagger UI)
                           |
                           v
                  +------------------+
                  |     api.py       |   <-- FastAPI Web Server (entry point)
                  |   (6 endpoints)  |
                  +------------------+
                     /    |    \
                    /     |     \
                   v      v      v
      +-------------+ +----------+ +-----------+
      | review_     | | review_  | | database  |
      | generator.py| | analyzer | | .py       |
      | (creates    | | .py      | | (MongoDB  |
      |  reviews)   | | (analyzes| |  storage) |
      +-------------+ | reviews) | +-----------+
           |           +----------+      |
           |              |    |         |
           v              v    v         v
      +---------+   +--------+ +----------+
      | prompts | | config | | MongoDB  |
      | .py     | | .py    | | Database |
      +---------+ +--------+ +----------+
           |           |
           v           v
      +--------+  +--------+
      | models | | utils  |
      | .py    | | .py    |
      +--------+ +--------+
```

**In simple terms:** This is a hotel review management system that:
1. **Generates** fake but realistic hotel reviews using AI (Groq LLM)
2. **Analyzes** each review to detect problems (prices, abuse, spam, etc.)
3. **Decides** whether a review should be PUBLISHED or REJECTED
4. **Tags** each review with sentiment and topic labels
5. **Stores** everything in MongoDB
6. **Exposes** all functionality via a REST API with Swagger UI

---

## 2. How All Files Work Together

### The Request Journey (when you analyze a review):

```
Step 1: User sends a review via Swagger UI (http://localhost:8000/docs)
          |
Step 2: api.py receives the HTTP request
          |
Step 3: api.py calls ReviewAnalyzer from review_analyzer.py
          |
Step 4: ReviewAnalyzer sends the review text to Groq AI (using prompts.py template)
          |
Step 5: Groq AI returns: sentiment, signals, topic tags, summary
          |
Step 6: ReviewAnalyzer runs regex checks (backup detection from prompts.py patterns)
          |
Step 7: ReviewAnalyzer applies business rules (PUBLISH or REJECT decision)
          |
Step 8: api.py saves the result to MongoDB (via database.py)
          |
Step 9: api.py returns the full analysis as JSON to the user
```

### File Dependencies Map:

```
api.py ──────> config.py          (settings)
  |──────────> models.py          (request/response shapes)
  |──────────> database.py        (MongoDB operations)
  |──────────> review_generator.py (AI review creation)
  |──────────> review_analyzer.py  (AI review analysis)
  |──────────> utils.py            (file import/export)

review_generator.py ──> config.py  (API key, model name)
                    ──> prompts.py (generation prompt template)
                    ──> groq       (AI API calls)

review_analyzer.py ──> config.py   (API key, model, tags)
                   ──> prompts.py  (analysis prompt + regex patterns)
                   ──> groq        (AI API calls)

database.py ──> config.py         (MongoDB connection string)
            ──> pymongo           (MongoDB driver)

utils.py ──> pandas               (CSV operations)

generate_dataset.py ──> review_generator.py (uses it to create 500 reviews)
                    ──> config.py

create_sample_dataset.py ──> (standalone, no AI needed, hardcoded templates)
```

---

## 3. File-by-File Explanation

---

### 3.1 `config.py` — Configuration Center

**Purpose:** Central place for ALL settings. Every other file imports from here.

**What it does:**
- Loads environment variables from `.env` file using `python-dotenv`
- Stores LLM (AI) settings: which model to use, temperature, max tokens
- Stores MongoDB connection details: host, port, database name
- Defines ALL valid tags the system can assign to reviews
- Defines topics used for generating reviews

**Key Variables:**

| Variable | Value | What it controls |
|----------|-------|-----------------|
| `LLM_MODEL` | `"mixtral-8x7b-32768"` | Which Groq AI model to use |
| `LLM_TEMPERATURE` | `0.7` | AI creativity (0=strict, 1=creative) |
| `LLM_MAX_TOKENS` | `500` | Max length of AI response |
| `GROQ_API_KEY` | from `.env` | Authentication for Groq API |
| `MONGODB_URL` | built from parts | Connection string for MongoDB |
| `SENTIMENT_TAGS` | 3 tags | POSITIVE, NEUTRAL, NEGATIVE |
| `TOPIC_TAGS` | 14 tags | CLEANLINESS, ROOM_QUALITY, FOOD, etc. |
| `SPECIAL_TAGS` | 5 tags | PRICE_MENTIONED, ABUSIVE_CONTENT, etc. |
| `TOPICS_FOR_GENERATION` | 12 topics | Used when generating fake reviews |

**How others use it:**
```python
import config
# Every file does this to access settings like:
config.GROQ_API_KEY      # get the API key
config.LLM_MODEL          # get model name
config.SENTIMENT_TAGS     # get list of valid sentiment tags
```

---

### 3.2 `prompts.py` — AI Brain Instructions

**Purpose:** Contains the exact text instructions sent to the Groq AI, plus regex patterns for backup detection.

**What it does:**

**Part 1 — `REVIEW_GENERATION_PROMPT`:**
- Template sent to AI when GENERATING a new fake review
- Tells AI: "Write a 2-4 sentence realistic hotel review about {topic} with {rating} stars"
- Uses `.format()` to inject topic, rating, and reviewer name

**Part 2 — `REVIEW_ANALYSIS_PROMPT`:**
- Template sent to AI when ANALYZING an existing review
- Tells AI: "Read this review and return JSON with summary, sentiment, signals, tags, flags"
- The AI must return a structured JSON object with specific fields
- `signals` = boolean flags like `price_mentioned: true/false`
- `topic_tags` = what the review is about (CLEANLINESS, WIFI, etc.)
- `flags` = quality issues like "too_short", "generic"

**Part 3 — `REJECTION_REASONS_RULES`:**
- Dictionary mapping signal codes to human-readable rejection reasons
- Example: `"PRICE_MENTIONED"` → `"Price, tariff, or monetary amount mentioned"`

**Part 4 — Regex Patterns (backup detection):**
These are regular expressions that act as a SAFETY NET if the AI misses something:

| Pattern Group | What it catches | Example |
|--------------|----------------|---------|
| `PRICE_PATTERNS` | Money amounts | `₹5000`, `Rs. 3000`, `paid 6000` |
| `CONTACT_PATTERNS` | Phone/email | `9876543210`, `admin@hotel.com` |
| `OWNER_NAME_PATTERNS` | Owner names | `"owner Mr. Sharma"`, `"manager Priya"` |
| `PROFANITY_PATTERNS` | Bad language | `damn`, `bloody`, `shit` |
| `SUSPICIOUS_LINK_PATTERNS` | URLs/spam | `http://...`, `www.spam.com` |

**Why both AI + Regex?**
The AI might miss a price mention. The regex will ALWAYS catch `₹5000`. This dual approach ensures nothing slips through.

---

### 3.3 `models.py` — Data Shape Definitions

**Purpose:** Defines the EXACT structure of data going IN and coming OUT of the API using Pydantic models.

**What it does:**
Pydantic models are like "contracts" — they validate that data has the right fields and types.

**Models defined:**

| Model | Used For | Key Fields |
|-------|----------|------------|
| `ReviewInput` | Single review sent BY user | `hotel_id`, `review_text`, `rating` (1-5) |
| `ReviewAnalysisOutput` | Analysis result sent TO user | `publish_decision`, `sentiment`, `tags`, `rejection_reasons` |
| `BulkAnalysisInput` | Bulk analysis request | `hotel_id`, `input_format` (jsonl/csv), `input_path` |
| `BulkAnalysisOutput` | Bulk analysis result | `total_reviews`, `published_count`, `rejected_count` |
| `ReviewGenerationInput` | Generate request | `hotel_id`, `count` (1-5000) |
| `ReviewGenerationOutput` | Generate result | `total_generated`, `jsonl_path`, `csv_path` |
| `SummaryReportOutput` | Statistics report | `sentiment_distribution`, `tag_distribution` |

**Example — What `ReviewInput` enforces:**
```python
class ReviewInput(BaseModel):
    hotel_id: str          # MUST be a string
    review_text: str       # MUST be a string
    rating: int            # MUST be integer, between 1-5
    reviewer_name: str     # Optional
    source: str            # Optional, defaults to "internal"
```

If someone sends `rating: 7`, FastAPI automatically rejects it with a validation error because `ge=1, le=5` is specified.

---

### 3.4 `database.py` — MongoDB Connection

**Purpose:** Manages the MongoDB database connection, collection creation, and index setup.

**What it does:**

**`init_db()`** — Called once when the server starts:
1. Connects to MongoDB using the URL from config.py
2. Pings the server to verify connection works
3. Creates two collections if they don't exist:
   - `reviews_raw` — stores original/generated reviews
   - `reviews_enriched` — stores analyzed reviews with tags, sentiment, decisions
4. Creates database indexes for fast querying

**Collections explained:**

```
reviews_raw (original reviews)
├── review_id (unique index)
├── hotel_id (indexed for filtering)
├── rating
├── review_text
├── reviewer_name
├── source
└── created_at (indexed, newest first)

reviews_enriched (analyzed reviews)
├── review_id (unique index)
├── hotel_id (indexed)
├── publish_decision (indexed: "PUBLISH" or "REJECT")
├── sentiment (indexed: POSITIVE/NEUTRAL/NEGATIVE)
├── rejection_reasons []
├── tags []
├── detected_signals {}
├── summary
├── model_name
├── prompt_version
└── analyzed_at (indexed, newest first)
```

**Helper functions:**
- `get_reviews_raw_collection()` — returns the raw collection for reading/writing
- `get_reviews_enriched_collection()` — returns the enriched collection
- `close_db()` — gracefully closes connection on server shutdown

---

### 3.5 `review_generator.py` — AI Review Creator

**Purpose:** Generates realistic fake hotel reviews using Groq AI for testing the system.

**What it does:**

**`_get_client()`** — Lazy-loads the Groq API client:
- Only creates the client when first needed (not at import time)
- Validates that the API key exists

**`ReviewGenerator` class:**

**`generate_reviews(count)`** — Main loop that creates `count` reviews:
1. For each review, randomly picks: rating (weighted), topic, reviewer name, source
2. 80% of reviews → `_generate_normal_review()` (uses AI)
3. 20% of reviews → `_generate_problematic_review()` (hardcoded templates)
4. Each review gets a unique ID, random date (past year), and metadata
5. Logs progress every 50 reviews

**`_generate_normal_review()`** — Calls Groq AI:
```
Send prompt to Groq → "Write a review about {topic} with {rating} stars"
                    → Get back realistic review text
                    → Return it (or None if too short / error)
```

**`_generate_problematic_review()`** — Uses hardcoded templates:
- Creates reviews with prices: `"I paid ₹5000 per night"`
- Creates reviews with owner names: `"Owner Mr. Sharma was helpful"`
- Creates reviews with contact info: `"Call 9876543210"`
- Creates reviews with abuse: `"Damn awful place!"`
- Creates reviews with spam links: `"Visit www.myblog.com"`

These are intentionally "bad" reviews to test the analyzer's detection capabilities.

**`_weighted_random_rating()`:**
- Rating distribution: 1★=10%, 2★=10%, 3★=20%, 4★=30%, 5★=30%
- More positive reviews than negative (realistic distribution)

**`ReviewExporter` class:**
- `export_jsonl()` — Writes reviews as one JSON object per line
- `export_csv()` — Writes reviews as a CSV table using pandas

**`generate_and_export_reviews()`** — Convenience function that generates + exports in one call.

---

### 3.6 `review_analyzer.py` — The Core Analysis Engine

**Purpose:** This is the BRAIN of the system. Analyzes reviews using AI + regex + business rules to decide PUBLISH or REJECT.

**This is the most important file. Here's the 6-step analysis pipeline:**

```
Step 1: _analyze_with_llm()         → Send review to Groq AI for understanding
Step 2: _enhance_signals_with_regex() → Run regex patterns as backup detection
Step 3: _determine_sentiment()       → Finalize sentiment (cross-check with rating)
Step 4: _apply_publishing_rules()    → PUBLISH or REJECT based on signals
Step 5: _generate_tags()             → Create final tag list
Step 6: Create summary               → Use AI summary or auto-truncate
```

**Detailed step breakdown:**

**Step 1 — `_analyze_with_llm(rating, review_text)`:**
- Sends the review text to Groq AI with the analysis prompt
- AI returns a JSON object with: summary, sentiment, signals, topic_tags, flags
- Parses the JSON (handles markdown code blocks the AI might wrap it in)
- If AI fails or returns bad JSON → falls back to safe defaults

**Step 2 — `_enhance_signals_with_regex(review_text, signals)`:**
- Runs all regex patterns from prompts.py against the review text
- If regex finds a price (`₹5000`) → sets `price_mentioned = True`
- If regex finds a phone (`9876543210`) → sets `phone_email_present = True`
- This OVERRIDES the AI's opinion — if regex finds it, it's flagged regardless
- This is the safety net that makes the system reliable

**Step 3 — `_determine_sentiment(llm_sentiment, rating)`:**
- Takes the AI's sentiment opinion and cross-checks with the star rating
- If AI says NEGATIVE but rating is 4-5 stars → override to POSITIVE
- If AI says POSITIVE but rating is 1-2 stars → override to NEGATIVE
- This prevents inconsistencies between ratings and sentiment

**Step 4 — `_apply_publishing_rules(signals)`:**
- THE DECISION POINT — checks each signal against hard rejection rules:

```
price_mentioned = True      → REJECT ("Price, tariff, or monetary amount mentioned")
owner_name_mentioned = True → REJECT ("Hotel owner or manager name mentioned")
phone_email_present = True  → REJECT ("Phone number or email address present")
abusive_language = True     → REJECT ("Contains profanity or abusive language")
spam_or_links = True        → REJECT ("Contains spam, advertisements, or links")
hate_sexual_violent = True  → REJECT ("Contains hate speech, sexual, or violent content")
```

- If ANY signal is True → decision = "REJECT" + list of reasons
- If ALL signals are False → decision = "PUBLISH"

**Step 5 — `_generate_tags(signals, topic_tags, sentiment_tag)`:**
- Combines all tags into one list:
  - 1 sentiment tag (SENTIMENT_POSITIVE/NEUTRAL/NEGATIVE)
  - 0-14 topic tags (CLEANLINESS, WIFI, FOOD, etc.)
  - 0-5 special tags (PRICE_MENTIONED, ABUSIVE_CONTENT, etc.)
- Removes duplicates while preserving order

**Step 6 — Summary:**
- Uses AI-generated summary if available
- Otherwise truncates review text to 150 characters

**Error handling — `_get_safe_default_analysis()`:**
- If EVERYTHING fails (AI down, parsing error, etc.)
- Still runs regex checks (so problematic reviews still get caught)
- Returns neutral sentiment and flags `"llm_analysis_failed"`
- The system NEVER crashes — it always returns a valid result

---

### 3.7 `utils.py` — Helper Tools

**Purpose:** File import/export utilities and validation helpers.

**`DataImporter` class — Reading review files:**

| Method | What it reads | How |
|--------|--------------|-----|
| `import_jsonl(filepath)` | `.jsonl` files | Reads line by line, parses each line as JSON |
| `import_csv(filepath)` | `.csv` files | Uses pandas to read, converts rows to dicts |
| `import_json(filepath)` | `.json` files | Reads entire file as JSON array |
| `import_file(filepath, format)` | Any of above | Routes to correct method based on format |

All methods return Python **generators** (yield one review at a time) for memory efficiency with large files.

**`DataExporter` class — Writing results:**

| Method | What it writes | How |
|--------|---------------|-----|
| `export_enriched_csv()` | Analyzed reviews to CSV | Flattens nested data, joins arrays with `;` |
| `export_summary_json()` | Summary report to JSON | Simple JSON dump |

**`FileManager` class — Directory management:**
- `ensure_data_dir()` — Creates `data/` folder if it doesn't exist
- `ensure_exports_dir()` — Creates `exports/` folder if it doesn't exist
- `get_export_path(filename)` — Returns `exports/{filename}`

**`validate_review_input(review_dict)` — Input validation:**
- Checks required fields exist: `review_id`, `hotel_id`, `rating`, `review_text`
- Validates rating is numeric and between 1-5
- Validates review text is at least 5 characters
- Returns `True`/`False`

---

### 3.8 `api.py` — The Main API Server

**Purpose:** The FastAPI web application. This is what runs when you start the server. It connects everything together.

**Server setup:**
- Creates a FastAPI app with title, description, version
- Adds CORS middleware (allows any frontend to call the API)
- On startup → connects to MongoDB via `init_db()`
- On shutdown → closes MongoDB connection via `close_db()`

**6 API Endpoints:**

#### Endpoint 1: `GET /health`
- **What:** Health check — is the server running?
- **Returns:** `{"status": "healthy", "timestamp": "..."}`
- **Uses:** Nothing (standalone)

#### Endpoint 2: `POST /reviews/analyze-one`
- **What:** Analyze a SINGLE review
- **Input:** `ReviewInput` (hotel_id, review_text, rating)
- **Process:**
  1. Generates unique review ID
  2. Creates `ReviewAnalyzer` instance
  3. Calls `analyzer.analyze_review()` → gets full analysis
  4. Saves result to MongoDB `reviews_enriched` collection
  5. Returns `ReviewAnalysisOutput`
- **Uses:** `review_analyzer.py`, `database.py`, `models.py`

#### Endpoint 3: `POST /reviews/analyze-bulk`
- **What:** Analyze MANY reviews from a file
- **Input:** `BulkAnalysisInput` (hotel_id, input_format, input_path)
- **Process:**
  1. Reads reviews from file using `DataImporter`
  2. Validates each review using `validate_review_input()`
  3. Loops through all reviews, analyzing each one
  4. Saves each result to MongoDB
  5. Exports all results to CSV
  6. Returns counts and timing
- **Uses:** `review_analyzer.py`, `database.py`, `utils.py`, `models.py`

#### Endpoint 4: `POST /reviews/generate`
- **What:** Generate new AI-powered fake reviews
- **Input:** `ReviewGenerationInput` (hotel_id, count)
- **Process:**
  1. Calls `generate_and_export_reviews()`
  2. This internally uses Groq AI to create reviews
  3. Exports to JSONL and CSV
  4. Returns file paths and count
- **Uses:** `review_generator.py`, `models.py`

#### Endpoint 5: `GET /reports/summary?hotel_id=HOTEL_001`
- **What:** Get analytics/statistics for a hotel
- **Process:**
  1. Queries MongoDB for total/published/rejected counts
  2. Aggregates rejection reasons (which reasons appear most)
  3. Aggregates sentiment distribution (how many positive/negative)
  4. Aggregates tag distribution (which topics mentioned most)
  5. Returns complete statistics
- **Uses:** `database.py`, `models.py`, `config.py`

#### Endpoint 6: `GET /db/info`
- **What:** Check MongoDB status and document counts
- **Returns:** Raw count, enriched count, database details
- **Uses:** `database.py`, `config.py`

---

### 3.9 `generate_dataset.py` — Standalone Data Creator

**Purpose:** Standalone script (run from command line) to generate 500 sample reviews BEFORE starting the API.

**What it does:**
1. Creates `data/` directory
2. Creates a `ReviewGenerator` instance
3. Calls `generate_reviews(500)` — this makes 500 API calls to Groq
4. Exports results to `data/reviews_raw.jsonl` and `data/reviews_raw.csv`
5. Prints success message with next steps

**When to use:** Run this ONCE before starting the API, to have test data:
```bash
python generate_dataset.py
```

**Note:** This requires a working Groq API key and internet connection since 80% of reviews are AI-generated.

---

### 3.10 `create_sample_dataset.py` — Offline Data Creator

**Purpose:** Creates sample reviews WITHOUT using AI — purely from hardcoded templates. Works offline with no API key needed.

**What it does:**
- Has pre-written review templates organized by topic (cleanliness, room quality, food, wifi, etc.)
- Has problematic templates (prices, owner names, abuse, spam)
- Randomly combines templates with reviewer names, ratings, sources
- Creates 500 reviews and exports to JSONL + CSV

**When to use:** When you don't have a Groq API key or want to quickly generate test data:
```bash
python create_sample_dataset.py
```

---

## 4. Complete Data Flow

### Flow 1: Generating Reviews

```
User runs: python generate_dataset.py
  |
  v
generate_dataset.py
  |── Creates ReviewGenerator()
  |── Calls generate_reviews(500)
  |     |
  |     |── For each review (x500):
  |     |     |── Pick random: rating, topic, name, source
  |     |     |── 80% chance: Call Groq AI → get review text
  |     |     |── 20% chance: Use hardcoded problematic template
  |     |     |── Create review dict with ID, metadata
  |     |     └── Add to list
  |     |
  |     └── Return list of 500 reviews
  |
  |── Creates ReviewExporter()
  |── export_jsonl() → data/reviews_raw.jsonl
  |── export_csv()   → data/reviews_raw.csv
  └── Done! Files ready for analysis
```

### Flow 2: Analyzing a Single Review

```
User sends POST to /reviews/analyze-one:
{
  "hotel_id": "HOTEL_001",
  "review_text": "Room was clean but I paid ₹6500 per night",
  "rating": 3
}
  |
  v
api.py → analyze_single_review()
  |── Generate review_id: "HOTEL_001_a1b2c3d4e5f6"
  |── Create ReviewAnalyzer()
  |── Call analyze_review()
  |     |
  |     |── Step 1: Send to Groq AI
  |     |     AI returns: {
  |     |       sentiment: "SENTIMENT_NEUTRAL",
  |     |       signals: { price_mentioned: true },
  |     |       topic_tags: ["ROOM_QUALITY", "CLEANLINESS"],
  |     |       summary: "Clean room but found expensive"
  |     |     }
  |     |
  |     |── Step 2: Regex backup check
  |     |     Found "₹6500" → price_mentioned = True (confirmed)
  |     |
  |     |── Step 3: Determine sentiment
  |     |     AI said NEUTRAL + rating is 3 → SENTIMENT_NEUTRAL ✓
  |     |
  |     |── Step 4: Apply publishing rules
  |     |     price_mentioned = True → REJECT
  |     |     rejection_reason: "Price, tariff, or monetary amount mentioned"
  |     |
  |     |── Step 5: Generate tags
  |     |     ["SENTIMENT_NEUTRAL", "ROOM_QUALITY", "CLEANLINESS", "PRICE_MENTIONED"]
  |     |
  |     └── Return complete analysis dict
  |
  |── Save to MongoDB (reviews_enriched collection)
  |── Return JSON response to user:
      {
        "review_id": "HOTEL_001_a1b2c3d4e5f6",
        "publish_decision": "REJECT",
        "rejection_reasons": ["Price, tariff, or monetary amount mentioned"],
        "sentiment": "SENTIMENT_NEUTRAL",
        "tags": ["SENTIMENT_NEUTRAL", "ROOM_QUALITY", "CLEANLINESS", "PRICE_MENTIONED"]
      }
```

### Flow 3: Bulk Analysis

```
User sends POST to /reviews/analyze-bulk:
{
  "hotel_id": "HOTEL_001",
  "input_format": "jsonl",
  "input_path": "data/reviews_raw.jsonl"
}
  |
  v
api.py → analyze_bulk_reviews()
  |── DataImporter reads JSONL file (500 reviews)
  |── validate_review_input() filters invalid reviews
  |── For each valid review:
  |     |── ReviewAnalyzer.analyze_review() (same 6-step pipeline as above)
  |     |── Save to MongoDB
  |     |── Count: published++ or rejected++
  |     └── Log progress every 10 reviews
  |
  |── DataExporter.export_enriched_csv() → exports/reviews_enriched.csv
  |── Return: { total: 500, published: 390, rejected: 110, time: 45.2s }
```

---

## 5. Business Rules Explained

### Why are reviews REJECTED?

Hotels don't want certain content visible to the public:

| Rule | Why it's rejected | Example |
|------|-------------------|---------|
| **Price mentioned** | Competitors can undercut pricing; prices change seasonally | "I paid ₹6500 per night" |
| **Owner name** | Privacy concern; personal info shouldn't be public | "Owner Mr. Sharma was rude" |
| **Phone/Email** | Security risk; prevents spam/phishing | "Contact admin@hotel.com" |
| **Abusive language** | Cannot show profanity to other customers | "This damn hotel is terrible" |
| **Spam/Links** | Advertising or phishing | "Visit www.myblog.com" |
| **Hate/Sexual/Violent** | Legal liability; inappropriate content | Hate speech, threats |

### Dual Detection Strategy

```
                    Review Text
                    /          \
                   v            v
            Groq AI            Regex Patterns
         (understands          (pattern matching,
          context,              100% reliable for
          nuance)               known patterns)
                   \            /
                    v          v
                  COMBINED SIGNALS
                        |
                        v
                  FINAL DECISION
                 (PUBLISH / REJECT)
```

- **AI** catches: nuanced sentiment, context-dependent meanings, topic classification
- **Regex** catches: specific patterns like `₹5000`, phone numbers, URLs
- **Together** they are more reliable than either alone

### Tag System

Every analyzed review gets tagged with:

**1 Sentiment Tag:**
- `SENTIMENT_POSITIVE` (rating 4-5, positive words)
- `SENTIMENT_NEUTRAL` (rating 3, mixed feelings)
- `SENTIMENT_NEGATIVE` (rating 1-2, complaints)

**0-14 Topic Tags (what the review is about):**
- `CLEANLINESS`, `ROOM_QUALITY`, `BATHROOM`, `FOOD_BREAKFAST`, `RESTAURANT_FOOD`
- `SERVICE_STAFF`, `CHECKIN_CHECKOUT`, `LOCATION`, `AMENITIES`, `WIFI`
- `NOISE`, `PARKING`, `SAFETY_SECURITY`, `MAINTENANCE`

**0-5 Special Tags (flagged content):**
- `PRICE_MENTIONED`, `OWNER_MENTIONED`, `CONTACT_INFO_MENTIONED`
- `ABUSIVE_CONTENT`, `SPAM_SUSPECT`

---

## Summary

| File | Role | One-line Purpose |
|------|------|-----------------|
| `config.py` | Settings | Central configuration for AI, DB, tags |
| `prompts.py` | AI Instructions | Prompt templates + regex patterns |
| `models.py` | Data Contracts | Defines API request/response shapes |
| `database.py` | Storage | MongoDB connection, collections, indexes |
| `review_generator.py` | Data Creator | Generates fake reviews using AI |
| `review_analyzer.py` | Analysis Engine | 6-step pipeline: AI + regex + rules |
| `utils.py` | Helpers | File import/export, validation |
| `api.py` | Web Server | FastAPI with 6 endpoints |
| `generate_dataset.py` | Script | Creates 500 reviews (needs AI) |
| `create_sample_dataset.py` | Script | Creates 500 reviews (offline) |
