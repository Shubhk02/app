import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, EmailStr
from src.core.config import settings
from src.db.mongodb import get_database

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

from typing import Literal
from pydantic import BaseModel, EmailStr, validator, Field

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: str
    role: Literal["patient", "staff", "admin"] = "patient"

    @validator('name')
    def name_must_be_valid(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v

    @validator('phone')
    def phone_must_be_valid(cls, v):
        v = v.strip()
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone number must be exactly 10 digits')
        return v

    @validator('role')
    def role_must_be_valid(cls, v):
        if v not in ["patient", "staff", "admin"]:
            raise ValueError('Role must be one of: patient, staff, admin')
        return v

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_must_be_valid(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v.encode('utf-8')) > 72:  # bcrypt limit
            raise ValueError('Password cannot be longer than 72 bytes')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login(
    credentials: LoginRequest,
    db = Depends(get_database)
):
    """
    Login endpoint that accepts JSON data
    """
    try:
        logging.info(f"Login attempt for email: {credentials.email}")
        
        # Database connection is automatically checked by the dependency

        # Find user in database
        user_collection = db["users"]
        user = await user_collection.find_one({"email": credentials.email})
        
        if not user:
            logging.warning(f"Login failed: User not found for email {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        stored_password = user.get("password_hash") or user.get("hashed_password")
        if not stored_password:
            logging.error(f"User {credentials.email} has no password hash")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid user data"
            )

        try:
            if not bcrypt.checkpw(credentials.password.encode('utf-8'), stored_password.encode('utf-8')):
                logging.warning(f"Login failed: Invalid password for email {credentials.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
        except Exception as e:
            logging.error(f"Password verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying password"
            )
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + access_token_expires
        to_encode = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "name": user.get("full_name") or user.get("name", ""),
            "role": user.get("role", "patient"),
            "exp": expire
        }
        
        access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        logging.info(f"Login successful for email: {credentials.email}")
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("full_name") or user.get("name", ""),
                "role": user.get("role", "patient")
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/register", response_model=Token)
async def register(
    user: UserCreate,
    db = Depends(get_database)
):
    """
    Register new user with validation
    """
    try:
        # Check if user already exists
        user_collection = db["users"]
        if await user_collection.find_one({"email": user.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Additional role validation
        if user.role not in ["patient", "staff", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be one of: patient, staff, admin"
            )

        # Create user with validated data
        logging.info(f"Attempting to hash password for user: {user.email}")
        try:
            # Convert password to bytes and generate salt
            password_bytes = user.password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt)
            # Convert hash to string for storage
            hashed_password = hashed_password.decode('utf-8')
            logging.info("Password hashing successful")
        except Exception as e:
            logging.error(f"Password hashing error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid password format: {str(e)}"
            )

        new_user = {
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "role": user.role,
            "password_hash": hashed_password,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        try:
            result = await user_collection.insert_one(new_user)
        except Exception as e:
            logging.error(f"Database insertion error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + access_token_expires
        to_encode = {
            "sub": str(result.inserted_id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "exp": expire
        }
        
        try:
            access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        except Exception as e:
            logging.error(f"Token generation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate access token"
            )

        logging.info(f"Successfully registered user: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(result.inserted_id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "phone": user.phone
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )