import uuid

from core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hash_verify():
    h = hash_password("secret123")
    assert h != "secret123"
    assert h.startswith("pbkdf2_sha256$")
    assert verify_password("secret123", h)
    assert not verify_password("wrongpass", h)


def test_password_hash_is_salted():
    # 相同密码两次哈希结果不同（盐随机）
    assert hash_password("secret123") != hash_password("secret123")


def test_token_roundtrip():
    uid = uuid.uuid4()
    token = create_access_token(uid)
    assert decode_access_token(token) == uid


def test_token_invalid_or_expired():
    assert decode_access_token("not-a-valid-token") is None
