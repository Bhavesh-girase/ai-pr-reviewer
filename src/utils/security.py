import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from src.config import ENCRYPTION_KEY, SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Symmetric encryption service using Fernet (AES-128-CBC with HMAC authentication).
    Ensures Personal Access Tokens (PATs) and secrets are NEVER stored in plaintext.
    Requires an explicit backend ENCRYPTION_KEY secret.
    """
    
    def __init__(self, raw_key: Optional[str] = None):
        key = raw_key if raw_key is not None else ENCRYPTION_KEY
        if key:
            # Ensure key is valid Fernet key length (32 url-safe base64 bytes)
            if len(key) != 44 or not key.endswith("="):
                hashed = hashlib.sha256(key.encode()).digest()
                key = base64.urlsafe_b64encode(hashed).decode('utf-8')
            self.fernet: Optional[Fernet] = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            self.fernet = None

    def _derive_legacy_key(self) -> Optional[str]:
        """
        Derives the legacy development key strictly for backward-compatible decryption
        of existing database records during transition.
        """
        if SUPABASE_URL and SUPABASE_KEY:
            seed = f"pr-reviewer-security-seed-{SUPABASE_URL}-{SUPABASE_KEY}"
            hashed = hashlib.sha256(seed.encode()).digest()
            return base64.urlsafe_b64encode(hashed).decode('utf-8')
        return None

    def encrypt(self, plain_text: str) -> str:
        """
        Encrypts plaintext string (e.g., PAT) and returns URL-safe base64 string.
        Requires an explicitly configured ENCRYPTION_KEY.
        """
        if not plain_text:
            raise ValueError("Cannot encrypt empty value")
        
        if self.fernet is None:
            raise ValueError("ENCRYPTION_KEY is not configured on the backend. Cannot encrypt credentials.")
            
        encrypted_bytes = self.fernet.encrypt(plain_text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypts encrypted string back to plaintext.
        Falls back to legacy key solely for existing records if primary key fails.
        """
        if not encrypted_text:
            raise ValueError("Cannot decrypt empty value")
        
        if self.fernet is not None:
            try:
                decrypted_bytes = self.fernet.decrypt(encrypted_text.encode('utf-8'))
                return decrypted_bytes.decode('utf-8')
            except (InvalidToken, Exception):
                # Backward-compatibility fallback for existing DB records
                legacy_key = self._derive_legacy_key()
                if legacy_key:
                    try:
                        legacy_fernet = Fernet(legacy_key.encode('utf-8'))
                        decrypted_bytes = legacy_fernet.decrypt(encrypted_text.encode('utf-8'))
                        return decrypted_bytes.decode('utf-8')
                    except Exception:
                        pass
                raise ValueError("Failed to decrypt ciphertext. Invalid key or corrupted data.")
        else:
            legacy_key = self._derive_legacy_key()
            if legacy_key:
                try:
                    legacy_fernet = Fernet(legacy_key.encode('utf-8'))
                    decrypted_bytes = legacy_fernet.decrypt(encrypted_text.encode('utf-8'))
                    return decrypted_bytes.decode('utf-8')
                except Exception:
                    pass
            raise ValueError("ENCRYPTION_KEY is not configured on the backend. Cannot decrypt credentials.")

    def decrypt_or_passthrough(self, value: Optional[str]) -> Optional[str]:
        """
        Attempts decryption with primary/legacy key; if the value is not valid Fernet ciphertext
        (e.g., legacy plaintext custom_token), safely returns the value as plaintext.
        """
        if not value:
            return value
        try:
            return self.decrypt(value)
        except Exception:
            # If not decryptable as ciphertext, treat as legacy plaintext
            return value

# Global singleton instance
encryption_service = EncryptionService()

import re
from typing import Any

GIT_CREDENTIAL_PATTERNS = [
    # Match https://x-access-token:<token>@github.com or https://<user>:<token>@github.com
    (re.compile(r'https?://[^\s:@]+:[^\s@]+@github\.com', re.IGNORECASE), r'https://***@github.com'),
    # Match https://<token>@github.com
    (re.compile(r'https?://[^\s@]+@github\.com', re.IGNORECASE), r'https://***@github.com'),
    # Match Authorization: Bearer <token>
    (re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]+', re.IGNORECASE), r'Bearer ***'),
    # Match GitHub Personal Access Tokens (classic, fine-grained, OAuth, etc.)
    (re.compile(r'ghp_[a-zA-Z0-9]{15,}'), r'ghp_***'),
    (re.compile(r'github_pat_[a-zA-Z0-9_]{15,}'), r'github_pat_***'),
    (re.compile(r'gho_[a-zA-Z0-9]{15,}'), r'gho_***'),
    (re.compile(r'ghu_[a-zA-Z0-9]{15,}'), r'ghu_***'),
    (re.compile(r'ghs_[a-zA-Z0-9]{15,}'), r'ghs_***'),
    (re.compile(r'ghr_[a-zA-Z0-9]{15,}'), r'ghr_***'),
]

def sanitize_error_message(error: Any) -> str:
    """
    Sanitizes exception or error strings to remove any credentials, tokens, or authorization headers.
    """
    if error is None:
        return ""
    text = str(error)
    for pattern, replacement in GIT_CREDENTIAL_PATTERNS:
        text = pattern.sub(replacement, text)
    return text
