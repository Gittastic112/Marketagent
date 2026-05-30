import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException

def is_internal_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        # Block private networks, loopback, link-local, multicast, etc.
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved
    except ValueError:
        return False

def validate_safe_url(url: str) -> str:
    """
    Validates that a URL is safe to fetch (prevents SSRF).
    Raises ValueError or HTTPException if the URL points to localhost or an internal network.
    """
    if not url:
        raise ValueError("URL cannot be empty")
        
    parsed = urlparse(url)
    
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed.")
        
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a hostname")
        
    if hostname.lower() in ("localhost", "docker.internal"):
        raise ValueError("Localhost URLs are not allowed")
        
    # Check if the hostname is an IP address or resolves to an internal IP
    try:
        # socket.gethostbyname will resolve the hostname to an IP address
        # This prevents DNS rebinding to internal IPs, though a robust defense
        # would do this resolution immediately before fetching.
        # For our local-first tool, checking at ingestion setup is sufficient.
        ip = socket.gethostbyname(hostname)
        if is_internal_ip(ip):
            raise ValueError(f"URL resolves to an internal or private IP address: {ip}")
    except socket.gaierror:
        # If we can't resolve the host, we let it pass here and fail at fetch time
        pass
        
    return url

def escape_csv_formula(value: str | None) -> str:
    """
    Escapes a string to prevent CSV formula injection when opened in Excel/Google Sheets.
    If the string starts with =, +, -, @, \t, or \r, a single quote is prepended.
    """
    if value is None:
        return ""
        
    value_str = str(value)
    if not value_str:
        return value_str
        
    if value_str.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value_str}"
        
    return value_str

def get_fernet() -> "Fernet":
    from cryptography.fernet import Fernet
    from app.core.config import get_settings
    
    settings = get_settings()
    if not settings.encryption_key:
        raise ValueError("ENCRYPTION_KEY is not set in the environment")
    return Fernet(settings.encryption_key.encode())

def encrypt_token(plaintext: str) -> str:
    """Encrypts a sensitive token string."""
    if not plaintext:
        return plaintext
    fernet = get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_token(ciphertext: str) -> str:
    """Decrypts a sensitive token string."""
    if not ciphertext:
        return ciphertext
    fernet = get_fernet()
    return fernet.decrypt(ciphertext.encode()).decode()
