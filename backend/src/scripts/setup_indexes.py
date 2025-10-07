import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings
import logging

async def setup_indexes():
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DB_NAME]
        
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("role")
        
        # Tokens collection indexes
        await db.tokens.create_index("token_number", unique=True)
        await db.tokens.create_index("patient_id")
        await db.tokens.create_index("status")
        await db.tokens.create_index("priority_level")
        await db.tokens.create_index("created_at")
        
        # Appointments collection indexes
        await db.appointments.create_index("patient_id")
        await db.appointments.create_index("doctor_id")
        await db.appointments.create_index("appointment_time")
        await db.appointments.create_index("status")
        
        # Medical records collection indexes
        await db.medical_records.create_index("patient_id")
        await db.medical_records.create_index("appointment_id")
        
        # Departments collection indexes
        await db.departments.create_index("code", unique=True)
        await db.departments.create_index("head_doctor")
        
        print("Database indexes created successfully!")

    except Exception as e:
        print(f"Error setting up indexes: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(setup_indexes())