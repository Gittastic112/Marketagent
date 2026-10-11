import base64
import hashlib
import hmac
import json
import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from app.core.security import validate_safe_url, escape_csv_formula

def test_validate_safe_url_valid(monkeypatch):
    monkeypatch.setattr("socket.getaddrinfo", lambda *_a, **_k: [(2, 1, 6, "", ("93.184.216.34", 443))])
    assert validate_safe_url("https://example.com/feed.xml") == "https://example.com/feed.xml"
    assert validate_safe_url("http://google.com") == "http://google.com"

def test_validate_safe_url_invalid_scheme():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_safe_url("ftp://example.com")
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_safe_url("file:///etc/passwd")
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_safe_url("javascript:alert(1)")

def test_validate_safe_url_localhost():
    with pytest.raises(ValueError, match="Localhost URLs are not allowed"):
        validate_safe_url("http://localhost:8000")
    with pytest.raises(ValueError, match="Localhost URLs are not allowed"):
        validate_safe_url("http://docker.internal/api")

def test_validate_safe_url_internal_ip():
    # 127.0.0.1 is loopback
    with pytest.raises(ValueError, match="internal or private IP"):
        validate_safe_url("http://127.0.0.1/")
    # 10.0.0.1 is private
    with pytest.raises(ValueError, match="internal or private IP"):
        validate_safe_url("http://10.0.0.1/")
    # 192.168.1.1 is private
    with pytest.raises(ValueError, match="internal or private IP"):
        validate_safe_url("http://192.168.1.1/")

def test_escape_csv_formula():
    assert escape_csv_formula("Normal Text") == "Normal Text"
    assert escape_csv_formula("123") == "123"
    assert escape_csv_formula(None) == ""
    assert escape_csv_formula("") == ""

    # Injection vectors
    assert escape_csv_formula("=CMD()") == "'=CMD()"
    assert escape_csv_formula("+A1") == "'+A1"
    assert escape_csv_formula("-A1") == "'-A1"
    assert escape_csv_formula("@SUM()") == "'@SUM()"
    assert escape_csv_formula("\tTabbed") == "'\tTabbed"
    assert escape_csv_formula("\rNewline") == "'\rNewline"
    assert escape_csv_formula("\n=1+1") == "'\n=1+1"
    assert escape_csv_formula("  =1+1") == "'  =1+1"

def test_encrypt_decrypt_token(monkeypatch):
    from app.core.security import encrypt_token, decrypt_token
    from cryptography.fernet import Fernet
    from app.core.config import Settings

    test_key = Fernet.generate_key().decode()

    # Mock settings to return our test key
    def mock_get_settings():
        return Settings(
            database_url="sqlite:///:memory:",
            encryption_key=test_key,
            sec_user_agent="Test App test@example.com",
        )

    monkeypatch.setattr("app.core.security.get_settings", mock_get_settings)

    token = "secret_broker_oauth_token_123"
    encrypted = encrypt_token(token)

    assert encrypted != token
    assert isinstance(encrypted, str)

    decrypted = decrypt_token(encrypted)
    assert decrypted == token

def test_encrypt_decrypt_token_missing_key(monkeypatch):
    from app.core.security import encrypt_token
    from app.core.config import Settings

    def mock_get_settings():
        return Settings(
            database_url="sqlite:///:memory:",
            encryption_key=None,
            sec_user_agent="Test App test@example.com",
        )

    monkeypatch.setattr("app.core.security.get_settings", mock_get_settings)

    with pytest.raises(ValueError, match="ENCRYPTION_KEY is not set"):
        encrypt_token("test")


def _signed_identity_headers(
    *,
    secret: str,
    user_id: str = "local-user",
    email: str = "local@example.com",
    name: str = "Local User",
    issued_at: int | None = None,
) -> list[tuple[bytes, bytes]]:
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "iat": issued_at if issued_at is not None else int(time.time()),
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return [
        (b"x-market-intel-user", encoded.encode("ascii")),
        (b"x-market-intel-signature", signature.encode("ascii")),
    ]


def test_current_user_validates_signed_identity_and_provisions_user(db, monkeypatch):
    from app.api import dependencies
    from app.models.user import User

    secret = "test-nextauth-secret"
    original_commit = db.commit
    commit_count = 0

    def tracked_commit():
        nonlocal commit_count
        commit_count += 1
        return original_commit()

    monkeypatch.setattr(db, "commit", tracked_commit)
    monkeypatch.setattr(dependencies, "get_settings", lambda: SimpleNamespace(nextauth_secret=secret))
    request = Request(
        {
            "type": "http",
            "headers": _signed_identity_headers(secret=secret),
        }
    )

    import asyncio

    user = asyncio.run(dependencies.get_current_user(request, None, db))

    assert user["id"] == "local-user"
    assert db.get(User, "local-user").email == "local@example.com"
    assert commit_count == 1


def test_current_user_rejects_requests_without_signed_identity(db, monkeypatch):
    from app.api import dependencies
    from app.api.dependencies import get_current_user

    monkeypatch.setattr(
        dependencies,
        "get_settings",
        lambda: SimpleNamespace(nextauth_secret="test-nextauth-secret"),
    )
    request = Request({"type": "http", "headers": []})

    import asyncio

    with pytest.raises(HTTPException, match="Not authenticated") as error:
        asyncio.run(get_current_user(request, None, db))
    assert error.value.status_code == 401


def test_current_user_rejects_tampered_identity(db, monkeypatch):
    from app.api import dependencies

    secret = "test-nextauth-secret"
    monkeypatch.setattr(dependencies, "get_settings", lambda: SimpleNamespace(nextauth_secret=secret))
    headers = _signed_identity_headers(secret=secret)
    headers[0] = (headers[0][0], headers[0][1] + b"tampered")
    request = Request({"type": "http", "headers": headers})

    import asyncio

    with pytest.raises(HTTPException, match="Not authenticated") as error:
        asyncio.run(dependencies.get_current_user(request, None, db))
    assert error.value.status_code == 401


def test_current_user_rejects_expired_identity(db, monkeypatch):
    from app.api import dependencies

    secret = "test-nextauth-secret"
    monkeypatch.setattr(dependencies, "get_settings", lambda: SimpleNamespace(nextauth_secret=secret))
    request = Request(
        {
            "type": "http",
            "headers": _signed_identity_headers(
                secret=secret,
                issued_at=int(time.time()) - dependencies.INTERNAL_AUTH_MAX_AGE_SECONDS - 1,
            ),
        }
    )

    import asyncio

    with pytest.raises(HTTPException, match="Not authenticated") as error:
        asyncio.run(dependencies.get_current_user(request, None, db))
    assert error.value.status_code == 401
