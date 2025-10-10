from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from enum import IntEnum, Enum
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'hospital_management')]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "hospital-token-management-secret-key-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Create the main app
app = FastAPI(title="Hospital Token Management System", version="1.0.0")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: api_router will be defined later in the file

# Add health check endpoint at root level
@app.get("/health")
async def health_check():
    """
    Health check endpoint for the application.
    Returns basic health information including:
    - Status
    - Timestamp
    - MongoDB connection status
    """
    try:
        await db.command("ping")
        mongo_status = "healthy"
    except Exception as e:
        mongo_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": {
            "mongodb": mongo_status
        }
    }

# Create a router without extra prefix (mounted at /api/v1 below)
api_router = APIRouter()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            'patient': [],
            'staff': [],
            'admin': []
        }
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, user_role: str):
        await websocket.accept()
        self.user_connections[user_id] = websocket
        self.active_connections[user_role].append(websocket)
        logging.info(f"User {user_id} ({user_role}) connected. Total connections: {len(self.user_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: str, user_role: str):
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        if websocket in self.active_connections[user_role]:
            self.active_connections[user_role].remove(websocket)
        logging.info(f"User {user_id} ({user_role}) disconnected. Total connections: {len(self.user_connections)}")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(message)
            except Exception as e:
                logging.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast_to_role(self, message: str, role: str):
        if role in self.active_connections:
            disconnected = []
            for connection in self.active_connections[role]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logging.error(f"Error broadcasting to {role}: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                if connection in self.active_connections[role]:
                    self.active_connections[role].remove(connection)

    async def send_queue_update(self, queue_data: List[Dict[str, Any]]):
        """Send queue update to all staff and admin users"""
        message = json.dumps({
            "type": "queue_update",
            "data": queue_data
        })
        await self.broadcast_to_role(message, "staff")
        await self.broadcast_to_role(message, "admin")

    async def send_token_update(self, token_data: Dict[str, Any], user_id: str = None):
        """Send token update to specific user or all relevant users"""
        message = json.dumps({
            "type": "token_update",
            "data": token_data
        })
        
        if user_id:
            await self.send_personal_message(message, user_id)
        
        await self.broadcast_to_role(message, "staff")
        await self.broadcast_to_role(message, "admin")

# Global connection manager
manager = ConnectionManager()

# Enums
class UserRole(str, Enum):
    PATIENT = "patient"
    STAFF = "staff"
    ADMIN = "admin"

class TokenPriority(IntEnum):
    CRITICAL = 1      # Emergency - Immediate attention
    HIGH = 2          # Urgent medical - <15 mins
    MEDIUM_HIGH = 3   # Serious condition - <45 mins
    MEDIUM_LOW = 4    # Regular consultation - <2 hours
    REPORT_PICKUP = 5 # Document collection - <30 mins
    CONSULTATION = 6  # Report discussion - <1 hour

class TokenStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    phone: str
    name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    phone: str
    name: str
    password: str
    role: UserRole = UserRole.PATIENT

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token_number: str
    patient_id: str
    patient_name: str
    patient_phone: str
    priority_level: TokenPriority
    category: str
    status: TokenStatus = TokenStatus.ACTIVE
    symptoms: Optional[str] = None
    position: int
    estimated_wait_time: int  # in minutes
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenCreate(BaseModel):
    category: str
    symptoms: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None

class QueuePosition(BaseModel):
    token_id: str
    token_number: str
    patient_name: str
    priority_level: int
    position: int
    estimated_wait_time: int
    status: str
    created_at: datetime

# Utility Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Some existing users may have empty/invalid hashes; guard to avoid 500
    if not hashed_password or not isinstance(hashed_password, str):
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # UnknownHashError or backend issues should not 500 the request
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_token_number(priority: TokenPriority) -> str:
    priority_prefix = {
        TokenPriority.CRITICAL: "E",
        TokenPriority.HIGH: "H", 
        TokenPriority.MEDIUM_HIGH: "MH",
        TokenPriority.MEDIUM_LOW: "ML",
        TokenPriority.REPORT_PICKUP: "R",
        TokenPriority.CONSULTATION: "C"
    }
    
    date_str = datetime.now().strftime("%d%m%y")
    sequence = str(uuid.uuid4().int)[:3].zfill(3)
    return f"{priority_prefix[priority]}-{sequence}-{date_str}"

def assign_priority_by_category(category: str) -> TokenPriority:
    category_priority_map = {
        "emergency": TokenPriority.CRITICAL,
        "urgent_medical": TokenPriority.HIGH,
        "serious_condition": TokenPriority.MEDIUM_HIGH,
        "regular_consultation": TokenPriority.MEDIUM_LOW,
        "report_pickup": TokenPriority.REPORT_PICKUP,
        "report_consultation": TokenPriority.CONSULTATION
    }
    return category_priority_map.get(category, TokenPriority.MEDIUM_LOW)

def calculate_wait_time(position: int, priority: TokenPriority) -> int:
    base_time_per_patient = {
        TokenPriority.CRITICAL: 0,     # Immediate
        TokenPriority.HIGH: 5,         # 5 min avg
        TokenPriority.MEDIUM_HIGH: 15, # 15 min avg
        TokenPriority.MEDIUM_LOW: 20,  # 20 min avg
        TokenPriority.REPORT_PICKUP: 5, # 5 min avg
        TokenPriority.CONSULTATION: 10  # 10 min avg
    }
    return position * base_time_per_patient[priority]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

async def get_current_staff(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.STAFF, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user

async def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Authentication Routes
@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop("password")
    user_dict["password_hash"] = hashed_password
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "phone": current_user.phone
        }
    }

@api_router.post("/auth/login")
async def login_user(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is deactivated")
    
    access_token = create_access_token(data={"sub": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "phone": user.get("phone", "")
        }
    }

# Token Routes
@api_router.post("/tokens", response_model=Token)
async def create_token(token_data: TokenCreate, current_user: User = Depends(get_current_user)):
    # Determine patient info
    if current_user.role == UserRole.PATIENT:
        patient_id = current_user.id
        patient_name = current_user.name
        patient_phone = current_user.phone
    else:
        if not token_data.patient_id or not token_data.patient_name or not token_data.patient_phone:
            raise HTTPException(status_code=400, detail="Patient information required for staff token creation")
        patient_id = token_data.patient_id
        patient_name = token_data.patient_name
        patient_phone = token_data.patient_phone
    
    # Check for existing active token for patient
    existing_token = await db.tokens.find_one({
        "patient_id": patient_id,
        "status": TokenStatus.ACTIVE
    })
    
    if existing_token:
        raise HTTPException(status_code=400, detail="Patient already has an active token")
    
    # Assign priority based on category
    priority = assign_priority_by_category(token_data.category)
    
    # Generate token number
    token_number = generate_token_number(priority)
    
    # Calculate position in queue
    existing_tokens = await db.tokens.find({"status": TokenStatus.ACTIVE}).to_list(1000)
    position = 1
    
    # Find correct position based on priority (lower value = higher priority)
    for existing_token in existing_tokens:
        if priority >= existing_token["priority_level"]:
            position += 1
    
    # Update positions of lower priority tokens
    await db.tokens.update_many(
        {
            "status": TokenStatus.ACTIVE,
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
        created_by=current_user.id
    )
    
    await db.tokens.insert_one(token.dict())
    
    # Send real-time update to all connected users
    await manager.send_token_update(token.dict(), current_user.id)
    
    # Send queue update to staff/admin
    queue_tokens = await db.tokens.find({"status": TokenStatus.ACTIVE}).sort("position", 1).to_list(1000)
    queue_data = []
    for t in queue_tokens:
        queue_data.append({
            "token_id": t["id"],
            "token_number": t["token_number"],
            "patient_name": t["patient_name"],
            "priority_level": t["priority_level"],
            "position": t["position"],
            "estimated_wait_time": t["estimated_wait_time"],
            "status": t["status"],
            "created_at": t["created_at"]
        })
    await manager.send_queue_update(queue_data)
    
    return token

@api_router.get("/tokens/{token_id}")
async def get_token(token_id: str, current_user: User = Depends(get_current_user)):
    token = await db.tokens.find_one({"id": token_id})
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Patients can only see their own tokens
    if current_user.role == UserRole.PATIENT and token["patient_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Token(**token)

@api_router.get("/tokens", response_model=List[Token])
async def get_user_tokens(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.PATIENT:
        tokens = await db.tokens.find({"patient_id": current_user.id}).to_list(100)
    else:
        tokens = await db.tokens.find().to_list(1000)
    
    return [Token(**token) for token in tokens]

# Queue Routes
@api_router.get("/queue")
async def get_queue(current_user: User = Depends(get_current_user)):
    tokens = await db.tokens.find(
        {"status": TokenStatus.ACTIVE}
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

@api_router.put("/tokens/{token_id}/complete")
async def complete_token(token_id: str, current_user: User = Depends(get_current_staff)):
    token = await db.tokens.find_one({"id": token_id})
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Update token status
    await db.tokens.update_one(
        {"id": token_id},
        {
            "$set": {
                "status": TokenStatus.COMPLETED,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Update positions of remaining tokens
    await db.tokens.update_many(
        {
            "status": TokenStatus.ACTIVE,
            "position": {"$gt": token["position"]}
        },
        {"$inc": {"position": -1}}
    )
    
    # Send real-time update
    await manager.send_token_update({"id": token_id, "status": "completed"}, token["patient_id"])
    
    # Send updated queue to staff/admin
    queue_tokens = await db.tokens.find({"status": TokenStatus.ACTIVE}).sort("position", 1).to_list(1000)
    queue_data = []
    for t in queue_tokens:
        queue_data.append({
            "token_id": t["id"],
            "token_number": t["token_number"],
            "patient_name": t["patient_name"],
            "priority_level": t["priority_level"],
            "position": t["position"],
            "estimated_wait_time": t["estimated_wait_time"],
            "status": t["status"],
            "created_at": t["created_at"]
        })
    await manager.send_queue_update(queue_data)
    
    return {"message": "Token completed successfully"}

@api_router.put("/tokens/{token_id}/cancel")
async def cancel_token(token_id: str, current_user: User = Depends(get_current_user)):
    token = await db.tokens.find_one({"id": token_id})
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Patients can only cancel their own tokens
    if current_user.role == UserRole.PATIENT and token["patient_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update token status
    await db.tokens.update_one(
        {"id": token_id},
        {
            "$set": {
                "status": TokenStatus.CANCELLED,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Update positions of remaining tokens
    await db.tokens.update_many(
        {
            "status": TokenStatus.ACTIVE,
            "position": {"$gt": token["position"]}
        },
        {"$inc": {"position": -1}}
    )
    
    return {"message": "Token cancelled successfully"}

@api_router.put("/tokens/{token_id}/priority")
async def update_token_priority(
    token_id: str, 
    new_priority: int, 
    current_user: User = Depends(get_current_staff)
):
    if new_priority not in [p.value for p in TokenPriority]:
        raise HTTPException(status_code=400, detail="Invalid priority level")
    
    token = await db.tokens.find_one({"id": token_id})
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    old_priority = token["priority_level"]
    old_position = token["position"]
    
    if old_priority == new_priority:
        return {"message": "Priority unchanged"}
    
    # Remove from current position
    await db.tokens.update_many(
        {
            "status": TokenStatus.ACTIVE,
            "position": {"$gt": old_position}
        },
        {"$inc": {"position": -1}}
    )
    
    # Find new position based on new priority
    existing_tokens = await db.tokens.find({
        "status": TokenStatus.ACTIVE,
        "id": {"$ne": token_id}
    }).to_list(1000)
    
    new_position = 1
    for existing_token in existing_tokens:
        if new_priority >= existing_token["priority_level"]:
            new_position += 1
    
    # Update positions of tokens that will be after this one
    await db.tokens.update_many(
        {
            "status": TokenStatus.ACTIVE,
            "position": {"$gte": new_position},
            "id": {"$ne": token_id}
        },
        {"$inc": {"position": 1}}
    )
    
    # Update the token
    estimated_wait_time = calculate_wait_time(new_position, TokenPriority(new_priority))
    
    await db.tokens.update_one(
        {"id": token_id},
        {
            "$set": {
                "priority_level": new_priority,
                "position": new_position,
                "estimated_wait_time": estimated_wait_time,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Token priority updated successfully"}

# User Management Routes (Admin only)
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_admin)):
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.post("/users/create-staff")
async def create_staff_user(user_data: UserCreate, current_user: User = Depends(get_current_admin)):
    if user_data.role not in [UserRole.STAFF, UserRole.ADMIN]:
        raise HTTPException(status_code=400, detail="Can only create staff or admin users")
    
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop("password")
    user_dict["password_hash"] = hashed_password
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    return {"message": "Staff user created successfully", "user_id": user.id}

# Analytics Routes
@api_router.get("/analytics/dashboard")
async def get_dashboard_analytics(current_user: User = Depends(get_current_staff)):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_tokens_today = await db.tokens.count_documents({
        "created_at": {"$gte": today_start}
    })
    
    active_tokens = await db.tokens.count_documents({
        "status": TokenStatus.ACTIVE
    })
    
    completed_tokens_today = await db.tokens.count_documents({
        "status": TokenStatus.COMPLETED,
        "updated_at": {"$gte": today_start}
    })
    
    # Calculate average wait time
    tokens_with_wait = await db.tokens.find({
        "status": TokenStatus.COMPLETED,
        "updated_at": {"$gte": today_start}
    }).to_list(1000)
    
    avg_wait_time = 0
    if tokens_with_wait:
        total_wait = sum(token["estimated_wait_time"] for token in tokens_with_wait)
        avg_wait_time = total_wait / len(tokens_with_wait)
    
    # Priority distribution
    priority_distribution = {}
    for priority in TokenPriority:
        count = await db.tokens.count_documents({
            "priority_level": priority.value,
            "created_at": {"$gte": today_start}
        })
        priority_distribution[priority.name] = count
    
    return {
        "total_tokens_today": total_tokens_today,
        "active_tokens": active_tokens,
        "completed_tokens_today": completed_tokens_today,
        "average_wait_time": round(avg_wait_time, 2),
        "priority_distribution": priority_distribution
    }

# Include the router in the main app
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}/{user_role}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, user_role: str):
    await manager.connect(websocket, user_id, user_role)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for connection testing
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, user_role)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()