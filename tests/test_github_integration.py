import pytest
from unittest.mock import MagicMock, patch
from src.utils.security import EncryptionService
from src.schemas.project import ProjectResponseSchema, ProjectStatusEnum
from src.services.project_service import project_service

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

def test_missing_encryption_key_raises_on_encrypt():
    """H-1: Confirm that when ENCRYPTION_KEY is missing/empty, encrypt() fails clearly."""
    with patch("src.utils.security.ENCRYPTION_KEY", ""):
        service = EncryptionService(raw_key="")
        assert service.fernet is None
        with pytest.raises(ValueError, match="ENCRYPTION_KEY is not configured"):
            service.encrypt("ghp_test_token")

def test_public_supabase_values_cannot_be_used_for_new_encryption():
    """H-1: Confirm that missing ENCRYPTION_KEY does not secretly derive a key from public values to encrypt."""
    with patch("src.utils.security.ENCRYPTION_KEY", ""):
        with patch("src.utils.security.SUPABASE_URL", "https://public.supabase.co"):
            with patch("src.utils.security.SUPABASE_KEY", "public-anon-key"):
                service = EncryptionService(raw_key="")
                with pytest.raises(ValueError, match="ENCRYPTION_KEY is not configured on the backend"):
                    service.encrypt("ghp_my_secret_pat")

def test_legacy_ciphertext_backward_compatible_decryption():
    """H-1: Confirm that existing ciphertext encrypted with the legacy seed can still be decrypted gracefully."""
    supabase_url = "https://fltjwocficpdzfuulbxc.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
    
    # Simulate legacy encryption
    import base64, hashlib
    from cryptography.fernet import Fernet
    legacy_seed = f"pr-reviewer-security-seed-{supabase_url}-{supabase_key}"
    legacy_raw = base64.urlsafe_b64encode(hashlib.sha256(legacy_seed.encode()).digest()).decode('utf-8')
    legacy_cipher = Fernet(legacy_raw.encode()).encrypt(b"ghp_existing_legacy_token").decode('utf-8')

    with patch("src.utils.security.SUPABASE_URL", supabase_url):
        with patch("src.utils.security.SUPABASE_KEY", supabase_key):
            # Service with new explicit key can still decrypt legacy ciphertext fallback
            new_service = EncryptionService(raw_key="new-explicit-production-encryption-key")
            decrypted = new_service.decrypt(legacy_cipher)
            assert decrypted == "ghp_existing_legacy_token"

def test_project_response_schema_omits_custom_token():
    """L-1: Confirm ProjectResponseSchema includes has_custom_token and does NOT expose custom_token ciphertext."""
    schema_fields = ProjectResponseSchema.model_fields
    assert "custom_token" not in schema_fields
    assert "has_custom_token" in schema_fields

    project_data = {
        "id": "proj-uuid-1",
        "user_id": "user-uuid-1",
        "project_name": "Test Project",
        "github_owner": "owner",
        "github_repository": "repo",
        "default_branch": "main",
        "auth_type": "custom_token",
        "status": ProjectStatusEnum.READY,
        "has_custom_token": True,
        # Intentionally include custom_token to verify serialization exclusion
        "custom_token": "encrypted_ciphertext_should_be_dropped",
    }
    serialized = ProjectResponseSchema(**project_data).model_dump()
    assert "custom_token" not in serialized
    assert serialized["has_custom_token"] is True

def test_project_service_sanitizes_custom_token():
    """L-1: Confirm ProjectService._format_project strips custom_token and sets has_custom_token."""
    raw_record = {
        "id": "proj-1",
        "project_name": "Demo",
        "custom_token": "gAAAAABl...",
        "webhook_secret_encrypted": "gAAAAABl...",
    }
    sanitized = project_service._format_project(raw_record, sanitize=True)
    assert "custom_token" not in sanitized
    assert "webhook_secret_encrypted" not in sanitized
    assert sanitized["has_custom_token"] is True
