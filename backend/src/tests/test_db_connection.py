import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

async def test_connection():
    """Test MongoDB Atlas connection"""
    print("🔄 Testing MongoDB Atlas connection...")
    
    # Load environment variables
    load_dotenv()
    
    # Get MongoDB connection string
    mongodb_url = os.getenv("MONGODB_URL")
    mongodb_db = os.getenv("MONGODB_DB_NAME", "hospital_management")
    
    if not mongodb_url:
        print("❌ Error: MONGODB_URL not found in environment variables")
        return False
    
    try:
        # Create client
        client = AsyncIOMotorClient(mongodb_url)
        db = client[mongodb_db]
        
        # Test connection with a simple command
        await db.command("ping")
        
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # List all collections
        collections = await db.list_collection_names()
        if collections:
            print("\nExisting collections:")
            for collection in collections:
                count = await db[collection].count_documents({})
                print(f"📁 {collection}: {count} documents")
        else:
            print("\nNo collections found - database is empty")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())