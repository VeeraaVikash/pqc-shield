import hashlib
import hmac
import json
import base64
import time
import os

SECRET_KEY = os.getenv("JWT_SECRET", "pqc-shield-secret-change-in-prod-2026")
TOKEN_EXPIRE_HOURS = 24


def hash_password(password):
    salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return salt + ":" + hashed


def verify_password(password, stored):
    salt, hashed = stored.split(":")
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return hmac.compare_digest(check, hashed)


def create_token(data):
    payload = {**data, "exp": int(time.time()) + TOKEN_EXPIRE_HOURS * 3600}
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(
        hmac.new(SECRET_KEY.encode(), (header + "." + body).encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return header + "." + body + "." + sig


def decode_token(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        expected = base64.urlsafe_b64encode(
            hmac.new(SECRET_KEY.encode(), (header + "." + body).encode(), hashlib.sha256).digest()
        ).decode().rstrip("=")
        if not hmac.compare_digest(sig, expected):
            return None
        padding = 4 - len(body) % 4
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * padding))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None
