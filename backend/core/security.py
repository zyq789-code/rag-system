"""认证安全工具：PBKDF2 密码哈希 + JWT 签发/校验。

- 密码用 hashlib.pbkdf2_hmac（加盐，10 万次迭代），stdlib 实现，无额外依赖
- Token 用 PyJWT（HS256），有效期 7 天
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from core.config import get_settings

_TOKEN_TTL_DAYS = 7
_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """返回格式：pbkdf2_sha256$<salt>$<hexdigest>"""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt, hexdigest = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(digest.hex(), hexdigest)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=_TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> uuid.UUID | None:
    """校验并解析 token，返回 user_id；无效/过期返回 None。"""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        sub = payload.get("sub")
        if not sub:
            return None
        return uuid.UUID(sub)
    except (jwt.PyJWTError, ValueError):
        return None
