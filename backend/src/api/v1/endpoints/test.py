from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from src.db.mongodb import get_database
from src.core.config import settings

router = APIRouter()

class TestResponse(BaseModel):
    status: str
    message: str
    collections: list[str] = []

@router.get("/test", response_model=TestResponse)
async def test_database(db: AsyncIOMotorClient = Depends(get_database)):
    try:
        # List all collections
        collections = await db.list_collection_names()
        return TestResponse(
            status="success",
            message="Connected to MongoDB successfully",
            collections=collections
        )
    except Exception as e:
        return TestResponse(
            status="error",
            message=f"Database connection failed: {str(e)}",
            collections=[]
        )