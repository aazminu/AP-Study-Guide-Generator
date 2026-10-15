from typing import Optional
from bson import ObjectId  # Import to check and convert ObjectId
from fastapi import APIRouter, HTTPException, Query
from models.user import User
from db import users_collection
from datetime import datetime
from pydantic import BaseModel, Field
from db import study_guide_collection
from db import serialize_mongo_document
from models.generate_guide import generate_study_guide
router = APIRouter()

class StudyGuideRequest(BaseModel):
    # email: str
    # user_prompt: str
    # study_guide_id: str = None 
    # new_title: Optional[str] = Field(None, description="New title for renaming")
    email: str = Field(..., description="User's email")
    study_guide_id: Optional[str] = Field(None, description="ID of the study guide")
    user_prompt: Optional[str] = Field(None, description="User's input prompt")
    new_title: Optional[str] = Field(None, description="New title for renaming")

@router.post("/users")
async def create_user_endpoint(user: User):
    # Check if the user already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        return {
            "message": "User already exists",
            "user": serialize_mongo_document(existing_user),
            "exists": True  # Add a flag for frontend to handle
        }

    # If the user does not exist, create a new user entry
    user_data = user.model_dump()  # Convert Pydantic model to a dictionary
    result = await users_collection.insert_one(user_data)

    # Serialize the response
    user_data["id"] = str(result.inserted_id)
    return {
        "message": "User created successfully",
        "user": serialize_mongo_document(user_data),
        "exists": False  # Add a flag for frontend to handle
    }

@router.get("/users/check")
async def check_user_existence(email: str):
    print("Email received in /users/check:", email)  # Debugging log
    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        return {"exists": True}
    return {"exists": False}


@router.get("/get-study-guides")
async def get_study_guides(email: str):
    """Fetch all study guides including conversation history."""
    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"study_guides": user.get("study_guides", [])}


@router.post("/save-study-guide")
async def save_study_guide(email: str, study_guide: dict):
    """Save study guide under the user's account."""
    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_study_guide = {
        "_id": str(ObjectId()),  # Unique ID for the study guide
        "title": study_guide.get("title", "Untitled Study Guide"),
        "conversation": study_guide.get("conversation", []),
        "created_at": datetime.utcnow()
    }

    await users_collection.update_one(
        {"email": email},
        {"$push": {"study_guides": new_study_guide}}  # Append new study guide
    )

    return {"message": "Study guide saved successfully", "study_guide": new_study_guide}

@router.get("/get-study-guides")
async def get_study_guides(email: str):
    """Fetch all study guides for the given user, ensuring old guides have 'conversation'."""
    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert older study guides to have conversation field
    updated_study_guides = []
    for guide in user.get("study_guides", []):
        if "conversation" not in guide:
            guide["conversation"] = [
                {
                    "user_prompt": guide["title"],  # Treat the title as the original user question
                    "response": guide["content"],   # Treat the content as the AI response
                }
            ]
        updated_study_guides.append(guide)

    return {"study_guides": updated_study_guides}



class UpdateGuideRequest(BaseModel):
    email: str
    study_guide_id: str
    user_prompt: str

@router.post("/update-guide")
async def update_study_guide(request: UpdateGuideRequest):
    """Handles follow-up questions and appends responses to an existing study guide session."""
    try:
        # Extract data from the request body
        email = request.email
        study_guide_id = request.study_guide_id
        user_prompt = request.user_prompt

        # Find the study guide
        guide = await users_collection.find_one(
            {"email": email, "study_guides._id": study_guide_id}
        )

        if not guide:
            raise HTTPException(status_code=404, detail="Study guide not found")

        # Retrieve full conversation history
        conversation_history = next(
            (g["conversation"] for g in guide["study_guides"] if g["_id"] == study_guide_id),
            []
        )

        # Format conversation as context for AI
        context = "\n".join([f"User: {msg['user_prompt']}\nAI: {msg['response']}" for msg in conversation_history])
        full_prompt = f"{context}\nUser: {user_prompt}\nAI:"

        # Generate a response in context of the full conversation
        new_response = generate_study_guide(full_prompt)

        # Append new Q&A to conversation history
        await users_collection.update_one(
            {"email": email, "study_guides._id": study_guide_id},
            {"$push": {"study_guides.$.conversation": {"user_prompt": user_prompt, "response": new_response}}}
        )

        return {"message": "Follow-up response added", "response": new_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class DeleteGuideRequest(BaseModel):
    email: str
    study_guide_id: str

@router.post("/delete-study-guide")
async def delete_study_guide(request: StudyGuideRequest):
    """Deletes a study guide from a user's saved sessions."""
    try:
        email = request.email
        study_guide_id = request.study_guide_id

        # Verify if the study guide exists
        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        guide_exists = any(g["_id"] == study_guide_id for g in user.get("study_guides", []))
        if not guide_exists:
            raise HTTPException(status_code=404, detail="Study guide not found")

        # Delete the study guide
        result = await users_collection.update_one(
            {"email": email},
            {"$pull": {"study_guides": {"_id": study_guide_id}}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Failed to delete study guide")

        return {"message": "Study guide deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

class RenameGuideRequest(BaseModel):
    email: str
    study_guide_id: str
    new_title: str

@router.post("/rename-study-guide")
async def rename_study_guide(request: StudyGuideRequest):
    """Renames a study guide title."""
    try:
        print("Received Request:", request)  # ✅ Debugging step

        email = request.email
        study_guide_id = request.study_guide_id
        new_title = request.new_title

        if not study_guide_id or not new_title:
            raise HTTPException(status_code=400, detail="Study guide ID and new title are required")

        result = await users_collection.update_one(
            {"email": email, "study_guides._id": study_guide_id},
            {"$set": {"study_guides.$.title": new_title}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Study guide not found")

        return {"message": "Study guide renamed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
