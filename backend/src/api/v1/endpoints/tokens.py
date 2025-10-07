from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from src.db.mongodb import get_database
from src.api.v1.endpoints.users import get_current_user
import uuid

router = APIRouter()

class TokenCreate(BaseModel):
    category: str
    symptoms: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None

class Token(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token_number: str
    patient_id: str
    patient_name: str
    patient_phone: str
    priority_level: int
    category: str
    status: str = "active"
    symptoms: Optional[str] = None
    position: int
    estimated_wait_time: int
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QueuePosition(BaseModel):
    token_id: str
    token_number: str
    patient_name: str
    priority_level: int
    position: int
    estimated_wait_time: int
    status: str
    created_at: datetime

def assign_priority_by_category(category: str) -> int:
    category_priority_map = {
        "emergency": 1,
        "urgent_medical": 2,
        "serious_condition": 3,
        "regular_consultation": 4,
        "report_pickup": 5,
        "report_consultation": 6
    }
    return category_priority_map.get(category, 4)

def generate_token_number(priority: int) -> str:
    priority_prefix = {
        1: "E",  # Emergency
        2: "H",  # High
        3: "MH", # Medium High
        4: "ML", # Medium Low
        5: "R",  # Report
        6: "C"   # Consultation
    }
    
    date_str = datetime.now().strftime("%d%m%y")
    sequence = str(uuid.uuid4().int)[:3].zfill(3)
    return f"{priority_prefix[priority]}-{sequence}-{date_str}"

def calculate_wait_time(position: int, priority: int) -> int:
    base_time_per_patient = {
        1: 0,   # Emergency - Immediate
        2: 5,   # High - 5 min avg
        3: 15,  # Medium High - 15 min avg
        4: 20,  # Medium Low - 20 min avg
        5: 5,   # Report - 5 min avg
        6: 10   # Consultation - 10 min avg
    }
    return position * base_time_per_patient[priority]

@router.post("/tokens", response_model=Token)
async def create_token(
    token_data: TokenCreate, 
    current_user = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    # Determine patient info
    if current_user["role"] == "patient":
        patient_id = current_user["id"]
        patient_name = current_user["name"]
        patient_phone = current_user.get("phone", "")
    else:
        if not token_data.patient_id or not token_data.patient_name or not token_data.patient_phone:
            raise HTTPException(status_code=400, detail="Patient information required for staff token creation")
        patient_id = token_data.patient_id
        patient_name = token_data.patient_name
        patient_phone = token_data.patient_phone
    
    # Check for existing active token for patient
    existing_token = await db.tokens.find_one({
        "patient_id": patient_id,
        "status": "active"
    })
    
    if existing_token:
        raise HTTPException(status_code=400, detail="Patient already has an active token")
    
    # Assign priority based on category
    priority = assign_priority_by_category(token_data.category)
    
    # Generate token number
    token_number = generate_token_number(priority)
    
    # Calculate position in queue
    existing_tokens = await db.tokens.find({"status": "active"}).to_list(1000)
    position = 1
    
    # Find correct position based on priority (lower value = higher priority)
    for existing_token in existing_tokens:
        if priority >= existing_token["priority_level"]:
            position += 1
    
    # Update positions of lower priority tokens
    await db.tokens.update_many(
        {
            "status": "active",
            "priority_level": {"$gt": priority},
            "position": {"$gte": position}
        },
        {"$inc": {"position": 1}}
    )
    
    # Calculate estimated wait time
    estimated_wait_time = calculate_wait_time(position, priority)
    
    # Create token
    token = Token(
        token_number=token_number,
        patient_id=patient_id,
        patient_name=patient_name,
        patient_phone=patient_phone,
        priority_level=priority,
        category=token_data.category,
        symptoms=token_data.symptoms,
        position=position,
        estimated_wait_time=estimated_wait_time,
        created_by=current_user["id"]
    )
    
    await db.tokens.insert_one(token.dict())
    return token

@router.get("/tokens/{token_id}")
async def get_token(
    token_id: str, 
    current_user = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    token = await db.tokens.find_one({"id": token_id})
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Patients can only see their own tokens
    if current_user["role"] == "patient" and token["patient_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Token(**token)

@router.get("/tokens", response_model=List[Token])
async def get_user_tokens(
    current_user = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    if current_user["role"] == "patient":
        tokens = await db.tokens.find({"patient_id": current_user["id"]}).to_list(100)
    else:
        tokens = await db.tokens.find().to_list(1000)
    
    return [Token(**token) for token in tokens]

@router.get("/queue")
async def get_queue(
    current_user = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    tokens = await db.tokens.find(
        {"status": "active"}
    ).sort("position", 1).to_list(1000)
    
    queue_data = []
    for token in tokens:
        queue_data.append(QueuePosition(
            token_id=token["id"],
            token_number=token["token_number"],
            patient_name=token["patient_name"],
            priority_level=token["priority_level"],
            position=token["position"],
            estimated_wait_time=token["estimated_wait_time"],
            status=token["status"],
            created_at=token["created_at"]
        ))
    
    return {
        "queue": queue_data,
        "total_count": len(queue_data)
    }

@router.put("/tokens/{token_id}/complete")
async def complete_token(
    token_id: str, 
    current_user = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    # Only staff and admin can complete tokens
    if current_user["role"] not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Staff access required")
    
    token = await db.tokens.find_one({"id": token_id})
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Update token status
    await db.tokens.update_one(
        {"id": token_id},
        {
            "$set": {
                "status": "completed",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Update positions of remaining tokens
    await db.tokens.update_many(
        {
            "status": "active",
            "position": {"$gt": token["position"]}
        },
        {"$inc": {"position": -1}}
    )
    
    return {"message": "Token completed successfully"}

@router.put("/tokens/{token_id}/cancel")
async def cancel_token(
    token_id: str, 
    current_user = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    token = await db.tokens.find_one({"id": token_id})
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Patients can only cancel their own tokens
    if current_user["role"] == "patient" and token["patient_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update token status
    await db.tokens.update_one(
        {"id": token_id},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Update positions of remaining tokens
    await db.tokens.update_many(
        {
            "status": "active",
            "position": {"$gt": token["position"]}
        },
        {"$inc": {"position": -1}}
    )
    
    return {"message": "Token cancelled successfully"}

