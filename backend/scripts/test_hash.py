from passlib.context import CryptContext
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure password context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__truncate_error=False
)

def test_password_hashing():
    test_passwords = [
        "Pass123!",
        "Pass456!",
        "Pass789!"
    ]
    
    logger.info("Testing password hashing...")
    for pwd in test_passwords:
        try:
            logger.info(f"Attempting to hash password: {pwd}")
            hashed = pwd_context.hash(pwd)
            logger.info(f"Successfully hashed password. Length: {len(pwd.encode('utf-8'))} bytes")
            logger.info(f"Hashed password: {hashed}")
            
            # Verify the hash
            verified = pwd_context.verify(pwd, hashed)
            logger.info(f"Password verification result: {verified}")
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}")
        logger.info("-" * 50)

if __name__ == "__main__":
    test_password_hashing()