from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[Database] = None

    # Collections
    users: Optional[Collection] = None
    appointments: Optional[Collection] = None
    medical_records: Optional[Collection] = None

    @classmethod
    async def connect_to_mongo(cls, settings):
        """Connect to MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            
            # Initialize collections
            cls.users = cls.db.users
            cls.appointments = cls.db.appointments
            cls.medical_records = cls.db.medical_records
            
            # Create indexes
            await cls.create_indexes()
            
            print("✅ Connected to MongoDB successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {str(e)}")
            return False

    @classmethod
    async def close_mongo_connection(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            cls.client = None
            print("Closed MongoDB connection")

    @classmethod
    async def create_indexes(cls):
        """Create necessary indexes"""
        # Users collection indexes
        await cls.users.create_index("email", unique=True)
        await cls.users.create_index("role")
        
        # Appointments collection indexes
        await cls.appointments.create_index([("patient_id", 1), ("date", 1)])
        await cls.appointments.create_index([("doctor_id", 1), ("date", 1)])
        
        # Medical records collection indexes
        await cls.medical_records.create_index([("patient_id", 1), ("date", 1)])

mongodb = MongoDB()