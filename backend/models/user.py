from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from typing import List, Dict

class StudyGuideEntry(BaseModel):
    _id: str
    title: str  # Topic of the study guide
    content: str  # Generated study guide text
    created_at: datetime  # Timestamp

class User(BaseModel):
      # MongoDB's ObjectId will be converted to a string
    name: str          # Name of the user
    email: EmailStr    # Email with validation
    role: str
    educationLevel: str
    usagePurpose: str
    study_guides: List[StudyGuideEntry] = []

