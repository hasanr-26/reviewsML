"""
LLM Prompts for review analysis - VERSIONED
"""

PROMPT_VERSION = "v1.0"

REVIEW_GENERATION_PROMPT = """Generate a realistic hotel review for a 5-star hotel called "Grand Paradise Hotel" in HOTEL_001.

Requirements:
1. The review should be 2-4 sentences
2. Include specific details (not generic)
3. The review topic should be about: {topic}
4. Rating: {rating} stars
5. Reviewer name: {reviewer_name}

Guidelines:
- Write naturally as if from a real guest
- Be specific with details (e.g., "The biryani at the restaurant was delicious" instead of "Food was good")
- Some reviews should mention problems that would NOT be published (price, owner name, phone, emails, abuse)
- Approximately 20% of reviews should be "problematic" and contain rejection-worthy content

Return ONLY the review text, no other content.
"""

REVIEW_ANALYSIS_PROMPT = """Analyze the following hotel review and extract all required information. Return a JSON object with the exact structure shown.

Review Rating: {rating}
Review Text: {review_text}

Analyze and return a JSON object with:
{{
    "summary": "1-2 line summary of the review",
    "sentiment": "SENTIMENT_POSITIVE or SENTIMENT_NEUTRAL or SENTIMENT_NEGATIVE",
    "signals": {{
        "price_mentioned": true/false (mentions price, tariff, rupees, Rs, INR, amount paid),
        "owner_name_mentioned": true/false (mentions hotel owner/manager name),
        "phone_email_present": true/false (contains phone number or email),
        "abusive_language": true/false (contains profanity, abuse, vulgar language),
        "spam_or_links": true/false (contains links, advertising, spam),
        "hate_sexual_violent": true/false (contains hate speech, sexual content, violent language),
        "too_short": true/false (less than 15 words)
    }},
    "topic_tags": ["array of relevant tags from: CLEANLINESS, ROOM_QUALITY, BATHROOM, FOOD_BREAKFAST, RESTAURANT_FOOD, SERVICE_STAFF, CHECKIN_CHECKOUT, LOCATION, AMENITIES, WIFI, NOISE, PARKING, SAFETY_SECURITY, MAINTENANCE"],
    "flags": ["array of flag strings like 'too_short', 'generic', 'inconsistent_rating' etc"]
}}

Return ONLY the JSON object, no other text.
"""

REJECTION_REASONS_RULES = {
    "PRICE_MENTIONED": "Price, tariff, or monetary amount mentioned",
    "OWNER_MENTIONED": "Hotel owner or manager name mentioned",
    "CONTACT_INFO": "Phone number or email address present",
    "ABUSIVE_LANGUAGE": "Contains profanity or abusive language",
    "SPAM_LINKS": "Contains spam, advertisements, or links",
    "HATE_SEXUAL_VIOLENT": "Contains hate speech, sexual, or violent content",
}

# Regex patterns for backup detection (when LLM fails)
PRICE_PATTERNS = [
    r'₹\s*\d+',           # ₹ 5000
    r'rs\.?\s*\d+',       # Rs. 5000
    r'inr\s*\d+',         # INR 5000
    r'paid\s*(\d+|\w+)',  # paid 5000, paid rupees
    r'cost\s*(\d+|\w+)',  # cost 1000
    r'price\s*(\d+|\w+)', # price 2000
    r'\d+\s*(?:per night|per day|per room)', # 5000 per night
]

CONTACT_PATTERNS = [
    r'\b\d{10}\b',                    # 10-digit phone
    r'\b\d{3}-\d{3}-\d{4}\b',        # 123-456-7890
    r'[\w\.-]+@[\w\.-]+\.\w+',       # email@domain.com
]

OWNER_NAME_PATTERNS = [
    r'(?:owner|manager|proprietor|boss)\s+(?:is\s+)?(\w+)',
    r'(?:spoke|talked|met)\s+(?:with\s+)?(\w+)(?:\s+the\s+(?:owner|manager))?',
]

PROFANITY_PATTERNS = [
    r'\b(?:damn|shit|bloody|crap|hell)\b',  # Add more as needed for your language/context
]

SUSPICIOUS_LINK_PATTERNS = [
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    r'www\.\S+',
]
