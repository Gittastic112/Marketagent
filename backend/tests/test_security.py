import pytest
from app.core.security import validate_safe_url, escape_csv_formula

def test_validate_safe_url_valid():
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

def test_encrypt_decrypt_token(monkeypatch):
    from app.core.security import encrypt_token, decrypt_token
    from cryptography.fernet import Fernet
    from app.core.config import Settings
    
    test_key = Fernet.generate_key().decode()
    
    # Mock settings to return our test key
    def mock_get_settings():
        return Settings(database_url="sqlite:///:memory:", encryption_key=test_key)
        
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
        return Settings(database_url="sqlite:///:memory:", encryption_key=None)
        
    monkeypatch.setattr("app.core.security.get_settings", mock_get_settings)
    
    with pytest.raises(ValueError, match="ENCRYPTION_KEY is not set"):
        encrypt_token("test")
