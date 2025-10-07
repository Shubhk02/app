import asyncio
import aiohttp
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/api/v1"

test_users = [
    {
        "email": "patient1@test.com",
        "name": "Test Patient",
        "phone": "1234567890",
        "password": "TestPass123",
        "role": "patient"
    },
    {
        "email": "staff1@test.com",
        "name": "Test Staff",
        "phone": "2345678901",
        "password": "StaffPass123",
        "role": "staff"
    },
    {
        "email": "admin1@test.com",
        "name": "Test Admin",
        "phone": "3456789012",
        "password": "AdminPass123",
        "role": "admin"
    }
]

invalid_test_cases = [
    {
        "case": "Invalid email",
        "data": {
            "email": "invalid-email",
            "name": "Test User",
            "phone": "1234567890",
            "password": "TestPass123",
            "role": "patient"
        }
    },
    {
        "case": "Invalid phone",
        "data": {
            "email": "test2@test.com",
            "name": "Test User",
            "phone": "123",
            "password": "TestPass123",
            "role": "patient"
        }
    },
    {
        "case": "Invalid password (too short)",
        "data": {
            "email": "test3@test.com",
            "name": "Test User",
            "phone": "1234567890",
            "password": "Tp1",
            "role": "patient"
        }
    },
    {
        "case": "Invalid role",
        "data": {
            "email": "test4@test.com",
            "name": "Test User",
            "phone": "1234567890",
            "password": "TestPass123",
            "role": "invalid"
        }
    }
]

async def test_registration(session, user_data):
    """Test user registration"""
    try:
        async with session.post(f"{API_URL}/register", json=user_data) as response:
            result = await response.json()
            status = response.status
            logger.info(f"Registration response for {user_data['email']}: Status {status}")
            logger.info(f"Response: {result}")
            return status, result
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return None, None

async def test_login(session, email, password):
    """Test user login"""
    try:
        data = {"email": email, "password": password}
        async with session.post(f"{API_URL}/login", json=data) as response:
            result = await response.json()
            status = response.status
            logger.info(f"Login response for {email}: Status {status}")
            logger.info(f"Response: {result}")
            return status, result
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return None, None

async def run_registration_tests(session):
    """Run all registration test cases"""
    logger.info("\n=== Testing Valid Registrations ===")
    successful_registrations = []
    
    for user in test_users:
        status, result = await test_registration(session, user)
        if status == 200:
            logger.info(f"✓ Successfully registered {user['role']}: {user['email']}")
            successful_registrations.append(user)
        else:
            logger.error(f"✗ Failed to register {user['role']}: {user['email']}")
    
    logger.info("\n=== Testing Invalid Registrations ===")
    for case in invalid_test_cases:
        status, result = await test_registration(session, case['data'])
        if status != 200:
            logger.info(f"✓ Successfully caught {case['case']}")
        else:
            logger.error(f"✗ Failed to catch {case['case']}")
    
    return successful_registrations

async def run_login_tests(session, registered_users):
    """Run all login test cases"""
    logger.info("\n=== Testing Valid Logins ===")
    for user in registered_users:
        status, result = await test_login(session, user['email'], user['password'])
        if status == 200:
            logger.info(f"✓ Successfully logged in {user['role']}: {user['email']}")
        else:
            logger.error(f"✗ Failed to log in {user['role']}: {user['email']}")
    
    logger.info("\n=== Testing Invalid Logins ===")
    # Test with wrong password
    if registered_users:
        user = registered_users[0]
        status, result = await test_login(session, user['email'], 'WrongPass123!')
        if status != 200:
            logger.info("✓ Successfully caught login with wrong password")
        else:
            logger.error("✗ Failed to catch login with wrong password")
    
    # Test with non-existent user
    status, result = await test_login(session, 'nonexistent@test.com', 'TestPass123')
    if status != 200:
        logger.info("✓ Successfully caught login with non-existent user")
    else:
        logger.error("✗ Failed to catch login with non-existent user")

async def main():
    """Main test runner"""
    logger.info("Starting authentication system tests...")
    
    async with aiohttp.ClientSession() as session:
        # Run registration tests
        registered_users = await run_registration_tests(session)
        
        # Run login tests
        await run_login_tests(session, registered_users)
        
    logger.info("\nTest suite completed.")

if __name__ == "__main__":
    asyncio.run(main())
