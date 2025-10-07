import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_database():
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DB_NAME]
        
        # Test connection
        await db.command("ping")
        logger.info("Successfully connected to MongoDB")
        
        # Create collections if they don't exist
        collections = ["users", "appointments", "medical_records", "prescriptions", 
                      "departments", "rooms", "facilities"]
        
        for collection in collections:
            if collection not in await db.list_collection_names():
                await db.create_collection(collection)
                logger.info(f"Created collection: {collection}")
            else:
                logger.info(f"Collection already exists: {collection}")
        
        # Create indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("phone", unique=True)
        logger.info("Created indexes on users collection")
        
        # Get collection statistics
        for collection in collections:
            count = await db[collection].count_documents({})
            logger.info(f"{collection} collection has {count} documents")
            
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        raise
    finally:
        client.close()
        
if __name__ == "__main__":
    asyncio.run(verify_database())