from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

from bson import ObjectId

# Convert MongoDB objects to JSON-serializable format
def serialize_mongo_document(document):
    if "_id" in document:
        document["id"] = str(document["_id"])  # Convert ObjectId to string
        del document["_id"]  # Remove MongoDB's internal field if not needed
    return document
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["Tootur"]  # Replace with your database name
users_collection = db["users"]  # Users collection
study_guide_collection = db["study_guides"]  # Study guides collection

async def close_connection():
    client.close()