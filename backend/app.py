from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from models.rag_handler import RAGHandler
from routes.user_routes import router as user_router
from db import close_connection
from datetime import datetime
from bson import ObjectId
from db import users_collection

# Initialize RAG handler
rag_handler = RAGHandler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions (if needed)
    yield
    # Shutdown actions
    await close_connection()
    rag_handler.close()

# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origin instead of "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list allowed methods
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Input model
class Prompt(BaseModel):
    user_prompt: str


# Include user routes
app.include_router(user_router, prefix="/api")

@app.on_event("shutdown")
async def shutdown():
    await close_connection()

@app.get("/")
async def root():
    return {"message": "Welcome to TooturAI Backend"}

class StudyGuideRequest(BaseModel):
    email: str  # Ensure email is required
    user_prompt: str
    study_guide_id: str = None  # Optional for follow-ups


@app.post("/generate-guide")
async def generate_guide(request: StudyGuideRequest):
    try:
        # Extract data from the request body
        email = request.email
        user_prompt = request.user_prompt
        study_guide_id = request.study_guide_id

        # Validate email
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Generate AI response using RAG
        new_response = rag_handler.generate_response_with_context(user_prompt)

        # If modifying an existing study guide, append to it
        if study_guide_id:
            guide = await users_collection.find_one(
                {"email": email, "study_guides._id": study_guide_id}
            )

            if not guide:
                raise HTTPException(status_code=404, detail="Study guide not found")

            # Append conversation history
            await users_collection.update_one(
                {"email": email, "study_guides._id": study_guide_id},
                {"$push": {"study_guides.$.conversation": {"user_prompt": user_prompt, "response": new_response}}}
            )

            return {"message": "Response added to existing study guide", "response": new_response}

        # Create a new study guide session
        new_study_guide = {
            "_id": str(ObjectId()),  
            "title": user_prompt[:50],  # Use first few words as title
            "conversation": [{"user_prompt": user_prompt, "response": new_response}],
            "created_at": datetime.utcnow()
        }

        # Store new study guide in database
        await users_collection.update_one(
            {"email": email},
            {"$push": {"study_guides": new_study_guide}},
            upsert=True
        )

        return {"message": "New study guide created", "study_guide": new_study_guide}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-rag")
async def test_rag(prompt: Prompt):
    """Test endpoint to verify RAG functionality with detailed logging"""
    try:
        print("\n=== Testing RAG System ===")
        print(f"Received prompt: {prompt.user_prompt}")
        
        # Test database connection
        chunks_count = await users_collection.count_documents({})
        print(f"\nDatabase connection test:")
        print(f"Found {chunks_count} documents in users collection")
        
        # Get RAG response with all the logging we added
        response = rag_handler.generate_response_with_context(prompt.user_prompt)
        
        return {
            "status": "success",
            "prompt": prompt.user_prompt,
            "response": response,
            "message": "Check server logs for detailed RAG process information"
        }
    except Exception as e:
        print(f"Error in test-rag endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))