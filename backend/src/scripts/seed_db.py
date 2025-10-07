import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.config import settings

async def seed_database():
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DB_NAME]
        
        # Clear existing users and re-seed
        await db.users.delete_many({})
        print("Cleared existing users")

        # Create demo users
        demo_users = [
            {
                "email": "patient@demo.com",
                "name": "Demo Patient",
                "password_hash": bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "phone": "1234567890",
                "role": "patient",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "email": "staff@demo.com",
                "name": "Demo Staff",
                "password_hash": bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "phone": "1234567891",
                "role": "staff",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "email": "admin@demo.com",
                "name": "Demo Admin",
                "password_hash": bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "phone": "1234567892",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ]

        # Insert demo users
        await db.users.insert_many(demo_users)
        print("Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())