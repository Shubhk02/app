from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
from jose import JWTError, jwt
from src.core.config import settings
from src.db.mongodb import get_database
from bson import ObjectId

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncIOMotorClient = Depends(get_database)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
        
    user["id"] = str(user["_id"])
    del user["_id"]
    if "hashed_password" in user:
        del user["hashed_password"]
    if "password_hash" in user:
        del user["password_hash"]
    return user

@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user