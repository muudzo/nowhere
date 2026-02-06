import hmac
import hashlib
import base64
import time
from backend.config import get_settings


settings = get_settings()


def sign_device_token(device_id: str, ttl: int = 3600) -> str:
    expires = int(time.time()) + ttl
    payload = f"{device_id}:{expires}".encode()
    sig = hmac.new(settings.DEVICE_TOKEN_SECRET.encode(), payload, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(payload + b"." + sig).decode()
    return token


def verify_device_token(token: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        payload, sig = raw.split(b".")
        expected = hmac.new(settings.DEVICE_TOKEN_SECRET.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, sig):
            return False
        device_id, expires = payload.decode().split(":")
        if int(expires) < int(time.time()):
            return False
        return True
    except Exception:
        return False
