import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from src.config import ENCRYPTION_KEY, SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Symmetric encryption service using Fernet (AES-128-CBC with HMAC authentication).
    Ensures Personal Access Tokens (PATs) are NEVER stored in plaintext.
    """
    
    def __init__(self, raw_key: str = None):
        key = raw_key or ENCRYPTION_KEY
        if not key:
            # Fallback: Derive a deterministic Fernet key from SUPABASE_KEY + SUPABASE_URL if no ENCRYPTION_KEY provided
            seed = f"pr-reviewer-security-seed-{SUPABASE_URL}-{SUPABASE_KEY}"
            hashed = hashlib.sha256(seed.encode()).digest()
            key = base64.urlsafe_b64encode(hashed).decode('utf-8')
            logger.info("Using auto-derived security key for token encryption")
        else:
            # Ensure key is valid Fernet key length (32 url-safe base64 bytes)
            if len(key) != 44 or not key.endswith("="):
                hashed = hashlib.sha256(key.encode()).digest()
                key = base64.urlsafe_b64encode(hashed).decode('utf-8')
        
        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plain_text: str) -> str:
        """
        Encrypts plaintext string (e.g., PAT) and returns URL-safe base64 string.
        """
        if not plain_text:
            raise ValueError("Cannot encrypt empty value")
        encrypted_bytes = self.fernet.encrypt(plain_text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypts encrypted string back to plaintext.
        """
        if not encrypted_text:
            raise ValueError("Cannot decrypt empty value")
        decrypted_bytes = self.fernet.decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')

# Global singleton instance
encryption_service = EncryptionService()
