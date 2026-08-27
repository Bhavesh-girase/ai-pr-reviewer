import pytest
from src.utils.security import EncryptionService

def test_token_encryption_and_decryption():
    service = EncryptionService(raw_key="test-secret-encryption-key-for-unit-tests")
    test_pat = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    
    # Encrypt PAT
    encrypted = service.encrypt(test_pat)
    assert encrypted != test_pat
    assert len(encrypted) > 0

    # Decrypt PAT
    decrypted = service.decrypt(encrypted)
    assert decrypted == test_pat

def test_encryption_raises_on_empty():
    service = EncryptionService(raw_key="test-secret-key")
    with pytest.raises(ValueError):
        service.encrypt("")
    with pytest.raises(ValueError):
        service.decrypt("")
