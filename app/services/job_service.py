import ipaddress
import socket
import logging
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from app.domain.models.job import Job
from app.domain.models.user import User

logger = logging.getLogger(__name__)

# Blocked IP ranges for SSRF protection
BLOCKED_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private
    ipaddress.ip_network("172.16.0.0/12"),      # Private
    ipaddress.ip_network("192.168.0.0/16"),     # Private
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / cloud metadata
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 private
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
]

def validate_url(url: str) -> str:
    """Validate URL for safety (SSRF protection).
    
    Raises ValueError if the URL is invalid or points to internal resources.
    """
    parsed = urlparse(str(url))

    # Only allow HTTP(S)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only HTTP and HTTPS are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a valid hostname.")

    # Block common internal hostnames
    blocked_hostnames = {"localhost", "0.0.0.0", "metadata.google.internal"}
    if hostname.lower() in blocked_hostnames:
        raise ValueError(f"URL hostname '{hostname}' is not allowed.")

    # Resolve and check IP
    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in resolved_ips:
            ip = ipaddress.ip_address(sockaddr[0])
            for blocked in BLOCKED_RANGES:
                if ip in blocked:
                    raise ValueError(f"URL resolves to a blocked IP range.")
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")

    # Length check
    if len(str(url)) > 2048:
        raise ValueError("URL is too long (max 2048 characters).")

    return str(url)


def create_job(db: Session, url: str, current_user: User) -> Job:
    # Validate URL for SSRF
    safe_url = validate_url(url)
    
    parsed = urlparse(safe_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    job = Job(
        source_url=safe_url,
        base_url=base_url,
        user_id=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job