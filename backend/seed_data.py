import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid

# Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_demo_data():
    """Seed the database with demo users and sample tokens"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'hospital_token_db')]
    
    print("Seeding demo data...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.tokens.delete_many({})
    print("Cleared existing data")
    
    # Demo users
    demo_users = [
        {
            "id": str(uuid.uuid4()),
            "name": "Demo Patient",
            "email": "patient@demo.com",
            "phone": "9876543210",
            "password_hash": pwd_context.hash("demo123"),
            "role": "patient",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Demo Staff",
            "email": "staff@demo.com",
            "phone": "9876543211",
            "password_hash": pwd_context.hash("demo123"),
            "role": "staff",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Demo Admin",
            "email": "admin@demo.com",
            "phone": "9876543212",
            "password_hash": pwd_context.hash("demo123"),
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    # Insert demo users
    await db.users.insert_many(demo_users)
    print(f"Created {len(demo_users)} demo users")
    
    # Create sample tokens for testing
    patient_id = demo_users[0]["id"]
    staff_id = demo_users[1]["id"]
    
    sample_tokens = [
        {
            "id": str(uuid.uuid4()),
            "token_number": "H-001-" + datetime.now().strftime("%d%m%y"),
            "patient_id": patient_id,
            "patient_name": "Demo Patient",
            "patient_phone": "9876543210",
            "priority_level": 2,
            "category": "urgent_medical",
            "status": "active",
            "symptoms": "Severe headache and dizziness",
            "position": 1,
            "estimated_wait_time": 15,
            "created_by": patient_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "token_number": "ML-002-" + datetime.now().strftime("%d%m%y"),
            "patient_id": str(uuid.uuid4()),
            "patient_name": "John Smith",
            "patient_phone": "9876543213",
            "priority_level": 4,
            "category": "regular_consultation",
            "status": "active",
            "symptoms": "Regular checkup",
            "position": 2,
            "estimated_wait_time": 40,
            "created_by": staff_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "token_number": "R-003-" + datetime.now().strftime("%d%m%y"),
            "patient_id": str(uuid.uuid4()),
            "patient_name": "Jane Doe",
            "patient_phone": "9876543214",
            "priority_level": 5,
            "category": "report_pickup",
            "status": "active",
            "symptoms": None,
            "position": 3,
            "estimated_wait_time": 15,
            "created_by": staff_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    await db.tokens.insert_many(sample_tokens)
    print(f"Created {len(sample_tokens)} sample tokens")
    
    print("Demo data seeding completed!")
    print("\nDemo Login Credentials:")
    print("Patient: patient@demo.com / demo123")
    print("Staff: staff@demo.com / demo123")
    print("Admin: admin@demo.com / demo123")
    
    client.close()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    from pathlib import Path
    
    ROOT_DIR = Path(__file__).parent
    load_dotenv(ROOT_DIR / '.env')
    
    asyncio.run(seed_demo_data())