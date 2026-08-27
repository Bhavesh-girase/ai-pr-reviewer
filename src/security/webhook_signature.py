import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

def verify_github_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    """
    Verifies GitHub HMAC-SHA256 signature using constant-time comparison.
    Header format: 'sha256=<hex_digest>'
    """
    if not signature_header or not secret:
        return False

    parts = signature_header.strip().split("=", 1)
    if len(parts) != 2:
        return False

    prefix, received_hash = parts[0], parts[1]
    if prefix != "sha256":
        return False

    try:
        computed_hash = hmac.new(
            secret.encode("utf-8") if isinstance(secret, str) else secret,
            raw_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_hash, computed_hash)
    except Exception as e:
        logger.error(f"Error during signature calculation: {str(e)}")
        return False
