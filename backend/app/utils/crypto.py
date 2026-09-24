import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings

def _get_fernet() -> Fernet:
    """Derive a stable Fernet key from settings.ENCRYPTION_KEY or JWT_SECRET"""
    raw_key = settings.ENCRYPTION_KEY or settings.JWT_SECRET
    # Ensure key is valid Fernet 32-byte base64-encoded
    try:
        # Check if already a valid Fernet key
        key_bytes = raw_key.encode('utf-8')
        f = Fernet(key_bytes)
        return f
    except Exception:
        # Derive via PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"nmc_discord_salt_2026",
            iterations=100000,
        )
        derived = base64.urlsafe_b64encode(kdf.derive(raw_key.encode('utf-8')))
        return Fernet(derived)

fernet = _get_fernet()

def encrypt_token(plain_token: str) -> str:
    """Encrypt a plain text token string"""
    if not plain_token:
        return ""
    return fernet.encrypt(plain_token.encode('utf-8')).decode('utf-8')

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted token string"""
    if not encrypted_token:
        return ""
    try:
        return fernet.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""
