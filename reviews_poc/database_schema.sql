-- MongoDB Setup Instructions for Reviews POC

-- MongoDB doesn't require a schema definition like SQL
-- Collections and indexes are created automatically by the application
-- However, here are the expected collection structures:

/*
1. reviews_raw Collection
   Structure:
   {
     "_id": ObjectId,
     "review_id": String (unique),
     "hotel_id": String (indexed),
     "rating": Int (1-5),
     "review_text": String,
     "reviewer_name": String,
     "source": String,
     "created_at": ISODate
   }

2. reviews_enriched Collection
   Structure:
   {
     "_id": ObjectId,
     "review_id": String (unique, indexed),
     "hotel_id": String (indexed),
     "rating": Int (1-5),
     "review_text": String,
     "publish_decision": String (indexed, values: "PUBLISH" or "REJECT"),
     "rejection_reasons": [String],
     "flags": [String],
     "summary": String,
     "tags": [String],
     "sentiment": String (indexed),
     "detected_signals": {
       "price_mentioned": Boolean,
       "owner_name_mentioned": Boolean,
       "phone_email_present": Boolean,
       "abusive_language": Boolean,
       "spam_or_links": Boolean,
       "hate_sexual_violent": Boolean,
       "too_short": Boolean
     },
     "analyzed_at": ISODate (indexed),
     "model_name": String,
     "prompt_version": String
   }
*/

-- SETUP INSTRUCTIONS:

-- 1. Install MongoDB Community Edition from: https://www.mongodb.com/try/download/community

-- 2. Start MongoDB Server:
--    On Windows: 
--    mongod
--    
--    On Mac: 
--    brew services start mongodb-community
--    
--    On Linux:
--    sudo systemctl start mongod

-- 3. Verify MongoDB is running (in another terminal):
--    mongosh
--    Or: mongo

-- 4. The application will automatically:
--    - Create the database (reviews_poc)
--    - Create the collections (reviews_raw, reviews_enriched)
--    - Create the necessary indexes

-- 5. Optional: Verify collections in MongoDB shell:
/*
use reviews_poc
show collections
db.reviews_raw.getIndexes()
db.reviews_enriched.getIndexes()
db.reviews_raw.countDocuments()
db.reviews_enriched.countDocuments()
*/

-- 6. Optional: Create MongoDB user with credentials (for production)
/*
use admin
db.createUser({
  user: "reviews_app",
  pwd: "secure_password_here",
  roles: [
    { role: "dbOwner", db: "reviews_poc" }
  ]
})

-- Then update .env with:
DB_USER=reviews_app
DB_PASSWORD=secure_password_here
MONGODB_URL=mongodb://reviews_app:secure_password_here@localhost:27017/reviews_poc?retryWrites=true
*/
