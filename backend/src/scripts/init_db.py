from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings
import asyncio

async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    # Create collections with validators
    collections = [
        "users",
        "patients",
        "medical_staff",
        "admins",
        "appointments",
        "medical_records",
        "prescriptions",
        "departments",
        "rooms",
        "inventory",
        "billing"
    ]
    
    existing_collections = await db.list_collection_names()
    
    for collection in collections:
        if collection not in existing_collections:
            await db.create_collection(collection)
            print(f"Created collection: {collection}")
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.medical_staff.create_index("license_number", unique=True)
    await db.appointments.create_index([("patient_id", 1), ("date_time", 1)])
    await db.medical_records.create_index([("patient_id", 1), ("created_at", -1)])
    await db.rooms.create_index("number", unique=True)
    await db.inventory.create_index([("name", 1), ("department_id", 1)])
    
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())