"""
Generates sample dataset locally (without OpenAI API)
Use this for testing without spending API credits
For production, use generate_dataset.py with your OpenAI API key
"""
import json
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_sample_reviews(count=500):
    """Generate realistic reviews without API"""
    
    # Sample review templates organized by topic
    review_templates = {
        "cleanliness": [
            "Rooms were spotlessly clean and well-maintained throughout my stay.",
            "The cleanliness was excellent, everything was perfectly organized.",
            "I found dust under the bed and the bathroom wasn't very clean.",
            "Staff keeps the hotel very clean, impressed with the housekeeping.",
            "The room had some stains on the carpet and dirty windows.",
            "Spotless rooms and immaculate hallways, great maintenance.",
        ],
        "room_quality": [
            "Comfortable beds and spacious rooms, very luxurious.",
            "Room was small but comfortable for the price range.",
            "The bed was uncomfortable and the furniture was worn out.",
            "Beautiful room with modern decor and good lighting.",
            "Rooms are outdated and need renovation.",
            "Spacious room with excellent ventilation and views.",
        ],
        "bathroom": [
            "Bathroom was pristine with quality toiletries provided.",
            "Bathroom fixtures were old and water pressure was weak.",
            "Modern bathroom with rainfall shower and heated floors.",
            "Bathroom was cramped and had mold in the corners.",
            "Excellent bathroom amenities and premium toiletries.",
            "Bathroom was dirty and toilet wasn't working properly.",
        ],
        "food_breakfast": [
            "Breakfast buffet had amazing variety, loved the spread.",
            "Continental breakfast was basic but sufficient.",
            "Breakfast quality was poor, stale bread and cold food.",
            "Excellent breakfast with fresh fruits and local delicacies.",
            "Very limited breakfast options, disappointing.",
            "Breakfast was abundant with international and local cuisines.",
        ],
        "service_staff": [
            "Staff was incredibly helpful and responsive to all requests.",
            "Service was slow despite low occupancy, frustrating.",
            "Front desk was friendly and went above and beyond.",
            "Staff seemed disinterested and ignored our requests.",
            "Amazing service, staff attended to every need promptly.",
            "Service was below average, staff wasn't well-trained.",
        ],
        "location": [
            "Perfect location near main attractions and restaurants.",
            "Location is in a quiet area away from the city center.",
            "Excellent accessibility to tourist spots and transport.",
            "Situated in a noisy area with heavy traffic.",
            "Great location with walking distance to beaches.",
            "Remote location, difficult to reach main attractions.",
        ],
        "amenities": [
            "Pool was beautiful and well-maintained, enjoyed using it.",
            "Gym facilities were basic and outdated.",
            "World-class amenities including spa and fitness center.",
            "Limited amenities, no gym or swimming pool.",
            "Great recreational facilities for families.",
            "Amenities promised were not available during my stay.",
        ],
        "wifi": [
            "Strong WiFi throughout the hotel, perfect for work.",
            "WiFi kept disconnecting, very frustrating.",
            "Fast and reliable internet, excellent for streaming.",
            "WiFi signal was weak in the rooms.",
            "Excellent WiFi speed, no connectivity issues.",
            "WiFi password changes daily, very inconvenient.",
        ],
    }
    
    # Problematic templates (~20% of reviews)
    problematic_templates = [
        "I paid ₹{} per night which seemed expensive for the quality.",
        "Good hotel but Rs. {} seemed like a lot of money.",
        "For only {} rupees, I expected better facilities.",
        "Owner Rajesh was helpful but service was inconsistent.",
        "Spoke with manager Priya about the room issues.",
        "For complaints contact: support@hotelreviews.com or 9876543210",
        "Check my blog www.myhotelreview.blog for detailed thoughts.",
        "Damn awful place, would not recommend!",
        "This place is bloody terrible, waste of money!",
        "Horrendous stay, stay away at all costs!",
    ]
    
    reviewer_names = [
        "Rajesh Kumar", "Priya Singh", "Amit Patel", "Neha Sharma", "Vikram Rao",
        "Kavya Desai", "Arjun Menon", "Sangeeta Gupta", "Rohan Verma", "Isha Kapoor",
        "Deepak Mishra", "Anjali Nair", "Sanjay Reddy", "Pooja Kumari", "Nikhil Joshi",
        "Divya Sinha", "Rahul Chatterjee", "Sneha Dubey", "Varun Singh", "Meera Iyer",
        "John Smith", "Sarah Johnson", "Michael Brown", "Emma Davis", "Robert Wilson",
        "Lisa Anderson", "David Martinez", "Jennifer Taylor", "James Thomas", "Mary White"
    ]
    
    sources = ["google", "booking", "internal", "tripadvisor"]
    
    hotel_id = "HOTEL_001"
    reviews = []
    
    for i in range(count):
        # Decide if this should be problematic (~20%)
        is_problematic = random.random() < 0.2
        
        if is_problematic:
            # Generate problematic review
            template = random.choice(problematic_templates)
            if "{}" in template:
                amount = random.randint(2000, 8000)
                review_text = template.format(amount)
            else:
                review_text = template
            rating = random.choices([1, 2, 3, 4, 5], weights=[0.25, 0.25, 0.2, 0.15, 0.15])[0]
        else:
            # Generate normal review combining 1-3 templated statements
            num_sentences = random.randint(1, 3)
            topics = random.sample(list(review_templates.keys()), num_sentences)
            review_text = " ".join(random.choice(review_templates[topic]) for topic in topics)
            rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.1, 0.2, 0.3, 0.35])[0]
        
        review_id = f"{hotel_id}_{uuid.uuid4().hex[:12]}"
        created_at = datetime.utcnow() - timedelta(days=random.randint(1, 730))
        
        review = {
            "review_id": review_id,
            "hotel_id": hotel_id,
            "rating": rating,
            "review_text": review_text,
            "reviewer_name": random.choice(reviewer_names),
            "source": random.choice(sources),
            "created_at": created_at.isoformat()
        }
        reviews.append(review)
        
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1}/{count} reviews")
    
    return reviews

def export_reviews(reviews, jsonl_path, csv_path):
    """Export reviews to JSONL and CSV"""
    Path("data").mkdir(exist_ok=True)
    
    # Export to JSONL
    print(f"\nExporting to JSONL: {jsonl_path}")
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for review in reviews:
            f.write(json.dumps(review, ensure_ascii=False) + '\n')
    
    # Export to CSV
    print(f"Exporting to CSV: {csv_path}")
    import csv
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = reviews[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reviews)
    
    print(f"✓ Successfully created {len(reviews)} reviews!")

if __name__ == "__main__":
    print("Generating 500 sample reviews...")
    print("=" * 60)
    
    reviews = generate_sample_reviews(500)
    export_reviews(reviews, "data/reviews_raw.jsonl", "data/reviews_raw.csv")
    
    print("=" * 60)
    print("\n📊 Sample Review:")
    print(json.dumps(reviews[0], indent=2, ensure_ascii=False))
    print("\n✓ Dataset ready! You can now test with /reviews/analyze-bulk")
