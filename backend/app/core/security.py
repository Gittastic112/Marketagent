import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import get_settings

def is_internal_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return not ip.is_global or ip.is_multicast
    except ValueError:
        return True

def public_url_addresses(url: str) -> tuple[str, ...]:
    """Reject ambiguous URLs and every non-public DNS answer, including IPv6.

    Validation alone is not a DNS-rebinding defense. Untrusted fetchers must
    connect to one of these addresses, retaining the original TLS server name.
    """
    if not url:
        raise ValueError("URL cannot be empty")
    if len(url) > 4000 or any(ord(char) <= 32 or ord(char) == 127 for char in url) or "\\" in url:
        raise ValueError("URL contains unsupported characters")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme. Only http and https are allowed.")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a hostname")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise ValueError("URL credentials and fragments are not allowed")
    if hostname.rstrip(".").lower() in ("localhost", "docker.internal", "host.docker.internal", "gateway.docker.internal"):
        raise ValueError("Localhost URLs are not allowed")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        literal = ipaddress.ip_address(hostname)
        addresses = (str(literal),)
    except ValueError:
        addresses = ()
    try:
        if not addresses:
            answers = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
            addresses = tuple(dict.fromkeys(answer[4][0] for answer in answers))
    except socket.gaierror:
        raise ValueError("URL hostname could not be resolved") from None
    if not addresses or any(is_internal_ip(ip) for ip in addresses):
        raise ValueError("URL resolves to an internal or private IP address")
    return addresses


def validate_safe_url(url: str) -> str:
    public_url_addresses(url)
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

    if value_str.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) or value_str.lstrip().startswith(("=", "+", "-", "@")):
        return f"'{value_str}"

    return value_str

def get_fernet() -> "Fernet":
    from cryptography.fernet import Fernet

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
