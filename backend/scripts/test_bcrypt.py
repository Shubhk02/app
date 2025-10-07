import bcrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bcrypt():
    test_passwords = [
        "Pass123!",
        "Pass456!",
        "Pass789!"
    ]
    
    logger.info("Testing bcrypt password hashing...")
    for pwd in test_passwords:
        try:
            # Convert password to bytes
            pwd_bytes = pwd.encode('utf-8')
            logger.info(f"Password length: {len(pwd_bytes)} bytes")
            
            # Generate salt and hash
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(pwd_bytes, salt)
            logger.info(f"Successfully hashed password")
            logger.info(f"Salt: {salt}")
            logger.info(f"Hash: {hashed}")
            
            # Verify
            valid = bcrypt.checkpw(pwd_bytes, hashed)
            logger.info(f"Password verification result: {valid}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
        logger.info("-" * 50)

if __name__ == "__main__":
    test_bcrypt()