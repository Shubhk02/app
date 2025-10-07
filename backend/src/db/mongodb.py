import logging
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def get_database():
    if not hasattr(db, 'client') or db.client is None:
        await connect_to_mongo()
    # Ensure cached database handle
    if db.db is None:
        db.db = db.client[settings.MONGODB_DB_NAME]
    return db.db

async def connect_to_mongo():
    try:
        logging.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Test the connection
        await db.client.admin.command('ping')
        # Cache the database handle
        db.db = db.client[settings.MONGODB_DB_NAME]
        # Create minimal required indexes
        try:
            await db.db.users.create_index("email", unique=True)
            await db.db.users.create_index("role")
            await db.db.tokens.create_index("token_number", unique=True)
            await db.db.tokens.create_index("patient_id")
            await db.db.tokens.create_index("status")
            await db.db.tokens.create_index("priority_level")
            await db.db.tokens.create_index("created_at")
        except Exception as ie:
            logging.warning(f"Index creation warning: {str(ie)}")
        logging.info("Successfully connected to MongoDB")
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {str(e)}")
        db.client = None
        db.db = None
        raise
    
async def close_mongo_connection():
    if db.client:
        db.client.close()
        db.client = None
        db.db = None
        logging.info("MongoDB connection closed")